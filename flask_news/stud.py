import sqlite3
from functools import wraps
from flask import request, jsonify, session
from werkzeug.security import check_password_hash

DB_FILE = "database.db"

def verify_password(hash_, pwd):
    return check_password_hash(hash_, pwd)

def login_required_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("username") or session.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

def get_me():
    return jsonify({"username": session.get("username"), "role": session.get("role")})

def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(user[2], password):
        session["username"] = username
        session["role"] = user[3]
        return jsonify({"message": "Login successful", "role": user[3]})
    return jsonify({"error": "Invalid credentials"}), 401

def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

def get_categories():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM studverse_categories ORDER BY id")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({"categories": categories})

@login_required_admin
def add_category():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Missing category name"}), 400
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO studverse_categories (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Category already exists"}), 409
    conn.close()
    return jsonify({"success": True, "name": name})

@login_required_admin
def remove_category(category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM studverse_categories WHERE name=?", (category,))
    c.execute("DELETE FROM studverse_videos WHERE category=?", (category,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

def get_videos(category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT url FROM studverse_videos WHERE category=?", (category,))
    videos = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({"videos": videos})

@login_required_admin
def add_video(category):
    data = request.get_json()
    url = data.get("url")
    if not url or not category:
        return jsonify({"error": "Missing URL or category"}), 400
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO studverse_videos (category, url) VALUES (?, ?)", (category, url))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@login_required_admin
def delete_video(category):
    data = request.get_json()
    url = data.get("url")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM studverse_videos WHERE category=? AND url=?", (category, url))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
