import os
import sqlite3
import requests
import bcrypt
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, session
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (لو موجود)
load_dotenv()
app = Flask(__name__)
app.secret_key = "supersecretkey"  # غيّرها لاحقاً لقيمة عشوائية قوية

# تسجيل الخروج (Logout)
@app.route("/logout")
def logout():
    session.pop("user_id", None)  # ← حذف الجلسة الحقيقية الجديدة
    return redirect(url_for("login"))

# ------------------------------------------
# 🔹 دالة إنشاء اتصال بقاعدة البيانات المحلية app.db
# ------------------------------------------
def get_conn():
    return sqlite3.connect("app.db")

# ------------------------------------------
# 🔹 دالة إرسال تنبيه إلى Telegram
# ------------------------------------------
def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ لم يتم إعداد Telegram.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        resp = requests.post(url, data=payload, timeout=10)
        print("📤 تم إرسال التنبيه إلى Telegram:", resp.status_code)
    except Exception as e:
        print("❌ خطأ أثناء الإرسال إلى Telegram:", e)

# ------------------------------------------
# ------------------------------------------
# 🔹 دالة لتصنيف مستوى الخطورة تلقائيًا حسب الرسالة
# ------------------------------------------
def classify_event(message):
    msg = message.lower()
    if "unauthorized" in msg or "failed login" in msg or "attack" in msg:
        return "critical"
    elif "warning" in msg or "error" in msg or "timeout" in msg:
        return "high"
    elif "disconnect" in msg or "delay" in msg:
        return "medium"
    else:
        return "low"
    
app.secret_key = "supersecretkey"  # غيرها لاحقاً لقيمة عشوائية

def get_conn():
    return sqlite3.connect("app.db")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')



@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_conn()
        cursor = conn.cursor()

        # التحقق إذا المستخدم موجود مسبقاً
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            error = "Username already exists."
        else:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))

        conn.close()
    return render_template("register.html", error=error)

# 🔹 الصفحة الرئيسية (Dashboard)
# ------------------------------------------

@app.route('/')
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_conn()
    cursor = conn.cursor()

    def safe_count(query, params=None):
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0

    # الإحصائيات الخاصة بالمستخدم فقط
    total_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE user_id=?", (user_id,))
    critical_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='critical' AND user_id=?", (user_id,))
    high_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='high' AND user_id=?", (user_id,))
    medium_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='medium' AND user_id=?", (user_id,))
    low_alerts = safe_count("SELECT COUNT(*) FROM alerts WHERE severity='low' AND user_id=?", (user_id,))

    # آخر تنبيه حرج للمستخدم فقط
    cursor.execute(
        "SELECT created_at FROM alerts WHERE severity='critical' AND user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    last_alert = cursor.fetchone()

    if last_alert:
        dt = datetime.strptime(str(last_alert[0]), "%Y-%m-%d %H:%M:%S.%f")
        last_alert_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_alert_time = "No recent critical alerts"

    conn.close()

    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts_data = [low_alerts, medium_alerts, high_alerts, critical_alerts]

    return render_template(
        'home.html',
        total_alerts=total_alerts,
        critical_alerts=critical_alerts,
        last_alert_time=last_alert_time,
        last_update=last_update,
        alerts_data=alerts_data
    )



# ------------------------------------------
# 🔹 عرض كل التنبيهات (صفحة Alerts)
# ------------------------------------------
@app.route("/alerts")
def list_alerts():
    if "user_id" not in session:
        return redirect(url_for("login"))
    from datetime import datetime
    import pytz

    user_id = session["user_id"]
    sev = request.args.get("severity", "").lower()
    allowed = {"low", "medium", "high", "critical"}

    conn = get_conn()
    cur = conn.cursor()

    if sev in allowed:
        cur.execute(
            "SELECT id, source, event_type, severity, message, created_at FROM alerts WHERE LOWER(severity)=? AND user_id=? ORDER BY id DESC;",
            (sev, user_id),
        )
    else:
        cur.execute(
            "SELECT id, source, event_type, severity, message, created_at FROM alerts WHERE user_id=? ORDER BY id DESC;",
            (user_id,),
        )

    rows = cur.fetchall()
    conn.close()

    # 🔹 تعديل الوقت ليكون بتوقيت السعودية بدون النانو ثانية
    tz_riyadh = pytz.timezone('Asia/Riyadh')
    # 🔹 حذف النانو ثانية فقط بدون تعديل التوقيت
    new_rows = []
    for row in rows:
        row = list(row)
        try:
            row[5] = str(row[5]).split('.')[0]  # يشيل النانو ثانية فقط
        except:
            row[5] = str(row[5])
        new_rows.append(tuple(row))

    # 🔹 عرض النتائج في صفحة HTML
    return render_template("alerts.html", alerts=new_rows)


# ------------------------------------------
# 🔹 إضافة تنبيه جديد عبر API (محاكاة أو Telegram)
# ------------------------------------------
@app.route("/alerts/add", methods=["POST"])
def add_alert():
    if "user_id" not in session:
        return redirect(url_for("login"))
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400

    source = data.get("source", "manual")
    event_type = data.get("event_type", "test")
    message = data.get("message", "hello")

    severity = classify_event(message)

    if severity.lower() not in {"low", "medium", "high", "critical"}:
        return jsonify({"error": "Invalid severity"}), 400

    user_id = session["user_id"]   # ← إضافة user_id

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (source, event_type, severity, message, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?);",
        (source, event_type, severity, message, datetime.now(), user_id),
    )
    conn.commit()
    conn.close()

    if severity.lower() in {"high", "critical"}:
        send_telegram_alert(f"[{severity.upper()}] {source} — {message}")

    return jsonify({"status": "ok", "severity": severity, "message": message})

