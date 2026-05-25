import os, shutil, re, sys, subprocess
from datetime import datetime

# =====================================================================
# AUTO-DEPENDENCY CHECKER
# =====================================================================
def ensure_dependencies():
    # Check for playwright and beautifulsoup4 python modules
    try:
        import playwright
        from bs4 import BeautifulSoup
    except ImportError:
        print("Missing Python modules. Installing playwright and beautifulsoup4...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "beautifulsoup4"])
    
    # Check if the specific Chromium binary for playwright exists
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Quick test launch to see if the browser binary is present
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as e:
        # If launching fails due to missing binaries, force install them
        if "Executable doesn't exist" in str(e) or "browser" in str(e).lower():
            print("Chromium browser binaries missing. Installing Playwright drivers...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        else:
            raise e

# Run the system check before executing any scraping logic
ensure_dependencies()

# =====================================================================
# CORE SCRAPER LOGIC
# =====================================================================
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://mhtahiti.com/announcements/"
OUTPUT_FILE = "tahiti-feed.xml"
print(f"STARTING: Fetching from {URL}")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print("Waiting 5 seconds for content...")
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "T.A.H.I.T.I Announcements"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "News"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    announcements = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    text_nodes = soup.find_all(string=True)
    
    for i, node in enumerate(text_nodes):
        text = node.strip()
        if any(m in text for m in months) and (":" in text or "2026" in text):
            raw_timestamp = text
            author = ""
            message = ""
            
            for j in range(1, 5):
                if i - j >= 0:
                    prev_text = text_nodes[i - j].strip()
                    if prev_text and 2 < len(prev_text) < 15 and not any(m in prev_text for m in months):
                        if not any(x in prev_text for x in ["Latest", "Announcements", "News", "Project"]):
                            author = prev_text
                            break
            
            for k in range(1, 5):
                if i + k < len(text_nodes):
                    next_text = text_nodes[i + k].strip()
                    if not next_text or next_text == raw_timestamp or len(next_text) <= 1:
                        continue
                    if any(m in next_text for m in months):
                        continue
                    message = next_text
                    break
            
            if author and message:
                clean_timestamp = re.sub(r'\bat\b', '', raw_timestamp, flags=re.IGNORECASE)
                clean_timestamp = " ".join(clean_timestamp.split())
                
                entry_data = {
                    "header": f"{author.upper()} - {clean_timestamp}",
                    "body": message
                }
                
                if entry_data not in announcements:
                    announcements.append(entry_data)

    count = 0
    for entry in announcements:
        item = ET.SubElement(channel, "item")
        combined_text = f"{entry['header']}\n{entry['body']}"
        ET.SubElement(item, "title").text = combined_text
        ET.SubElement(item, "description").text = combined_text
        ET.SubElement(item, "link").text = URL
        ET.SubElement(item, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        count += 1
        if count >= 10: break

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"SUCCESS: Generated {count} formatted announcements without warnings.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")

try:
    s_dir = os.path.dirname(os.path.abspath(__file__))
    p_dir = os.path.dirname(s_dir)
    shutil.copy(OUTPUT_FILE, p_dir)
except Exception as ce:
    print(f"Copy missed: {ce}")
