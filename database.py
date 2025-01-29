import sqlite3
import time
from datetime import datetime

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE,
            start_time TIMESTAMP,
            last_active TIMESTAMP,
            messages_sent INTEGER DEFAULT 0,
            status TEXT,
            uptime INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    now = datetime.now()
    try:
        c.execute('INSERT OR REPLACE INTO users (token, start_time, last_active, status) VALUES (?, ?, ?, ?)',
                 (token, now, now, 'active'))
        conn.commit()
    except Exception as e:
        print(f"Error adding user: {str(e)}")
    finally:
        conn.close()

def update_user_status(token, status, messages=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    now = datetime.now()
    try:
        if messages is not None:
            c.execute('UPDATE users SET status = ?, last_active = ?, messages_sent = ? WHERE token = ?',
                     (status, now, messages, token))
        else:
            c.execute('UPDATE users SET status = ?, last_active = ? WHERE token = ?',
                     (status, now, token))
        conn.commit()
    except Exception as e:
        print(f"Error updating user: {str(e)}")
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('''
            SELECT token, start_time, last_active, messages_sent, status,
                   ROUND((julianday('now') - julianday(start_time)) * 24 * 60) as uptime_minutes
            FROM users
            WHERE last_active >= datetime('now', '-1 hour')
            ORDER BY start_time DESC
        ''')
        users = c.fetchall()
        return [{
            'token': user[0],
            'started': user[1],
            'last_active': user[2],
            'messages_sent': user[3],
            'status': user[4],
            'uptime': user[5]
        } for user in users]
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        return []
    finally:
        conn.close()

def cleanup_inactive_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE last_active < datetime('now', '-1 hour')")
        conn.commit()
    except Exception as e:
        print(f"Error cleaning up users: {str(e)}")
    finally:
        conn.close()
