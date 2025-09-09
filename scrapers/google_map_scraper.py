from playwright.sync_api import sync_playwright
import time
import re
import argparse

PHONE_RE = re.compile(r'(\+?\d[\d\-\s\(\)]{6,}\d)')

def extract_number_from_text(text):
    if not text:
        return None
    m = PHONE_RE.search(text)
    return m.group(1) if m else None

def scrape_google_map(area, city, max_result=20, headless=True, pause=2.0):
    results = []
    query = f"pg hostels {area} {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=30000)

        page.wait_for_selector('div[role="feed"]', timeout=30000)
        scroll_container = page.query_selector('div[role="feed"]') or page.query_selector('body')

        last_count = 0
        no_new_count = 0  

        while len(results) < max_result:
            #Use a more generic selector
            cards = page.query_selector_all('div[role="feed"] > div')

            print(f"Found {len(cards)} cards so far...")

            for card in cards:
                try:
                    name_el = card.query_selector('[aria-label]')
                    name = name_el.get_attribute('aria-label') if name_el else card.inner_text().split("\n")[0]

                    link_el = card.query_selector('a[href*="/place/"]')
                    href = link_el.get_attribute("href") if link_el else None

                    raw_text = card.inner_text()
                    phone = extract_number_from_text(raw_text)

                    if name and href:
                        unique_key = name + href
                        if unique_key in seen:
                            continue
                        seen.add(unique_key)

                        entry = {
                            "name": name.strip(),
                            "website": href.strip(),
                            "phone": phone,
                            "raw_text": raw_text
                        }
                        results.append(entry)
                        print("Added:", entry["name"])

                        if len(results) >= max_result:
                            break

                except Exception as e:
                    print("Error parsing card:", e)
                    continue

            if len(results) == last_count:
                no_new_count += 1
            else:
                no_new_count = 0
            last_count = len(results)

            if no_new_count >= 3:
                print("No more results found. Stopping scroll.")
                break

            scroll_container.evaluate("(el) => el.scrollBy(0, 1000)")
            time.sleep(pause)

        browser.close()
    return results