import os
import requests
from dotenv import load_dotenv

# تحميل القيم من .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TOKEN or not CHAT_ID:
        print("❌ Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload, timeout=10)
        print("✅ Sent:", r.json())
    except Exception as e:
        print("❌ Error:", e)

# نجرب إرسال رسالة
send_telegram_alert("Hello from Secure Notification System 🚀")
