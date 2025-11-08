import requests

url = "http://127.0.0.1:5000/alerts/add"

data = {
    "source": "lab",
    "event_type": "unauthorized",
    "severity": "critical",
    "message": "🚨 Telegram test from Flask"
}


response = requests.post(url, json=data)
print("Status Code:", response.status_code)
print("Response:", response.json())
