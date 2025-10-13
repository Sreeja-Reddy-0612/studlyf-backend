from flask import Flask, request, jsonify, session
import func
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "a968bac0ac08ac9e4f723563936fc8b01e37e1eaa2e1829b08be72f8e88ccaec"
CORS(app, supports_credentials=True, origins=["http://localhost:8080"])

app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

def login_required_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("username") or session.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = func.get_user_by_username(username)
    if user and func.verify_password(user[2], password):
        session["username"] = username
        session["role"] = user[3]
        return jsonify({"message": "Login successful", "role": user[3]})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/events", methods=["POST"])
@login_required_admin
def create_event():
    data = request.get_json()
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
        "registration_end_date": new_event[9]
    }), 201

@app.route("/events", methods=["GET"])
def list_events():
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
                "registration_end_date": e[9]
            } for e in events
        ]
    })

@app.route("/events/<int:event_id>", methods=["DELETE"])
@login_required_admin
def remove_event(event_id):
    func.delete_event(event_id)
    return jsonify({"message": "Event deleted"})

if __name__ == "__main__":
    app.run(debug=True)
