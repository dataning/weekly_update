import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import sys
import os
import re

# Set page to wide mode
st.set_page_config(layout="wide")

# Add a "Back to Home" navigation button at the top
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back to Home", key="back_to_home"):
        try:
            from streamlit.runtime.scriptrunner import RerunData, RerunException
            from streamlit.source_util import get_pages

            def switch_page(page_name):
                def standardize_name(name):
                    return name.lower().replace("_", " ")
                page_name = standardize_name(page_name)
                # Use the correct main page filename
                pages = get_pages("app.py")  
                for page_hash, config in pages.items():
                    if standardize_name(config["page_name"]) == page_name:
                        raise RerunException(
                            RerunData(
                                page_script_hash=page_hash,
                                page_name=page_name,
                            )
                        )
            # Optional: Debug output to see registered pages
            pages = get_pages("app.py")
            st.write(pages)  # Remove or comment out this line after debugging

            # Navigate to home (the home page is registered as "app")
            switch_page("app")
        except Exception as e:
            st.error(f"Navigation error: {e}")
            st.session_state.page = "home"
            st.rerun()

# Import the Opoint news function
# Assuming the module is in the same directory or in the Python path
try:
    from opoint_module import get_all_companies_news_sync
except ImportError:
    # If the import fails, we'll define a function to show a warning
    def get_all_companies_news_sync(*args, **kwargs):
        st.error("❌ Failed to import get_all_companies_news_sync. Make sure the opoint module is accessible.")
        return pd.DataFrame()

