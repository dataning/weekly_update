import streamlit as st
import json
import pathlib
from streamlit.components.v1 import html as st_html

# 1. Define path to the JSON data file and load its contents
data_file = pathlib.Path("presidential_chart_data.json")
chart_data = json.loads(data_file.read_text())

# 2. Read in the HTML template and accompanying JS for the charts
template_file = pathlib.Path("multi_line_chart.html")
js_file = pathlib.Path("multi_line_chart.js")
html_template = template_file.read_text()
js_code = js_file.read_text()

# 3. Inject the chart data and inline JS into the HTML template
#    - Replace the placeholder comment with a <script> tag carrying JSON
#    - Replace the external charts.js import with the raw JS code
injected_html = (
    html_template
    .replace(
        '<!--CHART_DATA-->',
        f'<script id="data" type="application/json">{json.dumps(chart_data)}</script>'
    )
    .replace(
        '<script src="charts.js"></script>',
        f'<script>{js_code}</script>'
    )
)

# 4. Configure the Streamlit page
st.set_page_config(
    page_title="Presidential Approval Ratings",
    layout="wide"
)

# 5. Render the fully-injected HTML using Streamlit's HTML component
#    - Height is set to accommodate all rendered charts
st_html(injected_html, height=1800)
