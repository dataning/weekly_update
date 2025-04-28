import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import traceback
from treemap_component import TreemapComponent
from highcharts_component import HighchartsBarComponent

# Set page configuration
st.set_page_config(
    page_title="Hierarchical Treemap Generator",
    page_icon="📊",
    layout="wide"
)

def read_file_to_dataframe(uploaded_file):
    """
    Read an uploaded file into a pandas DataFrame.
    Supports CSV, Excel, Parquet, and JSON formats.
    
    Parameters:
    -----------
    uploaded_file : UploadedFile
        Streamlit uploaded file object
        
    Returns:
    --------
    DataFrame or None
        Pandas DataFrame or None if the file type is unsupported
    """
    try:
        # Get file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Read file based on extension
        if file_extension == '.csv':
            return pd.read_csv(uploaded_file)
        elif file_extension in ['.xls', '.xlsx']:
            return pd.read_excel(uploaded_file)
        elif file_extension in ['.parquet', '.pq']:
            try:
                # Need to save to a BytesIO object first
                bytes_data = io.BytesIO(uploaded_file.getvalue())
                return pd.read_parquet(bytes_data)
            except ImportError:
                st.error("Parquet support requires 'pyarrow' or 'fastparquet' packages.")
                st.info("Install with: pip install pyarrow")
                return None
        elif file_extension == '.json':
            return pd.read_json(uploaded_file)
        else:
            st.error(f"Unsupported file format: {file_extension}")
            st.info("Supported formats: CSV, Excel (.xls, .xlsx), Parquet (.parquet, .pq), JSON")
            return None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        with st.expander("Error Details"):
            st.write(traceback.format_exc())
        return None

