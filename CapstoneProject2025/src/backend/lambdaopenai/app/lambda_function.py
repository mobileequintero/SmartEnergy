import json
import pymysql
import os
import boto3
import openai

# -------------------------------------------------
# 1️⃣ OBTENER CREDENCIALES DE LA BASE DE DATOS
# -------------------------------------------------
def get_db_credentials():
    secret_name = os.environ.get("DB_SECRET_NAME")
    region_name = os.environ.get("AWS_REGION", "us-east-1")

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    secret_value = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value["SecretString"])
    return secret["host"], secret["username"], secret["password"], secret["dbname"]

# -------------------------------------------------
# 2️⃣ CONFIGURAR OPENAI
# -------------------------------------------------
openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")

# -------------------------------------------------
# 3️⃣ DEFINIR EL ESQUEMA (estructura de tus tablas)
# -------------------------------------------------
SCHEMA = {
    "schema": "Smart",
    "tables": [
        {
            "name": "network_inventory",
            "columns": {
                "device_id": "INT PRIMARY KEY",
                "hostname": "VARCHAR(128)",
                "vendor": "VARCHAR(64)",
                "model": "VARCHAR(64)",
                "device_type": "VARCHAR(64)",
                "site": "INT",
                "area": "INT",
                "mgmt_ip": "VARCHAR(45)",
                "mac_address": "VARCHAR(32)",
                "os_version": "VARCHAR(64)",
                "serial_number": "VARCHAR(64)",
                "installed_at": "DATETIME",
                "status": "ENUM('active','maintenance','inactive')",
                "outlet_id": "INT"
            }
        },
        {
            "name": "outlet_specs",
            "columns": {
                "outlet_id": "INT PRIMARY KEY",
                "is_110v": "TINYINT",
                "is_220v": "TINYINT",
                "braker_amp": "INT",
                "max_watts": "INT"
            }
        },
        {
            "name": "raw_shelly_power",
            "columns": {
                "device_id": "INT",
                "ts": "TIMESTAMP",
                "power_w": "DOUBLE",
                "voltage_v": "DOUBLE",
                "current_a": "DOUBLE",
                "relay_on": "TINYINT",
                "energy_wh_acc": "BIGINT"
            }
        },
        {
            "name": "T_Area",
            "columns": {
                "Area_id": "INT PRIMARY KEY",
                "Area": "VARCHAR(45)"
            }
        },
        {
            "name": "T_Site",
            "columns": {
                "Site_id": "INT PRIMARY KEY",
                "Site": "VARCHAR(45)"
            }
        }
    ]
}

# -------------------------------------------------
# 4️⃣ FUNCIÓN PRINCIPAL DE LAMBDA
# -------------------------------------------------
def lambda_handler(event, context):
    try:
        # --- Leer el cuerpo del request desde API Gateway ---
        body = json.loads(event.get("body", "{}"))
        user_question = body.get("question", "").strip()

        if not user_question:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing question"})}

        # --- Construir el prompt para OpenAI ---
        prompt = f"""
        You are an SQL assistant for an IoT energy monitoring system.
        The database schema (simplified JSON) is as follows:
        {json.dumps(SCHEMA, indent=2)}

        Based on this schema, generate a safe MySQL SELECT query that answers:
        "{user_question}"

        Rules:
        - Use INNER JOINs only if necessary.
        - Only use SELECT statements (no modifications).
        - Limit results to 10 rows if unspecified.
        - Output only the SQL query.
        """

        # --- Llamar a OpenAI ---
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        sql_query = response.choices[0].message["content"].strip()

        # --- Validar que sea segura (solo SELECT) ---
        dangerous = ["update", "delete", "insert", "drop", "alter", "truncate"]
        if not sql_query.lower().startswith("select") or any(w in sql_query.lower() for w in dangerous):
            raise ValueError("Unsafe or invalid query generated")

        # --- Conexión a la base de datos ---
        host, user, password, dbname = get_db_credentials()
        conn = pymysql.connect(host=host, user=user, password=password, database=dbname)

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql_query)
            result = cursor.fetchall()

        conn.close()

        # --- Devolver respuesta JSON al API Gateway ---
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "generated_sql": sql_query,
                "result": result
            }, default=str)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
