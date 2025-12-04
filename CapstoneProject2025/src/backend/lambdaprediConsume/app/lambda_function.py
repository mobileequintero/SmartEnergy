import json
import joblib
import boto3
import numpy as np
import os
from botocore.exceptions import ClientError

# === S3 Model Locations ===
BUCKET_NAME = "sireieiplus"
MODEL_KEY = "Models/occupancy_model.pkl"
SCALER_KEY = "Models/occupancy_scaler.pkl"

# === Local cache paths ===
MODEL_PATH = "/tmp/occupancy_model.pkl"
SCALER_PATH = "/tmp/occupancy_scaler.pkl"

# === Global variables to avoid reloading ===
model = None
scaler = None

def download_from_s3(bucket, key, local_path):
    """Download a file from S3 if it does not exist locally."""
    s3 = boto3.client("s3")
    try:
        print(f"📦 Downloading {key} from S3 bucket {bucket}...")
        s3.download_file(bucket, key, local_path)
        print(f"✅ Downloaded and saved to {local_path}")
    except ClientError as e:
        raise RuntimeError(f"Error downloading {key} from S3: {e}")

def load_artifacts():
    """Load model and scaler from S3 or local cache."""
    global model, scaler
    if not os.path.exists(MODEL_PATH):
        download_from_s3(BUCKET_NAME, MODEL_KEY, MODEL_PATH)
    if not os.path.exists(SCALER_PATH):
        download_from_s3(BUCKET_NAME, SCALER_KEY, SCALER_PATH)

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("✅ Model and scaler loaded successfully.")

def parse_input(event):
    """Parse JSON input and extract features."""
    if isinstance(event, str):
        event = json.loads(event)

    if isinstance(event, dict) and "features" in event:
        return np.array(event["features"]).reshape(1, -1)

    if isinstance(event, list):
        return np.array(event).reshape(1, -1)

    raise ValueError("Invalid input format. Use {'features': [...]}")

def lambda_handler(event, context):
    """AWS Lambda handler."""
    try:
        global model, scaler
        if model is None or scaler is None:
            load_artifacts()

        X = parse_input(event)
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)
        proba = model.predict_proba(X_scaled)[0]

        result = {
            "label": int(pred[0]),
            "label_name": "Occupied" if int(pred[0]) == 1 else "Unoccupied",
            "prob_unoccupied": float(proba[0]),
            "prob_occupied": float(proba[1])
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "results": [result]})
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": str(e)})
        }