def create_sp500_sample_data(num_companies=44, negative_bias=True, include_nan=False):
    """
    Create a sample dataset with S&P 500 tickers organized by sector and industry.
    """
    sectors = {
        'Technology': ['Software','Hardware','Semiconductors','Internet'],
        'Financial':  ['Banks','Insurance','Asset Management','Real Estate'],
        'Healthcare': ['Pharmaceuticals','Medical Devices','Biotech','Healthcare Services'],
        'Energy':     ['Oil & Gas','Renewable Energy','Utilities','Energy Equipment'],
        'Consumer':   ['Retail','Food & Beverage','Luxury Goods','Entertainment']
    }
    tickers = {
        'Technology': {
            'Software':      ['MSFT','ORCL','ADBE','CRM','INTU'],
            'Hardware':      ['AAPL','HPQ','DELL','IBM','NTAP'],
            'Semiconductors':['NVDA','AMD','INTC','TXN','QCOM'],
            'Internet':      ['GOOG','META','AMZN','NFLX','PYPL']
        },
        'Financial': {
            'Banks':           ['JPM','BAC','C','WFC','GS'],
            'Insurance':       ['BRK.B','PGR','AIG','MET','PRU'],
            'Asset Management':['BLK','BEN','TROW','IVZ','SCHW'],
            'Real Estate':     ['AMT','SPG','PLD','WELL','EQR']
        },
        'Healthcare': {
            'Pharmaceuticals': ['JNJ','PFE','MRK','ABBV','LLY'],
            'Medical Devices': ['MDT','ABT','SYK','BSX','ZBH'],
            'Biotech':         ['AMGN','BIIB','GILD','REGN','VRTX'],
            'Healthcare Services':['UNH','CVS','ANTM','HUM','CI']
        },
        'Energy': {
            'Oil & Gas':        ['XOM','CVX','COP','EOG','OXY'],
            'Renewable Energy': ['NEE','PCG','AES','BEP','CWEN'],
            'Utilities':        ['DUK','SO','D','AEP','EXC'],
            'Energy Equipment': ['SLB','HAL','BKR','NOV','FTI']
        },
        'Consumer': {
            'Retail':         ['WMT','TGT','HD','LOW','COST'],
            'Food & Beverage':['KO','PEP','MCD','SBUX','YUM'],
            'Luxury Goods':   ['NKE','LULU','TPR','UAA','VFC'],
            'Entertainment':  ['DIS','CMCSA','CHTR','VIAC','FOXA']
        }
    }

    # Choose sector bias
    if negative_bias:
        sector_bias = {
            'Technology': -8,
            'Financial': -15,
            'Healthcare': -5,
            'Energy': -20,
            'Consumer': 15
        }
    else:
        sector_bias = {
            'Technology': 5,
            'Financial': -5,
            'Healthcare': 10,
            'Energy': -10,
            'Consumer': 8
        }

    np.random.seed(42)
    companies = []
    for sector, inds in sectors.items():
        base = sector_bias[sector]
        for industry in inds:
            off = np.random.uniform(-5, 3)
            ibase = base + off
            choices = tickers[sector][industry]
            selected = np.random.choice(choices, min(3, len(choices)), replace=False)
            for t in selected:
                coff = np.random.uniform(-7, 5)
                ret = ibase + coff
                # force first ticker negative if sector bias negative
                if t == choices[0] and base < 0:
                    ret = min(ret, -10)
                companies.append({
                    'Sector': sector,
                    'Industry': industry,
                    'Company': t,
                    'Return': round(ret, 2)
                })

    df = pd.DataFrame(companies)
    # sample or duplicate to get exact count
    if len(df) > num_companies:
        df = df.sample(num_companies, random_state=42)
    elif len(df) < num_companies:
        extra = num_companies - len(df)
        dup = df.sample(extra, replace=True, random_state=43)
        dup['Return'] += np.random.uniform(-2, 2, size=len(dup))
        df = pd.concat([df, dup], ignore_index=True)

    # enforce ~60% negative
    if negative_bias:
        target = int(0.6 * len(df))
        curr = (df['Return'] < 0).sum()
        if curr < target:
            pos_idx = df[df['Return'] > 0].index
            need = min(len(pos_idx), target - curr)
            for i in np.random.choice(pos_idx, need, replace=False):
                df.at[i, 'Return'] = -abs(df.at[i, 'Return'])

    # add some extremes
    extremes = [-30, -25, -20, -15, 10, 15, 20, 25]
    for idx, val in zip(np.random.choice(df.index, len(extremes), replace=False), extremes):
        df.at[idx, 'Return'] = val

    df['Return'] = df['Return'].astype(float)

    # introduce NaNs
    if include_nan:
        cnt = max(1, int(0.1 * len(df)))
        for i in np.random.choice(df.index, cnt, replace=False):
            df.at[i, 'Return'] = np.nan
        st.write(f"Added {cnt} NaN values for testing")
    else:
        df['Return'] = df['Return'].fillna(0)

    return df

def generate_code_snippet(
    df_name,
    level1_column,
    level2_column,
    level3_column,
    value_column,
    handle_nan="show",
    nan_label="N/A",
    nan_color="#333333",
    height=700,
    value_min=-30,
    value_max=30,
    color_min="#d40000",
    color_max="#00b52a",
    chart_title="Hierarchical Performance Treemap",
    chart_subtitle="Click to drill down"
):
    """Generate a code snippet for treemap visualization"""
    code = f"""
# Import the TreemapComponent
from treemap_component import TreemapComponent

# Create a treemap component
treemap = TreemapComponent(
    title="{chart_title}",
    subtitle="{chart_subtitle}"
)

# Render the treemap
treemap.render(
    df={df_name},
    level1_column='{level1_column}',
    level2_column='{level2_column}',
    level3_column='{level3_column}',
    value_column='{value_column}',
    height={height},
    value_min={value_min},
    value_max={value_max},
    color_min='{color_min}',
    color_max='{color_max}',
    size_by_magnitude=True,"""

    if handle_nan == "show":
        code += f"""
    nan_color="{nan_color}",
    nan_label="{nan_label}",
    handle_nan="show"
)
"""
    elif handle_nan == "zero":
        code += """
    handle_nan="zero"
)
"""
    else:  # hide
        code += """
    handle_nan="hide"
)
"""
    return code

