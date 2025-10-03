from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import sqlite3, os, requests, json, base64
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from func import (
    add_project, get_projects,
    add_event, get_events,
    fetch_courses_from_url, URLS  # <-- Add these imports
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "https://studlyf.in", "https://www.studlyf.in"])

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BLOGS_API_KEY = os.getenv("BLOGS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("WARNING: MONGO_URI not found in environment variables")
    MONGO_URI = "mongodb://localhost:27017/studlyf"

try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.studlyf  # Database name
    users_collection = db.users
    connections_collection = db.connections
    connection_requests_collection = db.connection_requests
    messages_collection = db.messages
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    db = None

# Firebase Admin Initialization
FIREBASE_ADMIN_KEY = os.getenv("FIREBASE_ADMIN_KEY")
if FIREBASE_ADMIN_KEY:
    try:
        # Decode base64 Firebase admin key
        firebase_key = json.loads(base64.b64decode(FIREBASE_ADMIN_KEY).decode('utf-8'))
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized")
    except Exception as e:
        print(f"❌ Firebase Admin initialization error: {e}")
else:
    print("WARNING: FIREBASE_ADMIN_KEY not found in environment variables")

# ----------------- COURSES, PROJECTS, CERTIFICATIONS SCRAPING ROUTES -----------------
@app.route('/free-courses')
def free_courses():
    courses = fetch_courses_from_url(URLS["courses"], "Coursera")
    return jsonify({"courses": courses[:20]})

@app.route('/projects')
def guided_projects():
    projects = fetch_courses_from_url(URLS["projects"], "Coursera")
    return jsonify({"projects": projects[:20]})

@app.route('/certifications')
def certifications():
    certificates = fetch_courses_from_url(URLS["certificates"], "Coursera")
    return jsonify({"certificates": certificates[:20]})

# Projects routes
@app.route("/project-hunt", methods=["GET", "POST"])
def projects():
    if request.method == "POST":
        data = request.json
        new_project = add_project(data)
        return jsonify({
            "id": new_project[0],
            "title": new_project[1],
            "description": new_project[2],
            "tech_stack": new_project[3],
            "roles": new_project[4],
            "duration": new_project[5],
            "last_date": new_project[6],
            "links": new_project[7]
        }), 201
    else:
        projects = get_projects()
        return jsonify({
            "projects": [
                {
                    "id": p[0],
                    "title": p[1],
                    "description": p[2],
                    "tech_stack": p[3],
                    "roles": p[4],
                    "duration": p[5],
                    "last_date": p[6],
                    "links": p[7]
                } for p in projects
            ]
        })

# Events routes
@app.route("/events", methods=["GET", "POST"])
def events():
    if request.method == "POST":
        data = request.json
        new_event = add_event(data)
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
    else:
        events = get_events()
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

cached_news = []
cached_blogs = []
cached_shorts = []

# ----------------- FETCH FUNCTIONS -----------------
def fetch_news():
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
    global cached_blogs
    query = "AI OR technology OR software OR cloud computing"
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
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_blogs)} blogs")
    else:
        print(f"Blogs fetch error: {r.status_code}, {r.text}")

def fetch_shorts():
    global cached_shorts
    query = "AI OR technology OR software OR jobs OR cloud computing"
    published_after = (datetime.utcnow() - timedelta(days=30)).isoformat("T") + "Z"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
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
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_shorts)} YouTube shorts")
    else:
        print(f"YouTube fetch error: {r.status_code}, {r.text}")

# ----------------- ROUTES -----------------
@app.route("/tech-news")
def tech_news():
    return jsonify({"news": cached_news})

@app.route("/blogs")
def blogs():
    return jsonify({"blogs": cached_blogs})

@app.route("/youtube-shorts")
def youtube_shorts():
    return jsonify({"shorts": cached_shorts})

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

# ----------------- SCHEDULER -----------------
def schedule_jobs():
    scheduler = BackgroundScheduler()
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(fetch_news, 'cron', hour=hour, minute=0)
    for hour in [0, 12]:
        scheduler.add_job(fetch_blogs, 'cron', hour=hour, minute=0)
        scheduler.add_job(fetch_shorts, 'cron', hour=hour, minute=0)
    scheduler.start()

# ----------------- MAIN -----------------
if __name__ == "__main__":
    fetch_news()
    fetch_blogs()
    fetch_shorts()
    schedule_jobs()
    app.run(debug=True, port=5001)