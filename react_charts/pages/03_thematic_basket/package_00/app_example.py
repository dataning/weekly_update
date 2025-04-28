import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from treemap_component import TreemapComponent

# Set page configuration
st.set_page_config(
    page_title="Hierarchical Treemap Demo",
    page_icon="📊",
    layout="wide"
)

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

# --- Streamlit UI ---

st.title("Hierarchical Treemap Visualization")
st.markdown("""
This app demonstrates how to build hierarchical treemap visualizations
using any DataFrame, with three-level drilldown and color-coded performance.
""")

tab1, tab2, tab3 = st.tabs(["Your Data", "S&P 500 Example", "Create Your Own"])

# Tab 1: Your Data
with tab1:
    st.header("Your Portfolio Data")
    st.markdown("Use your own portfolio DataFrame (`rel_df`) with three-level hierarchy:")
    st.code("""
from treemap_component import TreemapComponent

treemap = TreemapComponent(
    title="Investment Themes and Benchmarks",
    subtitle="Click to drill down. Color indicates performance."
)
treemap.render(
    df=rel_df,
    level1_column='Merged_Theme',
    level2_column='Benchmark',
    level3_column='Basket',
    value_column='MTD',
    height=800
)
    """, language="python")
    st.markdown("This will generate the same treemap with minimal boilerplate.")

# Tab 2: S&P 500 Example
with tab2:
    st.header("S&P 500 Market Performance")

    include_nan = st.checkbox(
        "Include NaN values (for testing)",
        value=False,
        key="sp500_include_nan"
    )

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

    # Summary metrics
    negative_pct = (df_sp['Return'] < 0).mean() * 100
    nan_count = df_sp['Return'].isna().sum()
    c1, c2 = st.columns(2)
    c1.info(f"Negative values: {negative_pct:.1f}%")
    if include_nan:
        c2.info(f"NaN values: {nan_count} ({nan_count/len(df_sp)*100:.1f}%)")

    # Sample data table
    st.subheader("Sample Data")
    st.dataframe(df_sp.head(10))
    if nan_count:
        with st.expander("Rows with NaN values"):
            st.dataframe(df_sp[df_sp['Return'].isna()])

    # Distribution plot
    st.subheader("Return Distribution")
    fig, ax = plt.subplots(figsize=(10, 3))
    vals = df_sp['Return'].dropna()
    ax.hist(vals, bins=np.linspace(-30, 30, 30), edgecolor='black')
    ax.axvline(0, color='red', linestyle='--', linewidth=2)
    if nan_count:
        ax.text(0.98, 0.95, f"NaN: {nan_count}", transform=ax.transAxes,
                ha='right', va='top', bbox=dict(facecolor='white', alpha=0.8))
    ax.set_xlabel('Return (%)')
    ax.set_ylabel('Count')
    st.pyplot(fig)

    # Treemap
    st.subheader("Treemap Visualization")
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
        handle_nan=handle_nan
    )

    st.subheader("Code Snippet")
    st.code("""
include_nan = st.checkbox("Include NaN values (for testing)", key="sp500_include_nan")
nan_handling = st.radio("How to handle NaN values:", [...], key="sp500_nan_handling")
nan_label = st.text_input("Label for NaN values:", key="sp500_nan_label")
nan_color = st.color_picker("Color for NaN boxes:", key="sp500_nan_color")
treemap.render(..., nan_color=nan_color, nan_label=nan_label, handle_nan=handle_nan)
    """, language="python")