def display_data_summary(df, value_column):
    """Display summary statistics for the dataframe"""
    # Data metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(df))
        
    with col2:
        negative_pct = (df[value_column] < 0).mean() * 100
        st.metric("Negative Values", f"{negative_pct:.1f}%")
        
    with col3:
        nan_count = df[value_column].isna().sum()
        st.metric("NaN Values", f"{nan_count} ({nan_count/len(df)*100:.1f}%)")
    
    # Sample Data
    st.subheader("Sample Data")
    st.dataframe(df.head(10))
    
    # NaN Values (if any)
    if nan_count > 0:
        show_nan = st.checkbox("Show rows with NaN values")
        if show_nan:
            st.dataframe(df[df[value_column].isna()])
        
    # Distribution Plot
    st.subheader("Distribution of Values")
    try:
        vals = df[value_column].dropna()
        
        if not vals.empty:
            # Create the histogram with Highcharts
            hist_chart = HighchartsBarComponent(
                title=f"Distribution of {value_column}",
                subtitle="Click and drag to zoom, click legend items to toggle series"
            )
            
            # Determine reasonable bin range
            min_val = vals.min()
            max_val = vals.max()
            buffer = (max_val - min_val) * 0.1
            
            hist_chart.render_histogram(
                values=vals,
                bins=20,  # Fewer bins for wider bars
                nan_count=nan_count,
                height=400,
                color_neg='#d40000',  # Match treemap negative color
                color_pos='#00b52a',  # Match treemap positive color
                bar_width_factor=0.8,  # Make bars wider (0.8 = 80% of available space)
                x_label=value_column,
                y_label="Count",
                x_min=min_val - buffer,
                x_max=max_val + buffer
            )
        else:
            st.warning("No numeric data available for histogram.")
    except Exception as e:
        st.error(f"Error creating histogram: {str(e)}")
        with st.expander("Error Details"):
            st.write(traceback.format_exc())

# --- App Header ---
st.title("Hierarchical Treemap Generator")
st.markdown("""
This app helps you create interactive, hierarchical treemap visualizations from your data.
Upload a CSV, Excel, Parquet, or JSON file, or use a sample dataset.
""")

# --- Main Navigation ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Upload Your Data", 
    "Sample Data (S&P 500)", 
    "Create Custom Sample", 
    "About & Documentation"
])

