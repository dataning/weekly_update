# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from portfolio_mechnins_01 import PortfolioPerformanceCalculator
import pandas as pd
from great_tables import GT, html
import json
from collections import defaultdict
from jinja2 import Template
from great_tables_agg import render_relative_performance_table, render_relative_contributions_table
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(
    page_title="ThemePark",
    page_icon="📊",
    layout="wide"
)
# Load baskets from files
calc = PortfolioPerformanceCalculator(
    data_loader=lambda: PortfolioPerformanceCalculator.load_weighted_baskets(
        format='parquet', directory='baskets'
    ),
    mapping_loader=lambda: PortfolioPerformanceCalculator.load_json_mapping(
        'basket_benchmark_mapping.json'
    )
)


# Compute returns
calc.calculate_daily_returns()

# Get aligned returns DataFrames
baskets_ret, benchmarks_ret = calc.get_aligned_performance_dfs(cumulative=True)

# Performance summary
perf_df = calc.calculate_performance_metrics()

# Relative performance vs benchmarks
rel_df = calc.calculate_relative_performance()

merge_map = {
    'us_defense': 'Defensive & Quality',
    'eu_quality': 'Defensive & Quality',
    'us_quality': 'Defensive & Quality',
    'enterprise_tech': 'Tech & Digital',
    'sbti_tech': 'Tech & Digital',
    'green_technologies': 'Energy Transition',
    'transition_materiality_long': 'Energy Transition',
    'global_energy_transition': 'Energy Transition',
    'global_clean_oil_gas': 'Energy Transition',
    'transition_materiality_short': 'Transition Risk Short',
    'biodiversity': 'Nature & ESG',
    'biodiversity_esg': 'Nature & ESG',
    'resource_efficiency': 'Nature & ESG',
    'global_brands': 'Global Brands',
    'global_brands_esg': 'Global Brands'
}

# Apply mapping to create new column
rel_df['Merged_Theme'] = rel_df['Basket'].map(merge_map)
# Reorder columns
cols = ['Basket', 'Benchmark', 'Merged_Theme'] + [col for col in rel_df.columns if col not in ['Basket', 'Benchmark', 'Merged_Theme']]
rel_df = rel_df[cols]

# Create a new nested structure organized by theme first, then benchmark
theme_first = defaultdict(lambda: defaultdict(list))

for _, row in rel_df.iterrows():
    bm = row["Benchmark"]
    theme = row["Merged_Theme"]
    basket = row["Basket"]
    mtd = row["MTD"]
    
    # Invert the hierarchy: theme -> benchmark -> basket
    theme_first[theme][bm].append({
        "basketName": basket,
        "MTD": mtd
    })

# Convert defaultdicts to plain dicts
theme_first = {theme: dict(benchmarks) for theme, benchmarks in theme_first.items()}

# Now rebuild the treemap with the new hierarchy
treemap = []

# 1) Add theme-level nodes as top level
for theme in theme_first:
    treemap.append({
        "id": theme,
        "name": theme,
        "custom": {"fullName": theme}
    })

# 2) Add benchmark-level nodes as second level
for theme, benchmarks in theme_first.items():
    for bm in benchmarks:
        treemap.append({
            "id": f"{theme}|{bm}",
            "name": bm,
            "parent": theme,
            "custom": {"fullName": bm}
        })

# 3) Add basket-level leaves
for theme, benchmarks in theme_first.items():
    for bm, baskets in benchmarks.items():
        benchmark_id = f"{theme}|{bm}"
        for basket in baskets:
            # Scale MTD to percentage
            pct = basket["MTD"] * 100
            
            treemap.append({
                "id": basket["basketName"],
                "name": basket["basketName"],
                "parent": benchmark_id,
                "value": pct,
                "custom": {
                    "fullName": basket["basketName"],
                    "performance": f"{pct:.2f}%"
                }
            })

# Continue with existing code to render the template
JS_FILE_PATH = "tree_chart_example.js"
HTML_TEMPLATE_PATH = "tree_chart_example.html"

with open(JS_FILE_PATH, encoding="utf-8") as fjs, open(HTML_TEMPLATE_PATH, encoding="utf-8") as fhtml:
    js_txt = fjs.read()
    html_tpl = fhtml.read()

