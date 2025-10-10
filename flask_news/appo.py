from flask import Flask
from flask_cors import CORS
from ai_tools_routes import ai_tools_api

app = Flask(__name__)
CORS(app)  # Allow frontend access

# Register your Blueprint
app.register_blueprint(ai_tools_api)

@app.route('/')
def home():
    return "Welcome to Stadiaverse AI Tools API!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
