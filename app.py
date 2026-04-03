import streamlit as st
import pandas as pd
import os
import time
import io
from datetime import datetime
from playwright.sync_api import sync_playwright
from scrapers.google_map_scraper import (
    scrape_google_map,
    scroll_and_collect_links,
    get_place_details,
    dismiss_consent,
)
from utils.excel import save_to_excel

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

# page config
st.set_page_config(
    page_title="Location Scraper",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# custom css
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main { background: #0a0a0f; }

    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 25, 0.95);
        border-right: 1px solid rgba(100, 100, 255, 0.1);
    }

    .title-block {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .title-block h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .title-block p {
        color: #8888aa;
        font-size: 0.95rem;
        font-weight: 300;
    }

    .stat-card {
        background: rgba(30, 30, 50, 0.6);
        border: 1px solid rgba(100, 100, 255, 0.15);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .stat-card .num {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .stat-card .label {
        font-size: 0.8rem;
        color: #8888aa;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    .log-box {
        background: rgba(10, 10, 20, 0.8);
        border: 1px solid rgba(100, 100, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.82rem;
        color: #aaaacc;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }

    .area-tag {
        display: inline-block;
        background: rgba(102, 126, 234, 0.15);
        border: 1px solid rgba(102, 126, 234, 0.3);
        color: #99aaee;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        margin: 2px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(100, 100, 255, 0.15);
        border-radius: 8px;
        overflow: hidden;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #0a0a0f;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }

    .stMultiSelect [data-baseweb="tag"] {
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.4);
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# title
st.markdown("""
<div class="title-block">
    <h1>Location Scraper</h1>
    <p>Google Maps data extraction tool</p>
</div>
""", unsafe_allow_html=True)

# sidebar inputs
with st.sidebar:
    st.markdown("### Configuration")

    city = st.text_input("City", value="ahmedabad", placeholder="ahmedabad")
    if not city:
        city = "ahmedabad"

    category = st.text_input(
        "Search Category",
        placeholder="e.g. cafes, restaurants, pg hostels"
    )

    st.markdown("---")
    st.markdown("### Area Selection")

    select_mode = st.radio(
        "Select areas",
        ["All areas", "Pick specific areas", "Type custom area"],
        horizontal=False,
    )

    selected_areas = []

    if select_mode == "All areas":
        selected_areas = AREAS[:]
        st.caption(f"{len(selected_areas)} areas selected")

    elif select_mode == "Pick specific areas":
        selected_areas = st.multiselect(
            "Choose areas",
            options=AREAS,
            default=[],
            placeholder="Select areas..."
        )

    elif select_mode == "Type custom area":
        custom = st.text_input("Enter area name(s)", placeholder="e.g. Bopal, Satellite")
        if custom:
            selected_areas = [a.strip() for a in custom.split(",") if a.strip()]

    st.markdown("---")

    can_start = bool(category and selected_areas)
    start_btn = st.button(
        "Start Scraping",
        disabled=not can_start,
        use_container_width=True,
    )

    if not category:
        st.caption("Enter a search category to begin")
    elif not selected_areas:
        st.caption("Select at least one area")


# session state
if "results" not in st.session_state:
    st.session_state.results = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "logs" not in st.session_state:
    st.session_state.logs = []


def run_scraper(city, category, areas):
    st.session_state.results = []
    st.session_state.logs = []
    st.session_state.is_running = True

    total = len(areas)
    all_results = []

    # ui elements
    progress_bar = st.progress(0, text="Starting...")
    col1, col2, col3 = st.columns(3)
    with col1:
        areas_done_ph = st.empty()
    with col2:
        places_found_ph = st.empty()
    with col3:
        phones_found_ph = st.empty()

    log_container = st.empty()
    table_container = st.empty()

    logs = []

    def log(msg):
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_html = "<br>".join(logs[-50:])
        log_container.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

    def update_stats(areas_done, total_areas):
        phone_count = sum(1 for r in all_results if r.get("phone"))
        with col1:
            areas_done_ph.markdown(
                f'<div class="stat-card"><div class="num">{areas_done}/{total_areas}</div><div class="label">Areas Done</div></div>',
                unsafe_allow_html=True
            )
        with col2:
            places_found_ph.markdown(
                f'<div class="stat-card"><div class="num">{len(all_results)}</div><div class="label">Places Found</div></div>',
                unsafe_allow_html=True
            )
        with col3:
            phones_found_ph.markdown(
                f'<div class="stat-card"><div class="num">{phone_count}</div><div class="label">Phone Numbers</div></div>',
                unsafe_allow_html=True
            )

    update_stats(0, total)
    log(f"Starting: {category} in {total} area(s) of {city}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            for i, area in enumerate(areas):
                progress = (i) / total
                progress_bar.progress(progress, text=f"Scraping {area}... ({i+1}/{total})")
                log(f"--- [{i+1}/{total}] {area} ---")

                start = time.time()
                try:
                    data = scrape_area_with_logs(page, area, city, category, log)
                    all_results.extend(data)
                    elapsed = time.time() - start
                    log(f"{area}: {len(data)} results ({elapsed:.0f}s)")
                except Exception as e:
                    log(f"{area}: error - {str(e)[:60]}")

                update_stats(i + 1, total)

                # update table
                if all_results:
                    df = pd.DataFrame([
                        {
                            "Name": r.get("name", ""),
                            "Phone": r.get("phone", ""),
                            "Address": r.get("address", ""),
                            "Rating": r.get("rating", ""),
                            "Area": r.get("area", ""),
                        }
                        for r in all_results
                    ])
                    table_container.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            log(f"Error: {e}")
        finally:
            browser.close()

    progress_bar.progress(1.0, text="Done!")
    st.session_state.results = all_results
    st.session_state.is_running = False
    log(f"Finished. Total: {len(all_results)} results")

    return all_results


def scrape_area_with_logs(page, area, city, search_type, log):
    query = f"{search_type} in {area} {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)
    except Exception as e:
        log(f"  failed to load page")
        return []

    dismiss_consent(page)

    links = scroll_and_collect_links(page, pause=2.0)
    if not links:
        log(f"  no places found")
        return []

    log(f"  {len(links)} places, getting details...")

    results = []
    for i, link in enumerate(links):
        info = get_place_details(page, link)
        info["area"] = area
        results.append(info)
        ph = info["phone"] if info["phone"] else "-"
        if (i + 1) % 5 == 0 or i == len(links) - 1:
            log(f"  progress: {i+1}/{len(links)} | last: {info['name'][:30]} | ph: {ph}")

    return results


# main flow
if start_btn and can_start:
    results = run_scraper(city, category, selected_areas)

    if results:
        st.markdown("---")
        st.markdown("### Download Results")

        # save to excel in memory
        filepath = os.path.join("data", f"{category.replace(' ', '_')}_{city}.xlsx")
        os.makedirs("data", exist_ok=True)
        save_to_excel(results, filepath)

        with open(filepath, "rb") as f:
            excel_bytes = f.read()

        st.download_button(
            label=f"Download Excel ({len(results)} results)",
            data=excel_bytes,
            file_name=f"{category.replace(' ', '_')}_{city}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.info(f"Also saved to: {os.path.abspath(filepath)}")

# show previous results if any
elif st.session_state.results and not st.session_state.is_running:
    results = st.session_state.results
    st.markdown("### Previous Results")

    col1, col2, col3 = st.columns(3)
    phone_count = sum(1 for r in results if r.get("phone"))
    with col1:
        st.markdown(
            f'<div class="stat-card"><div class="num">{len(results)}</div><div class="label">Total Places</div></div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f'<div class="stat-card"><div class="num">{phone_count}</div><div class="label">Phone Numbers</div></div>',
            unsafe_allow_html=True
        )
    with col3:
        areas_count = len(set(r.get("area", "") for r in results))
        st.markdown(
            f'<div class="stat-card"><div class="num">{areas_count}</div><div class="label">Areas Covered</div></div>',
            unsafe_allow_html=True
        )

    df = pd.DataFrame([
        {
            "Name": r.get("name", ""),
            "Phone": r.get("phone", ""),
            "Address": r.get("address", ""),
            "Rating": r.get("rating", ""),
            "Area": r.get("area", ""),
        }
        for r in results
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    # empty state
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0; color: #555577;">
        <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">Configure your search in the sidebar and click Start Scraping</p>
        <p style="font-size: 0.85rem;">Supports: cafes, restaurants, pg hostels, gyms, salons, and more</p>
    </div>
    """, unsafe_allow_html=True)

    # show selected areas preview
    if selected_areas:
        st.markdown("**Selected Areas:**")
        tags = "".join([f'<span class="area-tag">{a}</span>' for a in selected_areas])
        st.markdown(f'<div style="margin-top:8px">{tags}</div>', unsafe_allow_html=True)
