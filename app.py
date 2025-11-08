import os, sqlite3
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
from dotenv import load_dotenv
load_dotenv()
# تحميل المتغيرات من ملف .env
load_dotenv()

print("DBG TOKEN:", os.getenv("TELEGRAM_TOKEN"))
print("DBG CHAT_ID:", os.getenv("TELEGRAM_CHAT_ID"))


app = Flask(__name__)
import psycopg2

def get_conn():
    # اتصال بقاعدة بيانات PostgreSQL من Render
    db_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(db_url)

# دالة إرسال تنبيه إلى تيليجرام
def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram not configured")
        return

    # هنا نحدد رابط واجهة تيليجرام
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        resp = requests.post(url, data=payload, timeout=10)
        print("TG status:", resp.status_code, resp.text)
    except Exception as e:
        print("Error sending telegram message:", e)

@app.route('/')
def home():
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # دالة ترجع صفر بدل None لو ما فيه نتيجة
    def safe_count(query):
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0

    # الإحصائيات الأساسية
    total_alerts = safe_count("SELECT COUNT(*) FROM alerts")
    critical_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='critical'")
    high_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='high'")
    medium_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='medium'")
    low_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='low'")

    # آخر وقت تنبيه
    cursor.execute("SELECT created_at FROM alerts ORDER BY id DESC LIMIT 1")
    last_alert = cursor.fetchone()
    last_alert_time = last_alert[0] if last_alert else "No alerts yet"

    conn.close()

    # آخر تحديث
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # نرسل القيم كمصفوفة JSON للرسم البياني
    alerts_data = [low_alerts, medium_alerts, high_alerts, critical_alerts]

    return render_template(
        'home.html',
        total_alerts=total_alerts,
        critical_alerts=critical_alerts,
        last_alert_time=last_alert_time,
        last_update=last_update,
        alerts_data=alerts_data
    )

@app.route("/alerts")
def list_alerts():
    # نقرأ قيمة الفلتر من الرابط: ?severity=critical مثلاً
    sev = request.args.get("severity", "").lower()
    allowed = {"low", "medium", "high", "critical"}

    conn = get_conn()
    cur = conn.cursor()

    if sev in allowed:
        cur.execute(
            "SELECT id, source, event_type, severity, message, created_at FROM alerts WHERE LOWER(severity)=? ORDER BY id DESC LIMIT 50;",
            (sev,),
        )
    else:
        cur.execute(
            "SELECT id, source, event_type, severity, message, created_at FROM alerts ORDER BY id DESC LIMIT 50;"
        )

    rows = cur.fetchall()
    conn.close()
    return render_template("alerts.html", alerts=rows)

@app.route("/alerts/add", methods=["POST"])
def add_alert():
    # API key check (no hidden spaces)
    api_key = (request.headers.get("X-API-Key") or "").strip()
    expected_key = (os.getenv("API_KEY") or "").strip()

    # debug prints to see real values read by server
    print("DBG expected:", repr(expected_key))
    print("DBG sent    :", repr(api_key))

    if not expected_key or api_key != expected_key:
        return jsonify({"error": "Forbidden"}), 403

    # read JSON body
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400

    source = data.get("source", "manual")
    event_type = data.get("event_type", "test")
    severity = data.get("severity", "low")
    message = data.get("message", "hello")

    if severity.lower() not in {"low", "medium", "high", "critical"}:
        return jsonify({"error": "Invalid severity"}), 400

    # insert into DB
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (source, event_type, severity, message) VALUES (?, ?, ?, ?);",
        (source, event_type, severity, message),
    )
    conn.commit()
    conn.close()

    # notify telegram on critical/high
    if severity.lower() in {"high", "critical"}:
        send_telegram_alert(f"[{severity.upper()}] {source} — {message}")

    return jsonify({"status": "ok", "severity": severity, "message": message})
import csv
from flask import Response

@app.route("/alerts/export.csv")
def export_csv():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, source, event_type, severity, message, created_at FROM alerts ORDER BY id DESC;")
    rows = cur.fetchall()
    conn.close()

    def generate():
        data = csv.writer([])
    # نرجع ملف CSV بشكل مباشر بدون حفظه
    output = []
    output.append(["ID", "Source", "Event Type", "Severity", "Message", "Time"])
    for row in rows:
        output.append(row)
    csv_data = "\n".join([",".join(map(str, r)) for r in output])

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts.csv"},
    )
@app.route("/manual", methods=["GET", "POST"])
def manual_alert():
    if request.method == "POST":
        source = request.form.get("source")
        event_type = request.form.get("event_type")
        severity = request.form.get("severity")
        message = request.form.get("message")

        # حفظ البيانات في قاعدة البيانات
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO alerts (source, event_type, severity, message) VALUES (?, ?, ?, ?);",
            (source, event_type, severity, message),
        )
        conn.commit()
        conn.close()

        # إرسال تنبيه لتلقرام لو الخطورة عالية
        if severity.lower() in ("high", "critical"):
            send_telegram_alert(f"⚠️ [{severity.upper()}] {source}: {message}")

        return render_template("manual.html", message_sent=True)

    return render_template("manual.html", message_sent=False)
@app.route("/status.json")
def status_json():
    # حالة قاعدة البيانات + آخر تنبيه
    db_ok = False
    last_alert = None
    db_error = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT MAX(created_at) FROM alerts;")
        row = cur.fetchone()
        last_alert = row[0] if row and row[0] else None
        db_ok = True
    except Exception as e:
        db_error = str(e)
    finally:
        try:
            conn.close()
        except:
            pass

    # حالة تيليجرام (بدون إرسال رسالة)
    tg_status = "not_configured"
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
            tg_status = "ok" if (r.status_code == 200 and r.json().get("ok") is True) else f"http_{r.status_code}"
        except Exception:
            tg_status = "error"

    return jsonify({
        "db": {"ok": db_ok, "last_alert": last_alert, "error": db_error},
        "telegram": tg_status
    })
@app.route("/healthz")
def healthz():
    return {"status": "ok"}, 200
@app.route('/alerts/delete/<int:alert_id>', methods=['POST'])
def delete_alert(alert_id):
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('list_alerts'))
    except Exception as e:
        print("Error deleting alert:", e)
        return redirect(url_for('list_alerts'))


@app.route('/alerts/delete_all', methods=['POST'])
def delete_all_alerts():
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts")
        conn.commit()
        conn.close()
        return redirect(url_for('list_alerts'))
    except Exception as e:
        print("Error deleting all alerts:", e)
        return redirect(url_for('list_alerts'))
if __name__ == "__main__":
    app.run(debug=True)