# ------------------------------------------
# 🔹 إرسال تنبيه يدوي (Manual Alert)
# ------------------------------------------
@app.route("/manual", methods=["GET", "POST"])
def manual_alert():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        source = request.form.get("source")
        event_type = request.form.get("event_type")
        severity = request.form.get("severity")
        message = request.form.get("message")

        user_id = session["user_id"]  # ← إضافة user_id

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO alerts (source, event_type, severity, message, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?);",
            (source, event_type, severity, message, datetime.now(), user_id),
        )
        conn.commit()
        conn.close()

        if severity.lower() in ("high", "critical"):
            send_telegram_alert(f"⚠️ [{severity.upper()}] {source}: {message}")

        return render_template("manual.html", message_sent=True)

    return render_template("manual.html", message_sent=False)

# ------------------------------------------
# 🔹 حذف تنبيه واحد
# ------------------------------------------
@app.route('/alerts/delete/<int:alert_id>', methods=['POST'])
def delete_alert(alert_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    try:
        user_id = session["user_id"]
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts WHERE id=? AND user_id=?", (alert_id, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('list_alerts'))
    except Exception as e:
        print("Error deleting alert:", e)
        return redirect(url_for('list_alerts'))

# ------------------------------------------
# 🔹 حذف جميع التنبيهات
# ------------------------------------------
@app.route('/alerts/delete_all', methods=['POST'])
def delete_all_alerts():
    if "user_id" not in session:
        return redirect(url_for("login"))
    try:
        user_id = session["user_id"]
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('list_alerts'))
    except Exception as e:
        print("Error deleting all alerts:", e)
        return redirect(url_for('list_alerts'))

# ------------------------------------------
# 🔹 Health Check (للتأكد أن السيرفر شغال)
# ------------------------------------------
@app.route("/healthz")
def healthz():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return {"status": "ok"}, 200

# ------------------------------------------
# 📤 تصدير التنبيهات إلى ملف CSV
# ------------------------------------------
@app.route('/alerts/export.csv')
def export_alerts():
    if "user_id" not in session:
        return redirect(url_for("login"))
    import csv
    from io import StringIO

    user_id = session["user_id"]

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT event_type, severity, message, created_at FROM alerts WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Event Type', 'Severity', 'Message', 'Time'])

    # 🔹 حذف النانو ثانية فقط
    for event_type, severity, message, created_at in rows:
        clean_time = str(created_at).split('.')[0]
        writer.writerow([event_type, severity, message, clean_time])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=alerts.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

if __name__ == "__main__":
    app.run(debug=True)
