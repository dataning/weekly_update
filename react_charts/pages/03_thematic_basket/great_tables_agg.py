import streamlit as st
from great_tables import GT

def render_relative_performance_table(df, height: int = 800):
    """
    Render a styled relative performance table using Great Tables (GT) in Streamlit.

    Parameters:
    - df: pandas.DataFrame containing relative performance metrics with columns:
          ['MTD', '1m', 'QTD', '3m', '6m', 'YTD', '12m']
    - height: int height of the HTML component in Streamlit (default: 800)
    """
    # Define numeric metric columns for formatting
    numeric_columns = ["MTD", "1m", "QTD", "3m", "6m", "YTD", "12m"]

    # Build GT table with styling
    gt_table = (
        GT(df, rowname_col=None)
        .fmt_percent(columns=numeric_columns, decimals=2)
        .data_color(
            columns=numeric_columns,
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
            domain=[-0.4, 0.2],
            na_color="white",
            autocolor_text=True
        )
        .tab_header(
            title="Relative Performance Metrics",
            subtitle="Performance metrics across various baskets and benchmarks, with color gradation."
        )
        .sub_missing(missing_text="")
    )

    # Convert to HTML and render
    html_str = gt_table.as_raw_html()
    st.components.v1.html(html_str, height=height, scrolling=True)


def render_relative_contributions_table(df, basket_name: str, height: int = 600):
    """
    Render a styled relative contribution table for a specific basket using Great Tables (GT) in Streamlit.

    Parameters:
    - df: pandas.DataFrame containing ticker contributions, including columns:
          ['Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type', '<metric>_rel', ...]
    - basket_name: str name of the basket for title formatting
    - height: int height of the HTML component in Streamlit (default: 600)
    """
    # Identify relative contribution columns
    rel_cols = [col for col in df.columns if col.endswith("_rel")]

    # Build display DataFrame
    display_df = df[['Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type'] + rel_cols].copy()
    # Rename for readability
    display_df.columns = [
        'Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type'
    ] + [col.replace('_rel', ' Rel') for col in rel_cols]

    # Reset index for GT
    display_df = display_df.reset_index(drop=True)

    # Percentage formatting columns
    percent_columns = display_df.columns[5:]

    # Build GT table with styling
    gt_table = (
        GT(display_df, rowname_col='Company')
        .fmt_percent(columns=list(percent_columns), decimals=2)
        .data_color(
            columns=list(percent_columns),
            palette=[
                "#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b",
                "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"
            ],
            domain=[-1, 1],
            na_color="white",
            autocolor_text=True
        )
        .tab_header(
            title=f"Relative Contribution Metrics for {basket_name.capitalize()}",
            subtitle="Relative performance contributions with color gradation."
        )
        .sub_missing(missing_text="")
    )

    # Convert to HTML and render
    html_str = gt_table.as_raw_html()
    st.components.v1.html(html_str, height=height, scrolling=True)
