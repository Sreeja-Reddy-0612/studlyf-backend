from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

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

    # Return only entries with a name
    return [c for c in results if c["name"]]

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

if __name__ == "__main__":
    app.run(port=5001, debug=True)
