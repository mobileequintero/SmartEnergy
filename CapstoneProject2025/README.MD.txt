# SmartEnergy IoT & AI System
Fall 2025 – Capstone Project ITAI 2277
Developer: Leah

## ?? Overview
SmartEnergy is an end-to-end IoT + AI platform that collects real-time sensor data, processes events through AWS Lambda & API Gateway, stores analytics in AWS RDS/MySQL, and generates energy predictions, occupancy insights, and anomaly alerts.
This project integrates multiple technologies from the AI & Robotics program, including:
* IoT sensor ingestion
* Machine Learning for predictions
* Energy anomaly detection
* Occupancy detection (presence + lux + consumption)
* Web dashboard visualization
* Cloud deployment (AWS)
* Automation rules & alerting
This system is fully functional and ready to be extended for real-world home and business energy automation.

## ?? Project Goals
* Create a scalable IoT ingestion pipeline
* Predict energy consumption and equipment failures
* Detect room occupancy using sensor fusion
* Provide a modern interactive dashboard
* Deploy a cloud-native serverless architecture
* Deliver an industry-quality AI solution

## ?? Architecture Overview
IoT Devices (Shelly, Sensors, Temperature, Lux, Presence ? JSON)
           ?
           ?
AWS API Gateway ? AWS Lambda ? MySQL (RDS)
           ?
           ?
   ML Engine (Python, Scikit-learn)
           ?
           ?
Interactive Dashboard (HTML/JS/CSS)
Key components:
* IoT ingestion layer: multiple endpoints for sensor categories
* AWS Lambda: validation, processing, routing
* Machine Learning: predictive analytics
* Dashboard: real-time visualization
* Database: storage of raw & processed features
* REST API: unified access to system capabilities

## ?? Tech Stack
LayerTechnologyCloudAWS Lambda, API Gateway, S3, RDSDatabaseMySQL / Amazon AuroraBackendPython 3.12FrontendHTML / Bootstrap / JavaScriptMLScikit-Learn, Pandas, NumpyVisualizationHTML Dashboard + Chart.jsAutomationAWS EventBridge SchedulerMonitoringCloudWatch Logs
## ?? API Documentation
Base URL (DEV):
https://luvhyijxnd.execute-api.us-east-1.amazonaws.com/DEV
Endpoints
EndpointMethodDescription/InventoryPOSTRegister/update device metadata/IoTDevicePOSTGeneric IoT event ingestion/luxPOSTLight sensor (Lux) telemetry/presencePOSTPresence/occupancy sensor events/temperaturePOSTTemperature/humidity telemetryExample Request (Lux):
{
  "device_id": "lux01",
  "ts": "2025-09-17 12:34:56",
  "lux": 300.5
}
Example Response:
{
  "ok": true,
  "message": "Lux data saved"
}
Full API Documentation is included in /docs/API_Documentation.pdf.

## ?? Machine Learning Component
Models Included
* Energy Failure Prediction Model
* Energy Cost Prediction Model
* Occupancy Detection Model
Files
* models/model.pkl
* models/model_training.ipynb
Features Used
* Power consumption (W)
* Voltage (V)
* Room presence (boolean)
* Lux levels
* Temperature & humidity
* Historical timeseries data
Output Examples
{
  "prediction": "normal",
  "risk_score": 0.12,
  "recommendation": "No action required"
}

## ?? Dashboard
Located in:
/src/frontend
Main files:
* index.html
* dashboard.js
* styles.css
Includes:
* Real-time sensor table
* Energy charts
* Occupancy states
* ML predictions (normal vs abnormal)
* Manual JSON test editor

## ?? Repository Structure
CapstoneSmartEnergy/
?
??? README.md
??? LICENSE
?
??? /docs
?   ??? Presentation.pdf
?   ??? Presentation.pptx
?   ??? API_Documentation.pdf
?   ??? Architecture.png
?   ??? Flowchart.png
?
??? /src
?   ??? /backend
?   ?   ??? lambda_handler.py
?   ?   ??? requirements.txt
?   ?   ??? config.py
?   ?   ??? /models
?   ?   ?   ??? model.pkl
?   ?   ?   ??? model_training.ipynb
?   ?   ??? /utils
?   ?   ?   ??? helpers.py
?   ?   ??? /tests
?   ??? /frontend
?       ??? index.html
?       ??? dashboard.js
?       ??? styles.css
?       ??? assets/
?
??? /deployment
?   ??? Dockerfile
?   ??? docker-compose.yml
?   ??? serverless.yml
?
??? /data
    ??? raw_data.csv
    ??? cleaned_data.csv
    ??? features.csv

## ?? How to Install & Run
1. Clone the repository
git clone https://github.com/<your-user>/SmartEnergy.git
cd SmartEnergy/src/backend
2. Install dependencies
pip install -r requirements.txt
3. Run local backend
python lambda_handler.py
4. Open the Dashboard
Simply open:
src/frontend/index.html

## ?? Testing (Postman / Curl)
Example POST:
POST /DEV/lux
curl -X POST "https://luvhyijxnd.execute-api.us-east-1.amazonaws.com/DEV/lux" \
-H "Content-Type: application/json" \
-d '{"device_id":"lux01","ts":"2025-09-17 12:34:56","lux":350}'
Expected:
{"ok": true, "message": "Lux data saved"}

## ??? Error Codes
CodeMeaning400Missing or invalid parameters500Lambda internal error200Successful ingestion
## ?? Developer
Leah
AI & Robotics – Associate Degree
Houston Community College – ITAI 2277
Fall 2025

## ?? License
MIT License — free to use and expand.

## ?? Final Notes
This Capstone demonstrates end-to-end AI/ML, cloud architecture, IoT integration, dashboards, and predictive analytics.
It is designed to meet industry standards and is deployable in any real environment (home, Airbnb, small business).