# Tab 1: Upload Your Data
with tab1:
    st.header("Create a Treemap from Your Data")
    
    # File uploader
    st.subheader("Step 1: Upload Your Data File")
    supported_formats = "CSV, Excel, Parquet, or JSON"
    uploaded_file = st.file_uploader(
        f"Upload a file ({supported_formats})",
        type=["csv", "xlsx", "xls", "parquet", "pq", "json"],
        key="data_upload"
    )
    
    if uploaded_file:
        try:
            with st.spinner("Reading file..."):
                user_df = read_file_to_dataframe(uploaded_file)
                
            if user_df is not None:
                st.success(f"Successfully loaded data with {len(user_df)} rows and {len(user_df.columns)} columns")
                
                # Display summary statistics
                display_data_summary(user_df, user_df.select_dtypes(include='number').columns[0])
                
                # Column selection
                st.subheader("Step 2: Select Hierarchy and Value Columns")
                
                col1, col2 = st.columns(2)
                with col1:
                    lvl1 = st.selectbox("Level 1 column (top):", user_df.columns, key="upload_lvl1")
                    lvl2 = st.selectbox("Level 2 column (middle):", user_df.columns, key="upload_lvl2")
                    lvl3 = st.selectbox("Level 3 column (bottom):", user_df.columns, key="upload_lvl3")
                    
                with col2:
                    numeric_cols = user_df.select_dtypes(include='number').columns.tolist()
                    if not numeric_cols:
                        st.error("No numeric columns found in your data. The value column must be numeric.")
                        valc = None
                    else:
                        valc = st.selectbox(
                            "Value column (for color coding):",
                            numeric_cols,
                            key="upload_val"
                        )
                    
                    has_nan = user_df[valc].isna().any() if valc else False
                    if has_nan:
                        nan_choice = st.radio(
                            "How to handle NaN values:",
                            ["Show with custom label", "Replace with zeros", "Hide (exclude)"],
                            key="upload_nan_handling"
                        )
                        if nan_choice == "Show with custom label":
                            custom_nan_label = st.text_input("Label for NaN values:", "N/A", key="upload_nan_label")
                            custom_nan_color = st.color_picker("Color for NaN boxes:", "#333333", key="upload_nan_color")
                            handle_nan = "show"
                        elif nan_choice == "Replace with zeros":
                            custom_nan_label = "0.00%"
                            custom_nan_color = "#414555"
                            handle_nan = "zero"
                        else:
                            custom_nan_label = ""
                            custom_nan_color = ""
                            handle_nan = "hide"
                    else:
                        handle_nan = "zero"
                        custom_nan_label = "0.00%"
                        custom_nan_color = "#333333"
                
                # Visualization settings
                st.subheader("Step 3: Customize Visualization")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    chart_title = st.text_input("Chart title:", "My Treemap", key="upload_title")
                    chart_sub = st.text_input("Chart subtitle:", "Click to drill down", key="upload_sub")
                    chart_height = st.slider("Chart height:", 400, 1000, 700, key="upload_height")
                    
                with col2:
                    vmin = st.number_input("Min value:", value=-30.0, key="upload_vmin")
                    vmax = st.number_input("Max value:", value=30.0, key="upload_vmax")
                    
                with col3:
                    cmin = st.color_picker("Min color (negative):", "#d40000", key="upload_cmin")
                    cmax = st.color_picker("Max color (positive):", "#00b52a", key="upload_cmax")
                
                # Generate visualization
                if st.button("Generate Treemap", key="upload_generate") and valc:
                    with st.spinner("Creating treemap visualization..."):
                        try:
                            tm = TreemapComponent(title=chart_title, subtitle=chart_sub)
                            tm.render(
                                df=user_df,
                                level1_column=lvl1,
                                level2_column=lvl2,
                                level3_column=lvl3,
                                value_column=valc,
                                height=chart_height,
                                value_min=vmin,
                                value_max=vmax,
                                color_min=cmin,
                                color_max=cmax,
                                validate_data=True,
                                nan_color=custom_nan_color if has_nan else "#333333",
                                nan_label=custom_nan_label if has_nan else "N/A",
                                handle_nan=handle_nan,
                                size_by_magnitude=True  # Always use magnitude sizing
                            )
                            
                            # Show code snippet for replicating the visualization
                            with st.expander("📋 Code to Replicate This Visualization", expanded=True):
                                st.subheader("Python Code")
                                code = generate_code_snippet(
                                    df_name="your_dataframe", 
                                    level1_column=lvl1,
                                    level2_column=lvl2,
                                    level3_column=lvl3,
                                    value_column=valc,
                                    handle_nan=handle_nan,
                                    nan_label=custom_nan_label if has_nan else "N/A",
                                    nan_color=custom_nan_color if has_nan else "#333333",
                                    height=chart_height,
                                    value_min=vmin,
                                    value_max=vmax,
                                    color_min=cmin,
                                    color_max=cmax,
                                    chart_title=chart_title,
                                    chart_subtitle=chart_sub
                                )
                                st.code(code, language="python")
                                
                                st.caption("Copy this code and replace 'your_dataframe' with your actual DataFrame variable.")
                        except Exception as e:
                            st.error(f"Error creating treemap: {str(e)}")
                            with st.expander("Error Details"):
                                st.write(traceback.format_exc())
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            with st.expander("Error Details"):
                st.write(traceback.format_exc())
    else:
        st.info(f"Upload a file to get started. Supported formats: {supported_formats}")
        
        with st.expander("Expected Data Format"):
            st.markdown("""
            ### Data Requirements
            
            Your data should have at least 4 columns:
            
            1. **Level 1 Column**: Top-level categories (e.g., Sectors, Departments, Regions)
            2. **Level 2 Column**: Mid-level categories (e.g., Industries, Teams, Cities)
            3. **Level 3 Column**: Bottom-level items (e.g., Companies, Employees, Stores)
            4. **Value Column**: Numeric values for color coding (e.g., Returns, Performance, Growth)
            
            ### Example:
            
            | Sector     | Industry        | Company | Return  |
            |------------|----------------|---------|---------|
            | Technology | Software       | MSFT    | 12.5    |
            | Technology | Hardware       | AAPL    | 8.3     |
            | Financial  | Banks          | JPM     | -5.2    |
            | Energy     | Oil & Gas      | XOM     | -10.8   |
            | Consumer   | Retail         | WMT     | 3.1     |
            
            The treemap will organize items hierarchically, with box size based on item count and color based on the value column.
            """)

