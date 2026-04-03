from playwright.sync_api import sync_playwright
from scrapers.google_map_scraper import scrape_google_map
from utils.excel import save_to_excel
import os, time

AREAS = [
    "Ambawadi", "Amraiwadi", "Asarwa", "Ashram Road", "Aslali",
    "Astodia", "Bapunagar", "Bardolpura", "Behrampura", "Bhadra",
    "Bodakdev", "Bopal", "CG Road", "Chandkheda", "Chandlodia",
    "Changodar", "CTM", "CTM Char Rasta", "Dani Limbada", "Dariapur",
    "Delhi Chakla", "Delhi Darwaja", "Drive In Road", "Dudheshwar",
    "Dudheshwar Road", "Ellis Bridge", "Gandhi Road", "Geeta Mandir",
    "Geeta Mandir Road", "Ghatlodia", "Gheekanta", "Gheekanta Road",
    "Ghodasar", "Gomtipur", "Gota", "Gulbai Tekra", "Gurukul",
    "Hatkeshwar", "Income Tax", "Isanpur", "Jamalpur", "Jasodanagar",
    "Jivraj Park", "Jodhpur", "Juhapura", "Juna Wadaj", "Kalupur",
    "Kankaria", "Kankaria Road", "Kathwada", "Khadia", "Khamasa",
    "Khanpur", "Khokhara", "Krishnanagar", "Kuber Nagar", "Madhupura",
    "Manek Chowk", "Maninagar", "Meghani Nagar", "Memnagar",
    "Mirzapur", "Mirzapur Road", "Naranpura", "Naroda", "Naroda GIDC",
    "Naroda road", "Narol", "Nava Wadaj", "Navarangpura Gam", "Nikol",
    "Nirnay Nagar", "Odhav", "Odhav GIDC", "Odhav Road", "Paldi",
    "Pankore Naka", "Patharkuva", "Patthar Kuva", "Raipur", "Rakhial",
    "Ranip", "Ranna Park", "Ratan Pole", "Revdi Bazaar", "Sabarmati",
    "Sahijpur Bogha", "Sarangpur", "Saraspur", "Sardar Nagar", "Sarkej",
    "Sarkhej Gandhinagar Highway", "Satellite", "Satellite Road",
    "Shah Alam Road", "Shahibagh", "Shahibaug Road", "Shahpur", "Sola",
    "Sola Road", "Subhash Bridge", "Tavdipura", "Teen Darwaja",
    "Thakkarbapa Nagar", "Thaltej", "Usmanpura", "Vasna", "Vastral",
    "Vastrapur", "Vatva", "Vatva GIDC", "Vejalpur",
]


def get_input():
    print("\n--- Location Scraper ---\n")

    city = input("City (default: ahmedabad): ").strip()
    if not city:
        city = "ahmedabad"

    category = input("What to search (e.g. cafes, pg hostels, restaurants): ").strip()
    if not category:
        print("Category is required.")
        return None

    print(f"\nAvailable areas ({len(AREAS)} total):")
    for i, a in enumerate(AREAS, 1):
        print(f"  {i:3}. {a}")

    print("\nOptions:")
    print("  - Press Enter to scrape ALL areas")
    print("  - Type area numbers separated by comma (e.g. 1,5,10)")
    print("  - Type area names separated by comma")

    area_input = input("\nAreas: ").strip()

    if not area_input:
        selected = AREAS[:]
    else:
        selected = []
        parts = [p.strip() for p in area_input.split(",")]
        for p in parts:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(AREAS):
                    selected.append(AREAS[idx])
                else:
                    print(f"Invalid index: {p}")
            else:
                match = [a for a in AREAS if a.lower() == p.lower()]
                if match:
                    selected.append(match[0])
                else:
                    selected.append(p)

    if not selected:
        print("No areas selected.")
        return None

    return city, category, selected


def save_results(all_results, category, city):
    if not all_results:
        print("\nNo results to save.")
        return
    filename = f"{category.replace(' ', '_')}_{city}.xlsx"
    filepath = os.path.join("data", filename)
    os.makedirs("data", exist_ok=True)
    save_to_excel(all_results, filepath)
    print(f"\nSaved {len(all_results)} results to {os.path.abspath(filepath)}")


def run():
    result = get_input()
    if not result:
        return

    city, category, areas = result
    total = len(areas)
    all_results = []

    print(f"\nStarting: {category} in {total} area(s) of {city}")
    print(f"Scraping all available results for each area")
    print(f"Press Ctrl+C to stop - partial results will be saved\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            for i, area in enumerate(areas, 1):
                print(f"[{i}/{total}] {area}...")
                start = time.time()
                try:
                    data = scrape_google_map(page, area, city, search_type=category)
                    all_results.extend(data)
                    print(f"  -> {len(data)} results ({time.time() - start:.1f}s)")
                except Exception as e:
                    print(f"  error: {e}")
        except KeyboardInterrupt:
            print("\n\nInterrupted. Saving collected results...")
        finally:
            try:
                browser.close()
            except:
                pass

    save_results(all_results, category, city)


if __name__ == "__main__":
    run()
