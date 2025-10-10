# backend/ai_categorizer.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def categorize_tool(name, short_description):
    """Use OpenAI to generate category, tags, and summary."""
    prompt = f"""
    You are an AI tool classifier.
    Given the tool name and short description, return a JSON with fields:
    category, tags (list), and long_summary.

    Example:
    Input: Name: Notion AI, Description: AI writing assistant for productivity
    Output: {{
      "category": "Productivity",
      "tags": ["Writing", "Automation", "Assistant"],
      "long_summary": "Notion AI helps users write and summarize content using integrated AI features."
    }}

    Now classify this:
    Name: {name}
    Description: {short_description}
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.4
    )

    result_text = response.output[0].content[0].text
    print(f"🔹 Categorized: {name}")
    return result_text
