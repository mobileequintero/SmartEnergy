import json
import joblib
import requests
import numpy as np
import os

MODEL_URL = "https://sireieiplus.s3.us-east-1.amazonaws.com/Models/model.pkl"
SCALER_URL = "https://sireieiplus.s3.us-east-1.amazonaws.com/Models/scaler.pkl"

MODEL_PATH = "/tmp/model.pkl"
SCALER_PATH = "/tmp/scaler.pkl"

model = None
scaler = None


def download_file(url, local_path):
    """Descarga archivos desde S3 (público o prefirmado)."""
    r = requests.get(url)
    r.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(r.content)


def load_artifacts():
    """Carga modelos desde /tmp o los descarga si no existen."""
    global model, scaler
    if not os.path.exists(MODEL_PATH):
        download_file(MODEL_URL, MODEL_PATH)
    if not os.path.exists(SCALER_PATH):
        download_file(SCALER_URL, SCALER_PATH)
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)


def parse_input(event):
    """Normaliza el formato de entrada aceptando múltiples tipos."""
    # Si viene en string, parsea JSON
    if isinstance(event, str):
        try:
            event = json.loads(event)
        except Exception:
            raise ValueError("No se pudo decodificar el JSON")

    # Caso 1: formato directo con 'features'
    if isinstance(event, dict) and "features" in event:
        return np.array(event["features"]).reshape(1, -1)

    # Caso 2: formato con 'records'
    if isinstance(event, dict) and "records" in event:
        if len(event["records"]) == 0:
            raise ValueError("El campo 'records' está vacío.")
        # Tomamos el primer registro
        record = list(event["records"][0].values())
        return np.array(record).reshape(1, -1)

    # Caso 3: arreglo plano
    if isinstance(event, list):
        return np.array(event).reshape(1, -1)

    # Ninguno de los anteriores
    raise ValueError(
        "Formato inválido. Usa {'features': [...]}, {'records': [{...}]} o un array plano."
    )


def lambda_handler(event, context):
    try:
        global model, scaler
        if model is None or scaler is None:
            load_artifacts()

        X = parse_input(event)
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)
        prob = (
            model.predict_proba(X_scaled)[0]
            if hasattr(model, "predict_proba")
            else [None, None]
        )

        result = {
            "label": int(pred[0]),
            "prob_normal": float(prob[0]) if prob[0] is not None else None,
            "prob_anormal": float(prob[1]) if prob[1] is not None else None,
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "results": [result]}),
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "ok": False,
                    "error": str(e),
                }
            ),
        }
