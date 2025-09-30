from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ----------------- SETUP -----------------
load_dotenv()
app = Flask(__name__)
CORS(app, origins=["http://localhost:8080"])  # Adjust to your frontend

DB_FILE = "database.db"

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BLOGS_API_KEY = os.getenv("BLOGS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ----------------- DATABASE -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Projects Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tech_stack TEXT NOT NULL,
            roles TEXT NOT NULL,
            duration TEXT NOT NULL,
            last_date TEXT NOT NULL,
            links TEXT
        )
    """)

    # Events Table (schema matches frontend fields)
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        event_date TEXT NOT NULL,
        time TEXT NOT NULL,
        attendees INTEGER DEFAULT 0,
        registration_link TEXT,
        registration_end_date TEXT NOT NULL
    )
""")


    conn.commit()
    conn.close()

init_db()

# ----------------- PROJECTS -----------------
@app.route("/projects", methods=["GET", "POST"])
def projects():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == "POST":
        data = request.json
        c.execute("""
            INSERT INTO projects (title, description, tech_stack, roles, duration, last_date, links)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title"),
            data.get("description"),
            data.get("tech_stack"),
            data.get("roles"),
            data.get("duration"),
            data.get("last_date"),
            data.get("links"),
        ))
        conn.commit()
        new_id = c.lastrowid

        # Fetch newly inserted project
        c.execute("SELECT * FROM projects WHERE id=?", (new_id,))
        new_project = c.fetchone()
        conn.close()

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

    else:  # GET
        c.execute("SELECT * FROM projects ORDER BY id DESC")
        projects = c.fetchall()
        conn.close()

        return jsonify({
            "projects": [
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "tech_stack": row[3],
                    "roles": row[4],
                    "duration": row[5],
                    "last_date": row[6],
                    "links": row[7]
                } for row in projects
            ]
        })

# ----------------- EVENTS -----------------
@app.route("/events", methods=["GET", "POST"])
def events():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == "POST":
        data = request.json
        # Accept both camelCase and snake_case from frontend for compatibility
        event_date = data.get("event_date") or data.get("date")
        registration_end_date = data.get("registration_end_date") or data.get("lastRegistrationDate")
        registration_link = data.get("registration_link") or data.get("registrationLink")
        c.execute("""
            INSERT INTO events (title, description, type, location, event_date, time, attendees, registration_link, registration_end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title"),
            data.get("description"),
            data.get("type"),
            data.get("location"),
            event_date,
            data.get("time"),
            data.get("attendees", 0),
            registration_link,
            registration_end_date,
        ))
        conn.commit()
        new_id = c.lastrowid

        # Fetch newly inserted event
        c.execute("SELECT * FROM events WHERE id=?", (new_id,))
        new_event = c.fetchone()
        conn.close()

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
        }), 201

    else:  # GET
        c.execute("SELECT * FROM events ORDER BY id DESC")
        events = c.fetchall()
        conn.close()

        return jsonify({
            "events": [
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "type": row[3],
                    "location": row[4],
                    "event_date": row[5],
                    "time": row[6],
                    "attendees": row[7],
                    "registration_link": row[8],
                    "registration_end_date": row[9],
                } for row in events
            ]
        })


# ----------------- CACHES -----------------
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