html = Template(html_tpl).render(
    CHART_JS=js_txt,
    TREE_DATA_JSON=treemap
)

components.html(
    html,
    height=900,
    scrolling=True
)

# Ticker contributions for a basket
# contrib_df = calc.calculate_ticker_contributions('us_defense')

# Add a title
st.title("ThemePark")

# def to_treemap_data_bucketed(df: pd.DataFrame) -> list[dict]:
#     """
#     Build treemap data with:
#       • Parent nodes = Benchmark (id=name, value=sum(MTD), custom.performance)
#       • Child nodes  = Basket    (parent=benchmark, value=MTD, custom.performance)
#     """
#     totals = df.groupby('Benchmark')['MTD'].sum().reset_index()

#     nodes = []
#     # 1) Parent nodes must include value=sum(MTD)
#     for _, r in totals.iterrows():
#         nodes.append({
#             'id':      r.Benchmark,
#             'name':    r.Benchmark.upper(),
#             'value':   r.MTD,
#             'custom':  {'performance': f"{r.MTD*100:.2f}%"}
#         })

#     # 2) Then child nodes
#     for _, r in df.iterrows():
#         nodes.append({
#             'name':   r.Basket,
#             'parent': r.Benchmark,
#             'value':  r.MTD,
#             'custom': {'performance': f"{r.MTD*100:.2f}%"}
#         })

#     return nodes

# treemap_data = to_treemap_data_bucketed(rel_df[['Basket', 'Benchmark', 'MTD']])


# # 2. Highcharts JS template
# chart_js = r"""
# function renderChart(data) {
#   Highcharts.chart('container', {
#     chart: {
#       backgroundColor: '#252931',
#       spacing: [10,10,60,10]
#     },
#     credits:{enabled:false},
#     series:[{
#       type:'treemap',
#       layoutAlgorithm:'squarified',
#       allowDrillToNode:false,
#       colorByPoint:true,
#       data:data,
#       levels:[
#         {
#           level:1,
#           borderWidth:3,
#           dataLabels:{
#             enabled:true,
#             align:'left',
#             style:{fontWeight:'bold',fontSize:'1.1em',color:'white'},
#             format:'{point.name}<br><span style="font-size:0.9em">{point.custom.performance}</span>'
#           }
#         },
#         {
#           level:2,
#           dataLabels:{
#             enabled:true,
#             align:'center',
#             style:{color:'white',fontSize:'0.75em'},
#             format:'{point.name}<br><span style="font-size:0.75em">{point.custom.performance}</span>'
#           }
#         }
#       ]
#     }],
#     title:{text:'Basket MTD Performance by Benchmark',style:{color:'white'}},
#     subtitle:{text:'Size = total MTD by Benchmark; baskets nested inside.',style:{color:'silver'}},
#     tooltip:{pointFormatter:function(){return `<b>${this.name}</b>: ${(this.value*100).toFixed(2)}%`;}},
#     colorAxis:{
#       min:-0.10,
#       max:0.10,
#       minColor:'#f73539',
#       maxColor:'#2ecc59',
#       stops:[[0,'#f73539'],[0.5,'#414555'],[1,'#2ecc59']],
#       labels:{style:{color:'white'},format:'{value:.0%}'},
#       legend:{
#         enabled:true,
#         layout:'horizontal',
#         align:'center',
#         verticalAlign:'bottom',
#         symbolWidth:300,
#         symbolHeight:12,
#         itemStyle:{color:'white'},
#         margin:0,padding:0
#       }
#     },
#     exporting:{enabled:false}
#   });
# }
# """

# html = f"""
# <!DOCTYPE html><html><head>
#   <script src="https://code.highcharts.com/highcharts.js"></script>
#   <script src="https://code.highcharts.com/modules/treemap.js"></script>
# </head>
# <body style="margin:0;background:#252931;">
#   <div id="container" style="width:100%;height:650px;"></div>
#   <script>
#     {chart_js}
#     renderChart({treemap_data});
#   </script>
# </body></html>
# """

# st.components.v1.html(html, height=700)

# Add some text
st.write("This is a simple demonstration of PAG's capabilities.")

# Create a sidebar
st.sidebar.header("Performance visualization")

# Create two columns
# col1, col2 = st.columns(2)

