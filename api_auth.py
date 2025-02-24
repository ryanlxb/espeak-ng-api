"""
API认证模块

提供API密钥的生成、存储和验证功能。
使用SQLite数据库存储API密钥信息。

功能：
- 生成安全的API密钥
- 存储API密钥到数据库
- 验证API密钥的有效性
- 提供API认证装饰器
"""

import secrets
import sqlite3
from functools import wraps
from flask import request, jsonify
import datetime
import os

def init_db():
    """
    初始化SQLite数据库
    创建存储API密钥的表结构
    """
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
    """生成一个安全的随机API密钥"""
    return secrets.token_urlsafe(32)

def store_api_key(api_key):
    """
    将API密钥存储到数据库
    
    参数：
    - api_key: 要存储的API密钥
    """
    db_path = os.environ.get('SQLITE_DB_PATH', 'api_keys.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO api_keys VALUES (?, ?, ?, ?)",
              (api_key, datetime.datetime.now(), datetime.datetime.now(), True))
    conn.commit()
    conn.close()

def validate_api_key(api_key):
    """
    验证API密钥的有效性
    
    参数：
    - api_key: 要验证的API密钥
    
    返回：
    - bool: 密钥是否有效
    """
    db_path = os.environ.get('SQLITE_DB_PATH', 'api_keys.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 检查密钥是否有效且在30天内使用过
    c.execute("""
        SELECT is_active 
        FROM api_keys 
        WHERE key = ? 
        AND datetime(last_used) > datetime('now', '-30 day')
    """, (api_key,))
    result = c.fetchone()
    if result and result[0]:
        # 更新最后使用时间
        c.execute("UPDATE api_keys SET last_used = ? WHERE key = ?",
                 (datetime.datetime.now(), api_key))
        conn.commit()
    conn.close()
    return result is not None and result[0]

def require_api_key(f):
    """
    API认证装饰器
    用于保护需要API密钥的路由
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function
