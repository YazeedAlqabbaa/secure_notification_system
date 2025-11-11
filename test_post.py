import requests

# عنوان السيرفر المحلي
url = "http://127.0.0.1:5000/alerts/add"

# بيانات اختبار فيها كلمات خطيرة
data = {
    "source": "test_system",
    "event_type": "login",
    "message": "Unauthorized access attempt detected"
}

# أرسل الطلب كـ JSON
r = requests.post(url, json=data)

print("Status:", r.status_code)
print("Response:", r.text)