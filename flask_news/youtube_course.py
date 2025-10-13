from flask import Blueprint, request, jsonify, session
import sqlite3
from functools import wraps

youtubecourse_api = Blueprint("youtubecourse_api", __name__)
DB_FILE = "database.db"

def login_required_admin(f):
    @wraps(f)
    def wrap(*a, **k):
        if not (session.get("role") == "admin"):
            return jsonify({"error": "unauthorized"}), 403
        return f(*a, **k)
    return wrap

# Ensure the table exists
def ensure_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS custom_courses
        (id INTEGER PRIMARY KEY AUTOINCREMENT, heading TEXT, tags TEXT, src_link TEXT, description TEXT)
    """)
    conn.commit(); conn.close()
ensure_table()

@youtubecourse_api.route("/admin-courses")
def admin_courses_get():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, heading, tags, src_link, description FROM custom_courses ORDER BY id DESC")
    data = [{"id": row[0], "heading": row[1], "tags": row[2].split(","), "src_link": row[3], "description": row[4]} for row in c.fetchall()]
    conn.close()
    return jsonify({"courses": data})

@youtubecourse_api.route("/admin-courses", methods=["POST"])
@login_required_admin
def admin_course_post():
    data = request.get_json()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO custom_courses (heading, tags, src_link, description) VALUES (?, ?, ?, ?)",
              (data.get("heading"), ",".join(data.get("tags", [])), data.get("src_link"), data.get("description")))
    conn.commit(); conn.close()
    return jsonify({"success": True})

@youtubecourse_api.route("/admin-courses/<int:cid>", methods=["DELETE"])
@login_required_admin
def admin_course_delete(cid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM custom_courses WHERE id=?", (cid,))
    conn.commit(); conn.close()
    return jsonify({"success": True})
