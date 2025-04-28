import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import inspect # To get component code
import textwrap # To format code nicely
from treemap_component import TreemapComponent # Import the updated component

# Set page configuration
st.set_page_config(
    page_title="Hierarchical Treemap Demo",
    page_icon="📊",
    layout="wide"
)

# --- Helper Function ---
def generate_render_code(params):
    """Generates the Python code string for the treemap.render() call."""
    # CORRECTION: Removed title/subtitle from the render() part of the example code.
    # They are set during instantiation.
    code = "import streamlit as st\n"
    code += "import pandas as pd\n"
    code += "from treemap_component import TreemapComponent\n\n"
    code += "# Load or create your DataFrame 'df' here\n"
    code += "# Example structure:\n"
    code += "# df = pd.DataFrame({\n"
    code += f"#     '{params.get('level1_column', 'Level1')}': ['A', 'A', 'B', ...],\n"
    code += f"#     '{params.get('level2_column', 'Level2')}': ['X', 'Y', 'Z', ...],\n"
    code += f"#     '{params.get('level3_column', 'Level3')}': ['Item1', 'Item2', 'Item3', ...],\n"
    code += f"#     '{params.get('value_column', 'Value')}': [10.5, -5.2, 8.0, ...],\n"
    if params.get('size_column'):
         code += f"#     '{params.get('size_column')}': [100, 50, 120, ...]\n"
    code += "# })\n\n"

    # Instantiate with title and subtitle
    code += f"treemap = TreemapComponent(\n"
    code += f"    title=\"{params.get('title', 'My Treemap')}\",\n"  # Title goes here
    code += f"    subtitle=\"{params.get('subtitle', 'Click to drill down')}\"\n" # Subtitle goes here
    code += ")\n\n"

    # Render call without title/subtitle
    code += "treemap.render(\n"
    code += f"    df=df, # Your DataFrame\n"
    code += f"    level1_column='{params.get('level1_column', 'Level1')}',\n"
    code += f"    level2_column='{params.get('level2_column', 'Level2')}',\n"
    code += f"    level3_column='{params.get('level3_column', 'Level3')}',\n"
    code += f"    value_column='{params.get('value_column', 'Value')}',\n"
    if params.get('size_column'):
        code += f"    size_column='{params.get('size_column')}',\n"
    else:
         code += f"    size_column=None, # Or omit this line to use item count\n"
    code += f"    height={params.get('height', 800)},\n"
    code += f"    value_min={params.get('value_min', -30)},\n"
    code += f"    value_max={params.get('value_max', 30)},\n"
    code += f"    color_min='{params.get('color_min', '#d40000')}',\n"
    code += f"    color_max='{params.get('color_max', '#00b52a')}',\n"
    code += f"    nan_color='{params.get('nan_color', '#333333')}',\n"
    code += f"    nan_label='{params.get('nan_label', 'N/A')}',\n"
    code += f"    handle_nan='{params.get('handle_nan', 'show')}',\n"
    code += f"    auto_scale_percentage={params.get('auto_scale_percentage', False)},\n"
    code += f"    fill_hierarchy_na='{params.get('fill_hierarchy_na', 'Unknown')}',\n"
    code += f"    validate_data={params.get('validate_data', True)}\n"
    code += ")"
    return code

