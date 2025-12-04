import json
import os
import sys
import traceback
import warnings
from typing import List, Dict, Any
from datetime import datetime, timezone

# Silencia warning de versiones distintas al deserializar modelos
try:
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except Exception:
    pass

# --- Configuración por ENV ---
S3_BUCKET         = os.getenv("MODEL_S3_BUCKET", "sireieiplus")
S3_REGION         = os.getenv("MODEL_S3_REGION", "us-east-1")
S3_MODEL_KEY      = os.getenv("MODEL_S3_KEY", "failure_predictor_rf.pkl")
S3_SCALER_KEY     = os.getenv("SCALER_S3_KEY", "failure_predictor_scaler.pkl")
S3_FEATURES_KEY   = os.getenv("FEATURES_S3_KEY", "final_features.pkl")  # 👈 lista de columnas
NUMPY_MIN_VER     = os.getenv("NUMPY_MIN_VERSION", "1.26")  # opcional

# Rutas locales (cache en /tmp)
LOCAL_MODEL_PATH    = "/tmp/failure_predictor_rf.pkl"
LOCAL_SCALER_PATH   = "/tmp/failure_predictor_scaler.pkl"
LOCAL_FEATURES_PATH = "/tmp/final_features.pkl"  # 👈 aquí guardamos la lista de features

# --- Orden de features que llegan en tu payload (one-hot y numéricas) ---
FEATURES = [
    "power_w",
    "voltage_v",
    "current_a",
    "relay_on",
    "energy_wh_acc",
    "presence",
    "presence_confidence",
    "temp_c_avg",
    "Bracker_amp",
    "max_watts",
    "power_rate",
    "hour",
    "is_daytime",
    "weekday",
    "voltage_type",
    "area_1",
    "area_2",
    "area_3",
    "device_type_1",
    "device_type_2",
    "device_type_3",
    "device_type_4",
    "device_type_5",
    "device_type_6",
    "device_type_7",
    "device_type_8",
]

# Alias → nombre real
FEATURE_ALIASES = {
    "Breaker_amp": "Bracker_amp",
    "breaker_amp": "Bracker_amp",
}

LABEL_NAMES = {0: "normal", 1: "anormal"}

# Caches globales
_model = None
_scaler = None
_boto3 = None
_expected_cols = None  # 👈 se llena desde final_features.pkl o feature_names_in_

# ----------------- Utilidades -----------------
def _ensure_numpy_ok():
    """
    NumPy válido: aceptamos /var/task, /opt/python, /var/lang.
    También valida versión mínima mayor.menor.
    """
    try:
        import numpy as _np, os
        np_file = os.path.abspath(getattr(_np, "__file__", ""))
        allowed_roots = ("/var/task", "/opt/python", "/var/lang")
        if not np_file.startswith(allowed_roots):
            raise ImportError(
                f"NumPy se está importando desde una ruta inesperada: {np_file!r}. "
                "Se esperaban prefijos /var/task, /opt/python o /var/lang."
            )
        def _parse_ver(v: str):
            try:
                parts = v.split(".")
                return (int(parts[0]), int(parts[1]))
            except Exception:
                return (0, 0)
        if _parse_ver(_np.__version__) < _parse_ver(NUMPY_MIN_VER):
            raise ImportError(f"NumPy { _np.__version__ } < requerido { NUMPY_MIN_VER }.")
    except Exception as e:
        raise ImportError(f"Error al validar NumPy: {e}.") from e


def _get_boto3():
    global _boto3
    if _boto3 is None:
        import boto3
        _boto3 = boto3
    return _boto3


def _download_file_if_needed(s3_key: str, local_path: str):
    if not s3_key:
        return
    need = (not os.path.isfile(local_path)) or os.path.getsize(local_path) == 0
    if need:
        b3 = _get_boto3()
        client = b3.client("s3", region_name=S3_REGION)
        client.download_file(S3_BUCKET, s3_key, local_path)


def _download_if_needed():
    """Descarga modelo, scaler y features a /tmp si no existen."""
    _download_file_if_needed(S3_MODEL_KEY, LOCAL_MODEL_PATH)
    _download_file_if_needed(S3_SCALER_KEY, LOCAL_SCALER_PATH)
    _download_file_if_needed(S3_FEATURES_KEY, LOCAL_FEATURES_PATH)
    return LOCAL_MODEL_PATH, LOCAL_SCALER_PATH, LOCAL_FEATURES_PATH