# Tab 2: S&P 500 Example
with tab2:
    st.header("S&P 500 Market Performance Example")
    st.markdown("""
    This example shows a hierarchical treemap of S&P 500 companies, organized by sector and industry,
    with color indicating performance returns.
    """)

    include_nan = st.checkbox(
        "Include NaN values (for testing)",
        value=False,
        key="sp500_include_nan"
    )

    with st.spinner("Generating sample data..."):
        df_sp = create_sp500_sample_data(
            num_companies=44,
            include_nan=include_nan
        )

    if include_nan:
        nan_handling = st.radio(
            "How to handle NaN values:",
            ["Show with custom label", "Replace with zeros", "Hide (exclude)"],
            index=0,
            key="sp500_nan_handling"
        )
        if nan_handling == "Show with custom label":
            nan_label = st.text_input(
                "Label for NaN values:",
                "N/A",
                key="sp500_nan_label"
            )
            nan_color = st.color_picker(
                "Color for NaN boxes:",
                "#333333",
                key="sp500_nan_color"
            )
            handle_nan = "show"
        elif nan_handling == "Replace with zeros":
            nan_label = "0.00%"
            nan_color = "#414555"
            handle_nan = "zero"
        else:
            nan_label = ""
            nan_color = ""
            handle_nan = "hide"
    else:
        nan_label = "N/A"
        nan_color = "#333333"
        handle_nan = "zero"

    # Display data summary
    display_data_summary(df_sp, 'Return')

    # Treemap
    st.subheader("Treemap Visualization")
    
    with st.spinner("Creating treemap visualization..."):
        treemap = TreemapComponent(
            title="S&P 500 Performance by Sector",
            subtitle="Click to drill down. Color indicates performance (%)"
        )
        treemap.render(
            df=df_sp,
            level1_column='Sector',
            level2_column='Industry',
            level3_column='Company',
            value_column='Return',
            height=700,
            value_min=-30,
            value_max=30,
            color_min='#d40000',
            color_max='#00b52a',
            validate_data=True,
            nan_color=nan_color,
            nan_label=nan_label,
            handle_nan=handle_nan,
            size_by_magnitude=True  # Always use magnitude sizing
        )

    with st.expander("📋 Code to Replicate This Visualization", expanded=False):
        st.subheader("Python Code")
        code = generate_code_snippet(
            df_name="df_sp", 
            level1_column='Sector',
            level2_column='Industry',
            level3_column='Company',
            value_column='Return',
            handle_nan=handle_nan,
            nan_label=nan_label,
            nan_color=nan_color,
            height=700,
            value_min=-30,
            value_max=30,
            color_min='#d40000',
            color_max='#00b52a',
            chart_title="S&P 500 Performance by Sector",
            chart_subtitle="Click to drill down. Color indicates performance (%)"
        )
        st.code(code, language="python")

