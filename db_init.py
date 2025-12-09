import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,         -- مصدر الحدث (مثلاً: lab, mqtt, manual)
    event_type TEXT NOT NULL,     -- نوع الحدث (unauthorized, threshold, out_of_hours, ... )
    severity TEXT NOT NULL,       -- درجة الخطورة (low, medium, high, critical)
    message TEXT NOT NULL,        -- وصف مختصر للحدث
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

print(f"OK. Database created/updated at: {DB_PATH}")

import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("Users table created successfully!")