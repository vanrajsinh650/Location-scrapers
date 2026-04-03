import streamlit as st
import pandas as pd
import os
import glob

# -- config --
st.set_page_config(page_title="Location Scraper", layout="wide", initial_sidebar_state="expanded")

# -- init session state once --
for key, default in [("view_file", None), ("view_sheets", None), ("upload_sheets", None)]:
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
    h1,h2,h3,h4,h5,p,span,label,div { color:#888; }
</style>
""", unsafe_allow_html=True)

# -- title --
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
        st.error(f"Failed to read file: {e}")
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
    return areas


def render_download(filepath):
    name = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        st.download_button(
            label=f"[ download ] {name}", data=f.read(), file_name=name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# -- sidebar --
with st.sidebar:
    st.markdown("### Source")
    mode = st.radio("mode", ["View scraped data", "Upload Excel"], label_visibility="collapsed")

    # clear other mode's state when switching
    if mode == "View scraped data":
        st.session_state.upload_sheets = None
    else:
        st.session_state.view_file = None
        st.session_state.view_sheets = None

with st.sidebar:
    if mode == "View scraped data":
        st.markdown("---")
        data_dir = "data"
        files = sorted(glob.glob(os.path.join(data_dir, "*.xlsx"))) if os.path.exists(data_dir) else []

        if files:
            names = [os.path.basename(f) for f in files]
            pick = st.selectbox("File", names, index=0)
            path = os.path.join(data_dir, pick)

            # load button
            if st.button("Load", use_container_width=True):
                sheets = read_excel(path)
                if sheets:
                    st.session_state.view_file = path
                    st.session_state.view_sheets = sheets

            # clear button
            if st.session_state.view_sheets is not None:
                if st.button("Clear", use_container_width=True):
                    st.session_state.view_file = None
                    st.session_state.view_sheets = None
                    st.rerun()
        else:
            st.caption("No .xlsx files in data/ folder")


# -- main content --
if mode == "View scraped data":
    sheets = st.session_state.view_sheets
    fpath = st.session_state.view_file

    if sheets and fpath:
        main = sheets.get("All Results", list(sheets.values())[0])
        area_list = [n for n in sheets if n != "All Results"]

        render_stats(len(main), count_phones(main), len(area_list))
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        render_sheets(sheets)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        render_download(fpath)
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