# Tab 3: Create Your Own
with tab3:
    st.header("Create a Custom Sample Dataset")
    st.markdown("""
    Generate a sample dataset with customizable categories and visualize it as a treemap.
    This is useful for testing or demonstrating the treemap functionality.
    """)
    
    # Sample data generation parameters
    st.subheader("Step 1: Define Custom Categories")
    num_lv1 = st.slider(
        "Number of top-level categories:", 2, 10, 5,
        key="sample_lv1_count"
    )
    
    cols = st.columns(min(5, num_lv1))
    lvl1_names = []
    for i in range(num_lv1):
        with cols[i % len(cols)]:
            name = st.text_input(f"Category {i+1} name:", f"Category {i+1}", key=f"sample_name_{i}")
            lvl1_names.append(name)
    
    include_nan_sample = st.checkbox(
        "Include NaN values in sample",
        key="sample_include_nan"
    )
    
    if st.button("Generate Sample Dataset", key="sample_generate"):
        with st.spinner("Generating sample data..."):
            try:
                sample_rows = []
                np.random.seed(99)
                # create biases
                biases = {}
                for idx, name in enumerate(lvl1_names):
                    if idx < 0.8 * len(lvl1_names):
                        biases[name] = np.random.uniform(-25, -5)
                    else:
                        biases[name] = np.random.uniform(5, 20)
                        
                for lvl1 in lvl1_names:
                    base = biases[lvl1]
                    num_lvl2 = np.random.randint(2, 4)
                    for g in range(num_lvl2):
                        lvl2 = f"{lvl1} Group {g+1}"
                        offset2 = np.random.uniform(-7, 4)
                        mid = base + offset2
                        num_lvl3 = np.random.randint(3, 6)
                        for j in range(num_lvl3):
                            lvl3 = f"{lvl2} Item {j+1}"
                            if mid < 0:
                                off3 = np.random.uniform(-8, 4)
                            else:
                                off3 = np.random.uniform(-12, 3)
                            val = max(min(mid + off3, 30), -30)
                            sample_rows.append({
                                'Level1': lvl1,
                                'Level2': lvl2,
                                'Level3': lvl3,
                                'Value': round(val, 2)
                            })
                            
                sample_df = pd.DataFrame(sample_rows)
                
                # enforce 60% negative
                total = len(sample_df)
                need_neg = int(0.6 * total)
                curr_neg = (sample_df['Value'] < 0).sum()
                if curr_neg < need_neg:
                    pos_idx = sample_df[sample_df['Value'] > 0].index
                    needed = min(len(pos_idx), need_neg - curr_neg)
                    for i in np.random.choice(pos_idx, needed, replace=False):
                        sample_df.at[i, 'Value'] = -abs(sample_df.at[i, 'Value'])
                        
                # add NaNs
                if include_nan_sample:
                    ncnt = max(1, int(0.1 * len(sample_df)))
                    for i in np.random.choice(sample_df.index, ncnt, replace=False):
                        sample_df.at[i, 'Value'] = np.nan
                    st.write(f"Added {ncnt} NaN values to sample")
                    handle = "show"
                    lbl = st.text_input("NaN label:", "N/A", key="sample_nan_label")
                    clr = st.color_picker("NaN color:", "#333333", key="sample_nan_color")
                else:
                    handle = "zero"
                    lbl = "0.00%"
                    clr = "#414555"

                # Display data summary
                display_data_summary(sample_df, 'Value')
                
                # Visualization settings
                st.subheader("Step 2: Customize Visualization")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    chart_title = st.text_input("Chart title:", "Custom Sample Treemap", key="sample_title")
                    chart_sub = st.text_input("Chart subtitle:", "Generated from inputs", key="sample_sub")
                    chart_height = st.slider("Chart height:", 400, 1000, 700, key="sample_height")
                    
                with col2:
                    vmin = st.number_input("Min value:", value=-30.0, key="sample_vmin")
                    vmax = st.number_input("Max value:", value=30.0, key="sample_vmax")
                    
                with col3:
                    cmin = st.color_picker("Min color (negative):", "#d40000", key="sample_cmin")
                    cmax = st.color_picker("Max color (positive):", "#00b52a", key="sample_cmax")
                
                if st.button("Generate Treemap from Sample", key="sample_visualize"):
                    with st.spinner("Creating treemap visualization..."):
                        tm2 = TreemapComponent(title=chart_title, subtitle=chart_sub)
                        tm2.render(
                            df=sample_df,
                            level1_column='Level1',
                            level2_column='Level2',
                            level3_column='Level3',
                            value_column='Value',
                            height=chart_height,
                            value_min=vmin,
                            value_max=vmax,
                            color_min=cmin,
                            color_max=cmax,
                            validate_data=True,
                            nan_color=clr,
                            nan_label=lbl,
                            handle_nan=handle
                        )
                        
                        # Show code snippet
                        with st.expander("📋 Code to Replicate This Visualization", expanded=True):
                            st.subheader("Python Code")
                            code = generate_code_snippet(
                                df_name="sample_df", 
                                level1_column='Level1',
                                level2_column='Level2',
                                level3_column='Level3',
                                value_column='Value',
                                handle_nan=handle,
                                nan_label=lbl,
                                nan_color=clr,
                                height=chart_height,
                                value_min=vmin,
                                value_max=vmax,
                                color_min=cmin,
                                color_max=cmax,
                                chart_title=chart_title,
                                chart_subtitle=chart_sub
                            )
                            st.code(code, language="python")
                
                # Option to download sample data
                csv = sample_df.to_csv(index=False)
                st.download_button(
                    label="Download Sample Data as CSV",
                    data=csv,
                    file_name="treemap_sample_data.csv",
                    mime="text/csv",
                    key="download_sample"
                )
                
            except Exception as e:
                st.error(f"Error generating sample: {str(e)}")
                with st.expander("Error Details"):
                    st.write(traceback.format_exc())

