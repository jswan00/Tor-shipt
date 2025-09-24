import requests
from bs4 import BeautifulSoup
import datetime
import os

URL_TO_CHECK = "https://shubham-shipt.github.io/Tor-Project/"
REPORT_FILE_PATH = "SEO/Day.txt"

print(f"Starting SEO check for: {URL_TO_CHECK}")

try:
    response = requests.get(URL_TO_CHECK, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title else "No Title Found"
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag['content'].strip() if meta_desc_tag else "No Meta Description Found"
    h1_count = len(soup.find_all("h1"))
    img_without_alt = len([img for img in soup.find_all("img") if not img.get("alt", "").strip()])
    links_count = len(soup.find_all("a"))

    report = f"""
Date & Time (UTC): {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
URL Checked: {URL_TO_CHECK}
==================================
- Title: {title}
- Meta Description: {meta_desc}
- H1 Tags Count: {h1_count}
- Images without Alt Tag: {img_without_alt}
- Total Links: {links_count}
----------------------------------
"""

    os.makedirs(os.path.dirname(REPORT_FILE_PATH), exist_ok=True)

    with open(REPORT_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ SEO report successfully updated in {REPORT_FILE_PATH}")

except requests.exceptions.RequestException as e:
    print(f"❌ Error: Website fetch nahi ho payi. Error: {e}")
except Exception as e:
    print(f"❌ Ek anjaan error aayi: {e}")

