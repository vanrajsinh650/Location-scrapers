from playwright.sync_api import sync_playwright

def scrape_generic_site(url):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        
        elements = page.query_selector_all("a")
        for el in elements:
            name = el.inner_text().strip()
            href = el.get_attribute("href")
            if name and href:
                results.append({"name": name, "website": href})
                
                
        browser.close()
    return results