# --- Data Generation Functions ---
def create_sp500_sample_data(num_companies=50, negative_bias=True, include_nan=False, include_size=True):
    """
    Create a sample dataset with S&P 500 tickers organized by sector and industry.
    Includes optional Market Cap for sizing.
    """
    sectors = {
        'Technology': ['Software','Hardware','Semiconductors','Internet'],
        'Financials': ['Banks','Insurance','Asset Management','Real Estate'], # Renamed for clarity
        'Healthcare': ['Pharmaceuticals','Medical Devices','Biotech','Healthcare Services'],
        'Energy':     ['Oil & Gas','Renewable Energy','Utilities','Energy Equipment'],
        'Consumer':   ['Retail','Food & Beverage','Luxury Goods','Entertainment']
    }
    tickers = {
        'Technology': {
            'Software':      ['MSFT','ORCL','ADBE','CRM','INTU'], 'Hardware':      ['AAPL','HPQ','DELL','IBM','NTAP'],
            'Semiconductors':['NVDA','AMD','INTC','TXN','QCOM'], 'Internet':      ['GOOG','META','AMZN','NFLX','PYPL'] },
        'Financials': {
            'Banks':           ['JPM','BAC','C','WFC','GS'], 'Insurance':       ['BRK.B','PGR','AIG','MET','PRU'],
            'Asset Management':['BLK','BEN','TROW','IVZ','SCHW'], 'Real Estate':     ['AMT','SPG','PLD','WELL','EQR'] },
        'Healthcare': {
            'Pharmaceuticals': ['JNJ','PFE','MRK','ABBV','LLY'], 'Medical Devices': ['MDT','ABT','SYK','BSX','ZBH'],
            'Biotech':         ['AMGN','BIIB','GILD','REGN','VRTX'], 'Healthcare Services':['UNH','CVS','ANTM','HUM','CI'] },
        'Energy': {
            'Oil & Gas':        ['XOM','CVX','COP','EOG','OXY'], 'Renewable Energy': ['NEE','PCG','AES','BEP','CWEN'],
            'Utilities':        ['DUK','SO','D','AEP','EXC'], 'Energy Equipment': ['SLB','HAL','BKR','NOV','FTI'] },
        'Consumer': {
            'Retail':         ['WMT','TGT','HD','LOW','COST'], 'Food & Beverage':['KO','PEP','MCD','SBUX','YUM'],
            'Luxury Goods':   ['NKE','LULU','TPR','UAA','VFC'], 'Entertainment':  ['DIS','CMCSA','CHTR','VIAC','FOXA'] }
    }

    if negative_bias: sector_bias = {'Technology': -8, 'Financials': -15, 'Healthcare': -5, 'Energy': -20, 'Consumer': 15}
    else: sector_bias = {'Technology': 5, 'Financials': -5, 'Healthcare': 10, 'Energy': -10, 'Consumer': 8}

    np.random.seed(42)
    companies = []
    for sector, inds in sectors.items():
        base = sector_bias[sector]
        for industry in inds:
            off = np.random.uniform(-5, 3)
            ibase = base + off
            choices = tickers[sector][industry]
            # Select slightly more per group to allow for sampling down
            selected = np.random.choice(choices, min(4, len(choices)), replace=False)
            for t in selected:
                coff = np.random.uniform(-7, 5)
                ret = ibase + coff
                if t == choices[0] and base < 0: ret = min(ret, -10) # Force first negative sometimes
                # Add Market Cap (randomized for example)
                market_cap = np.random.uniform(50, 500) # Billions
                if sector == 'Technology' and industry == 'Hardware': market_cap *= np.random.uniform(2, 5) # Make hardware bigger
                if sector == 'Financials' and industry == 'Banks': market_cap *= np.random.uniform(1.5, 3)
                companies.append({
                    'Sector': sector, 'Industry': industry, 'Company': t,
                    'Return': round(ret, 2),
                    'MarketCap': round(market_cap, 1) if include_size else np.nan
                })

    df = pd.DataFrame(companies)
    if len(df) > num_companies: df = df.sample(num_companies, random_state=42)
    elif len(df) < num_companies:
        extra = num_companies - len(df)
        dup = df.sample(extra, replace=True, random_state=43)
        dup['Return'] += np.random.uniform(-2, 2, size=len(dup))
        dup['MarketCap'] += np.random.uniform(-20, 20, size=len(dup))
        df = pd.concat([df, dup], ignore_index=True)

    if negative_bias: # Ensure ~60% negative returns
        target = int(0.6 * len(df))
        curr = (df['Return'] < 0).sum()
        if curr < target:
            pos_idx = df[df['Return'] > 0].index
            need = min(len(pos_idx), target - curr)
            for i in np.random.choice(pos_idx, need, replace=False):
                df.at[i, 'Return'] = -abs(df.at[i, 'Return'])

    # Add some return extremes
    extremes = [-30, -25, -20, -15, 10, 15, 20, 25]
    for idx, val in zip(np.random.choice(df.index, len(extremes), replace=False), extremes):
        df.at[idx, 'Return'] = val
    # Make some market caps extreme
    if include_size:
        cap_extremes = [10, 20, 800, 1000, 1500]
        for idx, val in zip(np.random.choice(df.index, len(cap_extremes), replace=False), cap_extremes):
             if idx in df.index: # Ensure index exists after potential sampling
                 df.at[idx, 'MarketCap'] = val

    df['Return'] = df['Return'].astype(float)
    if include_size and 'MarketCap' in df.columns:
        df['MarketCap'] = df['MarketCap'].astype(float)

    # Introduce NaNs in Return and MarketCap
    if include_nan:
        cnt_ret = max(1, int(0.08 * len(df))) # 8% NaN returns
        for i in np.random.choice(df.index, cnt_ret, replace=False):
            df.at[i, 'Return'] = np.nan
        st.write(f"Added {cnt_ret} NaN values to 'Return' column.")
        if include_size and 'MarketCap' in df.columns:
            cnt_cap = max(1, int(0.05 * len(df))) # 5% NaN caps
            # Choose indices that don't already have NaN return if possible
            valid_indices_for_cap_nan = df[df['Return'].notna()].index
            if len(valid_indices_for_cap_nan) >= cnt_cap:
                 chosen_indices = np.random.choice(valid_indices_for_cap_nan, cnt_cap, replace=False)
            else: # If not enough non-NaN return rows, sample from all
                 chosen_indices = np.random.choice(df.index, cnt_cap, replace=False)
            for i in chosen_indices:
                df.at[i, 'MarketCap'] = np.nan
            st.write(f"Added {cnt_cap} NaN values to 'MarketCap' column.")

    # Don't fillna here - let the component handle it based on 'handle_nan'
    return df


