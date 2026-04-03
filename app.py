import streamlit as st
import pandas as pd
import subprocess
import os
import sys
import time
import glob
from datetime import datetime

# page config
st.set_page_config(
    page_title="Location Scraper",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
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
    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #0a0a0f;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        width: 100%;
    }
    .info-box {
        background: rgba(30, 30, 50, 0.6);
        border: 1px solid rgba(100, 100, 255, 0.15);
        border-radius: 10px;
        padding: 1.5rem;
        color: #aaaacc;
        margin: 1rem 0;
    }
    .info-box h4 { color: #667eea; margin-bottom: 0.5rem; }
    .info-box code {
        background: rgba(0,0,0,0.3);
        padding: 2px 6px;
        border-radius: 4px;
        color: #38ef7d;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
    <h1>Location Scraper</h1>
    <p>Google Maps data extraction - View & Download results</p>
</div>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.markdown("### Data Source")
    mode = st.radio("", ["View scraped data", "Upload Excel file"], label_visibility="collapsed")

    if mode == "View scraped data":
        st.markdown("---")
        # find existing excel files in data/
        data_dir = "data"
        excel_files = []
        if os.path.exists(data_dir):
            excel_files = sorted(glob.glob(os.path.join(data_dir, "*.xlsx")))

        if excel_files:
            file_names = [os.path.basename(f) for f in excel_files]
            selected_file = st.selectbox("Select file", file_names)
            selected_path = os.path.join(data_dir, selected_file) if selected_file else None
        else:
            selected_path = None
            st.caption("No data files found. Run the scraper locally first.")

        st.markdown("---")


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
        st.error(f"Error reading file: {e}")
        return None


def display_data(sheets, filepath):
    if not sheets:
        st.warning("No data found in this file.")
        return

    filename = os.path.basename(filepath)

    # get combined sheet
    main_sheet = sheets.get("All Results", list(sheets.values())[0])
    all_areas = [name for name in sheets.keys() if name != "All Results"]

    # stats
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
        f'<div class="stat-card"><div class="num">{total}</div><div class="label">Total Results</div></div>',
        unsafe_allow_html=True)
    col2.markdown(
        f'<div class="stat-card"><div class="num">{phone_count}</div><div class="label">With Phone</div></div>',
        unsafe_allow_html=True)
    col3.markdown(
        f'<div class="stat-card"><div class="num">{len(all_areas)}</div><div class="label">Areas</div></div>',
        unsafe_allow_html=True)

    st.markdown("")

    # tabs for sheets
    if len(sheets) > 1:
        tab_names = list(sheets.keys())
        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            with tab:
                st.dataframe(sheets[name], use_container_width=True, hide_index=True)
    else:
        st.dataframe(main_sheet, use_container_width=True, hide_index=True)

    # download button
    st.markdown("")
    with open(filepath, "rb") as f:
        data = f.read()

    st.download_button(
        label=f"Download {filename}",
        data=data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # show areas as tags
    if all_areas:
        st.markdown("")
        st.markdown("**Areas covered:**")
        tags = "".join([f'<span class="area-tag">{a}</span>' for a in all_areas])
        st.markdown(f'<div style="margin-top:8px">{tags}</div>', unsafe_allow_html=True)


# main content
if mode == "View scraped data":
    if selected_path and os.path.exists(selected_path):
        sheets = load_excel(selected_path)
        if sheets:
            display_data(sheets, selected_path)
    else:
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; padding: 3rem 0; color: #555577;">
            <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">No scraped data found</p>
            <p style="font-size: 0.85rem;">Run <code style="color:#38ef7d">python main.py</code> locally to scrape data, then push to GitHub</p>
        </div>
        """, unsafe_allow_html=True)

elif mode == "Upload Excel file":
    st.markdown("---")
    uploaded = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
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
                    f'<div class="stat-card"><div class="num">{total}</div><div class="label">Total Results</div></div>',
                    unsafe_allow_html=True)
                col2.markdown(
                    f'<div class="stat-card"><div class="num">{len(all_areas)}</div><div class="label">Areas</div></div>',
                    unsafe_allow_html=True)
                col3.markdown(
                    f'<div class="stat-card"><div class="num">{len(sheets)}</div><div class="label">Sheets</div></div>',
                    unsafe_allow_html=True)

                if len(sheets) > 1:
                    tabs = st.tabs(list(sheets.keys()))
                    for tab, name in zip(tabs, sheets.keys()):
                        with tab:
                            st.dataframe(sheets[name], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(main_sheet, use_container_width=True, hide_index=True)

                if all_areas:
                    st.markdown("")
                    st.markdown("**Areas:**")
                    tags = "".join([f'<span class="area-tag">{a}</span>' for a in all_areas])
                    st.markdown(f'<div style="margin-top:8px">{tags}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 0; color: #555577;">
            <p style="font-size: 1.1rem;">Upload a scraped Excel file to view the data</p>
        </div>
        """, unsafe_allow_html=True)
