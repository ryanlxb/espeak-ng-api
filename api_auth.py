import secrets
import sqlite3
from functools import wraps
from flask import request, jsonify
import datetime
import os

def init_db():
    db_path = os.environ.get('SQLITE_DB_PATH', 'api_keys.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                 (key text PRIMARY KEY, 
                  created_at timestamp,
                  last_used timestamp,
                  is_active boolean)''')
    conn.commit()
    conn.close()

def generate_api_key():
    return secrets.token_urlsafe(32)

def store_api_key(api_key):
    db_path = os.environ.get('SQLITE_DB_PATH', 'api_keys.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO api_keys VALUES (?, ?, ?, ?)",
              (api_key, datetime.datetime.now(), datetime.datetime.now(), True))
    conn.commit()
    conn.close()

def validate_api_key(api_key):
    db_path = os.environ.get('SQLITE_DB_PATH', 'api_keys.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT is_active FROM api_keys WHERE key = ?", (api_key,))
    result = c.fetchone()
    conn.close()
    return result is not None and result[0]

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function 