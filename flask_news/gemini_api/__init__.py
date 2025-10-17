from flask import Blueprint
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create blueprint
gemini_bp = Blueprint("gemini_bp", __name__)

# Import routes (avoid circular import)
from . import gemini_chat
