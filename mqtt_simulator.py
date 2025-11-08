import time
import requests
import json
import random

API_KEY = "YazSecinfo"
URL = "http://127.0.0.1:5000/alerts/add"

devices = [
    {"id": "Temp_Sensor_01", "type": "temperature"},
    {"id": "Motion_Sensor_02", "type": "motion"},
    {"id": "Door_Lock_01", "type": "door"},
    {"id": "Smoke_Detector_01", "type": "smoke"}
]

def generate_alert(device):
    event_type = device["type"]

    if event_type == "temperature":
        temp = random.randint(25, 95)
        severity = "critical" if temp > 70 else "medium" if temp > 50 else "low"
        message = f"Temperature anomaly detected: {temp}°C"

    elif event_type == "motion":
        motion_detected = random.choice([True, False])
        severity = "high" if motion_detected else "low"
        message = "Motion detected in restricted area!" if motion_detected else "No motion detected."

    elif event_type == "door":
        door_opened = random.choice([True, False])
        severity = "medium" if door_opened else "low"
        message = "Unauthorized door access detected!" if door_opened else "Door status normal."

    elif event_type == "smoke":
        smoke_level = random.randint(0, 100)
        severity = "critical" if smoke_level > 70 else "medium" if smoke_level > 40 else "low"
        message = f"Smoke level: {smoke_level}%"

    else:
        severity = "low"
        message = "Unknown event."

    return {
        "source": device["id"],
        "event_type": event_type,
        "severity": severity,
        "message": message
    }

def send_fake_alert(data):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    r = requests.post(URL, headers=headers, data=json.dumps(data))
    print("Status:", r.status_code, "|", data["source"], "-", data["message"])

if __name__ == "__main__":
    print("🚀 Starting Smart Building Security Simulation...\n")
    while True:
        device = random.choice(devices)
        alert = generate_alert(device)
        send_fake_alert(alert)
        time.sleep(random.randint(5, 12))  # فاصل عشوائي بين 5 إلى 12 ثانية