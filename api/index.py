from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

app = FastAPI()

BASE_URL = "https://tms-logistics.tfg.co.th/tms-api/api/tripHeader/517bf823-324c-4c0a-923d-2fd9e89ad7fb/pages"
PAGE_SIZE = 50

# Get token from Render environment variable
AUTH_TOKEN = os.getenv("TMS_AUTH_TOKEN")

HEADERS = {
    "Authorization": AUTH_TOKEN
}

# In-memory cache
cached_data = None
last_fetch_time = None

def fetch_data_from_tms():
    all_results = []
    page = 1

    while True:
        params = {
            "page": page,
            "pageSize": PAGE_SIZE,
            "filters": ""
        }
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        data = response.json()
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        page += 1
        if page > data.get("pageCount", 1):
            break

    df = pd.DataFrame(all_results)[[
        "tripNo", "mainLicensePlate", "statusName",
        "transporterName", "newDate", "canceledBy", "canceledDate"
    ]]
    return df.to_dict(orient="records")

@app.get("/")
def get_trip_data():
    global cached_data, last_fetch_time

    if not last_fetch_time or (datetime.utcnow() - last_fetch_time > timedelta(minutes=10)):
        cached_data = fetch_data_from_tms()
        last_fetch_time = datetime.utcnow()

    return JSONResponse(content=cached_data)
