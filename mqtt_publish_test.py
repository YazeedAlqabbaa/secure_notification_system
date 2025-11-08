import paho.mqtt.publish as publish
import json

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "yazeed/alerts/test"

data = {
    "source": "MQTT_Test_Device",
    "event_type": "door",
    "severity": "critical",
    "message": "🚨 MQTT test alert triggered!"
}

payload = json.dumps(data)

publish.single(MQTT_TOPIC, payload, hostname=MQTT_BROKER, port=MQTT_PORT)
print("MQTT test message sent!")