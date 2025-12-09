import sqlite3
import bcrypt

username = input("Enter username: ")
password = input("Enter password: ")

hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
conn.commit()
conn.close()

print(f"User '{username}' created successfully!")