# --- Streamlit UI ---
st.title("Hierarchical Treemap Visualization")
st.markdown("""
This app demonstrates the `TreemapComponent` for visualizing hierarchical data.
Explore the tabs to see how to use it with your data or generate examples.
""")

tab1, tab2, tab3, tab4 = st.tabs([
    "How to Use",
    "S&P 500 Example",
    "Create Your Own",
    "Component Code"
])

# --- Tab 1: How to Use ---
with tab1:
    st.header("Using the Treemap Component")
    st.markdown("1.  **Import:** Add `from treemap_component import TreemapComponent` to your script.")
    st.markdown("2.  **Prepare Data:** Ensure you have a pandas DataFrame with columns for at least 3 hierarchy levels and 1 numeric value column (for color). Optionally, add a numeric column for size.")
    st.markdown("3.  **Instantiate & Render:** Create an instance and call the `.render()` method.")

    st.subheader("Minimal Example")
    st.code("""
import streamlit as st
import pandas as pd
from treemap_component import TreemapComponent

# Example DataFrame Structure
# Your actual data loading would go here
rel_df = pd.DataFrame({
    'Theme': ['Growth', 'Growth', 'Value', 'Value', 'Income', 'Income'],
    'Strategy': ['Aggressive', 'Moderate', 'Core', 'Defensive', 'Dividend', 'Fixed'],
    'Holding': ['Stock A', 'Stock B', 'Stock C', 'Bond X', 'Stock D', 'Bond Y'],
    'Performance': [0.15, 0.08, -0.02, 0.01, 0.05, 0.03], # Example: Decimal returns
    'Weight': [10.0, 15.0, 25.0, 20.0, 18.0, 12.0]        # Example: Portfolio weight
})

# Instantiate the component with title and subtitle
treemap = TreemapComponent(
    title="Portfolio Overview",
    subtitle="Size by Weight, Color by Performance"
)

# Render the chart (title/subtitle are NOT passed here)
treemap.render(
    df=rel_df,
    level1_column='Theme',
    level2_column='Strategy',
    level3_column='Holding',
    value_column='Performance',     # Column for color
    size_column='Weight',         # Column for size (optional)
    # --- Customization Options ---
    height=700,
    value_min=-0.1,               # Min value for color scale (e.g., -10%)
    value_max=0.2,                # Max value for color scale (e.g., +20%)
    auto_scale_percentage=True,   # Convert Performance (0.15) to 15% for color axis
    handle_nan='show',            # How to treat NaNs in 'Performance'
    # ... other options like colors, labels, etc.
)
    """, language="python")

