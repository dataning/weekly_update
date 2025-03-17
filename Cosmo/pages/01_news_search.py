"""
News Search page for the Gravity app
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.session_state import initialize_session_state
from utils.data_processing import clean_dataframe
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
from modules.news_search import search_news, filter_news_data, create_company_distribution_chart

# Set page config
st.set_page_config(
    page_title="News Search - Gravity",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session_state()

# Render header
render_header()

# Main page content
st.title("🔍 Company News Search")
st.write("Search for latest news about companies using the Opoint API")

# Add button to go to analysis page if we have filtered data
if ("filtered_news_df" in st.session_state and 
    st.session_state.filtered_news_df is not None and 
    not st.session_state.filtered_news_df.empty):
    # Check if any rows are selected
    selected_rows = st.session_state.filtered_news_df[st.session_state.filtered_news_df['selected'] == True]
    if not selected_rows.empty:
        # Use a completely unique key with timestamp
        button_key = f"goto_tagging_btn_{int(time.time() * 1000)}"
        if st.button("→ Go to News Tagging", type="primary", key=button_key):
            # Filter the dataframe to only include selected rows
            st.session_state.selected_news_df = selected_rows.copy()
            # Reset 'selected' column in the analysis tab to allow re-selection
            st.session_state.selected_news_df['selected'] = False
            # Store in tagged_news_df for the newsletter tab
            st.session_state.tagged_news_df = st.session_state.selected_news_df.copy()
            # Switch to the tagging page
            st.switch_page("pages/02_news_tagging.py")
    else:
        st.warning("Please select at least one article to tag by checking the 'Select' column")

with st.sidebar:
    st.header("Search Parameters")
    
    # Companies input
    st.subheader("Companies")
    default_companies = ["BlackRock", "Tesla", "Microsoft", "Apple"]
    companies_text = st.text_area(
        "Enter company names (one per line):",
        value="\n".join(default_companies),
        height=150,
        key="companies_text_area"
    )
    companies = [c.strip() for c in companies_text.split("\n") if c.strip()]
    
    # Time range
    st.subheader("Time Range")
    days_back_options = [1, 2, 3, 5, 7, 14, 30]
    days_back_select = st.select_slider(
        "Days to look back:",
        options=days_back_options,
        value=3,
        key="days_back_slider"
    )
    # Convert days to hours for the API
    hours_back = days_back_select * 24
    
    # Advanced options in an expander
    with st.expander("Advanced Options"):
        initial_limit = st.number_input(
            "Initial articles limit per company:",
            min_value=10,
            max_value=1000,
            value=500,
            step=10,
            key="initial_limit_input"
        )
        
        use_proxy = st.checkbox("Use Proxy", value=False, key="use_proxy_checkbox")
        
        if use_proxy:
            st.info("Using proxy: http://webproxy.blackrock.com:8080")
    
    # Search button
    search_button = st.button("🔍 Search News", type="primary", use_container_width=True, key="search_news_btn")

# Main content area
if "news_df" not in st.session_state:
    st.session_state.news_df = None

if search_button:
    if not companies:
        st.error("Please enter at least one company name")
    else:
        # Call search function
        df = search_news(
            companies=companies,
            hours_back=hours_back,
            initial_limit=initial_limit,
            use_proxy=use_proxy
        )
        
        # Store in session state
        st.session_state.news_df = df

# Display results if we have them
if st.session_state.news_df is not None and not st.session_state.news_df.empty:
    df = st.session_state.news_df
    
    # Filters section
    st.header("Filters")
    
    # Row 1: Company + Site Rank
    filter_row1_col1, filter_row1_col2 = st.columns(2)
    
    # Filter by company
    with filter_row1_col1:
        if 'search_term' in df.columns:
            company_filter = st.multiselect(
                "Filter by Company:",
                options=sorted(df['search_term'].unique()),
                default=sorted(df['search_term'].unique()),
                key="company_filter_multiselect"
            )
        else:
            company_filter = None
    
    # Filter by site rank
    with filter_row1_col2:
        if 'site_rank_rank_country' in df.columns:
            # Get max rank for setting appropriate intervals
            max_rank = int(df['site_rank_rank_country'].max())
            # Create intervals (100, 200, 300, etc.)
            rank_intervals = list(range(0, max_rank + 100, 100))
            if rank_intervals[-1] < max_rank:
                rank_intervals.append(max_rank)
                
            # Select interval as a range
            rank_min, rank_max = st.select_slider(
                "Filter by Site Rank:",
                options=rank_intervals,
                value=(0, rank_intervals[-1]),
                key="site_rank_slider"
            )
        else:
            rank_min, rank_max = None, None
    
    # Row 2: Country + Term Matching
    filter_row2_col1, filter_row2_col2 = st.columns(2)
    
    # Filter by country
    with filter_row2_col1:
        if 'countryname' in df.columns:
            # Convert all values to strings and filter out NaN values
            country_values = df['countryname'].dropna()
            country_values = [str(x) for x in country_values.unique()]
            country_values.sort()
            
            country_filter = st.multiselect(
                "Filter by Country:",
                options=country_values,
                default=[],
                key="country_filter_multiselect"
            )
        else:
            country_filter = None
    
    # Filter by all search terms in header or summary
    with filter_row2_col2:
        search_terms_filter = st.checkbox("Filter for any search term in headline/summary", value=False, key="search_terms_filter_checkbox")
        st.caption("Searches for selected companies in headline/summary")
    
    # Row 3: News Source + Days
    filter_row3_col1, filter_row3_col2 = st.columns(2)
    
    # Filter by first_source_name (news outlet)
    with filter_row3_col1:
        if 'first_source_name' in df.columns:
            # Get top 50 most common sources to avoid overwhelming the UI
            try:
                top_sources = df['first_source_name'].dropna().value_counts().nlargest(50).index.tolist()
                # Convert all to strings to avoid sorting issues
                top_sources = [str(x) for x in top_sources]
                top_sources.sort()
                
                source_filter = st.multiselect(
                    "Filter by News Source (Top 50):",
                    options=top_sources,
                    default=[],
                    key="source_filter_multiselect"
                )
            except:
                # Fallback if there's an error with the sorting
                source_filter = []
                st.warning("Unable to process news sources")
        else:
            source_filter = None
    
    # Filter by time
    with filter_row3_col2:
        if 'local_time_text' in df.columns:
            # Filter by days back from today
            days_back = st.slider(
                "Filter by Days (from today):",
                min_value=1,
                max_value=30,  # Default to max 30 days
                value=7,       # Default to 7 days
                step=1,
                key="days_filter_slider"
            )
            # Calculate the date range based on days back
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            try:
                # Convert string format to datetime - with better error handling
                df['local_time_datetime'] = pd.to_datetime(df['local_time_text'], format='%Y%m%dT%H:%M:%S%z', errors='coerce')
            except Exception as e:
                st.warning(f"Could not parse time format: {str(e)}")
                days_back = None
                start_date = None
                end_date = None
        else:
            days_back = None
            start_date = None
            end_date = None
    
    # Apply all filters to create filtered dataframe
    filter_params = {
        'company_filter': company_filter,
        'source_filter': source_filter,
        'country_filter': country_filter,
        'rank_min': rank_min,
        'rank_max': rank_max,
        'days_back': days_back,
        'search_terms_filter': search_terms_filter
    }
    
    filtered_df = filter_news_data(df, filter_params)
    
    # Add 'selected' column to the filtered dataframe if it doesn't exist
    if 'selected' not in filtered_df.columns:
        filtered_df['selected'] = False
        
    # Store the filtered dataframe in session state for the analysis page
    st.session_state.filtered_news_df = filtered_df
    
    # RESULTS SECTION
    # Dashboard stats based on filtered data
    st.header("📊 Search Results")
    st.subheader(f"Showing {len(filtered_df)} articles")
    
    # Create two columns for stats and chart
    stats_col, chart_col = st.columns(2)
    
    with stats_col:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Articles", len(filtered_df))
        with col2:
            if 'search_term' in filtered_df.columns:
                st.metric("Companies", filtered_df['search_term'].nunique())
        
        col3, col4 = st.columns(2)
        with col3:
            if 'datetime' in filtered_df.columns:
                df_with_dates = filtered_df[filtered_df['datetime'].notna()]
                if not df_with_dates.empty:
                    earliest = df_with_dates['datetime'].min()
                    st.metric("Earliest", earliest.strftime('%Y-%m-%d %H:%M'))
        with col4:
            if 'datetime' in filtered_df.columns:
                df_with_dates = filtered_df[filtered_df['datetime'].notna()]
                if not df_with_dates.empty:
                    latest = df_with_dates['datetime'].max()
                    st.metric("Latest", latest.strftime('%Y-%m-%d %H:%M'))
    
    # Company distribution chart based on filtered data
    with chart_col:
        fig = create_company_distribution_chart(filtered_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Choose columns to display in the data editor
    display_cols = []
    priority_cols = [
        'selected', 'search_term', 'header_text', 'summary_text', 'first_source_name', 
        'countryname', 'site_rank_rank_country', 'local_time_text'
    ]
    
    # Add columns that exist in the dataframe
    for col in priority_cols:
        if col in filtered_df.columns:
            display_cols.append(col)
    
    # If no columns matched, use all columns
    if not display_cols:
        display_cols = filtered_df.columns.tolist()
    
    # Display data editor - ensure 'selected' is displayed first
    if 'selected' in display_cols:
        display_cols.remove('selected')
        display_cols.insert(0, 'selected')
        
    news_editor = st.data_editor(
        filtered_df[display_cols],
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="news_data_editor_search"
    )
    
    # Update filtered_df with any edits from the data editor, especially selected column
    for col in display_cols:
        if col in news_editor.columns:
            filtered_df[col] = news_editor[col]
    
    # Store the updated filtered dataframe in session state
    st.session_state.filtered_news_df = filtered_df
    
    # Calculate how many rows are selected
    selected_count = filtered_df['selected'].sum()
    
    # Add button to navigate to the analysis page
    col1, col2 = st.columns([1, 3])
    with col1:
        button_label = f"→ Tag {int(selected_count)} Selected Articles" if selected_count > 0 else "→ Select Articles to Tag"
        tag_button = st.button(button_label, type="primary", use_container_width=True, key="goto_tagging_btn_search2")
        
        if tag_button:
            if selected_count > 0:
                # Store only selected rows
                selected_rows = filtered_df[filtered_df['selected'] == True]
                st.session_state.selected_news_df = selected_rows.copy()
                # Reset 'selected' column in the analysis tab to enable re-selection
                st.session_state.selected_news_df['selected'] = False
                # Store in tagged_news_df for the newsletter tab
                st.session_state.tagged_news_df = st.session_state.selected_news_df.copy()
                # Navigate to tagging page
                st.switch_page("pages/02_news_tagging.py")
            else:
                st.warning("Please select at least one article by checking the 'Select' column")
    
    # Download button
    with col2:
        st.download_button(
            label="📥 Download Results as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name=f"news_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_results_btn_search"
        )

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()