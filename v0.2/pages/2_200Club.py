import streamlit as st
import pandas as pd
from components.pro200club_2nd import create_charts
import polars as pl
from pathlib import Path

# Page config
st.set_page_config(layout="wide")

# Load data
@st.cache_data
def load_ntee_data():
    """
    Load and filter NTEE data from parquet file with caching.
    Filters for 2023 data and organizations with net assets > $20M.
    
    Returns:
        pl.DataFrame: Filtered DataFrame containing nonprofit data
    """
    try:
        # Check if file exists
        file_path = Path('app_data/nonprofit_wide_20250107.parquet')
        if not file_path.exists():
            st.error("Parquet file not found. Please check the file path.")
            return None

        # Load and filter data
        filtered_main_df = (
            pl.read_parquet(file_path)
            .filter(pl.col("tax_prd").dt.year() == 2023)  # Filter for 2023 dates
            .filter(
                pl.col("totnetassetend")
                .cast(pl.Float64, strict=False)  # Add strict=False to handle potential parsing errors
                .gt(20_000_000)
            )  # Filter for assets > $20M
        )
        
        # Add success message
        # st.success(f"Successfully loaded {filtered_main_df.height} organizations")
        
        return filtered_main_df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

ntee_df = load_ntee_data()

required_columns = [
    # Identifier and Classification Columns
    'name',              # Organization identifier
    'ein',
    'ntee_code_std',         # NTEE code for filtering
    'Description',       # NTEE code description
    'Definition',        # NTEE code definition
    
    # Financial Metrics - Net Assets
    'totnetassetend',    # Net assets
    'totassetsend',      # Total assets
    'totliabend',        # Total liabilities
    
    # Financial Metrics - Revenue
    'totrevenue',        # Total revenue
    'invstmntinc',       # Investment income
    'totcntrbgfts',      # Contributions and grants
    'totprgmrevnue',     # Program service revenue
    
    # Financial Metrics - Expenses
    'totfuncexpns',      # Total functional expenses
    'compnsatncurrofcr', # Officer compensation
    'othrsalwages',      # Other salaries
    'payrolltx'          # Payroll tax
]

def filter_ntee_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Filter and process NTEE dataframe to include only required columns
    and proper data types for analysis and visualization.
    """
    # Get intersection of required columns and available columns
    available_columns = [col for col in required_columns if col in df.columns]
    
    # Select only the columns we need
    filtered_df = df.select(available_columns)
    
    # Split columns by type
    string_columns = ['name', 'ntee_code_std', 'Description', 'Definition']
    numeric_columns = [col for col in available_columns if col not in string_columns]
    
    # Apply transformations
    if numeric_columns:
        filtered_df = filtered_df.with_columns([
            pl.col(col).cast(pl.Float64).fill_null(0) for col in numeric_columns
        ])
    
    return filtered_df

ntee_df = filter_ntee_columns(ntee_df).to_pandas()

# Sidebar
with st.sidebar:
    st.header("NTEE Code Selection")
    
    # Get unique NTEE codes with their descriptions
    ntee_summary = (ntee_df.groupby('ntee_code_std')
                   .agg({
                       'Description': 'first',
                       'Definition': 'first'
                   })
                   .reset_index())
    
    # Add count for sorting but don't display it
    ntee_counts = ntee_df.groupby('ntee_code_std').size().reset_index(name='count')
    ntee_summary = ntee_summary.merge(ntee_counts, on='ntee_code_std')
    ntee_summary = ntee_summary.sort_values('count', ascending=False)
    
    # Create selection options with just code and description
    ntee_options = [f"{code} - {desc}"
                   for code, desc in zip(ntee_summary['ntee_code_std'], 
                                       ntee_summary['Description'])]
    
    # Single NTEE code selector
    selected_option = st.selectbox(
        "Select NTEE Code",
        options=ntee_options,
        index=0,
        key='ntee_selector'
    )
    
    # Extract selected code from the option
    selected_ntee = selected_option.split(' - ')[0]

# Filter dataframe for selected NTEE code
filtered_df = ntee_df[ntee_df['ntee_code_std'] == selected_ntee]

# Get description and definition for selected NTEE code
selected_info = ntee_summary[ntee_summary['ntee_code_std'] == selected_ntee].iloc[0]

# Main content
st.title(f"NTEE Code: {selected_ntee}")

# Description and Definition
col1, col2 = st.columns(2)

with col1:
    st.subheader("Description")
    st.markdown(
        f'''
        <div style="
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #e51ec7;
            margin: 10px 0;">
            <p style="
                font-size: 20px;
                color: #000000;
                margin: 0;
                line-height: 1.5;">
                {selected_info["Description"]}
            </p>
        </div>
        ''', 
        unsafe_allow_html=True
    )

with col2:
    st.subheader("Definition")
    st.markdown(
        f'''
        <div style="
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #391ee5;
            margin: 10px 0;">
            <p style="
                font-size: 20px;
                color: #000000;
                margin: 0;
                line-height: 1.5;">
                {selected_info["Definition"]}
            </p>
        </div>
        ''', 
        unsafe_allow_html=True
    )

# Number of Organizations and Median Net Asset
col1, col2 = st.columns(2)

with col1:
    st.subheader("Number of Organizations")
    st.markdown(
        f'''
        <div style="
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #e51ec7;
            margin: 10px 0;">
            <p style="
                font-size: 20px;
                color: #000000;
                margin: 0;
                line-height: 1.5;">
                {len(filtered_df)}
            </p>
        </div>
        ''', 
        unsafe_allow_html=True
    )

with col2:
    st.subheader("Median Net Asset (in Millions)")
    # Ensure that the 'totnetassetend' column exists and handle missing values
    if 'totnetassetend' in filtered_df.columns:
        # Attempt to convert to numeric, coercing errors to NaN
        filtered_df = filtered_df.copy()  # Avoid SettingWithCopyWarning
        filtered_df['totnetassetend'] = pd.to_numeric(filtered_df['totnetassetend'], errors='coerce')
        
        # Calculate the median, ignoring NaN values
        median_net_asset = filtered_df['totnetassetend'].median()
        
        if pd.notnull(median_net_asset):
            # Convert to millions
            median_net_asset_millions = median_net_asset / 1_000_000
            # Format the median value with two decimal places and 'M' suffix
            median_net_asset_formatted = f"${median_net_asset_millions:,.2f}M"
        else:
            median_net_asset_formatted = "N/A"
    else:
        median_net_asset_formatted = "N/A"
    
    st.markdown(
        f'''
        <div style="
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #391ee5;
            margin: 10px 0;">
            <p style="
                font-size: 20px;
                color: #000000;
                margin: 0;
                line-height: 1.5;">
                {median_net_asset_formatted}
            </p>
        </div>
        ''', 
        unsafe_allow_html=True
    )

st.divider()

st.header("Exploration")

# Display charts
create_charts(filtered_df)