# --- Tab 4: Component Code ---
with tab4:
    st.header("`TreemapComponent` Source Code")
    st.markdown("You can copy this code into a `treemap_component.py` file in your project.")
    try:
        # Make sure the component file is in the same directory or PYTHONPATH
        component_code = inspect.getsource(TreemapComponent)
        st.code(component_code, language="python", line_numbers=True)
    except Exception as e:
        st.error(f"Could not retrieve component source code: {e}")
        st.error("Ensure 'treemap_component.py' is accessible.")


# --- Tab 2: S&P 500 Example ---
with tab2:
    st.header("S&P 500 Market Performance Example")
    st.markdown("Visualizing Sector > Industry > Company hierarchy.")

    col1, col2 = st.columns(2)
    with col1:
        use_market_cap = st.checkbox(
            "Size boxes by Market Cap?", value=True, key="sp500_use_size"
        )
        include_nan_sp = st.checkbox(
            "Include NaN values (for testing)?", value=False, key="sp500_include_nan"
        )

    df_sp = create_sp500_sample_data(
        num_companies=75, # Slightly more data
        include_nan=include_nan_sp,
        include_size=True # Always generate size, checkbox controls using it
    )

    # Define title and subtitle separately first
    sp_title = "S&P 500 Performance"
    sp_subtitle = f"Color by Return (%), {'Size by Market Cap (B)' if use_market_cap else 'Size by Item Count'}"

    # Prepare parameters for render call - **NO title/subtitle HERE**
    render_params_sp = {
        'df': df_sp,
        'level1_column': 'Sector',
        'level2_column': 'Industry',
        'level3_column': 'Company',
        'value_column': 'Return',
        'size_column': 'MarketCap' if use_market_cap else None,
        'height': 750,
        'value_min': -30,
        'value_max': 30,
        'color_min': '#d40000',
        'color_max': '#00b52a',
        'validate_data': True,
        'auto_scale_percentage': False, # Returns are already percentages
        'fill_hierarchy_na': "Unknown Category",
        # 'title' and 'subtitle' removed from this dict
    }

    with col2:
        if include_nan_sp:
            nan_handling_sp = st.radio(
                "Handle NaN values in 'Return'/'MarketCap':",
                ["Show (default color/label)", "Replace with Zero", "Hide Rows"],
                index=0, key="sp500_nan_handling", horizontal=True,
                help="'Show': Display NaNs with specific style. 'Zero': Replace Return NaNs with 0, MarketCap NaNs with 1. 'Hide': Remove rows with NaNs in Return."
            )
            if nan_handling_sp == "Show (default color/label)":
                render_params_sp['handle_nan'] = "show"
                render_params_sp['nan_label'] = st.text_input("Label for NaN:", "N/A", key="sp500_nan_label")
                render_params_sp['nan_color'] = st.color_picker("Color for NaN:", "#333333", key="sp500_nan_color")
            elif nan_handling_sp == "Replace with Zero":
                render_params_sp['handle_nan'] = "zero"
                render_params_sp['nan_label'] = "0.0%" # Will be used if zeroing results in 0
                render_params_sp['nan_color'] = "#414555" # Default gray
            else: # Hide Rows
                render_params_sp['handle_nan'] = "hide"
                render_params_sp['nan_label'] = "" # Not used
                render_params_sp['nan_color'] = "" # Not used
        else:
            render_params_sp['handle_nan'] = "zero" # Default if no NaNs introduced
            render_params_sp['nan_label'] = "N/A"
            render_params_sp['nan_color'] = "#333333"


    # Display data overview
    st.subheader("Sample Data & Configuration")
    st.dataframe(df_sp.head(10), use_container_width=True)
    # Check for NaNs in relevant columns before showing expander
    check_cols_nan = [render_params_sp['value_column']]
    if render_params_sp['size_column']:
        check_cols_nan.append(render_params_sp['size_column'])
    if df_sp[check_cols_nan].isna().any().any():
        with st.expander(f"Rows with NaN values ('{render_params_sp['value_column']}' or '{render_params_sp['size_column'] if render_params_sp['size_column'] else 'N/A'}')"):
            nan_mask = df_sp[render_params_sp['value_column']].isna()
            if render_params_sp['size_column']:
                 nan_mask |= df_sp[render_params_sp['size_column']].isna()
            st.dataframe(df_sp[nan_mask], use_container_width=True)

    # Distribution plot
    st.subheader("Return Distribution (Original Data)")
    fig, ax = plt.subplots(figsize=(10, 3))
    vals = df_sp['Return'].dropna()
    if len(vals) > 0:
        ax.hist(vals, bins=np.linspace(-35, 35, 35), edgecolor='black', color='#69b3a2')
        ax.axvline(0, color='red', linestyle='--', linewidth=1.5)
        ax.set_title('Distribution of Returns (%)')
        ax.set_xlabel('Return (%)')
        ax.set_ylabel('Count')
        # Add NaN count text if relevant
        nan_count_ret = df_sp['Return'].isna().sum()
        if nan_count_ret > 0:
             ax.text(0.98, 0.95, f"NaN Returns: {nan_count_ret}", transform=ax.transAxes,
                    ha='right', va='top', bbox=dict(boxstyle='round,pad=0.3', fc='wheat', alpha=0.8))
        st.pyplot(fig)
    else:
        st.warning("No valid 'Return' data to plot distribution (might be all NaNs).")


    # --- Render the Treemap ---
    st.subheader("Treemap Visualization")
    # Instantiate with title and subtitle
    tm_sp = TreemapComponent(
        title=sp_title,
        subtitle=sp_subtitle
    )
    # Render using the dictionary **WITHOUT** title/subtitle
    try:
        tm_sp.render(**render_params_sp)
    except Exception as e:
         st.error(f"Error during rendering: {e}")
         st.exception(e)


    # --- Show Generated Code ---
    st.subheader("Code to Reproduce This Chart")
    st.markdown("Copy and paste this code into your Streamlit app. Make sure you have the `treemap_component.py` file and your DataFrame (`df`) ready.")
    # Create a temporary dict *including* title/subtitle JUST for the code generator helper
    code_gen_params_sp = render_params_sp.copy()
    code_gen_params_sp['title'] = sp_title
    code_gen_params_sp['subtitle'] = sp_subtitle
    # Ensure df is removed from params dict before generating code example
    code_gen_params_sp.pop('df', None)
    repro_code_sp = generate_render_code(code_gen_params_sp)
    st.code(repro_code_sp, language="python")


