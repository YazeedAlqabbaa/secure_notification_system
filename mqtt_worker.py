import os, json, requests
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "test.mosquitto.org")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "yazeed/alerts/#")
MQTT_USER = os.getenv("MQTT_USER")  # اختياري
MQTT_PASS = os.getenv("MQTT_PASS")  # اختياري

API_KEY = (os.getenv("API_KEY") or "").strip()
FLASK_URL = "http://127.0.0.1:5000/alerts/add"

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8").strip()
        print(f"[MQTT] {msg.topic} -> {payload}")

        data = json.loads(payload)  # لازم يكون JSON
        # شكل متوقع: {"source":"dev1","event_type":"intrusion","severity":"high","message":"Door forced"}

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        r = requests.post(FLASK_URL, headers=headers, data=json.dumps(data), timeout=10)
        print("POST ->", r.status_code, r.text)
    except Exception as e:
        print("Error handling MQTT msg:", e)

def main():
    client = mqtt.Client()
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: API_KEY missing. Set it in .env")
    else:
        main()