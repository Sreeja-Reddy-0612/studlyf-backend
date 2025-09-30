import os
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # <-- Add this import

DB_FILE = "database.db"
load_dotenv()  # Ensure .env file is loaded before keys fetched

def fetch_shorts():
    global cached_shorts
    query = "AI OR technology OR software OR jobs OR cloud computing"
    published_after = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat("T") + "Z"
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

def add_project(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    c.execute("SELECT * FROM projects WHERE id=?", (new_id,))
    new_project = c.fetchone()
    conn.close()
    return new_project

def get_projects():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return projects

def add_event(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    c.execute("SELECT * FROM events WHERE id=?", (new_id,))
    new_event = c.fetchone()
    conn.close()
    return new_event

def get_events():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY id DESC")
    events = c.fetchall()
    conn.close()
    return events

# Coursera scraping URLs
URLS = {
    "courses": "https://www.coursera.org/search?productTypeDescription=Courses&sortBy=BEST_MATCH",
    "projects": "https://www.coursera.org/search?productTypeDescription=Guided%20Projects&productTypeDescription=Projects&sortBy=BEST_MATCH",
    "certificates": "https://www.coursera.org/search?productTypeDescription=MasterTrack%C2%AE%20Certificates&productTypeDescription=Professional%20Certificates&sortBy=BEST_MATCH"
}

def fetch_courses_from_url(url, provider_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {provider_name} URL {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    cards = soup.find_all('div', class_="cds-ProductCard-content")
    for card in cards:
        title_div = card.find('div', class_="cds-ProductCard-header")
        title = title_div.get_text(strip=True) if title_div else ""

        description_div = card.find('div', class_="cds-ProductCard-body")
        description = description_div.get_text(strip=True) if description_div else ""

        image_url = ""
        parent = card.parent
        if parent:
            prevs = parent.find_all('div', class_="cds-CommonCard-previewImage")
            if prevs:
                img = prevs[-1].find('img')
                if img:
                    image_url = img.get('src', '')

        level = ""
        duration = ""
        footer_div = card.find_next_sibling('div', class_="cds-ProductCard-footer")
        metadata_div = footer_div.find('div', class_="cds-CommonCard-metadata") if footer_div else None
        if metadata_div:
            p_tag = metadata_div.find('p')
            if p_tag:
                meta_parts = [x.strip() for x in p_tag.get_text(strip=True).split('·')]
                if len(meta_parts) >= 2:
                    level = meta_parts[0]
                    duration = meta_parts[-1]
                elif len(meta_parts) == 1:
                    level = meta_parts[0]

        url_full = ""
        if title_div:
            a_tag = title_div.find('a', href=True)
            if a_tag:
                href = a_tag.get('href', '')
                url_full = "https://www.coursera.org" + href if href.startswith('/') else href

        if title:
            results.append({
                "name": title,
                "provider": provider_name,
                "description": description,
                "level": level,
                "duration": duration,
                "url": url_full,
                "image": image_url
            })

    return [c for c in results if c["name"]]