# --- Tab 3: Create Your Own ---
with tab3:
    st.header("Create Your Own Treemap")
    st.markdown("""
    Upload a CSV or generate a custom sample dataset. Then, configure the columns
    and appearance for your treemap. The code to reproduce it will be generated below.
    """)

    data_source = st.radio(
        "Select Data Source:",
        ["Upload CSV", "Generate Sample Data"],
        key="custom_source", horizontal=True
    )

    user_df = None
    # Start with render-specific params, title/subtitle handled separately
    render_params_custom = {'validate_data': True} # Start with validation on
    custom_title = "Custom Treemap" # Initialize defaults for title/subtitle
    custom_subtitle = "Color by Value, Size optional"

    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload your CSV file", type=["csv"], key="custom_upload"
        )
        if uploaded_file:
            try:
                user_df = pd.read_csv(uploaded_file)
                st.success(f"Successfully loaded {uploaded_file.name} ({len(user_df)} rows)")
                st.dataframe(user_df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                user_df = None # Ensure df is None if loading fails
        else:
            st.info("Upload a CSV file to begin configuration.")

    else: # Generate Sample Data
        st.subheader("Generate Custom Sample Data")
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            num_lv1 = st.slider("Number of Level 1 categories:", 2, 8, 4, key="sample_lv1_count")
            num_items_per_group = st.slider("Avg items per Level 3 group:", 3, 10, 5, key="sample_item_count")
            include_size_sample = st.checkbox("Include 'Size' column?", True, key="sample_include_size")
        with col_gen2:
            neg_bias_sample = st.checkbox("Bias towards negative values?", True, key="sample_neg_bias")
            include_nan_sample = st.checkbox("Include some NaN values?", False, key="sample_include_nan")


        if st.button("Generate Sample Data", key="sample_generate"):
            lvl1_names = [f"Category {chr(65+i)}" for i in range(num_lv1)] # A, B, C...
            sample_rows = []
            np.random.seed(101)
            biases = np.random.uniform(-20 if neg_bias_sample else -5, 15 if neg_bias_sample else 25, num_lv1)

            for i, lvl1_name in enumerate(lvl1_names):
                base_val = biases[i]
                num_lvl2 = np.random.randint(2, 5)
                for g in range(num_lvl2):
                    lvl2_name = f"{lvl1_name} Group {g+1}"
                    offset2 = np.random.uniform(-8, 8)
                    mid_val = base_val + offset2
                    num_lvl3 = np.random.randint(max(2,num_items_per_group-2), num_items_per_group+3)
                    for j in range(num_lvl3):
                        lvl3_name = f"Item {np.random.randint(100,999)}-{j+1}" # More unique names
                        offset3 = np.random.uniform(-10, 10)
                        val = np.clip(mid_val + offset3, -40, 40) # Clip values
                        size = np.random.uniform(10, 200) * (1 + i*0.2) # Make later categories bigger
                        sample_rows.append({
                            'Level1': lvl1_name, 'Level2': lvl2_name, 'Level3': lvl3_name,
                            'Value': round(val, 2),
                            'Size': round(size, 1) if include_size_sample else np.nan
                        })

            user_df = pd.DataFrame(sample_rows)

            # Introduce NaNs if requested
            if include_nan_sample:
                 nan_frac = 0.07
                 n_nan_val = max(1, int(nan_frac * len(user_df)))
                 nan_val_indices = np.random.choice(user_df.index, n_nan_val, replace=False)
                 user_df.loc[nan_val_indices, 'Value'] = np.nan
                 st.write(f"Added {n_nan_val} NaNs to 'Value'.")
                 if include_size_sample and 'Size' in user_df.columns:
                      n_nan_size = max(1, int(nan_frac * len(user_df)))
                      # Try to pick different indices for size NaNs
                      potential_size_nan_indices = user_df.index.difference(nan_val_indices)
                      if len(potential_size_nan_indices) < n_nan_size:
                           potential_size_nan_indices = user_df.index # Fallback to all if needed
                      nan_size_indices = np.random.choice(potential_size_nan_indices, n_nan_size, replace=False)
                      user_df.loc[nan_size_indices, 'Size'] = np.nan
                      st.write(f"Added {n_nan_size} NaNs to 'Size'.")

            st.success(f"Generated sample data ({len(user_df)} rows).")
            st.dataframe(user_df.head(), use_container_width=True)
            st.session_state['user_df_generated'] = user_df # Store in session state

    # Retrieve generated df from session state if button wasn't just clicked
    if data_source == "Generate Sample Data" and 'user_df_generated' in st.session_state and user_df is None:
         user_df = st.session_state['user_df_generated']
         if user_df is not None:
              st.dataframe(user_df.head(), use_container_width=True) # Show head again if retrieved


    # --- Configuration Columns ---
    if user_df is not None:
        st.divider()
        st.subheader("Configure Treemap")
        cols = user_df.columns.tolist()
        numeric_cols = user_df.select_dtypes(include=np.number).columns.tolist()
        # Allow selecting 'None' for size column
        size_options = [None] + numeric_cols

        cfg1, cfg2 = st.columns(2)

        with cfg1:
            st.markdown("**Hierarchy Columns**")
            # Set defaults based on generated data column names if available
            l1_index = cols.index('Level1') if 'Level1' in cols else 0
            l2_index = cols.index('Level2') if 'Level2' in cols else min(1, len(cols)-1)
            l3_index = cols.index('Level3') if 'Level3' in cols else min(2, len(cols)-1)
            render_params_custom['level1_column'] = st.selectbox("Level 1 (Top):", cols, index=l1_index, key="custom_lvl1")
            render_params_custom['level2_column'] = st.selectbox("Level 2 (Middle):", cols, index=l2_index, key="custom_lvl2")
            render_params_custom['level3_column'] = st.selectbox("Level 3 (Leaf):", cols, index=l3_index, key="custom_lvl3")
            render_params_custom['fill_hierarchy_na'] = st.text_input("Fill Hierarchy NaNs with:", "Unknown", key="custom_fill_hier")

            st.markdown("**Data Columns**")
            val_index = numeric_cols.index('Value') if 'Value' in numeric_cols else 0
            size_index = size_options.index('Size') if 'Size' in size_options else 0
            render_params_custom['value_column'] = st.selectbox(
                "Value Column (for Color):", numeric_cols, index=val_index, key="custom_val"
            )
            render_params_custom['size_column'] = st.selectbox(
                "Size Column (Optional):", size_options, index=size_index,
                format_func=lambda x: 'None (Use Item Count)' if x is None else x,
                key="custom_size"
            )
            render_params_custom['auto_scale_percentage'] = st.checkbox(
                 "Auto-scale Value (x100 if between -1 and 1)?", value=False,
                 help="Enable if your value column has decimals (e.g., 0.15) instead of percentages (e.g., 15).",
                 key="custom_autoscale"
            )


        with cfg2:
            st.markdown("**Appearance**")
            # Get title/subtitle directly into variables, not the render dict
            custom_title = st.text_input("Chart Title:", custom_title, key="custom_title")
            custom_subtitle = st.text_input("Chart Subtitle:", custom_subtitle, key="custom_sub")
            render_params_custom['height'] = st.slider("Chart Height:", 400, 1200, 750, key="custom_height")

            st.markdown("**Color Axis**")
             # Calculate dynamic min/max based on selected value column
            try:
                val_col_name = render_params_custom['value_column']
                if val_col_name in user_df:
                    value_series = user_df[val_col_name].dropna()
                    scale_factor = 100 if render_params_custom['auto_scale_percentage'] else 1
                    default_min = -10.0
                    default_max = 10.0
                    if not value_series.empty:
                        default_min = round(value_series.min() * scale_factor, 1)
                        default_max = round(value_series.max() * scale_factor, 1)
                    # Ensure min < max, handle edge case where min=max
                    if default_min >= default_max:
                        default_min = default_max - 1
                        if default_max == 0 : default_max = 1 # Avoid min=-1, max=0

                else: # Fallback if column name somehow invalid
                    default_min = -10.0
                    default_max = 10.0
            except Exception: # Broad catch for safety during dynamic calculation
                 default_min = -10.0
                 default_max = 10.0

            render_params_custom['value_min'] = st.number_input("Min Value (Color):", value=default_min, step=1.0, key="custom_vmin")
            render_params_custom['value_max'] = st.number_input("Max Value (Color):", value=default_max, step=1.0, key="custom_vmax")
            render_params_custom['color_min'] = st.color_picker("Min Color (Negative):", "#d40000", key="custom_cmin")
            render_params_custom['color_max'] = st.color_picker("Max Color (Positive):", "#00b52a", key="custom_cmax")

            st.markdown("**NaN Handling (Value/Size Columns)**")
            has_nan_val = False
            if render_params_custom['value_column'] in user_df:
                has_nan_val = user_df[render_params_custom['value_column']].isna().any()

            has_nan_size = False
            if render_params_custom['size_column'] and render_params_custom['size_column'] in user_df:
                 has_nan_size = user_df[render_params_custom['size_column']].isna().any()

            if has_nan_val or has_nan_size:
                 nan_info_text = f"Handle NaNs in '{render_params_custom['value_column']}'"
                 if has_nan_size:
                     nan_info_text += f" or '{render_params_custom['size_column']}'"
                 nan_info_text += ":"

                 nan_handling_custom = st.radio(
                     nan_info_text,
                     ["Show", "Zero", "Hide"], index=0, key="custom_nan_handling", horizontal=True,
                     help="'Show': Display NaNs with specific style. 'Zero': Replace Value NaNs with 0, Size NaNs with 1. 'Hide': Remove rows with Value NaNs."
                 )
                 render_params_custom['handle_nan'] = nan_handling_custom.lower()
                 if render_params_custom['handle_nan'] == "show":
                      render_params_custom['nan_label'] = st.text_input("NaN Label:", "N/A", key="custom_nan_label")
                      render_params_custom['nan_color'] = st.color_picker("NaN Color:", "#333333", key="custom_nan_color")
                 else: # zero or hide
                      render_params_custom['nan_label'] = "N/A" # Defaults, not used by JS if zero/hide
                      render_params_custom['nan_color'] = "#333333"
            else:
                 st.info("No NaNs detected in selected Value/Size columns.")
                 render_params_custom['handle_nan'] = 'show' # Default if no NaNs
                 render_params_custom['nan_label'] = "N/A"
                 render_params_custom['nan_color'] = "#333333"

        st.divider()

        # --- Render Custom Treemap ---
        if st.button("Generate Custom Treemap", key="custom_generate_btn", type="primary"):
            st.subheader("Generated Treemap")
            # Instantiate with title/subtitle
            tm_custom = TreemapComponent(
                title=custom_title,
                subtitle=custom_subtitle
            )
            # Add dataframe to params just before render
            render_params_custom['df'] = user_df
            # Render using the dictionary **WITHOUT** title/subtitle
            try:
                tm_custom.render(**render_params_custom)
            except Exception as e:
                 st.error(f"Error during rendering: {e}")
                 st.exception(e)


            # --- Show Generated Code ---
            st.subheader("Code to Reproduce This Chart")
            # Create a temporary dict *including* title/subtitle JUST for the code generator helper
            code_gen_params_custom = render_params_custom.copy()
            code_gen_params_custom['title'] = custom_title
            code_gen_params_custom['subtitle'] = custom_subtitle
            # Ensure df is removed from params dict before generating code example
            code_gen_params_custom.pop('df', None)
            repro_code_custom = generate_render_code(code_gen_params_custom)
            st.code(repro_code_custom, language="python")

    elif data_source == "Upload CSV" and uploaded_file is None:
         st.warning("Please upload a CSV file above.")
    elif data_source == "Generate Sample Data" and 'user_df_generated' not in st.session_state:
         st.info("Click 'Generate Sample Data' to create data.")