# Tab 4: About & Documentation
with tab4:
    st.header("About the Treemap Component")
    
    st.markdown("""
    ## What is a Hierarchical Treemap?
    
    A hierarchical treemap is a visualization that displays hierarchical data using nested rectangles. 
    The treemap created by this component has three levels:
    
    1. **Level 1**: Top level categories (larger rectangles)
    2. **Level 2**: Middle level categories (medium rectangles within Level 1)
    3. **Level 3**: Bottom level items (smallest rectangles within Level 2)
    
    Each rectangle's **size** represents the number of items within that category, while the **color** 
    represents a numeric value (like performance or returns).
    
    ## Features
    
    - **Interactive**: Click to drill down into categories
    - **Color-coded**: Red-to-green color gradient for negative-to-positive values
    - **Customizable**: Adjust colors, labels, and value ranges
    - **NaN handling**: Options for displaying or handling missing values
    - **Export**: Download as PNG, JPEG, PDF, or SVG
    - **Fullscreen**: Expand the treemap to fullscreen for better viewing
    
    ## Installation
    
    To use this component in your own projects:
    
    ```bash
    pip install streamlit
    pip install pandas numpy matplotlib jinja2
    
    # For Parquet support
    pip install pyarrow  # or fastparquet
    ```
    
    Copy the `treemap_component.py` file to your project directory.
    
    ## Basic Usage
    
    ```python
    import pandas as pd
    import streamlit as st
    from treemap_component import TreemapComponent
    
    # Load your data
    df = pd.read_csv('your_data.csv')
    
    # Create and render treemap
    treemap = TreemapComponent(
        title="Your Treemap Title",
        subtitle="Click to drill down"
    )
    
    treemap.render(
        df=df,
        level1_column='top_level_column',
        level2_column='mid_level_column',
        level3_column='bottom_level_column',
        value_column='numeric_value_column'
    )
    ```
    """)
    
    st.subheader("Customization Options")
    
    st.markdown("""
    ### Appearance
    
    - **Title and Subtitle**: Set custom title and subtitle text
    - **Height**: Adjust the height of the treemap in pixels
    - **Color Range**: Set minimum and maximum colors for the gradient
    - **Value Range**: Set minimum and maximum values for the color scale
    
    ### NaN Handling
    
    - **Show**: Display NaN values with a custom label and color
    - **Zero**: Replace NaN values with zeros
    - **Hide**: Remove rows with NaN values from the visualization
    
    ### Data Validation
    
    The component includes a data validation feature that:
    
    - Compares source data with generated treemap data
    - Checks for discrepancies between values and display text
    - Reports on negative value percentages and NaN value counts
    """)