def _ensure_loaded():
    """Carga modelo, scaler y expected_cols (desde final_features.pkl si existe)."""
    _ensure_numpy_ok()
    global _model, _scaler, _expected_cols
    if _model is not None and _scaler is not None:
        return

    from joblib import load

    model_p, scaler_p, feats_p = _download_if_needed()
    _model = load(model_p)
    _scaler = load(scaler_p)

    # expected_cols desde final_features.pkl si existe
    if os.path.isfile(feats_p) and os.path.getsize(feats_p) > 0:
        try:
            vals = load(feats_p)  # lista de strings (o pandas Index)
            if hasattr(vals, "tolist"):
                vals = vals.tolist()
            if isinstance(vals, (list, tuple)) and all(isinstance(x, str) for x in vals):
                _expected_cols = list(vals)
        except Exception:
            _expected_cols = None

    # fallback a metadatos del scaler/modelo
    if _expected_cols is None:
        if hasattr(_scaler, "feature_names_in_"):
            _expected_cols = list(_scaler.feature_names_in_)
        elif hasattr(_model, "feature_names_in_"):
            _expected_cols = list(_model.feature_names_in_)

    # Evitar multiprocessing en Lambda
    try:
        if hasattr(_model, "set_params") and "n_jobs" in _model.get_params():
            _model.set_params(n_jobs=1)
    except Exception:
        pass


def _normalize_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(d)
    for alias, real in FEATURE_ALIASES.items():
        if alias in out and real not in out:
            out[real] = out[alias]
    return out


def _to_float(value: Any, key: str) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value is None:
        raise ValueError(f"Feature '{key}' no puede ser None")
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "on"}:
            return 1.0
        if v in {"false", "no", "off"}:
            return 0.0
        try:
            return float(value)
        except Exception:
            pass
    try:
        return float(value)
    except Exception:
        raise ValueError(f"Feature '{key}' no es numérico convertible: {value!r}")


# ---------- Backfill / derivación de columnas faltantes ----------
def _derive_month(event: Any) -> int:
    """Month del evento (timestamp ISO/epoch) o del reloj UTC."""
    ts = None
    if isinstance(event, dict):
        ts = event.get("timestamp")
        if isinstance(event.get("body"), str):
            try:
                body = json.loads(event["body"])
                ts = body.get("timestamp", ts)
            except Exception:
                pass
    if isinstance(ts, (int, float)):
        try:
            return int(datetime.fromtimestamp(float(ts), tz=timezone.utc).month)
        except Exception:
            pass
    if isinstance(ts, str):
        try:
            return int(datetime.fromisoformat(ts.replace("Z","+00:00")).astimezone(timezone.utc).month)
        except Exception:
            pass
    return int(datetime.now(timezone.utc).month)


def _argmax_onehot(d: Dict[str, Any], keys: List[str]) -> int:
    mx, idx = -float("inf"), 0
    for i, k in enumerate(keys, start=1):
        try:
            v = float(d.get(k, 0) or 0)
        except Exception:
            v = 0.0
        if v > mx:
            mx, idx = v, i
    return idx if mx > 0 else 0


