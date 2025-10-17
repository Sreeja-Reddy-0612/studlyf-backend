import os
import sqlite3
from flask import request, jsonify
from werkzeug.utils import secure_filename

DB_FILE = "database.db"
UPLOAD_FOLDER = "static/ads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_ads():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, image, link FROM ads ORDER BY id DESC")
    ads = [{"id": row[0], "image": f"/{row[1]}", "link": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({"ads": ads})

def add_ad():
    if "image" not in request.files or "link" not in request.form:
        return jsonify({"error": "Missing image or link"}), 400

    image = request.files["image"]
    link = request.form["link"]

    if not image or not link:
        return jsonify({"error": "Missing data"}), 400

    filename = secure_filename(image.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO ads (image, link) VALUES (?, ?)", (os.path.join("static/ads", filename), link))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

def delete_ad(ad_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT image FROM ads WHERE id=?", (ad_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Ad not found"}), 404

    image_path = row[0]
    full_path = os.path.join(os.getcwd(), image_path)
    if os.path.exists(full_path):
        os.remove(full_path)

    c.execute("DELETE FROM ads WHERE id=?", (ad_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})
