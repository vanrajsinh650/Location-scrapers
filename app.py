import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(
    page_title="Location Scraper",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #000000;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-image:
            linear-gradient(rgba(20,255,80,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(20,255,80,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    section[data-testid="stSidebar"] {
        background: #050505;
        border-right: 1px solid rgba(20,255,80,0.08);
    }
    section[data-testid="stSidebar"] * {
        color: #888 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #14ff50 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
    }

    .block-container { position: relative; z-index: 1; }

    .title-bar {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
    }
    .title-bar h1 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: #14ff50;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
        text-shadow: 0 0 30px rgba(20,255,80,0.3);
    }
    .title-bar .sub {
        font-family: 'JetBrains Mono', monospace;
        color: #333;
        font-size: 0.85rem;
        font-weight: 400;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    .stat-card {
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 1.4rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #14ff50, transparent);
    }
    .stat-card .num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .stat-card .label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #14ff50;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 6px;
        opacity: 0.8;
    }

    .area-tag {
        display: inline-block;
        background: transparent;
        border: 1px solid #1a1a1a;
        color: #555;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        margin: 2px;
        transition: all 0.2s ease;
    }
    .area-tag:hover {
        border-color: #14ff50;
        color: #14ff50;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #1a1a1a;
        border-radius: 6px;
        overflow: hidden;
    }

    .stDownloadButton > button {
        background: transparent;
        color: #14ff50;
        border: 1px solid #14ff50;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 0.85rem;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background: #14ff50;
        color: #000;
    }

    .stButton > button {
        background: transparent;
        color: #14ff50;
        border: 1px solid #222;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        width: 100%;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #050505;
        border-radius: 6px;
        padding: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #444;
        border-radius: 4px;
    }
    .stTabs [aria-selected="true"] {
        color: #14ff50 !important;
        background: #111 !important;
    }

    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #1a1a1a, transparent);
        margin: 1.5rem 0;
    }

    .empty-state {
        text-align: center;
        padding: 4rem 0;
    }
    .empty-state p {
        font-family: 'JetBrains Mono', monospace;
        color: #222;
        font-size: 0.9rem;
    }
    .empty-state .cmd {
        color: #14ff50;
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        padding: 8px 16px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 12px;
        font-size: 0.85rem;
    }

    /* file uploader */
    .stFileUploader {
        border-color: #1a1a1a !important;
    }

    h1, h2, h3, h4, h5, p, span, label, div {
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-bar">
    <h1>LOCATION SCRAPER</h1>
    <div class="sub">google maps data extraction</div>
</div>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.markdown("### Source")
    mode = st.radio("", ["View scraped data", "Upload Excel file"], label_visibility="collapsed")

    if mode == "View scraped data":
        st.markdown("---")
        data_dir = "data"
        excel_files = []
        if os.path.exists(data_dir):
            excel_files = sorted(glob.glob(os.path.join(data_dir, "*.xlsx")))

        if excel_files:
            file_names = [os.path.basename(f) for f in excel_files]
            selected_file = st.selectbox("File", file_names)
            selected_path = os.path.join(data_dir, selected_file) if selected_file else None
        else:
            selected_path = None
            st.caption("No data files found")


def load_excel(filepath):
    try:
        xl = pd.ExcelFile(filepath)
        sheets = {}
        for name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=name)
            if len(df) > 0:
                sheets[name] = df
        return sheets
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def display_data(sheets, filepath):
    if not sheets:
        st.warning("No data found.")
        return

    filename = os.path.basename(filepath)
    main_sheet = sheets.get("All Results", list(sheets.values())[0])
    all_areas = [name for name in sheets.keys() if name != "All Results"]

    total = len(main_sheet)
    phone_count = 0
    if len(main_sheet.columns) > 2:
        for p in main_sheet.iloc[:, 2]:
            try:
                val = str(p).strip() if p is not None else ""
                if val and val != "nan" and val != "None" and val != "No Info":
                    phone_count += 1
            except:
                pass

    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f'<div class="stat-card"><div class="num">{total}</div><div class="label">total results</div></div>',
        unsafe_allow_html=True)
    col2.markdown(
        f'<div class="stat-card"><div class="num">{phone_count}</div><div class="label">with phone</div></div>',
        unsafe_allow_html=True)
    col3.markdown(
        f'<div class="stat-card"><div class="num">{len(all_areas)}</div><div class="label">areas covered</div></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if len(sheets) > 1:
        tabs = st.tabs(list(sheets.keys()))
        for tab, name in zip(tabs, sheets.keys()):
            with tab:
                st.dataframe(sheets[name], use_container_width=True, hide_index=True)
    else:
        st.dataframe(main_sheet, use_container_width=True, hide_index=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    with open(filepath, "rb") as f:
        data = f.read()

    st.download_button(
        label=f"[ download ] {filename}",
        data=data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    if all_areas:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        tags = "".join([f'<span class="area-tag">{a}</span>' for a in all_areas])
        st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)


# main content
if mode == "View scraped data":
    if selected_path and os.path.exists(selected_path):
        sheets = load_excel(selected_path)
        if sheets:
            display_data(sheets, selected_path)
    else:
        st.markdown("""
        <div class="empty-state">
            <p>no data files found</p>
            <div class="cmd">python main.py</div>
        </div>
        """, unsafe_allow_html=True)

elif mode == "Upload Excel file":
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
    if uploaded:
        try:
            xl = pd.ExcelFile(uploaded)
            sheets = {}
            for name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=name)
                if len(df) > 0:
                    sheets[name] = df

            if sheets:
                main_sheet = sheets.get("All Results", list(sheets.values())[0])
                total = len(main_sheet)
                all_areas = [name for name in sheets.keys() if name != "All Results"]

                col1, col2, col3 = st.columns(3)
                col1.markdown(
                    f'<div class="stat-card"><div class="num">{total}</div><div class="label">total results</div></div>',
                    unsafe_allow_html=True)
                col2.markdown(
                    f'<div class="stat-card"><div class="num">{len(all_areas)}</div><div class="label">areas</div></div>',
                    unsafe_allow_html=True)
                col3.markdown(
                    f'<div class="stat-card"><div class="num">{len(sheets)}</div><div class="label">sheets</div></div>',
                    unsafe_allow_html=True)

                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

                if len(sheets) > 1:
                    tabs = st.tabs(list(sheets.keys()))
                    for tab, name in zip(tabs, sheets.keys()):
                        with tab:
                            st.dataframe(sheets[name], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(main_sheet, use_container_width=True, hide_index=True)

                if all_areas:
                    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                    tags = "".join([f'<span class="area-tag">{a}</span>' for a in all_areas])
                    st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.markdown("""
        <div class="empty-state">
            <p>drop an excel file to view data</p>
        </div>
        """, unsafe_allow_html=True)
