# extractor.py
from bs4 import BeautifulSoup

def extract_from_text(html):
    """Extract tool info from HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # Example extraction (adjust selectors as per website)
    tool_name = soup.select_one("h1.tool-name")
    description = soup.select_one("p.description")
    url = soup.select_one("a.website-link")

    data = {
        "name": tool_name.get_text(strip=True) if tool_name else "Unknown",
        "short_description": description.get_text(strip=True) if description else "",
        "website_url": url.get("href") if url else "",
        "long_description": "",
        "use_cases": [],
        "supported_tech": [],
        "tags": [],
        "pricing_info": "",
        "source_url": "",
        "validated": False
    }
    return data
