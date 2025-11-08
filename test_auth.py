import requests, json

url = "http://127.0.0.1:5000/alerts/add"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "YazSecinfo"  # نفس القيمة اللي كتبتها في .env
}
data = {
    "source": "sensor_101",
    "event_type": "intrusion",
    "severity": "high",
    "message": "Unauthorized access detected"
}

r = requests.post(url, headers=headers, data=json.dumps(data))
print("Status Code:", r.status_code)
print("Response:", r.text)