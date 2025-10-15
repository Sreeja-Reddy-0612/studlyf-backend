from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
from werkzeug.utils import secure_filename
import os
import func

# -------------------- Flask setup --------------------
app = Flask(__name__)
app.secret_key = "a968bac0ac08ac9e4f723563936fc8b01e37e1eaa2e1829b08be72f8e88ccaec"

# Allow frontend access (local & production)
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:8080",
        "http://localhost:3000",
        "https://studlyf.in",
        "https://www.studlyf.in",
    ],
)

# Secure session cookies
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# -------------------- Upload Config --------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    """Validate image file extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------- Admin Authentication --------------------
def login_required_admin(f):
    """Decorator for admin-only routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("username") or session.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return wrapper


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Admin login endpoint."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = func.get_user_by_username(username)
    if user and func.verify_password(user[2], password):
        session["username"] = username
        session["role"] = user[3]
        return jsonify({"message": "Admin login successful", "role": user[3]})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    """Clear admin session."""
    session.clear()
    return jsonify({"message": "Admin logged out"})


# -------------------- Event CRUD --------------------
@app.route("/events", methods=["POST"])
# @login_required_admin  # Uncomment to restrict to admins
def create_event():
    """
    Create a new event with optional image (<500KB).
    """
    try:
        # ----- Handle image upload -----
        image = request.files.get("image")
        image_url = None

        if image and allowed_file(image.filename):
            image.seek(0, os.SEEK_END)
            size = image.tell()
            image.seek(0)
            if size > 500 * 1024:  # limit 500KB
                return jsonify({"error": "Image exceeds 500 KB limit"}), 400

            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))
            image_url = f"/{UPLOAD_FOLDER}/{filename}"

        # ----- Get other form data -----
        data = {k: request.form.get(k) for k in request.form.keys()}
        data["image_url"] = image_url

        # ----- Insert into DB -----
        new_event = func.add_event(data)

        return jsonify({
            "id": new_event[0],
            "title": new_event[1],
            "description": new_event[2],
            "type": new_event[3],
            "location": new_event[4],
            "event_date": new_event[5],
            "time": new_event[6],
            "attendees": new_event[7],
            "registration_link": new_event[8],
            "registration_end_date": new_event[9],
            "image_url": new_event[10],
        }), 201

    except Exception as e:
        print("Error creating event:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/events", methods=["GET"])
def list_events():
    """Fetch all events."""
    try:
        events = func.get_events()
        return jsonify({
            "events": [
                {
                    "id": e[0],
                    "title": e[1],
                    "description": e[2],
                    "type": e[3],
                    "location": e[4],
                    "event_date": e[5],
                    "time": e[6],
                    "attendees": e[7],
                    "registration_link": e[8],
                    "registration_end_date": e[9],
                    "image_url": e[10],
                }
                for e in events
            ]
        })
    except Exception as e:
        print("Error fetching events:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/events/<int:event_id>", methods=["DELETE"])
# @login_required_admin
def remove_event(event_id):
    """Delete event by ID."""
    try:
        func.delete_event(event_id)
        return jsonify({"message": "Event deleted successfully"})
    except Exception as e:
        print("Error deleting event:", e)
        return jsonify({"error": str(e)}), 500


# -------------------- Serve Uploaded Images --------------------
@app.route("/uploads/<path:filename>")
def serve_image(filename):
    """Serve uploaded images."""
    return send_from_directory(UPLOAD_FOLDER, filename)


# -------------------- Run the Flask App --------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
