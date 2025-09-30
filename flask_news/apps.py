from flask import Flask, jsonify
import requests, os
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS
from dotenv import load_dotenv

# ---------- LOAD API KEYS ----------
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BLOGS_API_KEY = os.getenv("BLOGS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080"])  # Allow your frontend

# ---------- IN-MEMORY CACHE ----------
cached_news = []
cached_blogs = []
cached_shorts = []

# ---------- FETCH FUNCTIONS ----------
def fetch_news():
    """Fetch latest tech/AI news"""
    global cached_news
    query = "AI OR technology OR software OR cloud computing"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={NEWS_API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        cached_news = r.json().get("articles", [])
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_news)} news articles")
    else:
        print(f"News fetch error: {r.status_code}, {r.text}")


def fetch_blogs():
    """Fetch currently popular blogs (recent, popular)"""
    global cached_blogs
    query = "AI OR technology OR software OR cloud computing"

    # Restrict results to the past 3 days for freshness
    from_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en"
        f"&from={from_date}"
        f"&sortBy=popularity"
        f"&pageSize=15&apiKey={BLOGS_API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        cached_blogs = r.json().get("articles", [])
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_blogs)} recent popular blogs")
    else:
        print(f"Blogs fetch error: {r.status_code}, {r.text}")


def fetch_shorts():
    """Fetch trending YouTube shorts (past 30 days) related to tech/AI/software"""
    global cached_shorts
    query = "AI OR technology OR software OR jobs OR cloud computing"

    # Only fetch shorts from the past 30 days
    published_after = (datetime.utcnow() - timedelta(days=30)).isoformat("T") + "Z"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",  # trending content by views
        "maxResults": 15,
        "publishedAfter": published_after,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
    if r.status_code == 200:
        items = r.json().get("items", [])
        cached_shorts = [
            {
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "published_at": item["snippet"]["publishedAt"]
            }
            for item in items
        ]
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_shorts)} trending YouTube shorts")
    else:
        print(f"YouTube shorts fetch error: {r.status_code}, {r.text}")

# ---------- ROUTES ----------
@app.route("/tech-news")
def tech_news():
    return jsonify({"news": cached_news})

@app.route("/blogs")
def blogs():
    return jsonify({"blogs": cached_blogs})

@app.route("/youtube-shorts")
def youtube_shorts():
    return jsonify({"shorts": cached_shorts})

# Manual refresh routes for testing
@app.route("/refresh-news")
def refresh_news():
    fetch_news()
    return jsonify({"status": "news refreshed"})

@app.route("/refresh-blogs")
def refresh_blogs():
    fetch_blogs()
    return jsonify({"status": "blogs refreshed"})

@app.route("/refresh-shorts")
def refresh_shorts():
    fetch_shorts()
    return jsonify({"status": "shorts refreshed"})

# ---------- SCHEDULER ----------
def schedule_jobs():
    scheduler = BackgroundScheduler()

    # News: 4 times/day
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(fetch_news, 'cron', hour=hour, minute=0)

    # Blogs: twice/day (12 AM, 12 PM)
    for hour in [0, 12]:
        scheduler.add_job(fetch_blogs, 'cron', hour=hour, minute=0)

    # Shorts: twice/day (12 AM, 12 PM)
    for hour in [0, 12]:
        scheduler.add_job(fetch_shorts, 'cron', hour=hour, minute=0)

    scheduler.start()

# ---------- MAIN ----------
if __name__ == "__main__":
    # Initial fetch on startup
    fetch_news()
    fetch_blogs()
    fetch_shorts()
    schedule_jobs()
    app.run(debug=True, port=5001)
