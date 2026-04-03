# Location Scraper: Google Maps Business Data Extraction Engine

Location Scraper is an automated data extraction pipeline designed to collect comprehensive business information from Google Maps across configurable geographic areas. Built for researchers, marketers, and data analysts, it provides structured output with business names, phone numbers, addresses, and ratings — all exported to professionally formatted Excel files.

## Architecture & Core Logic

### 1. Two-Phase Extraction Engine

The scraper uses a two-step approach to maximize data accuracy:

- **Phase 1 — Discovery:** Navigates to Google Maps, scrolls through the results feed, and collects all unique place URLs. Detects end-of-list markers to avoid infinite scrolling.
- **Phase 2 — Detail Extraction:** Visits each place URL individually to extract name, phone, address, and rating from the detail page.

### 2. Multi-Fallback Phone Extraction

Phone numbers are often hidden or inconsistently formatted on Google Maps. The engine employs five sequential extraction methods:

1. `tel:` anchor links
2. "Copy phone number" button (`data-tooltip`)
3. Phone icon parent element traversal
4. `aria-label` scanning on all interactive buttons
5. Regex pattern matching on the full page text

If any method succeeds, the remaining methods are skipped.

### 3. Excel Output Formatting

The output engine generates styled Excel files using OpenPyXL:

- **Dark teal themed headers** with white text
- **Alternating row coloring** for readability
- **Dynamic column naming** based on the search category (e.g., "Cafes Name", "PG Hostels Name")
- **Phone-only filtering:** Only entries with valid phone numbers are included in the Excel output
- **Per-area sheets:** Individual sheets for each geographic area, plus a combined "All Results" sheet

### 4. Streamlit Cloud Dashboard

A web-based viewer for browsing and downloading scraped data. Supports three modes:

- **Scrape New Data:** Run the scraper directly from the browser with city, category, and area selection
- **View Saved Data:** Browse previously scraped Excel files stored in the `data/` directory
- **Upload Excel:** Upload any Excel file to view and analyze

Live Dashboard: [Launch on Streamlit Cloud](https://location-scrapers.streamlit.app)

---

## Quick Start

### Option A: Local Setup (Recommended)

Local execution provides the highest reliability since Google Maps does not block residential IP addresses.

**Linux / macOS**

```bash
git clone https://github.com/vanrajsinh650/Location-scrapers.git
cd Location-scrapers

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/vanrajsinh650/Location-scrapers.git
cd Location-scrapers

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### Option B: Streamlit Cloud

The application is deployed on Streamlit Cloud for browser-based access. No local setup required for viewing data. Scraping from cloud has limited reliability due to datacenter IP restrictions from Google.

---

## Usage

### Terminal Scraper (Full Control)

```bash
python main.py
```

The interactive CLI will prompt for:

| Prompt | Description | Default |
|--------|-------------|---------|
| City | Target city for scraping | `ahmedabad` |
| Category | What to search (cafes, restaurants, pg hostels, gyms, salons, etc.) | Required |
| Areas | Select from 112 predefined Ahmedabad areas, or enter custom area names | All areas |

**Example session:**

```
--- Location Scraper ---

City (default: ahmedabad): ahmedabad
What to search: pg hostels
Areas: [Enter for all]

Starting: pg hostels in 112 area(s) of ahmedabad
[1/112] Ambawadi...
  45 places found, extracting details...
    [1/45] Shree Hostel | ph: 09876543210
    [2/45] Royal PG | ph: -
    ...
  -> 45 results (180.2s)

Total scraped: 2400 | With phone: 1800 | Without: 600
Saved 1800 results (with phone only) to data/pg_hostels_ahmedabad.xlsx
```

**Graceful interruption:** Press `Ctrl+C` at any time. The scraper will save all results collected up to that point.

### Streamlit Dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Use the sidebar to switch between scraping, viewing, and uploading modes.

---

## Project Structure

```
Location-scrapers/
├── main.py                        # Terminal CLI entry point
├── app.py                         # Streamlit web dashboard
├── requirements.txt               # Python dependencies
├── packages.txt                   # System dependencies (Streamlit Cloud)
├── scrapers/
│   └── google_map_scraper.py      # Core extraction engine
├── utils/
│   └── excel.py                   # Excel formatting and export
└── data/                          # Output directory (generated Excel files)
```

### File Responsibilities

| File | Purpose |
|------|---------|
| `main.py` | Interactive terminal interface. Handles user input, browser lifecycle, and graceful interruption. Reuses a single browser instance across all areas. |
| `app.py` | Streamlit dashboard with three modes: scrape, view, upload. Includes live progress, stat cards, and download buttons. |
| `google_map_scraper.py` | Contains `scrape_google_map()`, `scroll_and_collect_links()`, `get_place_details()`, and `dismiss_consent()`. All extraction logic lives here. |
| `excel.py` | `save_to_excel()` generates themed workbooks with per-area sheets. Filters out entries without phone numbers. |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | 1.54.0 | Browser automation for Google Maps navigation |
| openpyxl | 3.1.5 | Excel file generation with styling |
| streamlit | latest | Web dashboard |
| pandas | latest | Data handling for Streamlit views |

Playwright requires a Chromium binary. Install it after pip:

```bash
playwright install chromium
```

---

## Configuration

### Predefined Areas

The scraper ships with 112 predefined areas of Ahmedabad. These can be modified in the `AREAS` list in `main.py` and `app.py`. Custom areas can also be entered at runtime without modifying the source code.

### Headless Mode

The browser runs in headless mode by default (`headless=True`). To debug visually, change this to `False` in `main.py` line 108:

```python
browser = p.chromium.launch(headless=False)
```

### Output Directory

All Excel files are saved to the `data/` directory. File names follow the pattern:

```
{category}_{city}.xlsx
```

Examples: `cafes_ahmedabad.xlsx`, `pg_hostels_ahmedabad.xlsx`, `restaurants_ahmedabad.xlsx`

---

## Known Limitations

- **Cloud IP blocking:** Google Maps may restrict or block requests from datacenter IPs (Streamlit Cloud, AWS, etc.). Local execution from a residential IP is recommended for production scraping.
- **Rate limiting:** Scraping large numbers of areas (100+) takes significant time (2-4 hours) because each place detail page is visited individually.
- **No resume support:** If the scraper is stopped mid-run, it restarts from the beginning on next execution. Partial results are saved on interruption.
- **Language:** Some business names may appear in Gujarati or Hindi depending on the Google Maps listing.

---

## License

MIT
