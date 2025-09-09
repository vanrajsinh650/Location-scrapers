from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import re

PHONE_RE = re.compile(r'(\+?\d[\d\-\s\(\)]{6,}\d)')

def extract_number_from_text(text):
    print("Input text:", text)
    if not text:
        print("Number is not found")
        return None
    m = PHONE_RE.search(text)
    print("Show what the regex match object:", m)
    if m:
        print("Matched group(1):", m.group(1))
        return m.group(1)
    else:
        print("No match found")
        return None
    
def scrape_google_map(area, city, max_result=20, headless=True, pause=1.0):
    results = []
    query = f"pg hostels {area} {city}"
    maps_url = "https://www.google.com/maps/search" + query.replace(" ", "+") + "/"
    seen = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        
        page.wait_for_selector('div[role="articale"], div.section-result', timeout=30000)
        
        scroll_container = page.query_selector('div[role="feed"]') or page.query_selector('body')
        
        while len(results) < max_result:
            cards = page.query_selector_all('div[role="article"], div.section-result')
            for card in cards:
                try:
                    name_el = card.query_selector('[aria-label]')
                    name = name_el.get_attribute('aria-label') if name_el else card.inner_text().split("\n")[0]
                    link_el = card.query_selector('a[href*="/place/"]')
                    href = link_el.get_attribute("href") if link_el else None
                    raw_text = card.inner_text()
                    
                    phone_match = PHONE_RE.search(raw_text)
                    phone = phow_match.group(1) if phone_match else None
                    
                    if name and href:
                        entry = {
                            "name": name.strip(),
                            "website": href.strip(),
                            "phone": phone,
                            "raw_text": raw_text
                        }
                        
                        if entry not in results:
                            results.append(entry)
                            if len(results) >= max_result:
                                break
                            
                except Exception:
                    continue
                
            scroll_container.evaluate("(el) => el.scrollby(0, 1000)", scroll_container)
            time.sleep(1)
            
        browser.close()
    return results