import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import glob
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from scrapers.google_map_scraper import scroll_and_collect_links, get_place_details, dismiss_consent
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

# -- install browser --
@st.cache_resource
def install_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       check=True, capture_output=True, text=True)
        return True
    except:
        return False

install_browser()

# -- config --
st.set_page_config(page_title="Location Scraper", layout="wide", initial_sidebar_state="expanded")

for key, default in [("view_file", None), ("view_sheets", None), ("scrape_results", []),
                      ("scrape_logs", []), ("scrape_running", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# -- styles --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #000; }
    .stApp::before {
        content:''; position:fixed; top:0; left:0; width:100%; height:100%;
        background-image:
            linear-gradient(rgba(20,255,80,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(20,255,80,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events:none; z-index:0;
    }
    section[data-testid="stSidebar"] {
        background:#050505; border-right:1px solid rgba(20,255,80,0.08);
    }
    .block-container { position:relative; z-index:1; }
    .title-bar { text-align:center; padding:2.5rem 0 1.5rem; }
    .title-bar h1 {
        font-family:'JetBrains Mono',monospace; font-size:2.4rem; font-weight:700;
        color:#14ff50; letter-spacing:-1px; margin-bottom:0.2rem;
        text-shadow:0 0 30px rgba(20,255,80,0.3);
    }
    .title-bar .sub {
        font-family:'JetBrains Mono',monospace; color:#333; font-size:0.85rem;
        letter-spacing:3px; text-transform:uppercase;
    }
    .stat-card {
        background:#0a0a0a; border:1px solid #1a1a1a; border-radius:8px;
        padding:1.4rem; text-align:center; position:relative; overflow:hidden;
    }
    .stat-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg,transparent,#14ff50,transparent);
    }
    .stat-card .num {
        font-family:'JetBrains Mono',monospace; font-size:2.2rem; font-weight:700; color:#fff;
    }
    .stat-card .label {
        font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#14ff50;
        text-transform:uppercase; letter-spacing:2px; margin-top:6px; opacity:0.8;
    }
    .area-tag {
        display:inline-block; background:transparent; border:1px solid #1a1a1a;
        color:#555; padding:4px 10px; border-radius:4px;
        font-family:'JetBrains Mono',monospace; font-size:0.7rem; margin:2px;
        transition:all 0.2s;
    }
    .area-tag:hover { border-color:#14ff50; color:#14ff50; }
    div[data-testid="stDataFrame"] { border:1px solid #1a1a1a; border-radius:6px; overflow:hidden; }
    .stDownloadButton>button {
        background:transparent; color:#14ff50; border:1px solid #14ff50;
        border-radius:6px; font-family:'JetBrains Mono',monospace; font-weight:500; width:100%;
        transition:all 0.2s;
    }
    .stDownloadButton>button:hover { background:#14ff50; color:#000; }
    .stButton>button {
        background:transparent; color:#14ff50; border:1px solid #222;
        border-radius:6px; font-family:'JetBrains Mono',monospace; font-weight:500; width:100%;
    }
    .stTabs [data-baseweb="tab-list"] { gap:0; background:#050505; border-radius:6px; padding:2px; }
    .stTabs [data-baseweb="tab"] {
        font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#444; border-radius:4px;
    }
    .stTabs [aria-selected="true"] { color:#14ff50 !important; background:#111 !important; }
    .divider { height:1px; background:linear-gradient(90deg,transparent,#1a1a1a,transparent); margin:1.5rem 0; }
    .empty-state { text-align:center; padding:4rem 0; }
    .empty-state p { font-family:'JetBrains Mono',monospace; color:#222; font-size:0.9rem; }
    .log-box {
        background:#050505; border:1px solid #1a1a1a; border-radius:6px;
        padding:1rem; font-family:'JetBrains Mono',monospace; font-size:0.75rem;
        color:#14ff50; max-height:350px; overflow-y:auto; line-height:1.8;
    }
    .log-box .dim { color:#333; }
    .log-box .err { color:#ff4444; }
    h1,h2,h3,h4,h5,p,span,label,div { color:#888; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-bar">
    <h1>LOCATION SCRAPER</h1>
    <div class="sub">google maps data extraction</div>
</div>
""", unsafe_allow_html=True)


# -- helpers --
def read_excel(filepath):
    try:
        xl = pd.ExcelFile(filepath)
        return {name: pd.read_excel(xl, sheet_name=name) for name in xl.sheet_names}
    except Exception as e:
        st.error(f"Failed to read: {e}")
        return None

def count_phones(df):
    if len(df.columns) < 3:
        return 0
    count = 0
    for val in df.iloc[:, 2]:
        try:
            s = str(val).strip()
            if s and s not in ("nan", "None", "No Info", ""):
                count += 1
        except:
            pass
    return count

def render_stats(total, phones, areas):
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><div class="num">{total}</div><div class="label">total results</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><div class="num">{phones}</div><div class="label">with phone</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><div class="num">{areas}</div><div class="label">areas covered</div></div>', unsafe_allow_html=True)

def render_sheets(sheets):
    if len(sheets) > 1:
        tabs = st.tabs(list(sheets.keys()))
        for tab, name in zip(tabs, sheets.keys()):
            with tab:
                st.dataframe(sheets[name], use_container_width=True, hide_index=True)
    else:
        st.dataframe(list(sheets.values())[0], use_container_width=True, hide_index=True)

def render_areas(sheets):
    areas = [n for n in sheets.keys() if n != "All Results"]
    if areas:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        tags = "".join(f'<span class="area-tag">{a}</span>' for a in areas)
        st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)

def render_download_file(filepath):
    name = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        st.download_button(label=f"[ download ] {name}", data=f.read(), file_name=name,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

def render_download_bytes(data, filename):
    st.download_button(label=f"[ download ] {filename}", data=data, file_name=filename,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)


# -- sidebar --
with st.sidebar:
    st.markdown("### Mode")
    mode = st.radio("mode", ["Scrape New Data", "View Saved Data", "Upload Excel"], label_visibility="collapsed")

# -- scrape mode sidebar --
if mode == "Scrape New Data":
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Scraper Config")
        city = st.text_input("City", value="ahmedabad")
        if not city:
            city = "ahmedabad"
        category = st.text_input("Category", placeholder="cafes, restaurants, pg hostels...")
        st.markdown("---")
        area_mode = st.radio("Areas", ["All areas", "Select areas", "Custom"])

        sel_areas = []
        if area_mode == "All areas":
            sel_areas = AREAS[:]
            st.caption(f"{len(sel_areas)} areas")
        elif area_mode == "Select areas":
            sel_areas = st.multiselect("Pick", AREAS, placeholder="Choose...")
        else:
            custom = st.text_input("Type areas", placeholder="Bopal, Satellite")
            if custom:
                sel_areas = [a.strip() for a in custom.split(",") if a.strip()]

        st.markdown("---")
        can_scrape = bool(category and sel_areas and not st.session_state.scrape_running)
        scrape_btn = st.button("Start Scraping", disabled=not can_scrape, use_container_width=True)

elif mode == "View Saved Data":
    with st.sidebar:
        st.markdown("---")
        data_dir = "data"
        files = sorted(glob.glob(os.path.join(data_dir, "*.xlsx"))) if os.path.exists(data_dir) else []
        if files:
            names = [os.path.basename(f) for f in files]
            pick = st.selectbox("File", names)
            path = os.path.join(data_dir, pick)
            load_btn = st.button("Load", use_container_width=True)
            if st.session_state.view_sheets and st.button("Clear", use_container_width=True):
                st.session_state.view_file = None
                st.session_state.view_sheets = None
                st.rerun()
        else:
            files = []
            st.caption("No files in data/ folder")


# -- scraper engine --
def run_cloud_scraper(city, category, areas):
    total = len(areas)
    all_results = []

    progress = st.progress(0, text="launching browser...")
    c1, c2, c3 = st.columns(3)
    stat_areas = c1.empty()
    stat_places = c2.empty()
    stat_phones = c3.empty()
    log_box = st.empty()
    table_box = st.empty()
    download_box = st.empty()
    logs = []

    def log(msg, level="ok"):
        ts = datetime.now().strftime("%H:%M:%S")
        cls = "err" if level == "err" else "dim" if level == "dim" else ""
        logs.append(f'<span class="{cls}">[{ts}]</span> {msg}')
        log_box.markdown(f'<div class="log-box">{"<br>".join(logs[-60:])}</div>', unsafe_allow_html=True)

    def update_stats(done):
        pc = sum(1 for r in all_results if r.get("phone"))
        stat_areas.markdown(f'<div class="stat-card"><div class="num">{done}/{total}</div><div class="label">areas</div></div>', unsafe_allow_html=True)
        stat_places.markdown(f'<div class="stat-card"><div class="num">{len(all_results)}</div><div class="label">places</div></div>', unsafe_allow_html=True)
        stat_phones.markdown(f'<div class="stat-card"><div class="num">{pc}</div><div class="label">phones</div></div>', unsafe_allow_html=True)

    update_stats(0)
    log(f"scraping: {category} in {city} ({total} areas)")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                    "--disable-gpu", "--disable-extensions", "--disable-background-networking",
                    "--single-process",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = context.new_page()
            log("browser ready", "dim")

            for i, area in enumerate(areas):
                progress.progress(i / total, text=f"scraping {area}... ({i+1}/{total})")
                log(f"--- [{i+1}/{total}] {area} ---")

                start = time.time()
                try:
                    query = f"{category} in {area} {city}"
                    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    time.sleep(3)
                    dismiss_consent(page)

                    links = scroll_and_collect_links(page, pause=2.0)
                    if not links:
                        log(f"  no places found", "dim")
                        update_stats(i + 1)
                        continue

                    log(f"  {len(links)} places found, extracting...")
                    for j, link in enumerate(links):
                        info = get_place_details(page, link)
                        info["area"] = area
                        all_results.append(info)
                        ph = info["phone"] if info["phone"] else "-"
                        if (j + 1) % 5 == 0 or j == len(links) - 1:
                            log(f"  {j+1}/{len(links)} | {info['name'][:28]} | ph: {ph}")

                    elapsed = time.time() - start
                    log(f"  {area}: {len(links)} results ({elapsed:.0f}s)")

                except Exception as e:
                    log(f"  error: {str(e)[:80]}", "err")

                update_stats(i + 1)

                # live table
                if all_results:
                    df = pd.DataFrame([{
                        "Name": r.get("name", ""), "Phone": r.get("phone", ""),
                        "Address": r.get("address", ""), "Rating": r.get("rating", ""),
                        "Area": r.get("area", ""),
                    } for r in all_results])
                    table_box.dataframe(df, use_container_width=True, hide_index=True)

            browser.close()

    except Exception as e:
        log(f"browser error: {str(e)[:100]}", "err")

    progress.progress(1.0, text="done!")
    with_phone = sum(1 for r in all_results if r.get("phone"))
    log(f"finished: {len(all_results)} total | {with_phone} with phone")

    # save and offer download
    if all_results:
        fname = f"{category.replace(' ', '_')}_{city}.xlsx"
        fpath = os.path.join("data", fname)
        os.makedirs("data", exist_ok=True)
        save_to_excel(all_results, fpath, category=category)
        log(f"saved: {fpath}")

        with open(fpath, "rb") as f:
            download_box.download_button(
                label=f"[ download ] {fname} ({with_phone} results with phone)",
                data=f.read(), file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    return all_results


# -- main content --
if mode == "Scrape New Data":
    if scrape_btn:
        st.session_state.scrape_running = True
        results = run_cloud_scraper(city, category, sel_areas)
        st.session_state.scrape_results = results
        st.session_state.scrape_running = False
    elif not st.session_state.scrape_running:
        st.markdown('<div class="empty-state"><p>configure scraper in sidebar and click start</p></div>', unsafe_allow_html=True)

elif mode == "View Saved Data":
    if files:
        if load_btn:
            sheets = read_excel(path)
            if sheets:
                st.session_state.view_file = path
                st.session_state.view_sheets = sheets

    sheets = st.session_state.view_sheets
    fpath = st.session_state.view_file

    if sheets and fpath:
        main = sheets.get("All Results", list(sheets.values())[0])
        area_list = [n for n in sheets if n != "All Results"]
        render_stats(len(main), count_phones(main), len(area_list))
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        render_sheets(sheets)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        render_download_file(fpath)
        render_areas(sheets)
    else:
        st.markdown('<div class="empty-state"><p>select a file and click load</p></div>', unsafe_allow_html=True)

elif mode == "Upload Excel":
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload .xlsx", type=["xlsx", "xls"], key="uploader")
    if uploaded:
        try:
            xl = pd.ExcelFile(uploaded)
            sheets = {n: pd.read_excel(xl, sheet_name=n) for n in xl.sheet_names}
            sheets = {k: v for k, v in sheets.items() if len(v) > 0}
            if sheets:
                main = sheets.get("All Results", list(sheets.values())[0])
                area_list = [n for n in sheets if n != "All Results"]
                render_stats(len(main), count_phones(main), len(area_list))
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                render_sheets(sheets)
                render_areas(sheets)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.markdown('<div class="empty-state"><p>drop an excel file to view</p></div>', unsafe_allow_html=True)
