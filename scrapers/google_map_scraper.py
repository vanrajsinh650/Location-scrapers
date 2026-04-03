from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
import time
import re

PHONE_RE = re.compile(r'(\+?\d[\d\-\s\(\)]{6,}\d)')


def extract_phone(text):
    if not text:
        return None
    m = PHONE_RE.search(text)
    return m.group(1).strip() if m else None


def dismiss_consent(page):
    """handle google cookie/consent popup if it shows up."""
    try:
        btn = page.query_selector('button[aria-label="Accept all"]')
        if btn:
            btn.click()
            time.sleep(1)
            return
        btn = page.query_selector('form[action*="consent"] button')
        if btn:
            btn.click()
            time.sleep(1)
    except:
        pass


def scroll_and_collect_links(page, pause=2.0):
    """scroll the results feed and collect all place links."""
    try:
        page.wait_for_selector('div[role="feed"]', timeout=10000)
    except:
        return []

    feed = page.query_selector('div[role="feed"]')
    if not feed:
        return []

    seen = set()
    links = []
    no_new = 0
    prev_count = 0

    while True:
        # check end of list
        try:
            spans = page.query_selector_all('p.fontBodyMedium span span')
            for s in spans:
                txt = s.inner_text().lower()
                if "end" in txt or "reached" in txt:
                    print("  end of list reached")
                    # collect one final time before returning
                    for a in page.query_selector_all('div[role="feed"] a[href*="/place/"]'):
                        href = a.get_attribute("href")
                        if href and href not in seen:
                            seen.add(href)
                            links.append(href)
                    return links
        except:
            pass

        # collect links from current view
        for a in page.query_selector_all('div[role="feed"] a[href*="/place/"]'):
            try:
                href = a.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    links.append(href)
            except:
                continue

        if len(links) == prev_count:
            no_new += 1
        else:
            no_new = 0
        prev_count = len(links)

        if no_new >= 5:
            print("  no more new results")
            break

        feed.evaluate("(el) => el.scrollBy(0, 800)")
        time.sleep(pause)

    return links


def get_place_details(page, url):
    """visit a place url and extract name, phone, address, rating."""
    info = {"website": url, "name": "", "phone": None, "address": "", "rating": ""}

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)
    except:
        return info

    # name
    try:
        h1 = page.query_selector('h1')
        if h1:
            info["name"] = h1.inner_text().strip()
    except:
        pass

    # phone - method 1: tel: link
    try:
        tel = page.query_selector('a[href^="tel:"]')
        if tel:
            href = tel.get_attribute("href")
            if href:
                info["phone"] = href.replace("tel:", "").strip()
    except:
        pass

    # phone - method 2: copy phone button
    if not info["phone"]:
        try:
            btn = page.query_selector('button[data-tooltip="Copy phone number"]')
            if btn:
                aria = btn.get_attribute("aria-label") or ""
                p = extract_phone(aria)
                if p:
                    info["phone"] = p
                else:
                    info["phone"] = extract_phone(btn.inner_text())
        except:
            pass

    # phone - method 3: look for phone icon row
    if not info["phone"]:
        try:
            phone_icons = page.query_selector_all('img[src*="phone"], svg')
            for icon in phone_icons:
                parent = icon.evaluate_handle("el => el.closest('button') || el.parentElement")
                if parent:
                    text = parent.inner_text()
                    p = extract_phone(text)
                    if p:
                        info["phone"] = p
                        break
        except:
            pass

    # phone - method 4: search aria-labels
    if not info["phone"]:
        try:
            buttons = page.query_selector_all('button[aria-label]')
            for btn in buttons:
                label = btn.get_attribute("aria-label") or ""
                if "phone" in label.lower() or "call" in label.lower():
                    p = extract_phone(label)
                    if p:
                        info["phone"] = p
                        break
        except:
            pass

    # phone - method 5: scan all text for phone-like patterns
    if not info["phone"]:
        try:
            main_el = page.query_selector('div[role="main"]')
            if main_el:
                text = main_el.inner_text()
                for line in text.split("\n"):
                    line = line.strip()
                    # match lines that look like phone numbers
                    if re.match(r'^[\+]?[\d][\d\s\-\(\)]{6,14}[\d]$', line):
                        info["phone"] = line
                        break
        except:
            pass

    # address
    try:
        addr_btn = page.query_selector('button[data-tooltip="Copy address"]')
        if addr_btn:
            info["address"] = addr_btn.inner_text().strip()
    except:
        pass

    # rating
    try:
        rating_el = page.query_selector('div[role="img"][aria-label*="star"]')
        if rating_el:
            info["rating"] = rating_el.get_attribute("aria-label").strip()
    except:
        pass

    return info


def scrape_google_map(page, area, city, pause=2.0, search_type="cafes"):
    query = f"{search_type} in {area} {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)
    except Exception as e:
        print(f"  failed to load: {e}")
        return []

    dismiss_consent(page)

    # collect all place links
    links = scroll_and_collect_links(page, pause)
    if not links:
        print(f"  no places found")
        return []

    print(f"  {len(links)} places found, extracting details...")

    results = []
    for i, link in enumerate(links):
        info = get_place_details(page, link)
        info["area"] = area
        results.append(info)
        phone_status = info["phone"] if info["phone"] else "-"
        print(f"    [{i+1}/{len(links)}] {info['name'][:45]} | ph: {phone_status}")

    return results