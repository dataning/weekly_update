import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import sys
import os
import re

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
        hours_back = st.slider(
            "Hours to look back:",
            min_value=1,
            max_value=168,  # One week
            value=24,
            step=1
        )
        
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
        
        # Dashboard stats
        st.header("📊 Search Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", len(df))
        with col2:
            if 'search_term' in df.columns:
                st.metric("Companies", df['search_term'].nunique())
        with col3:
            if 'datetime' in df.columns:
                df_with_dates = df[df['datetime'].notna()]
                if not df_with_dates.empty:
                    earliest = df_with_dates['datetime'].min()
                    st.metric("Earliest", earliest.strftime('%Y-%m-%d %H:%M'))
        with col4:
            if 'datetime' in df.columns:
                df_with_dates = df[df['datetime'].notna()]
                if not df_with_dates.empty:
                    latest = df_with_dates['datetime'].max()
                    st.metric("Latest", latest.strftime('%Y-%m-%d %H:%M'))
        
        # Company distribution chart
        if 'search_term' in df.columns:
            st.subheader("Articles by Company")
            company_counts = df['search_term'].value_counts().reset_index()
            company_counts.columns = ['Company', 'Count']
            
            fig = px.bar(
                company_counts, 
                x='Company', 
                y='Count',
                color='Company',
                labels={'Count': 'Number of Articles', 'Company': 'Company Name'},
                title=f"News Distribution ({len(df)} articles)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Time distribution chart
        if 'datetime' in df.columns:
            st.subheader("Articles by Time")
            df_with_dates = df[df['datetime'].notna()].copy()
            if not df_with_dates.empty:
                # Add hour column
                df_with_dates['hour'] = df_with_dates['datetime'].dt.floor('H')
                hourly_counts = df_with_dates.groupby(['hour', 'search_term']).size().reset_index(name='count')
                
                fig = px.line(
                    hourly_counts, 
                    x='hour', 
                    y='count', 
                    color='search_term',
                    labels={'count': 'Number of Articles', 'hour': 'Time', 'search_term': 'Company'},
                    title="News Activity Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Articles table with filtering
        st.header("📰 Articles")
        
        # Filters
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            if 'search_term' in df.columns:
                company_filter = st.multiselect(
                    "Filter by Company:",
                    options=sorted(df['search_term'].unique()),
                    default=sorted(df['search_term'].unique())
                )
            else:
                company_filter = None
        
        with filter_col2:
            if 'id_site' in df.columns:
                site_filter = st.multiselect(
                    "Filter by Site:",
                    options=sorted(df['id_site'].unique())[:30],  # Limit to top 30 sources
                    default=[]
                )
            else:
                site_filter = None
        
        # Apply filters
        filtered_df = df.copy()
        if company_filter and 'search_term' in df.columns:
            filtered_df = filtered_df[filtered_df['search_term'].isin(company_filter)]
        
        if site_filter and 'id_site' in df.columns:
            filtered_df = filtered_df[filtered_df['id_site'].isin(site_filter)]
        
        # Search in headlines
        search_query = st.text_input("🔍 Search in headlines:", "")
        if search_query and 'header' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['header'].str.contains(search_query, case=False, na=False)]
        
        # Display filtered articles
        st.write(f"Showing {len(filtered_df)} articles")
        
        # Sort by datetime (newest first) if available
        if 'datetime' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('datetime', ascending=False)
        
        # Create display columns
        display_cols = []
        if 'search_term' in filtered_df.columns:
            display_cols.append('search_term')
        if 'header' in filtered_df.columns:
            display_cols.append('header')
        if 'datetime' in filtered_df.columns:
            display_cols.append('datetime')
        if 'id_site' in filtered_df.columns:
            display_cols.append('id_site')
        
        # If no columns matched, use all columns
        if not display_cols:
            display_cols = filtered_df.columns.tolist()
        
        # Display articles
        for i, row in filtered_df.reset_index().iterrows():
            with st.expander(f"{i+1}. {row.get('header', f'Article {i+1}')}"):
                # Source and date info
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.caption(f"**Company:** {row.get('search_term', 'Unknown')}")
                with meta_col2:
                    if 'datetime' in row and pd.notna(row['datetime']):
                        st.caption(f"**Date:** {row['datetime'].strftime('%Y-%m-%d %H:%M')}")
                with meta_col3:
                    if 'id_site' in row:
                        st.caption(f"**Source:** {row.get('id_site', 'Unknown')}")
                
                # Summary
                if 'summary' in row and pd.notna(row['summary']):
                    st.markdown("**Summary:**")
                    st.info(clean_text(row['summary']))
                
                # Full text
                if 'text' in row and pd.notna(row['text']):
                    st.markdown("**Full Text:**")
                    st.markdown(clean_text(row['text']))
                
                # URL if available
                if 'url' in row and pd.notna(row['url']):
                    st.markdown(f"[Read Original Article]({row['url']})")
        
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