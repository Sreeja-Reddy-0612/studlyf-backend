from flask import request, jsonify
from . import gemini_bp
import google.generativeai as genai

@gemini_bp.route("/chat", methods=["POST"])
def chat_with_gemini():
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # Use your working Gemini model from test
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)

        text = response.text if response else "No response from Gemini."
        return jsonify({"reply": text}), 200

    except Exception as e:
        print("Gemini API Error:", e)
        return jsonify({"error": str(e)}), 500