# with col1:
st.header("Performance of baskets")

render_relative_performance_table(rel_df, height=800)

# Convert the filtered DataFrame to Highcharts-compatible format using Date.UTC for datetime parsing
series_data = [
    {
        "name": column,
        "data": [[int(date.timestamp() * 1000), value] for date, value in baskets_ret[column].dropna().items()]
    }
    for column in baskets_ret.columns
]

# Convert each date to Date.UTC format and remove the quotes to treat it as a JavaScript expression
series_data_str = str(series_data).replace('"Date.UTC(', 'Date.UTC(').replace(')"', ')')

# HTML template for Highcharts with Date.UTC and x-axis adjustments
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <div id="container"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function () {{
            Highcharts.chart('container', {{
                chart: {{
                    type: 'line'
                }},
                title: {{
                    text: 'Basket Performances Since January 2024'
                }},
                xAxis: {{
                    type: 'datetime',
                    dateTimeLabelFormats: {{
                        day: '%b-%d',
                        week: '%b-%d',
                        month: '%b-%d',
                        year: '%Y'
                    }},
                    title: {{
                        text: 'Date'
                    }}
                }},
                yAxis: {{
                    title: {{
                        text: 'Performance (Rebased to 100)'
                    }}
                }},
                series: {series_data_str},
                credits: {{
                    enabled: false
                }}
            }});
        }});
    </script>
</head>
</html>
"""

# Use Streamlit to display the Highcharts chart
st.components.v1.html(html_code, height=450)

st.header("Basket Relative Contributions")
basket_choice = st.selectbox("Select a Basket:", list(baskets_ret.columns))
ticker_contributions = calc.calculate_ticker_contributions(basket_choice)

render_relative_contributions_table(ticker_contributions, basket_choice, height=600)

ticker_contributions_comparison = ticker_contributions.copy()
# # Apply the cleaning function to each percentage column
ticker_contributions_comparison['Weight'] = ticker_contributions_comparison['Weight'] * 100
ticker_contributions_comparison['QTD_rel'] = ticker_contributions_comparison['QTD_rel'] * 100
ticker_contributions_comparison['YTD_rel'] = ticker_contributions_comparison['YTD_rel'] * 100

# # Prepare data for embedding in JavaScript
companies = ticker_contributions_comparison['Company'].tolist()
weight_data = ticker_contributions_comparison['Weight'].round(3).tolist()
qtd_data = ticker_contributions_comparison['QTD_rel'].round(3).tolist()
ytd_data = ticker_contributions_comparison['YTD_rel'].round(3).tolist()

# JavaScript Highcharts code embedded in an HTML component
html_code = f"""
<div id="container" style="width:100%; height:600px;"></div>
<script src="https://code.highcharts.com/highcharts.js"></script>
<script>
    Highcharts.chart('container', {{
        chart: {{
            type: 'bar'
        }},
        title: {{
            text: 'Tech Giants - Contribution Metrics',
            align: 'left'
        }},
        subtitle: {{
            text: 'Source: Contribution Data',
            align: 'left'
        }},
        xAxis: {{
            categories: {companies},
            title: {{
                text: null
            }},
            gridLineWidth: 1,
            lineWidth: 0
        }},
        yAxis: {{
            min: 0,
            title: {{
                text: 'Percentage (%)',
                align: 'high'
            }},
            labels: {{
                overflow: 'justify'
            }}
        }},
        tooltip: {{
            valueSuffix: '%'
        }},
        plotOptions: {{
            bar: {{
                borderRadius: '5%',
                dataLabels: {{
                    enabled: true
                }},
                groupPadding: 0.1
            }}
        }},
        legend: {{
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            x: -40,
            y: 80,
            floating: true,
            borderWidth: 1,
            backgroundColor: '#FFFFFF',
            shadow: true
        }},
        credits: {{
            enabled: false
        }},
        series: [{{
            name: 'Weight',
            data: {weight_data}
        }}, {{
            name: 'QTD Contribution',
            data: {qtd_data}
        }}, {{
            name: 'YTD Contribution',
            data: {ytd_data}
        }}]
    }});
</script>
"""

# Display in Streamlit using st.components.v1.html
st.components.v1.html(html_code, height=600)