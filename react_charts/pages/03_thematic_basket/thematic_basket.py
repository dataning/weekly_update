# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from portfolio_mechnins_01 import PortfolioPerformanceCalculator
import pandas as pd
from great_tables import GT, html


# Set page configuration
st.set_page_config(
    page_title="ThemePark",
    page_icon="📊",
    layout="wide"
)
# Load baskets from files
loaded_baskets_parquet = PortfolioPerformanceCalculator.load_weighted_baskets(format="parquet")
calculator = PortfolioPerformanceCalculator(weighted_baskets=loaded_baskets_parquet)
calculator.calculate_daily_returns()

# Retrieve basket and benchmark performances as DataFrames
# basket_performances_df, benchmark_performances_df = calculator.get_aligned_performance_dfs()
performance_summary = calculator.calculate_performance_metrics()
relative_performance = calculator.calculate_relative_performance()
# # print(relative_performance)
# ticker_contributions = calculator.calculate_ticker_contributions('us_defense'); ticker_contributions
# ticker_contributions = calculator.calculate_ticker_contributions('us_defense')



# Add a title
st.title("ThemePark")

# Add some text
st.write("This is a simple demonstration of PAG's capabilities.")

# Create a sidebar
st.sidebar.header("Performance visualization")

# Create two columns
# col1, col2 = st.columns(2)

# with col1:
st.header("Performance of baskets")

# Define the columns with numeric metrics for styling
numeric_columns = ["MTD", "1m", "QTD", "3m", "6m", "YTD", "12m"]

# Create and style the GT table with the relative performance DataFrame
gt_table = (
    GT(relative_performance, rowname_col=None)  # No combined row name needed
    .fmt_percent(columns=numeric_columns, decimals=2)  # Format numeric columns as percentages
    .data_color(
        columns=numeric_columns,
        palette = [
            "#a50026",  # Darker red for low values
            "#d73027",  # Red
            "#f46d43",  # Orange-red
            "#fdae61",  # Light orange
            "#fee08b",  # Yellow
            "#d9ef8b",  # Light green-yellow
            "#a6d96a",  # Green
            "#66bd63",  # Medium green
            "#1a9850",  # Dark green
            "#006837"   # Darker green for high values
        ],
        domain=[-0.4, 0.2],  # Adjust the color scale range
        na_color="white",  # Set color for NaN or missing values
        autocolor_text=True  # Automatically adjust text color for readability
    )
    .tab_header(
        title="Relative Performance Metrics",
        subtitle="Performance metrics across various baskets and benchmarks, with color gradation."
    )
    .sub_missing(missing_text="")  # Display an empty cell for missing data
)

# Convert the GT table to HTML and display it in Streamlit
html_str = gt_table.as_raw_html()
st.components.v1.html(html_str, height=600, scrolling=True)


# # with col2: 

# # Calculate time series performance rebased to 100 starting from 2024-01-02
# analyzer.calculate_time_series_performance(start_date='2024-01-02')
# performance_ts = analyzer.get_time_series_performance()

# Convert DataFrame to Highcharts-compatible format using Date.UTC for datetime parsing
# Filter the DataFrame to include data only from 2024-01-01 onwards

basket_rebased_df, benchmark_rebased_df = calculator.get_aligned_performance_dfs(
    rebase=True,
    base_value=100,
    start_date="2024-01-01",
    end_date="2024-10-30"
)

# Convert the filtered DataFrame to Highcharts-compatible format using Date.UTC for datetime parsing
series_data = [
    {
        "name": column,
        "data": [[int(date.timestamp() * 1000), value] for date, value in basket_rebased_df[column].dropna().items()]
    }
    for column in basket_rebased_df.columns
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


# Function to prepare GT-styled table for relative contributions only
def create_gt_table_rel_only(df, basket_name):
    # Filter for only relative columns
    rel_cols = [col for col in df.columns if "_rel" in col]

    # Create a DataFrame with company, sector, industry, market cap, issuer type, and relative contribution columns
    display_df = df[['Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type'] + rel_cols].copy()
    
    # Rename relative columns for display
    display_df.columns = ['Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type'] + \
                         [col.replace('_rel', ' Rel') for col in rel_cols]
    
    # Reset index to use it as a rowname in GT
    display_df = display_df.reset_index(drop=True)

    # Convert column names to a list of strings to bypass selection issue
    percent_columns = display_df.columns[5:].tolist()  # Skip the first five columns for percentage formatting

    # GT table styling setup
    gt_table = (
        GT(display_df, rowname_col="Company")  # Use "Company" as the row name
        .fmt_percent(columns=[col for col in percent_columns], decimals=2)  # Format all relative columns as percentages
        .data_color(
            columns=percent_columns,
            palette=[
                "#a50026",  # Darker red for low values
                "#d73027",  # Red
                "#f46d43",  # Orange-red
                "#fdae61",  # Light orange
                "#fee08b",  # Yellow
                "#d9ef8b",  # Light green-yellow
                "#a6d96a",  # Green
                "#66bd63",  # Medium green
                "#1a9850",  # Dark green
                "#006837"   # Darker green for high values
            ],
            domain=[-1, 1],  # Adjust the color scale range
            na_color="white",  # Set color for NaN or missing values
            autocolor_text=True  # Automatically adjust text color for readability
        )
        .tab_header(
            title=f"Relative Contribution Metrics for {basket_name.capitalize()}",
            subtitle="Relative performance contributions with color gradation."
        )
        .sub_missing(missing_text="")  # Display an empty cell for missing data
    )
    
    # Render the table as HTML
    return gt_table.as_raw_html()

# Streamlit app
st.header("Basket Relative Contributions")
basket_choice = st.selectbox("Select a Basket:", list(basket_rebased_df.columns))
ticker_contributions = calculator.calculate_ticker_contributions(basket_choice)

# Display the selected basket's relative contributions with GT styling
html_str = create_gt_table_rel_only(ticker_contributions, basket_choice)
st.components.v1.html(html_str, height=500, scrolling=True)

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