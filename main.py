# from scrapers.generic import scrape_generic_site
from scrapers.google_map_scraper import scrape_google_map

if __name__ == "__main__":
    # site_data = scrape_generic_site("https://example.com")
    # print("Generic Site Results:")
    # for item in site_data[:5]:
    #     print(item)

    # print("\n" + "-"*50 + "\n")

    maps_data = scrape_google_map("navrangpura", "ahmedabad")
    print("Google Maps Results:")
    for item in maps_data:
        print(item)
