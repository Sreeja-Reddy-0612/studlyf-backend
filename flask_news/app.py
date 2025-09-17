from flask import Flask, jsonify
import requests, os
from datetime import datetime, UTC
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BLOGS_API_KEY = os.getenv("BLOGS_API_KEY")

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080"])  # Allow your frontend

# In-memory cache
cached_news = []
cached_blogs = []

# ---------- FETCH FUNCTIONS ----------
def fetch_news():
    global cached_news
    query = "AI OR technology OR software OR cloud computing"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={NEWS_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        cached_news = r.json().get("articles", [])
        print(f"[{datetime.now(UTC)}] Fetched {len(cached_news)} news articles")
    else:
        print(f"News fetch error: {r.status_code}")

def fetch_blogs():
    global cached_blogs
    query = "AI OR technology OR software OR cloud computing"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=popularity&pageSize=15&apiKey={BLOGS_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        cached_blogs = r.json().get("articles", [])
        print(f"[{datetime.now(UTC)}] Fetched {len(cached_blogs)} blogs")
    else:
        print(f"Blogs fetch error: {r.status_code}")

# ---------- ROUTES ----------
@app.route("/tech-news")
def tech_news():
    return jsonify({"news": cached_news})

@app.route("/blogs")
def blogs():
    return jsonify({"blogs": cached_blogs})

@app.route("/refresh-blogs")
def refresh_blogs():
    fetch_blogs()
    return jsonify({"status": "refreshed"})

# ---------- SCHEDULER ----------
def schedule_jobs():
    scheduler = BackgroundScheduler()
    # Schedule news at 6am, 12pm, 6pm, 12am
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(fetch_news, 'cron', hour=hour, minute=0)
        scheduler.add_job(fetch_blogs, 'cron', hour=hour, minute=0)
    scheduler.start()

if __name__ == "__main__":
    fetch_news()  # initial fetch
    fetch_blogs() # initial fetch
    schedule_jobs()
    app.run(debug=True, port=5001)

