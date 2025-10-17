from flask import Flask, jsonify
from flask_cors import CORS

# Import your blueprint
from gemini_api import gemini_bp

app = Flask(__name__)
CORS(app)  # allow frontend localhost:8080 to access backend

# Register Gemini blueprint
app.register_blueprint(gemini_bp, url_prefix="/api")

@app.route("/")
def index():
    return jsonify({"message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