def _backfill_expected_columns(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deriva columnas que el scaler/modelo espera si faltan en el payload:
    Month, area, device_type, illuminance_lux, is_110v, is_220v, is_weekend, outlet_id.
    """
    r = dict(row)
    if "Month" not in r:
        r["Month"] = _derive_month(row)
    if "area" not in r:
        r["area"] = _argmax_onehot(r, ["area_1", "area_2", "area_3"])
    if "device_type" not in r:
        r["device_type"] = _argmax_onehot(r, [
            "device_type_1","device_type_2","device_type_3","device_type_4",
            "device_type_5","device_type_6","device_type_7","device_type_8",
        ])
    if "illuminance_lux" not in r:
        r["illuminance_lux"] = 0.0
    try:
        vv = float(r.get("voltage_v", 0) or 0)
    except Exception:
        vv = 0.0
    if "is_110v" not in r:
        r["is_110v"] = 1 if 100 <= vv < 130 else 0
    if "is_220v" not in r:
        r["is_220v"] = 1 if 200 <= vv < 250 else 0
    if "is_weekend" not in r:
        try:
            wd = int(r.get("weekday", 0))
        except Exception:
            wd = 0
        r["is_weekend"] = 1 if wd >= 5 else 0
    if "outlet_id" not in r:
        r["outlet_id"] = 0
    return r


# ---------- Predicción ----------
def _predict_batch(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza, deriva columnas faltantes si el scaler/modelo las espera,
    alinea orden y predice. Usa final_features.pkl si está disponible.
    """
    import numpy as np
    import pandas as pd

    _ensure_loaded()

    expected_cols = _expected_cols  # puede venir de final_features.pkl
    if expected_cols is None:
        if hasattr(_scaler, "feature_names_in_"):
            expected_cols = list(_scaler.feature_names_in_)
        elif hasattr(_model, "feature_names_in_"):
            expected_cols = list(_model.feature_names_in_)

    normalized = []
    for raw in rows:
        r = _normalize_keys(raw)
        if expected_cols is not None:
            r = _backfill_expected_columns(r)
            faltan = [c for c in expected_cols if c not in r]
            if faltan:
                raise ValueError(f"El scaler/modelo espera columnas que no llegaron: {sorted(faltan)}")
            normalized.append({k: _to_float(r[k], k) for k in expected_cols})
        else:
            missing = [k for k in FEATURES if k not in r]
            if missing:
                raise ValueError(f"Faltan features requeridos: {missing}")
            normalized.append({k: _to_float(r[k], k) for k in FEATURES})

    df = pd.DataFrame(normalized, columns=expected_cols if expected_cols is not None else FEATURES)

    X = df.values
    Xs = X
    if _scaler is not None:
        try:
            Xs = _scaler.transform(X)
        except Exception as e:
            raise RuntimeError(f"Error al escalar features: {e}")

    try:
        preds = _model.predict(Xs).tolist()
    except Exception as e:
        raise RuntimeError(f"Error en predict(): {e}")

    if hasattr(_model, "predict_proba"):
        try:
            probs = _model.predict_proba(Xs)
        except Exception:
            return [{"label": int(y), "label_name": LABEL_NAMES.get(int(y), str(y))} for y in preds]
        classes = getattr(_model, "classes_", None)
        if classes is not None and len(classes) == 2 and 1 in set(classes):
            idx1 = int((classes == 1).nonzero()[0][0]) if hasattr(classes, "nonzero") else list(classes).index(1)
            p1 = probs[:, idx1]
            p0 = 1.0 - p1
            return [
                {
                    "label": int(y),
                    "label_name": LABEL_NAMES.get(int(y), str(y)),
                    "prob_normal": float(pn),
                    "prob_anormal": float(pa),
                }
                for y, pn, pa in zip(preds, p0.tolist(), p1.tolist())
            ]

    return [{"label": int(y), "label_name": LABEL_NAMES.get(int(y), str(y))} for y in preds]


# ---------- Parseo de evento ----------
def _parse_event(event) -> List[Dict[str, Any]]:
    """
    Soporta:
      - API Gateway: {"body": "...json..."} con o sin "timestamp"
      - JSON plano de features
      - {"features": {...}}  (single)
      - {"records": [{...}, {...}]}  (batch)
    """
    if isinstance(event, dict) and "body" in event and isinstance(event["body"], str):
        try:
            body = json.loads(event["body"])
            return _parse_event(body)
        except Exception:
            pass
    if isinstance(event, str):
        event = json.loads(event)
    if isinstance(event, dict):
        if "features" in event and isinstance(event["features"], dict):
            return [event["features"]]
        if "records" in event and isinstance(event["records"], list):
            if not all(isinstance(x, dict) for x in event["records"]):
                raise ValueError("Todos los elementos de 'records' deben ser objetos con features.")
            return event["records"]
        if any(k in event for k in FEATURES) or any(k in event for k in FEATURE_ALIASES.keys()):
            return [event]
    raise ValueError("Formato inválido. Usa {'features': {...}} o {'records': [{...}]} o JSON plano de features.")


# ---------- Handler ----------
def lambda_handler(event, context):
    try:
        rows = _parse_event(event)
        results = _predict_batch(rows)
        body = {"ok": True, "count": len(results), "results": results}
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body),
        }
    except Exception as e:
        err = {
            "ok": False,
            "error": str(e),
            "trace": traceback.format_exc(),
            "python": sys.version,
            "sys_path_sample": sys.path[:6],
        }
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(err),
        }