def clean_text(text):
    """Clean and format text content"""
    if not isinstance(text, str):
        return ""
    # Replace multiple newlines and spaces with single ones
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def news_search_page():
    st.title("🔍 Company News Search")
    st.write("Search for latest news about companies using the Opoint API")
    
    with st.sidebar:
        st.header("Search Parameters")
        
        # Companies input
        st.subheader("Companies")
        default_companies = ["BlackRock", "Tesla", "Microsoft", "Apple"]
        companies_text = st.text_area(
            "Enter company names (one per line):",
            value="\n".join(default_companies),
            height=150
        )
        companies = [c.strip() for c in companies_text.split("\n") if c.strip()]
        
        # Time range
        st.subheader("Time Range")
        days_back_options = [1, 2, 3, 5, 7, 14, 30]
        days_back_select = st.select_slider(
            "Days to look back:",
            options=days_back_options,
            value=3
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
                step=10
            )
            
            use_proxy = st.checkbox("Use Proxy", value=False)
            
            if use_proxy:
                st.info("Using proxy: http://webproxy.blackrock.com:8080")
        
        # Search button
        search_button = st.button("🔍 Search News", type="primary", use_container_width=True)
    
    # Main content area
    if "news_df" not in st.session_state:
        st.session_state.news_df = None
    
    if search_button:
        if not companies:
            st.error("Please enter at least one company name")
        else:
            with st.status("Searching for news...", expanded=True) as status:
                st.write(f"Looking for news about {', '.join(companies)}")
                st.write(f"Searching the past {hours_back} hours")
                
                # Start timer
                start_time = time.time()
                
                try:
                    # Call the function from the imported module
                    df = get_all_companies_news_sync(
                        companies=companies,
                        hours_back=hours_back,
                        initial_limit=initial_limit,
                        use_proxy=use_proxy
                    )
                    
                    # Store in session state
                    st.session_state.news_df = df
                    
                    # End timer
                    elapsed_time = time.time() - start_time
                    
                    if df is not None and not df.empty:
                        status.update(label=f"✅ Found {len(df)} articles in {elapsed_time:.2f} seconds", state="complete")
                    else:
                        status.update(label="❌ No articles found", state="error")
                
                except Exception as e:
                    st.error(f"Error during search: {str(e)}")
                    status.update(label="❌ Search failed", state="error")
    
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
                    default=sorted(df['search_term'].unique())
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
                    value=(0, rank_intervals[-1])
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
                    default=[]
                )
            else:
                country_filter = None
        
        # Filter by all search terms in header or summary
        with filter_row2_col2:
            search_terms_filter = st.checkbox("Filter for any search term in headline/summary", value=False)
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
                        default=[]
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
                    step=1
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
        filtered_df = df.copy()
        
        # Apply company filter
        if company_filter and 'search_term' in df.columns:
            filtered_df = filtered_df[filtered_df['search_term'].isin(company_filter)]
        
        # Apply source filter - handle string conversion
        if source_filter and 'first_source_name' in df.columns:
            # Convert source names in DataFrame to strings for proper comparison
            filtered_df['source_str'] = filtered_df['first_source_name'].astype(str)
            filtered_df = filtered_df[filtered_df['source_str'].isin(source_filter)]
            filtered_df = filtered_df.drop('source_str', axis=1)
        
        # Apply country filter - handle string conversion
        if country_filter and 'countryname' in df.columns:
            # Convert country names in DataFrame to strings for proper comparison
            # This prevents type mismatch issues when comparing
            filtered_df['countryname_str'] = filtered_df['countryname'].astype(str)
            filtered_df = filtered_df[filtered_df['countryname_str'].isin(country_filter)]
            filtered_df = filtered_df.drop('countryname_str', axis=1)
        
        # Apply site rank filter with intervals
        if rank_min is not None and rank_max is not None and 'site_rank_rank_country' in df.columns:
            filtered_df = filtered_df[
                (filtered_df['site_rank_rank_country'] >= rank_min) & 
                (filtered_df['site_rank_rank_country'] <= rank_max)
            ]
        
        # Apply date filter based on days back from today
        if start_date is not None and end_date is not None and 'local_time_datetime' in filtered_df.columns:
            try:
                # Convert dates to strings for comparison (to avoid timezone issues)
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Create a date-only string column for comparison
                filtered_df['date_str'] = filtered_df['local_time_datetime'].dt.strftime('%Y-%m-%d')
                
                # Filter based on string dates
                filtered_df = filtered_df[
                    (filtered_df['date_str'] >= start_date_str) & 
                    (filtered_df['date_str'] <= end_date_str)
                ]
                
                # Remove temporary column
                filtered_df = filtered_df.drop('date_str', axis=1)
            except Exception as e:
                st.warning(f"Could not filter by date: {str(e)}")
                # Continue without date filtering if it fails
                pass
        
        # Apply search term filter - using a single checkbox for all terms
        if search_terms_filter and 'search_term' in df.columns:
            # Get all active search terms
            active_search_terms = company_filter if company_filter else []
            
            if active_search_terms:
                # Initialize a Series of False values with the same index as filtered_df
                text_match = pd.Series(False, index=filtered_df.index)
                
                # Check for each term
                for term in active_search_terms:
                    term_match = pd.Series(False, index=filtered_df.index)
                    
                    # Check in header_text
                    if 'header_text' in filtered_df.columns:
                        header_match = filtered_df['header_text'].str.contains(term, case=False, na=False)
                        term_match = term_match | header_match
                    
                    # Check in summary_text
                    if 'summary_text' in filtered_df.columns:
                        summary_match = filtered_df['summary_text'].str.contains(term, case=False, na=False)
                        term_match = term_match | summary_match
                    
                    # Combine with overall match (OR logic between terms)
                    text_match = text_match | term_match
                
                # Apply the combined filter
                filtered_df = filtered_df[text_match]
        
        # RESULTS SECTION - MOVED TO TOP
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
            if 'search_term' in filtered_df.columns:
                company_counts = filtered_df['search_term'].value_counts().reset_index()
                company_counts.columns = ['Company', 'Count']
                
                fig = px.bar(
                    company_counts, 
                    x='Company', 
                    y='Count',
                    color='Company',
                    labels={'Count': 'Number of Articles', 'Company': 'Company Name'},
                    title=f"News Distribution ({len(filtered_df)} articles)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Choose columns to display in the data editor
        display_cols = []
        priority_cols = [
            'search_term', 'header_text', 'summary_text', 'first_source_name', 
            'countryname', 'site_rank_rank_country', 'local_time_text'
        ]
        
        # Add columns that exist in the dataframe
        for col in priority_cols:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        # If no columns matched, use all columns
        if not display_cols:
            display_cols = filtered_df.columns.tolist()
        
        # Display data editor
        st.data_editor(
            filtered_df[display_cols],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="news_data_editor"
        )
        
        # Download button
        st.download_button(
            label="📥 Download Results as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name=f"news_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# This allows the file to be imported into your main Streamlit app
if __name__ == "__main__":
    news_search_page()