# Tab 3: Create Your Own
with tab3:
    st.header("Create Your Own Treemap")
    st.markdown("""
Upload a CSV or generate a custom sample dataset and then choose the columns
for Level 1, Level 2, Level 3, and the value.
    """)
    source = st.radio(
        "Data source:",
        ["Upload CSV", "Generate Sample"],
        key="custom_source"
    )

    if source == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload a CSV file", type=["csv"],
            key="custom_upload"
        )
        if uploaded_file:
            user_df = pd.read_csv(uploaded_file)
            has_nan = user_df.select_dtypes(include='number').isna().any().any()
            if has_nan:
                nan_choice = st.radio(
                    "NaN handling:",
                    ["Show label", "Zero", "Hide"],
                    key="custom_nan_handling"
                )
                if nan_choice == "Show label":
                    custom_nan_label = st.text_input(
                        "Label for NaN:",
                        "N/A",
                        key="custom_nan_label"
                    )
                    custom_nan_color = st.color_picker(
                        "Color for NaN:",
                        "#333333",
                        key="custom_nan_color"
                    )
                    df_to_use = user_df
                elif nan_choice == "Zero":
                    df_to_use = user_df.fillna(0)
                    custom_nan_label = "0.00%"
                    custom_nan_color = "#414555"
                else:
                    df_to_use = user_df.dropna()
                    custom_nan_label = ""
                    custom_nan_color = ""
            else:
                df_to_use = user_df
                custom_nan_label = ""
                custom_nan_color = ""

            st.dataframe(df_to_use.head())
            lvl1 = st.selectbox("Level 1 column:", df_to_use.columns, key="custom_lvl1")
            lvl2 = st.selectbox("Level 2 column:", df_to_use.columns, key="custom_lvl2")
            lvl3 = st.selectbox("Level 3 column:", df_to_use.columns, key="custom_lvl3")
            valc = st.selectbox(
                "Value column (numeric):",
                [c for c in df_to_use.columns if pd.api.types.is_numeric_dtype(df_to_use[c])],
                key="custom_val"
            )
            chart_title = st.text_input("Chart title:", "My Treemap", key="custom_title")
            chart_sub = st.text_input("Chart subtitle:", "Click to drill down", key="custom_sub")
            chart_height = st.slider("Chart height:", 400, 1000, 700, key="custom_height")
            vmin = st.number_input("Min value:", -30.0, key="custom_vmin")
            vmax = st.number_input("Max value:", 30.0, key="custom_vmax")
            cmin = st.color_picker("Min color:", "#d40000", key="custom_cmin")
            cmax = st.color_picker("Max color:", "#00b52a", key="custom_cmax")

            if st.button("Generate Treemap", key="custom_generate"):
                tm = TreemapComponent(title=chart_title, subtitle=chart_sub)
                tm.render(
                    df=df_to_use,
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
                    nan_color=custom_nan_color,
                    nan_label=custom_nan_label,
                    handle_nan=("show" if has_nan else "zero")
                )

    else:  # Generate Sample
        st.subheader("Generate Custom Sample Data")
        num_lv1 = st.slider(
            "Number of top-level categories:", 2, 10, 5,
            key="sample_lv1_count"
        )
        lvl1_names = []
        for i in range(num_lv1):
            name = st.text_input(f"Category {i+1} name:", f"Cat{i+1}", key=f"sample_name_{i}")
            lvl1_names.append(name)
        include_nan_sample = st.checkbox(
            "Include NaN values in sample",
            key="sample_include_nan"
        )
        if st.button("Generate Sample", key="sample_generate"):
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

            st.subheader("Generated Sample Data")
            st.dataframe(sample_df)

            st.subheader("Sample Distribution")
            fig2, ax2 = plt.subplots(figsize=(10, 3))
            ax2.hist(sample_df['Value'].dropna(), bins=np.linspace(-30, 30, 30), edgecolor='black')
            ax2.axvline(0, color='red', linestyle='--', linewidth=2)
            st.pyplot(fig2)

            tm2 = TreemapComponent(title="Custom Sample Treemap", subtitle="Generated from inputs")
            tm2.render(
                df=sample_df,
                level1_column='Level1',
                level2_column='Level2',
                level3_column='Level3',
                value_column='Value',
                height=700,
                value_min=-30,
                value_max=30,
                color_min='#d40000',
                color_max='#00b52a',
                validate_data=True,
                nan_color=clr,
                nan_label=lbl,
                handle_nan=handle
            )