# streamlit_app.py

import json
from typing import List

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from jinja2 import Template
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from tree_chart_data_gen import get_latest_df  # optional helper to fetch fresh data
from calendar_widget import render_calendar      # your calendar widget

# Constants
PARQUET_PATH         = "data/latest_sp500.parquet"
CACHE_TTL            = 600  # cache for 10 minutes
JS_FILE_PATH         = "tree_chart_example.js"
HTML_TEMPLATE_PATH   = "tree_chart_example.html"
GRID_LITE_HTML_PATH  = "grid_lite_example.html"
GRID_LITE_JS_PATH    = "grid_lite_example.js"

@st.cache_data(ttl=CACHE_TTL)
def load_data(parquet_path: str = PARQUET_PATH) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path)
    df['Date_prev']   = pd.to_datetime(df['Date_prev'])
    df['Date_latest'] = pd.to_datetime(df['Date_latest'])
    return df


def generate_treemap_data(df: pd.DataFrame) -> str:
    nodes: List[dict] = []
    for industry in df["Industry"].unique():
        nodes.append({"id": industry, "name": industry, "custom": {"fullName": industry}})
    for _, row in df.iterrows():
        ind      = row["Industry"]
        sec      = row["Sector"]
        if not any(n["id"] == sec for n in nodes):
            nodes.append({"id": sec, "name": sec, "parent": ind, "custom": {"fullName": sec}})
        sym      = row["Symbol"]
        date_str = row['Date_latest'].date().isoformat()
        nodes.append({
            "id": sym,
            "name": sym,
            "parent": sec,
            "value": row["Market Cap"],
            "colorValue": row["Performance"],
            "custom": {
                "fullName": f"{sym} – {row['Name']}",
                "performance": f"{row['Performance']:+.2f}%",
                "asOfDate": date_str
            }
        })
    return json.dumps(nodes)


def configure_table(df: pd.DataFrame) -> dict:
    gb = GridOptionsBuilder.from_dataframe(df)

    dateFmt = JsCode(
        "function(params) { return params.value ? new Date(params.value).toLocaleDateString() : ''; }"
    )
    for col in ['Date_prev', 'Date_latest']:
        gb.configure_column(
            field=col,
            headerName=('Prev Date' if col=='Date_prev' else 'Latest Date'),
            valueFormatter=dateFmt,
            sortable=True,
            resizable=True
        )

    numFmt = JsCode(
        "function(params) { if (params.value == null) return ''; return parseFloat(params.value).toFixed(2) + '%'; }"
    )
    for col in ["Previous_Close", "Latest_Price", "Market Cap", "Performance"]:
        gb.configure_column(
            field=col,
            valueFormatter=numFmt,
            type=["numericColumn"],
            sortable=True,
            resizable=True
        )

    color_perf = JsCode(
        "function(params) {"
        "  if (params.value > 0) return {color:'white',backgroundColor:'#2ecc59'};"
        "  if (params.value < 0) return {color:'white',backgroundColor:'#f73539'};"
        "  return {}; }"
    )
    gb.configure_column("Performance", cellStyle=color_perf)
    gb.configure_default_column(sortable=True, resizable=True)
    return gb.build()


def main():
    st.set_page_config(page_title="S&P 500 Treemap", layout="wide")

    df = load_data()
    # Use the actual previous trading day from the dataset
    trading_day = df['Date_latest'].max().date().isoformat()

    # Render centered calendar with the trading day
    col1, col2, col3 = st.columns(3)
    with col2:
        html_snippet = render_calendar(trading_day)
        components.html(html_snippet, height=180)

    # Treemap
    st.markdown("### S&P 500 Treemap")
    treemap_data = generate_treemap_data(df)
    with open(JS_FILE_PATH, encoding="utf-8") as fjs, open(HTML_TEMPLATE_PATH, encoding="utf-8") as fhtml:
        js_txt   = fjs.read()
        html_tpl = fhtml.read()
    html = Template(html_tpl).render(
        CHART_JS=js_txt,
        TREE_DATA_JSON=treemap_data
    )
    components.html(html, height=900, scrolling=True)

    # Table
    st.markdown("### Interactive S&P 500 Table")
    grid_opts = configure_table(df)
    AgGrid(
        df,
        gridOptions=grid_opts,
        theme="alpine",
        height=500,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
    )

    # Grid‑Lite table section
    st.markdown("## S&P 500 Data Table")
    with open(GRID_LITE_JS_PATH,   encoding="utf-8") as fjs, \
         open(GRID_LITE_HTML_PATH, encoding="utf-8") as fhtml:
        grid_js   = fjs.read()
        grid_tpl  = fhtml.read()
    # Prepare the data JSON exactly as your HTML expects
    data_json = json.dumps({
        col: (
            df[col].dt.strftime('%Y-%m-%d').tolist()
            if col in ['Date_prev', 'Date_latest']
            else df[col].tolist()
        )
        for col in df.columns
    })
    grid_html = Template(grid_tpl).render(
        GRID_LITE_JS=grid_js,
        DATA_JSON=data_json
    )
    components.html(grid_html, height=600, scrolling=True)

if __name__ == "__main__":
    main()
