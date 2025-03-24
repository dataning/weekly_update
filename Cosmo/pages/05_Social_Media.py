import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
import os
import json
import inspect
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

# Make sure access_control.py is in the same directory as this file
from services.access_control import (
    initialize_session_state, login_ui, admin_settings_ui,
    load_config, save_config
)

# Import from services.vsocial - adjust the import path based on your project structure
from services.vsocial import (
    SocialMediaPost, ArticleReference, fetch_data_from_api, fetch_article_posts,
    convert_to_dataclass, create_dataframe, process_article_posts,
    analyze_data, analyze_article_posts, main as vsocial_main
)

# IMPROVED ARTICLE PROCESSING FUNCTION - Add this to your vsocial.py file
def improved_process_article_posts(data):
    """
    Process article posts data to extract both posts and article metadata
    
    Args:
        data: The raw data from fetch_article_posts API
        
    Returns:
        tuple: (list of SocialMediaPost objects, dict of ArticleReference objects)
    """
    posts = []
    article_metadata = {}
    
    # Debug the response
    print(f"Processing {len(data) if isinstance(data, list) else 'non-list'} article data items")
    
    # If data is not a list, handle it
    if not isinstance(data, list):
        if isinstance(data, dict) and 'posts' in data:
            data = data['posts']
            print(f"Extracted 'posts' array with {len(data)} items")
        else:
            print(f"Unable to process data of type {type(data)}")
            return [], {}
    
    # Process each item
    for item in data:
        try:
            # If the item is a string, try to parse it as JSON
            if isinstance(item, str):
                try:
                    import json
                    item = json.loads(item)
                except json.JSONDecodeError:
                    print(f"Could not parse item as JSON")
                    continue
            
            # Get all valid fields for SocialMediaPost
            valid_fields = set(inspect.signature(SocialMediaPost.__init__).parameters.keys()) - {'self'}
            
            # Filter the item to include only valid fields
            filtered_item = {k: v for k, v in item.items() if k in valid_fields}
            
            # Create a social media post object with only the valid fields
            post = SocialMediaPost(**filtered_item)
            posts.append(post)
            
            # Extract and store article metadata if we have both article_id and article_url
            if post.article_id and post.article_url:
                article_metadata[post.article_id] = ArticleReference(
                    article_id=post.article_id,
                    article_url=post.article_url,
                    url_headline_text=post.url_headline_text,
                    url_description=post.url_description,
                    url_preview_img_url=post.url_preview_img_url
                )
        except Exception as e:
            print(f"Error processing article post item: {e}")
            if isinstance(item, dict):
                print(f"Problem item keys: {sorted(item.keys())}")
    
    print(f"Successfully processed {len(posts)} posts and extracted {len(article_metadata)} article metadata items")
    return posts, article_metadata

# Set page config
st.set_page_config(
    page_title="BlackRock Social Media Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize the session state for authentication
initialize_session_state()

# Render header
render_header()

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        color: #888;
    }
    .dashboard-title {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 20px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .tab-subheader {
        font-size: 18px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 15px;
        color: #1E88E5;
    }
    .article-card {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .article-title {
        font-size: 16px;
        font-weight: bold;
    }
    .article-meta {
        font-size: 12px;
        color: #888;
        margin-top: 5px;
    }
    .article-stats {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }
    .data-table-container {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .data-table-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
    }
    .filter-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .comparison-card {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Check for authentication before showing the dashboard
if not login_ui():
    # If not authenticated, stop execution here
    st.stop()

# Title
st.markdown('<div class="dashboard-title">BlackRock Social Media Analysis Dashboard</div>', unsafe_allow_html=True)
st.markdown('Comprehensive analysis of social media posts and articles mentioning BlackRock from the Vinesight API')

# Add admin settings to the sidebar
with st.sidebar:
    st.header("Administration")
    admin_settings_ui()
    
    # Add proxy toggle
    use_proxy = st.checkbox(
        "BLK N@twork", 
        value=True,
        help="Use BLK N@twork for API connections"
    )
    
    # if use_proxy:
    #     st.info("Using proxy: http://webproxy.blackrock.com:8080")

# Function to load and process data using vsocial.py functionality
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(use_proxy=False):
    with st.spinner("Fetching social media and article data..."):
        try:
            # Create a placeholder for debug info
            debug_info = []
            debug_info.append("Starting data load process...")
            debug_info.append(f"Using proxy: {use_proxy}")
            
            # Use the main function from vsocial.py which now returns multiple dataframes
            debug_info.append("Calling vsocial_main(fetch_articles=True)...")
            try:
                result = vsocial_main(fetch_articles=True, use_proxy=use_proxy)
                debug_info.append(f"vsocial_main returned: {type(result)}")
            except Exception as e:
                debug_info.append(f"Error calling vsocial_main: {e}")
                import traceback
                debug_info.append(traceback.format_exc())
                result = None
            
            # Initialize our return values
            social_df = pd.DataFrame()
            article_posts_df = pd.DataFrame()
            article_metadata = {}
            
            # Check if result is a tuple with multiple items (social posts, article posts, and article metadata)
            if isinstance(result, tuple):
                debug_info.append(f"Result is a tuple with {len(result)} items")
                if len(result) == 3:
                    # Unpack the tuple of 3 items
                    social_df, article_posts_df, article_metadata = result
                    debug_info.append(f"Unpacked tuple: social_df: {type(social_df)}, rows: {len(social_df) if isinstance(social_df, pd.DataFrame) else 'not a DataFrame'}")
                    debug_info.append(f"Unpacked tuple: article_posts_df: {type(article_posts_df)}, rows: {len(article_posts_df) if isinstance(article_posts_df, pd.DataFrame) else 'not a DataFrame'}")
                    debug_info.append(f"Unpacked tuple: article_metadata: {type(article_metadata)}, items: {len(article_metadata) if isinstance(article_metadata, dict) else 'not a dict'}")
                elif len(result) == 2:
                    # Handle case where only two items are returned
                    social_df, article_posts_df = result
                    debug_info.append(f"Unpacked tuple (2 items): social_df: {type(social_df)}, article_posts_df: {type(article_posts_df)}")
            elif result is not None:
                # If only a single DataFrame is returned
                social_df = result
                debug_info.append(f"Single result: {type(social_df)}")
            
            # If social_df is None or empty, try direct fetch
            if social_df is None or (isinstance(social_df, pd.DataFrame) and social_df.empty):
                debug_info.append("social_df is None or empty, trying direct fetch")
                try:
                    # Try to fetch social media posts directly
                    raw_data = fetch_data_from_api(use_proxy=use_proxy)
                    debug_info.append(f"Direct fetch returned {len(raw_data) if isinstance(raw_data, list) else 'non-list'} items")
                    posts = convert_to_dataclass(raw_data)
                    debug_info.append(f"Converted to {len(posts)} dataclass instances")
                    social_df = create_dataframe(posts)
                    debug_info.append(f"Created DataFrame with {len(social_df)} rows")
                except Exception as fetch_error:
                    debug_info.append(f"Failed to fetch social media data: {fetch_error}")
                    st.warning(f"Failed to fetch social media data: {fetch_error}")
                    social_df = pd.DataFrame()  # Ensure we have at least an empty DataFrame
            
            # If article_posts_df is None or empty, try direct fetch
            if article_posts_df is None or (isinstance(article_posts_df, pd.DataFrame) and article_posts_df.empty):
                debug_info.append("article_posts_df is None or empty, trying direct fetch")
                try:
                    # Try to fetch article posts directly with proxy setting
                    debug_info.append(f"Calling fetch_article_posts() with use_proxy={use_proxy}")
                    article_data = fetch_article_posts(use_proxy=use_proxy)
                    debug_info.append(f"Direct article fetch returned {len(article_data) if isinstance(article_data, list) else 'non-list'} items")
                    
                    if isinstance(article_data, list) and article_data:
                        debug_info.append(f"First article item type: {type(article_data[0])}")
                        # Make sure we're passing proper dictionary objects, not strings
                        if isinstance(article_data[0], str):
                            debug_info.append("Converting string data to JSON")
                            import json
                            article_data = [json.loads(item) if isinstance(item, str) else item for item in article_data]
                    
                    # Use the improved processing function to handle missing fields
                    article_posts, article_metadata = improved_process_article_posts(article_data)
                    debug_info.append(f"Processed {len(article_posts)} article posts and {len(article_metadata)} metadata items")
                    article_posts_df = create_dataframe(article_posts)
                    debug_info.append(f"Created article DataFrame with {len(article_posts_df)} rows")
                except Exception as fetch_error:
                    debug_info.append(f"Failed to fetch article data: {fetch_error}")
                    import traceback
                    debug_info.append(traceback.format_exc())
                    st.warning(f"Failed to fetch article data: {fetch_error}")
                    article_posts_df = pd.DataFrame()  # Ensure we have at least an empty DataFrame
            
            # Add a column for BlackRock mentions if it doesn't exist in social_df
            if isinstance(social_df, pd.DataFrame) and not social_df.empty and 'mentions_blackrock' not in social_df.columns:
                social_df['mentions_blackrock'] = social_df['post_text'].str.lower().str.contains('blackrock')
                debug_info.append("Added mentions_blackrock column to social_df")
            
            # Add a column for BlackRock mentions if it doesn't exist in article_posts_df
            if isinstance(article_posts_df, pd.DataFrame) and not article_posts_df.empty and 'mentions_blackrock' not in article_posts_df.columns:
                article_posts_df['mentions_blackrock'] = article_posts_df['post_text'].str.lower().str.contains('blackrock')
                debug_info.append("Added mentions_blackrock column to article_posts_df")
            
            # Store debug info in session state for display later
            st.session_state['debug_info'] = debug_info
            
            return social_df, article_posts_df, article_metadata
        except Exception as e:
            st.error(f"Error loading data: {e}")
            import traceback
            st.session_state['debug_info'] = [f"Exception in load_data: {e}", traceback.format_exc()]
            # Return empty DataFrames - can be handled downstream
            return pd.DataFrame(), pd.DataFrame(), {}

# Load data
social_df, article_posts_df, article_metadata = load_data(use_proxy=use_proxy)

# Rest of your dashboard code remains the same...
# Check if both DataFrames are empty or None
if (social_df is None or (isinstance(social_df, pd.DataFrame) and social_df.empty)) and \
   (article_posts_df is None or (isinstance(article_posts_df, pd.DataFrame) and article_posts_df.empty)):
    st.error("No data available. Please check your API credentials or network connection.")
    
    # Add retry button with proxy toggle
    st.warning("You can try using the corporate proxy if you're behind a firewall")
    if st.button("🔄 Retry with " + ("Proxy Disabled" if use_proxy else "Proxy Enabled")):
        # Toggle proxy setting for retry
        new_proxy_setting = not use_proxy
        # Reset cache and reload with new proxy setting
        load_data.clear()
        social_df, article_posts_df, article_metadata = load_data(use_proxy=new_proxy_setting)
        # Update sidebar checkbox state
        st.session_state['use_proxy'] = new_proxy_setting
        # Rerun to refresh the page
        st.experimental_rerun()
    
    st.stop()

# Ensure we have valid DataFrames
if social_df is None or not isinstance(social_df, pd.DataFrame):
    social_df = pd.DataFrame()
    
if article_posts_df is None or not isinstance(article_posts_df, pd.DataFrame):
    article_posts_df = pd.DataFrame()

# Filter for BlackRock mentions in social posts
if isinstance(social_df, pd.DataFrame) and not social_df.empty and 'mentions_blackrock' in social_df.columns:
    blackrock_social_df = social_df[social_df['mentions_blackrock']]
else:
    blackrock_social_df = pd.DataFrame()

# Filter for BlackRock mentions in article posts
if isinstance(article_posts_df, pd.DataFrame) and not article_posts_df.empty and 'mentions_blackrock' in article_posts_df.columns:
    blackrock_article_df = article_posts_df[article_posts_df['mentions_blackrock']]
else:
    blackrock_article_df = pd.DataFrame()

# Calculate metrics safely
total_social_posts = len(social_df) if isinstance(social_df, pd.DataFrame) else 0
total_article_posts = len(article_posts_df) if isinstance(article_posts_df, pd.DataFrame) else 0
total_posts = total_social_posts + total_article_posts

blackrock_social_mentions = len(blackrock_social_df) if isinstance(blackrock_social_df, pd.DataFrame) else 0
blackrock_article_mentions = len(blackrock_article_df) if isinstance(blackrock_article_df, pd.DataFrame) else 0
blackrock_mentions = blackrock_social_mentions + blackrock_article_mentions

# Safely calculate averages and sums
avg_interactions = 0
avg_bot_percentage = 0
total_human_reach = 0

if isinstance(social_df, pd.DataFrame) and not social_df.empty:
    if 'interactions_count' in social_df.columns:
        avg_interactions = int(social_df['interactions_count'].mean()) if not social_df['interactions_count'].isna().all() else 0
        
    if 'percent_bots_retweets' in social_df.columns:
        avg_bot_percentage = int(social_df['percent_bots_retweets'].mean()) if not social_df['percent_bots_retweets'].isna().all() else 0
        
    if 'human_reach' in social_df.columns:
        total_human_reach = int(social_df['human_reach'].sum()) if not social_df['human_reach'].isna().all() else 0

# Extract unique articles from article_metadata
unique_articles = len(article_metadata) if isinstance(article_metadata, dict) else 0

# Display metrics in a row layout
st.subheader("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{total_posts}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Posts</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{blackrock_mentions}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">BlackRock Mentions</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{unique_articles}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Unique Articles</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{avg_interactions:,}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Avg. Interactions</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{avg_bot_percentage}%</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Avg. Bot Percentage</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Add a refresh data button with current proxy setting
refresh_col1, refresh_col2 = st.columns([3, 1])

with refresh_col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        # Clear the cache and reload data
        load_data.clear()
        st.experimental_rerun()

# Add connection info
with refresh_col1:
    st.info(f"API Connection: {'Using corporate proxy' if use_proxy else 'Direct connection'} | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Tabs for different visualizations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Engagement Analysis", "Bot & Demographics", "Top Posts", "Article Analysis", "Raw Data Explorer"])

# Tab 1: Engagement Analysis
with tab1:
    st.markdown('<div class="section-title">Engagement Analysis</div>', unsafe_allow_html=True)
    
    # Add filters for engagement analysis
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="data-table-title">Filter Options</div>', unsafe_allow_html=True)
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            # Filter by platform
            if not social_df.empty and 'platform' in social_df.columns:
                platform_options = ['All'] + sorted(social_df['platform'].unique().tolist())
                selected_platform = st.selectbox('Platform', platform_options)
            else:
                selected_platform = 'All'
        
        with filter_col2:
            # Filter by minimum interactions
            min_interactions = st.slider('Minimum Interactions', 0, int(social_df['interactions_count'].max()) if not social_df.empty and 'interactions_count' in social_df.columns else 100, 0)
        
        with filter_col3:
            # Filter by date range if date column exists
            if not social_df.empty and 'post_date' in social_df.columns:
                social_df['post_date_dt'] = pd.to_datetime(social_df['post_date'], errors='coerce')
                min_date = social_df['post_date_dt'].min().date()
                max_date = social_df['post_date_dt'].max().date()
                selected_date_range = st.date_input('Date Range', [min_date, max_date])
            else:
                selected_date_range = None
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_social_df = social_df.copy()
    
    if selected_platform != 'All':
        filtered_social_df = filtered_social_df[filtered_social_df['platform'] == selected_platform]
    
    if min_interactions > 0 and 'interactions_count' in filtered_social_df.columns:
        filtered_social_df = filtered_social_df[filtered_social_df['interactions_count'] >= min_interactions]
    
    if selected_date_range and len(selected_date_range) == 2 and 'post_date_dt' in filtered_social_df.columns:
        filtered_social_df = filtered_social_df[(filtered_social_df['post_date_dt'].dt.date >= selected_date_range[0]) & 
                                                (filtered_social_df['post_date_dt'].dt.date <= selected_date_range[1])]
    
    # Filter BlackRock mentions based on the same filters
    filtered_blackrock_df = filtered_social_df[filtered_social_df['mentions_blackrock']] if 'mentions_blackrock' in filtered_social_df.columns else pd.DataFrame()
    
    # Display metrics after filtering
    filtered_total = len(filtered_social_df)
    filtered_blackrock = len(filtered_blackrock_df)
    
    st.markdown(f"**Filtered Results:** {filtered_total} posts ({filtered_blackrock} mentioning BlackRock)")
    
    if not filtered_social_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Engagement Chart for BlackRock Posts
            if not filtered_blackrock_df.empty:
                engagement_data = filtered_blackrock_df.sort_values('interactions_count', ascending=False).head(10)
                
                # Prepare data for stacked bar chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=engagement_data['poster_name'],
                    y=engagement_data['likes_count'],
                    name='Likes',
                    marker_color='#4CAF50'
                ))
                fig.add_trace(go.Bar(
                    x=engagement_data['poster_name'],
                    y=engagement_data['shares_count'],
                    name='Shares',
                    marker_color='#2196F3'
                ))
                fig.add_trace(go.Bar(
                    x=engagement_data['poster_name'],
                    y=engagement_data['comments_count'],
                    name='Comments',
                    marker_color='#FF9800'
                ))
                
                fig.update_layout(
                    title='Engagement on Top BlackRock Posts',
                    xaxis_title='Account Name',
                    yaxis_title='Count',
                    barmode='stack',
                    height=400,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No BlackRock mentions found in social media posts.")
        
        with col2:
            # Platform Distribution
            platform_counts = filtered_social_df['platform'].value_counts().reset_index()
            platform_counts.columns = ['Platform', 'Count']
            
            fig = px.pie(
                platform_counts, 
                values='Count', 
                names='Platform',
                title='Platform Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Engagement Metrics Over Time
        st.markdown('<div class="section-title">Engagement Metrics Over Time</div>', unsafe_allow_html=True)
        
        if 'post_date_dt' in filtered_social_df.columns:
            # Group by date and calculate engagement metrics
            time_metrics = filtered_social_df.groupby(filtered_social_df['post_date_dt'].dt.date).agg({
                'interactions_count': 'mean',
                'likes_count': 'mean',
                'shares_count': 'mean',
                'comments_count': 'mean'
            }).reset_index()
            
            # Create a line chart for engagement metrics over time
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=time_metrics['post_date_dt'],
                y=time_metrics['interactions_count'],
                mode='lines+markers',
                name='Interactions',
                line=dict(color='#E91E63', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=time_metrics['post_date_dt'],
                y=time_metrics['likes_count'],
                mode='lines+markers',
                name='Likes',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=time_metrics['post_date_dt'],
                y=time_metrics['shares_count'],
                mode='lines+markers',
                name='Shares',
                line=dict(color='#2196F3', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=time_metrics['post_date_dt'],
                y=time_metrics['comments_count'],
                mode='lines+markers',
                name='Comments',
                line=dict(color='#FF9800', width=2)
            ))
            
            fig.update_layout(
                title='Engagement Metrics Over Time',
                xaxis_title='Date',
                yaxis_title='Average Count',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Interaction Comparison: BlackRock vs Non-BlackRock
        st.markdown('<div class="section-title">BlackRock vs Non-BlackRock Engagement Comparison</div>', unsafe_allow_html=True)
        
        if not filtered_social_df.empty and 'mentions_blackrock' in filtered_social_df.columns:
            # Prepare data for comparison
            blackrock_group = filtered_social_df[filtered_social_df['mentions_blackrock']].copy()
            non_blackrock_group = filtered_social_df[~filtered_social_df['mentions_blackrock']].copy()
            
            # Calculate metrics for both groups
            comparison_metrics = []
            
            # For BlackRock mentions
            if not blackrock_group.empty:
                blackrock_metrics = {
                    'Group': 'BlackRock Mentions',
                    'Avg Interactions': int(blackrock_group['interactions_count'].mean()) if 'interactions_count' in blackrock_group.columns else 0,
                    'Avg Likes': int(blackrock_group['likes_count'].mean()) if 'likes_count' in blackrock_group.columns else 0,
                    'Avg Shares': int(blackrock_group['shares_count'].mean()) if 'shares_count' in blackrock_group.columns else 0,
                    'Avg Comments': int(blackrock_group['comments_count'].mean()) if 'comments_count' in blackrock_group.columns else 0,
                    'Total Posts': len(blackrock_group)
                }
                comparison_metrics.append(blackrock_metrics)
            
            # For non-BlackRock mentions
            if not non_blackrock_group.empty:
                non_blackrock_metrics = {
                    'Group': 'Other Posts',
                    'Avg Interactions': int(non_blackrock_group['interactions_count'].mean()) if 'interactions_count' in non_blackrock_group.columns else 0,
                    'Avg Likes': int(non_blackrock_group['likes_count'].mean()) if 'likes_count' in non_blackrock_group.columns else 0,
                    'Avg Shares': int(non_blackrock_group['shares_count'].mean()) if 'shares_count' in non_blackrock_group.columns else 0,
                    'Avg Comments': int(non_blackrock_group['comments_count'].mean()) if 'comments_count' in non_blackrock_group.columns else 0,
                    'Total Posts': len(non_blackrock_group)
                }
                comparison_metrics.append(non_blackrock_metrics)
            
            # Display comparison table
            comparison_df = pd.DataFrame(comparison_metrics)
            
            # Create comparison bar chart
            if len(comparison_metrics) > 0:
                fig = go.Figure()
                
                # Add traces for each metric
                metrics = ['Avg Interactions', 'Avg Likes', 'Avg Shares', 'Avg Comments']
                colors = ['#E91E63', '#4CAF50', '#2196F3', '#FF9800']
                
                for i, metric in enumerate(metrics):
                    fig.add_trace(go.Bar(
                        x=[group['Group'] for group in comparison_metrics],
                        y=[group[metric] for group in comparison_metrics],
                        name=metric,
                        marker_color=colors[i]
                    ))
                
                fig.update_layout(
                    title='Engagement Comparison: BlackRock vs Other Posts',
                    xaxis_title='Post Group',
                    yaxis_title='Average Count',
                    barmode='group',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show the comparison table
                st.markdown('<div class="data-table-container">', unsafe_allow_html=True)
                st.markdown('<div class="data-table-title">Engagement Metrics Comparison</div>', unsafe_allow_html=True)
                st.table(comparison_df.set_index('Group'))
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Viral States Analysis
        st.markdown('<div class="section-title">Viral States Analysis</div>', unsafe_allow_html=True)
        
        # Extract viral states data
        viral_states = {}
        for idx, row in filtered_social_df.iterrows():
            if isinstance(row.get('retweeter_viral_states'), dict):
                for state, value in row['retweeter_viral_states'].items():
                    if state in viral_states:
                        viral_states[state] += value
                    else:
                        viral_states[state] = value
        
        if viral_states:
            viral_states_df = pd.DataFrame([
                {'State': state, 'Virality': value} 
                for state, value in viral_states.items()
            ]).sort_values('Virality', ascending=False)
            
            # Create a US choropleth map
            if len(viral_states_df) > 0:
                fig = px.choropleth(
                    viral_states_df,
                    locations='State',
                    locationmode='USA-states',
                    color='Virality',
                    scope='usa',
                    title='Viral Content Distribution by US State',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    geo=dict(
                        showcoastlines=True,
                        projection_type='albers usa'
                    ),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Show top viral states as a bar chart
            top_viral_states = viral_states_df.head(10)
            
            fig = px.bar(
                top_viral_states,
                x='State',
                y='Virality',
                title='Top States with Viral Retweets',
                color='Virality',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display viral states data table
            st.markdown('<div class="data-table-container">', unsafe_allow_html=True)
            st.markdown('<div class="data-table-title">Viral States Data</div>', unsafe_allow_html=True)
            st.dataframe(viral_states_df.sort_values('Virality', ascending=False), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No viral states data available.")
            
        # Add a data table for the filtered results
        with st.expander("View Engagement Data Table"):
            st.markdown('<div class="data-table-title">Filtered Social Media Posts</div>', unsafe_allow_html=True)
            
            # Select relevant columns for engagement analysis
            engagement_columns = [
                'poster_name', 'platform', 'post_date', 'interactions_count', 
                'likes_count', 'shares_count', 'comments_count', 'views_count',
                'mentions_blackrock'
            ]
            
            # Filter columns that exist in the DataFrame
            available_columns = [col for col in engagement_columns if col in filtered_social_df.columns]
            
            st.dataframe(filtered_social_df[available_columns], use_container_width=True)
    else:
        st.warning("No social media data available to analyze engagement.")

# Tab 2: Bot & Demographics Analysis
with tab2:
    st.markdown('<div class="section-title">Bot Analysis and Demographics</div>', unsafe_allow_html=True)
    
    # Add filters for bot analysis
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="data-table-title">Filter Options</div>', unsafe_allow_html=True)
        
        bot_filter_col1, bot_filter_col2 = st.columns(2)
        
        with bot_filter_col1:
            # Filter by bot percentage
            max_bot_percentage = int(social_df['percent_bots_retweets'].max()) if not social_df.empty and 'percent_bots_retweets' in social_df.columns else 100
            bot_threshold = st.slider('Minimum Bot Percentage', 0, max_bot_percentage, 0)
        
        with bot_filter_col2:
            # Filter by platform
            if not social_df.empty and 'platform' in social_df.columns:
                bot_platform_options = ['All'] + sorted(social_df['platform'].unique().tolist())
                bot_selected_platform = st.selectbox('Platform for Bot Analysis', bot_platform_options, key='bot_platform')
            else:
                bot_selected_platform = 'All'
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    bot_filtered_df = social_df.copy()
    
    if bot_selected_platform != 'All':
        bot_filtered_df = bot_filtered_df[bot_filtered_df['platform'] == bot_selected_platform]
    
    if bot_threshold > 0 and 'percent_bots_retweets' in bot_filtered_df.columns:
        bot_filtered_df = bot_filtered_df[bot_filtered_df['percent_bots_retweets'] >= bot_threshold]
    
    # Filter for BlackRock mentions
    bot_blackrock_df = bot_filtered_df[bot_filtered_df['mentions_blackrock']] if 'mentions_blackrock' in bot_filtered_df.columns else pd.DataFrame()
    
    if not bot_filtered_df.empty:
        st.markdown(f"**Filtered Results:** {len(bot_filtered_df)} posts ({len(bot_blackrock_df)} mentioning BlackRock)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bot vs Human Chart
            if not bot_blackrock_df.empty and 'percent_bots_retweets' in bot_blackrock_df.columns:
                bot_data = bot_blackrock_df.dropna(subset=['percent_bots_retweets']).sort_values('percent_bots_retweets', ascending=False).head(10)
                
                if not bot_data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=bot_data['poster_name'],
                        x=bot_data['percent_bots_retweets'],
                        name='Bot %',
                        orientation='h',
                        marker_color='#FF5722'
                    ))
                    fig.add_trace(go.Bar(
                        y=bot_data['poster_name'],
                        x=100 - bot_data['percent_bots_retweets'],
                        name='Human %',
                        orientation='h',
                        marker_color='#2196F3'
                    ))
                    
                    fig.update_layout(
                        title='Bot vs Human Retweets for BlackRock Mentions',
                        xaxis_title='Percentage',
                        yaxis_title='Account Name',
                        barmode='stack',
                        height=500,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No bot percentage data available.")
            else:
                st.info("No BlackRock mentions found to analyze bot activity.")
        
        with col2:
            # Gender Distribution Chart (if available)
            gender_data = bot_filtered_df[bot_filtered_df['percent_males'].notna()]
            
            if not gender_data.empty:
                # Group by platform for comparison
                gender_by_platform = gender_data.groupby('platform')['percent_males'].mean().reset_index()
                
                fig = px.bar(
                    gender_by_platform,
                    x='platform',
                    y='percent_males',
                    title='Gender Distribution by Platform',
                    color='percent_males',
                    color_continuous_scale='RdBu_r',
                    labels={'percent_males': 'Male %', 'platform': 'Platform'}
                )
                
                # Add a horizontal line at 50% for reference
                fig.add_shape(
                    type='line',
                    x0=-0.5,
                    y0=50,
                    x1=len(gender_by_platform)-0.5,
                    y1=50,
                    line=dict(color='black', width=2, dash='dash')
                )
                
                fig.update_layout(height=500)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a gender distribution treemap
                gender_treemap_data = gender_data.copy()
                gender_treemap_data['female_percent'] = 100 - gender_treemap_data['percent_males']
                
                # Prepare data for treemap
                treemap_data = []
                for platform in gender_treemap_data['platform'].unique():
                    platform_data = gender_treemap_data[gender_treemap_data['platform'] == platform]
                    avg_male = platform_data['percent_males'].mean()
                    avg_female = platform_data['female_percent'].mean()
                    
                    treemap_data.append({
                        'platform': platform,
                        'gender': 'Male',
                        'value': avg_male
                    })
                    treemap_data.append({
                        'platform': platform,
                        'gender': 'Female',
                        'value': avg_female
                    })
                
                treemap_df = pd.DataFrame(treemap_data)
                
                fig = px.treemap(
                    treemap_df,
                    path=['platform', 'gender'],
                    values='value',
                    color='gender',
                    color_discrete_map={'Male': '#2196F3', 'Female': '#E91E63'},
                    title='Gender Distribution Across Platforms'
                )
                
                fig.update_layout(height=500)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No gender data available.")
        
        # Bot Amplification Analysis
        st.markdown('<div class="section-title">Bot Amplification Analysis</div>', unsafe_allow_html=True)
        
        # Create a dataframe with bot percentage and amplification factor
        bot_amp_df = bot_filtered_df[['poster_name', 'percent_bots_retweets', 'amplification_multiplier', 'platform', 'mentions_blackrock']].dropna()
        
        if not bot_amp_df.empty:
            # Create scatter plot with platform coloring
            fig = px.scatter(
                bot_amp_df,
                x='percent_bots_retweets',
                y='amplification_multiplier',
                color='platform',
                symbol='mentions_blackrock',
                hover_name='poster_name',
                title='Bot Percentage vs Amplification Factor',
                labels={
                    'percent_bots_retweets': 'Bot Percentage (%)',
                    'amplification_multiplier': 'Amplification Multiplier',
                    'platform': 'Platform',
                    'mentions_blackrock': 'Mentions BlackRock'
                },
                height=600
            )
            
            # Add a trendline
            from scipy import stats
            
            # Calculate trend line
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                bot_amp_df['percent_bots_retweets'], 
                bot_amp_df['amplification_multiplier']
            )
            
            x_range = np.linspace(bot_amp_df['percent_bots_retweets'].min(), bot_amp_df['percent_bots_retweets'].max(), 100)
            y_range = slope * x_range + intercept
            
            fig.add_trace(
                go.Scatter(
                    x=x_range, 
                    y=y_range, 
                    mode='lines', 
                    name=f'Trend (r={r_value:.2f})',
                    line=dict(color='black', width=2, dash='dash')
                )
            )
            
            fig.update_layout(
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add correlation analysis
            correlation = bot_amp_df['percent_bots_retweets'].corr(bot_amp_df['amplification_multiplier'])
            
            st.markdown(f"""
            <div class="comparison-card">
                <div class="article-title">Correlation Analysis</div>
                <p>The correlation between bot percentage and amplification factor is <b>{correlation:.2f}</b>.</p>
                <p>
                    {'This suggests a <b>strong positive relationship</b> between bot activity and amplification.' if correlation > 0.7 else
                    'This suggests a <b>moderate positive relationship</b> between bot activity and amplification.' if correlation > 0.4 else
                    'This suggests a <b>weak positive relationship</b> between bot activity and amplification.' if correlation > 0 else
                    'This suggests a <b>negative relationship</b> between bot activity and amplification.'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show a histogram of bot percentages
            fig = px.histogram(
                bot_amp_df,
                x='percent_bots_retweets',
                color='platform',
                nbins=20,
                opacity=0.7,
                title='Distribution of Bot Percentages',
                labels={'percent_bots_retweets': 'Bot Percentage (%)'}
            )
            
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display the bot amplification data table
            with st.expander("View Bot Amplification Data"):
                st.markdown('<div class="data-table-title">Bot Amplification Data</div>', unsafe_allow_html=True)
                st.dataframe(bot_amp_df.sort_values('amplification_multiplier', ascending=False), use_container_width=True)
        else:
            st.info("Insufficient data for bot amplification analysis.")
        
        # Display verified vs bot accounts analysis
        st.markdown('<div class="section-title">Verified vs Bot Accounts</div>', unsafe_allow_html=True)
        
        # Create a dataframe with verification and bot status
        if 'tweeter_is_verified' in bot_filtered_df.columns and 'tweeter_is_bot' in bot_filtered_df.columns:
            status_df = bot_filtered_df[['poster_name', 'tweeter_is_verified', 'tweeter_is_bot', 'platform', 'mentions_blackrock']].dropna()
            
            if not status_df.empty:
                # Create a contingency table
                verified_bot_counts = pd.crosstab(
                    status_df['tweeter_is_verified'], 
                    status_df['tweeter_is_bot'],
                    rownames=['Verified'],
                    colnames=['Bot']
                )
                
                # Create a heatmap
                # Using .tolist() to ensure proper handling of index/columns
                fig = px.imshow(
                    verified_bot_counts,
                    text_auto=True,
                    labels=dict(x='Bot Status', y='Verified Status', color='Count'),
                    x=verified_bot_counts.columns.tolist(),
                    y=verified_bot_counts.index.tolist(),
                    color_continuous_scale='Viridis',
                    title='Verified vs Bot Account Distribution'
                )
                
                fig.update_layout(height=400)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create the crosstab
                platform_status = pd.crosstab(
                    [status_df['platform'], status_df['tweeter_is_verified']],
                    status_df['tweeter_is_bot'],
                    rownames=['Platform', 'Verified'],
                    colnames=['Bot']
                )

                # Reset the index to prepare for melting
                platform_status_reset = platform_status.reset_index()

                # Find the boolean columns (they might be stored as 0/1 or as strings)
                bot_columns = [col for col in platform_status_reset.columns 
                            if col not in ['Platform', 'Verified']]

                # Now melt with the correct column names
                platform_status_melted = pd.melt(
                    platform_status_reset, 
                    id_vars=['Platform', 'Verified'],
                    value_vars=bot_columns,
                    var_name='Bot',
                    value_name='Count'
                )

                # Create a proper status label for display
                platform_status_melted['Status'] = platform_status_melted.apply(
                    lambda x: f"{'Verified' if x['Verified'] else 'Not Verified'}, {'Bot' if x['Bot'] else 'Not Bot'}", 
                    axis=1
                )

                # Now you can create your visualization
                fig = px.bar(
                    platform_status_melted,
                    x='Platform',
                    y='Count',
                    color='Status',
                    title='Account Types by Platform',
                    barmode='stack'
                )
                
                fig.update_layout(height=500)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No account verification and bot status data available.")
        else:
            st.info("Account verification or bot status data not available.")
    else:
        st.warning("No social media data available to analyze bots and demographics.")

# Tab 3: Top Posts
with tab3:
    st.markdown('<div class="section-title">Top BlackRock Posts</div>', unsafe_allow_html=True)
    
    # Filters for top posts
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="data-table-title">Filter Options</div>', unsafe_allow_html=True)
        
        post_filter_col1, post_filter_col2, post_filter_col3 = st.columns(3)
        
        with post_filter_col1:
            # Sort by options
            sort_options = [
                'interactions_count', 'likes_count', 'shares_count', 
                'comments_count', 'views_count', 'percent_bots_retweets'
            ]
            # Filter sort options that exist in the DataFrame
            valid_sort_options = [col for col in sort_options if col in blackrock_social_df.columns]
            
            if valid_sort_options:
                sort_by = st.selectbox(
                    'Sort By', 
                    valid_sort_options,
                    index=0,
                    format_func=lambda x: {
                        'interactions_count': 'Total Interactions',
                        'likes_count': 'Likes',
                        'shares_count': 'Shares',
                        'comments_count': 'Comments',
                        'views_count': 'Views',
                        'percent_bots_retweets': 'Bot Percentage'
                    }.get(x, x)
                )
            else:
                sort_by = 'interactions_count'
        
        with post_filter_col2:
            # Platform filter
            if not blackrock_social_df.empty and 'platform' in blackrock_social_df.columns:
                post_platform_options = ['All'] + sorted(blackrock_social_df['platform'].unique().tolist())
                post_selected_platform = st.selectbox('Platform', post_platform_options, key='post_platform')
            else:
                post_selected_platform = 'All'
        
        with post_filter_col3:
            # Number of posts to display
            num_posts = st.slider('Number of Posts', 5, 20, 5)
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters to top posts
    top_posts_df = blackrock_social_df.copy()
    
    if post_selected_platform != 'All':
        top_posts_df = top_posts_df[top_posts_df['platform'] == post_selected_platform]
    
    # Make sure the sort column exists
    if sort_by not in top_posts_df.columns:
        sort_by = 'interactions_count' if 'interactions_count' in top_posts_df.columns else top_posts_df.columns[0]
    
    if not top_posts_df.empty:
        # Top Posts Table
        top_posts = top_posts_df.sort_values(sort_by, ascending=False).head(num_posts)
        
        # Create a more visually appealing table
        for i, row in top_posts.iterrows():
            html_content = f"""
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <div>
                        <span style="font-weight: bold; font-size: 16px;">{row['poster_name']}</span>
                        <span style="color: #888; margin-left: 5px;">@{row.get('poster_screen_name', '')}</span>
                        {' ✓' if row.get('tweeter_is_verified') else ''}
                        {' 🤖' if row.get('tweeter_is_bot') else ''}
                        <span style="background-color: #E3F2FD; color: #1565C0; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-left: 5px;">{row.get('platform', 'Unknown')}</span>
                    </div>
                    <div style="color: #888;">{row['post_date']}</div>
                </div>
                <div style="margin-bottom: 10px;">{row['post_text'][:280]}{'...' if len(row['post_text']) > 280 else ''}</div>
                <div style="display: flex; justify-content: space-between; color: #888;">
                    <div>❤️ {row.get('likes_count', 0):,}</div>
                    <div>🔄 {row.get('shares_count', 0):,}</div>
                    <div>💬 {row.get('comments_count', 0):,}</div>
                    <div>👁️ {row.get('views_count', 0):,}</div>
                </div>
                <div style="margin-top: 10px; display: flex; justify-content: space-between;">
                    <div style="color: #F44336;">Bot: {row.get('percent_bots_retweets', 'N/A')}%</div>
                    <div style="color: #4CAF50;">Human Reach: {row.get('human_reach', 0):,}</div>
                </div>
            </div>
            """
            st.components.v1.html(html_content, height=200)  # Adjust height as needed
        
        # Post Engagement Comparison
        st.markdown('<div class="section-title">Post Engagement Comparison</div>', unsafe_allow_html=True)
        
        if not top_posts.empty:
            # Create a radar chart comparing the top 5 posts
            radar_df = top_posts.head(5)[['poster_name', 'likes_count', 'shares_count', 'comments_count', 'views_count']].fillna(0)
            
            # Normalize the data for better visualization
            for col in ['likes_count', 'shares_count', 'comments_count', 'views_count']:
                if col in radar_df.columns:
                    max_val = radar_df[col].max()
                    if max_val > 0:
                        radar_df[f'{col}_norm'] = radar_df[col] / max_val
                    else:
                        radar_df[f'{col}_norm'] = 0
            
            # Create the radar chart
            fig = go.Figure()
            
            for _, row in radar_df.iterrows():
                fig.add_trace(go.Scatterpolar(
                    r=[
                        row.get('likes_count_norm', 0), 
                        row.get('shares_count_norm', 0), 
                        row.get('comments_count_norm', 0), 
                        row.get('views_count_norm', 0)
                    ],
                    theta=['Likes', 'Shares', 'Comments', 'Views'],
                    fill='toself',
                    name=row['poster_name']
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                title='Top Posts Engagement Comparison (Normalized)',
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a grouped bar chart for actual values
            fig = go.Figure()
            
            # Add traces for each post
            for i, col in enumerate(['likes_count', 'shares_count', 'comments_count', 'views_count']):
                if col in radar_df.columns:
                    fig.add_trace(go.Bar(
                        x=radar_df['poster_name'],
                        y=radar_df[col],
                        name=col.replace('_count', '').capitalize(),
                        marker_color=px.colors.qualitative.Set1[i]
                    ))
            
            fig.update_layout(
                title='Top Posts Engagement Metrics',
                xaxis_title='Poster',
                yaxis_title='Count',
                barmode='group',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Interaction Timeline - Using Plotly
        st.markdown('<div class="section-title">Interaction Timeline</div>', unsafe_allow_html=True)
        
        # Prepare timeline data
        timeline_df = blackrock_social_df.copy()
        timeline_df['post_date'] = pd.to_datetime(timeline_df['post_date'])
        timeline_df = timeline_df.sort_values('post_date')
        
        # Check if we have timeline data
        if not timeline_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timeline_df['post_date'],
                y=timeline_df['interactions_count'],
                mode='markers+lines',
                name='Interactions',
                marker=dict(
                    size=timeline_df['interactions_count'] / timeline_df['interactions_count'].max() * 20 + 5,
                    color=timeline_df['percent_bots_retweets'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Bot %")
                ),
                hovertemplate='<b>%{text}</b><br>Interactions: %{y}<br>Date: %{x}<br>Bot %: %{marker.color:.1f}%',
                text=timeline_df['poster_name']
            ))
            
            fig.update_layout(
                title='Interaction Timeline for BlackRock Posts',
                xaxis_title='Post Date',
                yaxis_title='Interactions',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a calendar heatmap
            timeline_df['day'] = timeline_df['post_date'].dt.day
            timeline_df['month'] = timeline_df['post_date'].dt.month
            
            # Aggregate by day and month
            agg_timeline = timeline_df.groupby(['month', 'day'])['interactions_count'].mean().reset_index()
            
            fig = px.scatter(
                agg_timeline,
                x='day',
                y='month',
                size='interactions_count',
                color='interactions_count',
                size_max=20,
                color_continuous_scale='Viridis',
                title='Interactions Calendar Heatmap',
                labels={'interactions_count': 'Avg. Interactions', 'day': 'Day', 'month': 'Month'}
            )
            
            # Configure y-axis to show month names
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            fig.update_layout(
                yaxis=dict(
                    tickvals=list(range(1, 13)),
                    ticktext=month_names
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available.")
        
        # Key Insights
        st.markdown('<div class="section-title">Key Insights</div>', unsafe_allow_html=True)
        
        # Calculate percentages safely
        blackrock_pct = (blackrock_mentions / total_posts * 100) if total_posts > 0 else 0
        
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <ul>
                <li><strong>{blackrock_pct:.1f}%</strong> of viral posts in this dataset mention BlackRock, indicating significant social media discussion</li>
                <li><strong>{avg_bot_percentage}%</strong> of retweets about BlackRock come from bot accounts, suggesting potential inauthentic amplification</li>
                <li>Posts about BlackRock receive an average of <strong>{avg_interactions:,}</strong> interactions, demonstrating high engagement</li>
                <li>Content about BlackRock and cryptocurrency attracts the most engagement, followed by discussions about real estate investments</li>
                <li>Total human reach for BlackRock content: <strong>{total_human_reach:,}</strong> users</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Add a wordcloud-like analysis of post text
        st.markdown('<div class="section-title">Popular Terms in BlackRock Posts</div>', unsafe_allow_html=True)
        
        # Simple term frequency analysis
        if 'post_text' in blackrock_social_df.columns:
            # Extract terms (extremely simplified approach)
            all_text = ' '.join(blackrock_social_df['post_text'].fillna('').str.lower())
            import re
            from collections import Counter
            
            # Remove URLs, special characters, and split into words
            words = re.sub(r'http\S+|www\S+|https\S+|[^\w\s]', ' ', all_text)
            words = re.sub(r'\s+', ' ', words).strip()
            word_list = words.split()
            
            # Remove common stopwords
            stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by', 'for', 'with', 'about', 'against', 
                         'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'of', 'in', 'on', 'is', 'are', 'was', 
                         'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'this', 'that', 'these', 
                         'those', 'not', 'blackrock', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            filtered_words = [word for word in word_list if word not in stopwords and len(word) > 2]
            
            # Count words
            word_counts = Counter(filtered_words)
            
            # Get top words
            top_words = pd.DataFrame(word_counts.most_common(50), columns=['Word', 'Count'])
            
            # Create a bar chart for top words
            fig = px.bar(
                top_words.head(20), 
                y='Word', 
                x='Count',
                orientation='h',
                color='Count',
                color_continuous_scale='Viridis',
                title='Most Common Terms in BlackRock Posts'
            )
            
            fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a bubble chart for top words
            fig = px.scatter(
                top_words.head(30),
                x=[i for i in range(30)],
                y=[i % 5 for i in range(30)],
                size='Count',
                text='Word',
                color='Count',
                color_continuous_scale='Viridis',
                title='Term Frequency Bubble Chart',
                size_max=60
            )
            
            fig.update_traces(textposition='middle center')
            
            fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Show full data table
        with st.expander("View Full Data for Top Posts"):
            st.dataframe(top_posts, use_container_width=True)
    else:
        st.warning("No BlackRock posts found to display.")

# Tab 4: IMPROVED ARTICLE ANALYSIS with fixes
with tab4:
    st.markdown('<div class="section-title">Article Analysis</div>', unsafe_allow_html=True)
    
    # Add debug section for easier troubleshooting
    with st.expander("Debug Information"):
        if 'debug_info' in st.session_state:
            for info in st.session_state['debug_info']:
                st.write(info)
        else:
            st.write("No debug information available")
    
    # Store processed data in session state if available
    if 'article_posts_df' not in st.session_state and not article_posts_df.empty:
        st.session_state['article_posts_df'] = article_posts_df
        
    if 'article_metadata' not in st.session_state and article_metadata:
        st.session_state['article_metadata'] = article_metadata
    
    # Button to fetch fresh article data
    fetch_col1, fetch_col2 = st.columns([3, 1])
    
    with fetch_col2:
        if st.button("🔄 Fetch Fresh Article Data", use_container_width=True):
            with st.spinner("Fetching and processing article data..."):
                try:
                    # Fetch article data directly with current proxy setting
                    article_data = fetch_article_posts(use_proxy=use_proxy)
                    
                    if article_data:
                        st.success(f"Successfully fetched {len(article_data)} article data items")
                        
                        # Process the article data using the improved function
                        article_posts, article_metadata = improved_process_article_posts(article_data)
                        
                        if article_posts:
                            # Convert to DataFrame
                            article_posts_df = create_dataframe(article_posts)
                            
                            # Store in session state
                            st.session_state['article_posts_df'] = article_posts_df
                            st.session_state['article_metadata'] = article_metadata
                            
                            # Add BlackRock mentions column
                            if 'mentions_blackrock' not in article_posts_df.columns:
                                article_posts_df['mentions_blackrock'] = article_posts_df['post_text'].str.lower().str.contains('blackrock')
                            
                            st.success(f"Successfully processed {len(article_posts)} article posts and {len(article_metadata)} article metadata items!")
                            
                            # Force a rerun to refresh the dashboard with the new data
                            st.experimental_rerun()
                        else:
                            st.error("No article posts were processed. Check the debug information.")
                    else:
                        st.error("No article data returned from API.")
                except Exception as e:
                    import traceback
                    st.error(f"Error loading article data: {e}")
                    st.code(traceback.format_exc(), language="python")
    
    with fetch_col1:
        # Show connection info
        st.info(f"Article API Connection: {'Using corporate proxy at http://webproxy.blackrock.com:8080' if use_proxy else 'Direct connection (no proxy)'}")
    
    # Use data from session state if available, or from the initial load
    current_article_df = st.session_state.get('article_posts_df', article_posts_df)
    current_metadata = st.session_state.get('article_metadata', article_metadata)
    
    # Determine if we have valid data to display
    has_article_data = isinstance(current_article_df, pd.DataFrame) and not current_article_df.empty
    has_metadata = bool(current_metadata)
    
    if has_article_data:
        # Add filters for article analysis
        with st.container():
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            st.markdown('<div class="data-table-title">Filter Options</div>', unsafe_allow_html=True)
            
            article_filter_col1, article_filter_col2, article_filter_col3 = st.columns(3)
            
            with article_filter_col1:
                # Platform filter
                if 'platform' in current_article_df.columns:
                    article_platform_options = ['All'] + sorted(current_article_df['platform'].unique().tolist())
                    article_selected_platform = st.selectbox('Platform', article_platform_options, key='article_platform')
                else:
                    article_selected_platform = 'All'
            
            with article_filter_col2:
                # BlackRock mention filter
                show_blackrock_only = st.checkbox('Show BlackRock Mentions Only', False)
            
            with article_filter_col3:
                # Date range filter if post_date column exists
                if 'post_date' in current_article_df.columns:
                    current_article_df['post_date_dt'] = pd.to_datetime(current_article_df['post_date'], errors='coerce')
                    min_date = current_article_df['post_date_dt'].min().date()
                    max_date = current_article_df['post_date_dt'].max().date()
                    selected_date_range = st.date_input('Date Range', [min_date, max_date], key='article_date_range')
                else:
                    selected_date_range = None
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Apply filters
        filtered_article_df = current_article_df.copy()
        
        if article_selected_platform != 'All':
            filtered_article_df = filtered_article_df[filtered_article_df['platform'] == article_selected_platform]
        
        if show_blackrock_only and 'mentions_blackrock' in filtered_article_df.columns:
            filtered_article_df = filtered_article_df[filtered_article_df['mentions_blackrock']]
        
        if selected_date_range and len(selected_date_range) == 2 and 'post_date_dt' in filtered_article_df.columns:
            filtered_article_df = filtered_article_df[(filtered_article_df['post_date_dt'].dt.date >= selected_date_range[0]) & 
                                                    (filtered_article_df['post_date_dt'].dt.date <= selected_date_range[1])]
        
        # Update metrics based on filtered data
        filtered_article_count = len(filtered_article_df)
        filtered_articles_unique = len(filtered_article_df['article_id'].unique()) if 'article_id' in filtered_article_df.columns else 0
        
        # Article Metrics
        st.markdown(f"**Filtered Results:** {filtered_article_count} posts from {filtered_articles_unique} unique articles")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{filtered_article_count}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Article-Related Posts</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{filtered_articles_unique}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Unique Articles</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            avg_article_interactions = int(filtered_article_df['interactions_count'].mean()) if 'interactions_count' in filtered_article_df.columns and not filtered_article_df['interactions_count'].isna().all() else 0
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_article_interactions:,}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Avg. Article Post Interactions</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Platform Distribution Visualization
        st.markdown('### Article Post Distribution by Platform')
        
        if not filtered_article_df.empty and 'platform' in filtered_article_df.columns:
            platform_counts = filtered_article_df['platform'].value_counts().reset_index()
            platform_counts.columns = ['Platform', 'Count']
            
            fig = px.bar(
                platform_counts,
                x='Platform',
                y='Count',
                color='Platform',
                title='Article Posts by Platform',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            
            fig.update_layout(
                xaxis_title='Platform',
                yaxis_title='Number of Posts',
                legend_title='Platform',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No platform data available to display.")
        
        # Timeline Visualization
        st.markdown('### Article Post Timeline')
        
        if 'post_date_dt' in filtered_article_df.columns:
            # Group by date
            timeline_df = filtered_article_df.groupby(filtered_article_df['post_date_dt'].dt.date).size().reset_index()
            timeline_df.columns = ['date', 'posts']
            
            # Also get interactions by date if available
            if 'interactions_count' in filtered_article_df.columns:
                interactions_by_date = filtered_article_df.groupby(filtered_article_df['post_date_dt'].dt.date)['interactions_count'].sum().reset_index()
                interactions_by_date.columns = ['date', 'interactions']
                
                # Create a dual-axis chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Add traces for posts count and interactions
                fig.add_trace(
                    go.Bar(
                        x=timeline_df['date'],
                        y=timeline_df['posts'],
                        name='Number of Posts',
                        marker_color='#1E88E5'
                    ),
                    secondary_y=False
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=interactions_by_date['date'],
                        y=interactions_by_date['interactions'],
                        name='Total Interactions',
                        line=dict(color='#E91E63', width=3),
                        mode='lines+markers'
                    ),
                    secondary_y=True
                )
                
                # Set titles and layout
                fig.update_layout(
                    title_text='Article Posts and Interactions Over Time',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    height=450
                )
                
                fig.update_xaxes(title_text='Date')
                fig.update_yaxes(title_text='Number of Posts', secondary_y=False)
                fig.update_yaxes(title_text='Interactions', secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Simple bar chart if no interactions data
                fig = px.bar(
                    timeline_df,
                    x='date',
                    y='posts',
                    title='Article Posts Over Time',
                    color_discrete_sequence=['#1E88E5']
                )
                
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Number of Posts',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available to display.")
        
        # Display article metadata information
        st.markdown('### Article Content Analysis')
        
        # Create a dataframe that counts posts per article
        if 'article_id' in filtered_article_df.columns:
            article_counts = filtered_article_df['article_id'].value_counts().reset_index()
            article_counts.columns = ['article_id', 'posts_count']
            
            # Add article details from metadata
            article_counts['headline'] = article_counts['article_id'].apply(
                lambda x: current_metadata.get(x).url_headline_text if x in current_metadata else "Unknown"
            )
            article_counts['url'] = article_counts['article_id'].apply(
                lambda x: current_metadata.get(x).article_url if x in current_metadata else None
            )
            
            # Add interactions if available
            if 'interactions_count' in filtered_article_df.columns:
                article_interactions = filtered_article_df.groupby('article_id')['interactions_count'].sum().reset_index()
                article_counts = article_counts.merge(article_interactions, on='article_id', how='left')
            else:
                article_counts['interactions_count'] = 0
            
            # Sort by most posts
            top_articles = article_counts.sort_values('posts_count', ascending=False).head(10)
            
            # Visualize top articles by post count
            fig = px.bar(
                top_articles,
                x='posts_count',
                y='headline',
                orientation='h',
                color='interactions_count',
                color_continuous_scale='Viridis',
                title='Top 10 Articles by Number of Posts',
                labels={
                    'posts_count': 'Number of Posts',
                    'headline': 'Article Headline',
                    'interactions_count': 'Total Interactions'
                }
            )
            
            fig.update_layout(
                yaxis_title='',
                yaxis={'categoryorder':'total ascending'},
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display top articles in a more readable format
            st.markdown('### Most Shared Articles')
            
            for i, (_, article) in enumerate(top_articles.head(5).iterrows(), 1):
                with st.container():
                    st.markdown(f"""
                    <div class="article-card">
                        <div class="article-title">{i}. {article['headline'] or "Unknown Title"}</div>
                        <div class="article-meta">
                            <a href="{article['url'] or '#'}" target="_blank">View article</a> | 
                            Article ID: {article['article_id']}
                        </div>
                        <div class="article-stats">
                            <div>Posts: <b>{article['posts_count']}</b></div>
                            <div>Total Interactions: <b>{article['interactions_count']:,}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # BlackRock mention analysis in articles
            if 'mentions_blackrock' in filtered_article_df.columns:
                st.markdown('### BlackRock Mentions Analysis')
                
                # Count posts with BlackRock mentions
                blackrock_mentions_count = filtered_article_df['mentions_blackrock'].sum()
                non_blackrock_mentions_count = len(filtered_article_df) - blackrock_mentions_count
                
                # Create a pie chart
                fig = px.pie(
                    values=[blackrock_mentions_count, non_blackrock_mentions_count],
                    names=['Mentions BlackRock', 'No BlackRock Mention'],
                    title='Posts Mentioning BlackRock',
                    color_discrete_sequence=['#1E88E5', '#E0E0E0'],
                    hole=0.4
                )
                
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                
                # Create columns for side-by-side visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Create a platform breakdown of BlackRock mentions
                    if 'platform' in filtered_article_df.columns:
                        # Use crosstab with boolean values
                        blackrock_by_platform = pd.crosstab(
                            filtered_article_df['platform'], 
                            filtered_article_df['mentions_blackrock']
                        )
                        
                        # For safety, make sure column labels are compatible with melt
                        blackrock_by_platform.columns = blackrock_by_platform.columns.astype(str)
                        
                        # Reset index to prepare for melting
                        blackrock_by_platform_reset = blackrock_by_platform.reset_index()
                        
                        # Now melt with string column names
                        blackrock_by_platform_melted = pd.melt(
                            blackrock_by_platform_reset,
                            id_vars=['platform'],
                            value_vars=[str(col) for col in blackrock_by_platform.columns],
                            var_name='mentions_blackrock',
                            value_name='Count'
                        )
                        
                        # Set better labels for display
                        blackrock_by_platform_melted['Mention Type'] = blackrock_by_platform_melted['mentions_blackrock'].map({
                            'False': 'No BlackRock Mention',
                            'True': 'Mentions BlackRock'
                        })
                        
                        # Create grouped bar chart
                        fig = px.bar(
                            blackrock_by_platform_melted,
                            x='platform',
                            y='Count',
                            color='Mention Type',
                            title='BlackRock Mentions by Platform',
                            barmode='group',
                            color_discrete_sequence=['#E0E0E0', '#1E88E5']
                        )
                        
                        fig.update_layout(height=400)
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            # User account analysis
            if 'poster_name' in filtered_article_df.columns:
                st.markdown('### User Account Analysis')
                
                # Get top user accounts sharing articles
                top_users = filtered_article_df['poster_name'].value_counts().reset_index().head(10)
                top_users.columns = ['User', 'Post Count']
                
                # Create a horizontal bar chart
                fig = px.bar(
                    top_users,
                    y='User',
                    x='Post Count',
                    orientation='h',
                    color='Post Count',
                    color_continuous_scale='Viridis',
                    title='Top Users Sharing Article Content'
                )
                
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Interactive data table with all posts
            st.markdown('### All Article Posts (Interactive Table)')
            
            # Prepare the display columns to show most relevant info
            display_columns = [
                'poster_name', 'platform', 'post_date', 'post_text', 'interactions_count', 
                'article_id', 'mentions_blackrock'
            ]
            # Filter to only include columns that exist
            display_columns = [col for col in display_columns if col in filtered_article_df.columns]
            
            # Create a more user-friendly dataframe for display
            display_df = filtered_article_df[display_columns].copy()
            
            # Add headline from metadata if available
            if has_metadata:
                display_df['article_headline'] = display_df['article_id'].apply(
                    lambda x: current_metadata.get(x).url_headline_text if x in current_metadata else "Unknown"
                )
                # Reorder columns to put headline after article_id
                headline_idx = display_df.columns.get_loc('article_headline')
                article_id_idx = display_df.columns.get_loc('article_id')
                cols = list(display_df.columns)
                cols.insert(article_id_idx + 1, cols.pop(headline_idx))
                display_df = display_df[cols]
            
            # Format date column if it exists
            if 'post_date' in display_df.columns:
                display_df['post_date'] = pd.to_datetime(display_df['post_date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Allow column renaming for better display
            renamed_columns = {
                'poster_name': 'User',
                'platform': 'Platform',
                'post_date': 'Date',
                'post_text': 'Post Content',
                'interactions_count': 'Interactions',
                'article_id': 'Article ID',
                'article_headline': 'Article Headline',
                'mentions_blackrock': 'BlackRock Mention'
            }
            # Only rename columns that exist
            renamed_columns = {k: v for k, v in renamed_columns.items() if k in display_df.columns}
            display_df = display_df.rename(columns=renamed_columns)
            
            # Display the dataframe
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600
            )
            
            # Add download button for the data
            csv = filtered_article_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Article Data as CSV",
                data=csv,
                file_name=f"blackrock_article_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.info("No article ID data available for article content analysis.")
    else:
        # No article data available
        st.warning("""
        No article posts data available for analysis. Please click the "Fetch Fresh Article Data" button above.
        
        This could be due to:
        1. No article data being returned from the API
        2. Issues with the API credentials or connection
        3. The fetch_article_posts function not returning expected data format
        
        Check the debug section for more details.
        """)
        
        # Test direct fetch button with proxy setting
        proxy_status = "with proxy" if use_proxy else "without proxy"
        if st.button(f"Test Direct Article Fetch ({proxy_status})"):
            try:
                with st.spinner("Testing direct article fetch..."):
                    # Call with proxy parameter
                    article_data = fetch_article_posts(use_proxy=use_proxy)
                    st.write(f"API returned {len(article_data) if isinstance(article_data, list) else type(article_data)} article data items")
                    
                    # Display sample of the data
                    if isinstance(article_data, list) and article_data:
                        # Check if we need to parse JSON strings
                        if isinstance(article_data[0], str):
                            st.write("First item is a string, attempting to parse as JSON")
                            import json
                            try:
                                sample_item = json.loads(article_data[0])
                                st.write("Parsed JSON:")
                                st.json(sample_item)
                            except:
                                st.write("Raw first item (string):", article_data[0][:500] + "..." if len(article_data[0]) > 500 else article_data[0])
                                
                            # Try to process the data with manual JSON parsing
                            try:
                                parsed_data = [json.loads(item) if isinstance(item, str) else item for item in article_data]
                                article_posts, article_metadata = improved_process_article_posts(parsed_data)
                                st.success(f"Successfully processed {len(article_posts)} posts and extracted {len(article_metadata)} article metadata items")
                                
                                # Store in session state
                                if article_posts:
                                    article_posts_df = create_dataframe(article_posts)
                                    st.session_state['article_posts_df'] = article_posts_df
                                    st.session_state['article_metadata'] = article_metadata
                                    
                                    # Add a button to refresh
                                    if st.button("Refresh Dashboard with Processed Data"):
                                        st.experimental_rerun()
                            except Exception as proc_error:
                                st.error(f"Error processing parsed data: {proc_error}")
                        else:
                            st.json(article_data[0])
                            
                            # Try to process the data directly
                            try:
                                article_posts, article_metadata = improved_process_article_posts(article_data)
                                st.success(f"Successfully processed {len(article_posts)} posts and extracted {len(article_metadata)} article metadata items")
                                
                                # Store in session state
                                if article_posts:
                                    article_posts_df = create_dataframe(article_posts)
                                    st.session_state['article_posts_df'] = article_posts_df
                                    st.session_state['article_metadata'] = article_metadata
                                    
                                    # Add a button to refresh
                                    if st.button("Refresh Dashboard with Processed Data"):
                                        st.experimental_rerun()
                            except Exception as proc_error:
                                st.error(f"Error processing data: {proc_error}")
                    else:
                        st.write("Article data is empty or not a list")
            except Exception as e:
                st.error(f"Error testing article fetch: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")
        
        # Add option to try with alternate proxy setting
        alternate_proxy = not use_proxy
        alternate_proxy_status = "with proxy" if alternate_proxy else "without proxy"
        if st.button(f"Try Fetch {alternate_proxy_status}", type="primary"):
            try:
                with st.spinner(f"Testing direct article fetch {alternate_proxy_status}..."):
                    # Call with alternate proxy parameter
                    article_data = fetch_article_posts(use_proxy=alternate_proxy)
                    if article_data:
                        st.success(f"Successfully fetched {len(article_data)} article data items {alternate_proxy_status}")
                        
                        # Process the article data using the improved function
                        article_posts, article_metadata = improved_process_article_posts(article_data)
                        
                        if article_posts:
                            # Convert to DataFrame
                            article_posts_df = create_dataframe(article_posts)
                            
                            # Store in session state
                            st.session_state['article_posts_df'] = article_posts_df
                            st.session_state['article_metadata'] = article_metadata
                            
                            # Add BlackRock mentions column
                            if 'mentions_blackrock' not in article_posts_df.columns:
                                article_posts_df['mentions_blackrock'] = article_posts_df['post_text'].str.lower().str.contains('blackrock')
                            
                            st.success(f"Successfully processed {len(article_posts)} article posts and {len(article_metadata)} article metadata items!")
                            
                            # Show a button to update the sidebar proxy setting and refresh
                            if st.button("Update proxy setting and refresh dashboard"):
                                # Toggle proxy setting in session state
                                st.session_state['use_proxy'] = alternate_proxy
                                # Force a rerun to refresh the dashboard with the new data
                                st.experimental_rerun()
                    else:
                        st.error(f"No article data returned from API {alternate_proxy_status}.")
            except Exception as e:
                st.error(f"Error testing article fetch {alternate_proxy_status}: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")

# Raw Data Explorer
with tab5:
    st.markdown('<div class="section-title">Raw Data Explorer</div>', unsafe_allow_html=True)
    
    # Add explanation
    st.markdown("""
    This tab provides direct access to the raw data returned by the Vinesight API. You can explore both social media posts 
    and article-related data, and filter or search for specific information.
    """)
    
    # Create subtabs
    raw_tab1, raw_tab2 = st.tabs(["Social Media Data", "Article Data"])
    
    # Social Media Data Explorer
    with raw_tab1:
        st.markdown('<div class="tab-subheader">Social Media Data</div>', unsafe_allow_html=True)
        
        if not social_df.empty:
            # Add search and filter options
            with st.container():
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.markdown('<div class="data-table-title">Search & Filter Options</div>', unsafe_allow_html=True)
                
                search_col1, search_col2, search_col3 = st.columns(3)
                
                with search_col1:
                    # Text search
                    search_text = st.text_input("Search in Post Text", "")
                
                with search_col2:
                    # Platform filter
                    if 'platform' in social_df.columns:
                        platform_options_raw = ['All'] + sorted(social_df['platform'].unique().tolist())
                        selected_platform_raw = st.selectbox('Platform', platform_options_raw, key='raw_platform')
                    else:
                        selected_platform_raw = 'All'
                
                with search_col3:
                    # Column selector
                    all_columns = social_df.columns.tolist()
                    default_columns = ['poster_name', 'platform', 'post_date', 'post_text', 'interactions_count']
                    selected_columns = st.multiselect(
                        "Select Columns to Display",
                        options=all_columns,
                        default=[col for col in default_columns if col in all_columns]
                    )
                    
                    if not selected_columns:
                        selected_columns = all_columns
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Apply filters
            filtered_raw_df = social_df.copy()
            
            if search_text:
                filtered_raw_df = filtered_raw_df[filtered_raw_df['post_text'].str.contains(search_text, case=False, na=False)]
            
            if selected_platform_raw != 'All':
                filtered_raw_df = filtered_raw_df[filtered_raw_df['platform'] == selected_platform_raw]
            
            # Show the filtered data
            st.markdown(f"**Showing {len(filtered_raw_df)} of {len(social_df)} posts**")
            
            # Add data download option
            csv = filtered_raw_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name=f"social_media_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
            
            # Show the dataframe
            st.dataframe(filtered_raw_df[selected_columns], use_container_width=True)
            
            # Show data schema
            with st.expander("View Data Schema"):
                schema_df = pd.DataFrame({
                    'Column': social_df.columns,
                    'Data Type': social_df.dtypes.astype(str),
                    'Non-Null Count': social_df.count(),
                    'Null %': (social_df.isna().mean() * 100).round(2),
                    'Sample Values': [str(social_df[col].dropna().sample(min(3, len(social_df[col].dropna()))).tolist())[:100] + '...' 
                                      if len(social_df[col].dropna()) > 0 else 'N/A' 
                                      for col in social_df.columns]
                })
                
                st.markdown('<div class="data-table-title">Social Media Data Schema</div>', unsafe_allow_html=True)
                st.dataframe(schema_df, use_container_width=True)
        else:
            st.warning("No social media data available to explore.")
    
    # Article Data Explorer
    with raw_tab2:
        st.markdown('<div class="tab-subheader">Article Data</div>', unsafe_allow_html=True)
        
        # Determine if article data is available
        has_article_data = isinstance(article_posts_df, pd.DataFrame) and not article_posts_df.empty
        has_metadata = bool(article_metadata)
        
        if has_article_data:
            # Add search and filter options
            with st.container():
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.markdown('<div class="data-table-title">Search & Filter Options</div>', unsafe_allow_html=True)
                
                article_search_col1, article_search_col2, article_search_col3 = st.columns(3)
                
                with article_search_col1:
                    # Text search
                    article_search_text = st.text_input("Search in Article Post Text", "")
                
                with article_search_col2:
                    # Platform filter
                    if 'platform' in article_posts_df.columns:
                        article_platform_options_raw = ['All'] + sorted(article_posts_df['platform'].unique().tolist())
                        selected_article_platform_raw = st.selectbox('Platform', article_platform_options_raw, key='raw_article_platform')
                    else:
                        selected_article_platform_raw = 'All'
                
                with article_search_col3:
                    # Article ID filter
                    if 'article_id' in article_posts_df.columns:
                        article_id_options = ['All'] + sorted(article_posts_df['article_id'].unique().tolist())
                        selected_article_id = st.selectbox('Article ID', article_id_options, key='article_id')
                    else:
                        selected_article_id = 'All'
                
                # Second row
                article_search_col4, article_search_col5 = st.columns(2)
                
                with article_search_col4:
                    # Column selector
                    all_article_columns = article_posts_df.columns.tolist()
                    default_article_columns = ['article_id', 'poster_name', 'platform', 'post_date', 'post_text']
                    selected_article_columns = st.multiselect(
                        "Select Columns to Display",
                        options=all_article_columns,
                        default=[col for col in default_article_columns if col in all_article_columns],
                        key='article_columns'
                    )
                    
                    if not selected_article_columns:
                        selected_article_columns = all_article_columns
                
                with article_search_col5:
                    # Show metadata
                    show_metadata = st.checkbox("Show Article Metadata", True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Apply filters
            filtered_raw_article_df = article_posts_df.copy()
            
            if article_search_text:
                filtered_raw_article_df = filtered_raw_article_df[filtered_raw_article_df['post_text'].str.contains(article_search_text, case=False, na=False)]
            
            if selected_article_platform_raw != 'All':
                filtered_raw_article_df = filtered_raw_article_df[filtered_raw_article_df['platform'] == selected_article_platform_raw]
            
            if selected_article_id != 'All':
                filtered_raw_article_df = filtered_raw_article_df[filtered_raw_article_df['article_id'] == selected_article_id]
            
            # Show the filtered data
            st.markdown(f"**Showing {len(filtered_raw_article_df)} of {len(article_posts_df)} article posts**")
            
            # Add data download option
            csv = filtered_raw_article_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Filtered Article Data as CSV",
                data=csv,
                file_name=f"article_posts_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
            
            # Show the dataframe
            st.dataframe(filtered_raw_article_df[selected_article_columns], use_container_width=True)
            
            # Show article metadata if selected
            if show_metadata and has_metadata:
                st.markdown('<div class="tab-subheader">Article Metadata</div>', unsafe_allow_html=True)
                
                # Create a DataFrame from article_metadata
                article_meta_df = pd.DataFrame([
                    {
                        'article_id': article_id,
                        'headline': meta.url_headline_text,
                        'description': meta.url_description,
                        'url': meta.article_url
                    }
                    for article_id, meta in article_metadata.items()
                ])
                
                # Filter metadata if a specific article is selected
                if selected_article_id != 'All':
                    article_meta_df = article_meta_df[article_meta_df['article_id'] == selected_article_id]
                
                st.dataframe(article_meta_df, use_container_width=True)
                
                # Add metadata download option
                meta_csv = article_meta_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Article Metadata as CSV",
                    data=meta_csv,
                    file_name=f"article_metadata_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            
            # Show data schema
            with st.expander("View Article Data Schema"):
                schema_df = pd.DataFrame({
                    'Column': article_posts_df.columns,
                    'Data Type': article_posts_df.dtypes.astype(str),
                    'Non-Null Count': article_posts_df.count(),
                    'Null %': (article_posts_df.isna().mean() * 100).round(2),
                    'Sample Values': [str(article_posts_df[col].dropna().sample(min(3, len(article_posts_df[col].dropna()))).tolist())[:100] + '...' 
                                      if len(article_posts_df[col].dropna()) > 0 else 'N/A' 
                                      for col in article_posts_df.columns]
                })
                
                st.markdown('<div class="data-table-title">Article Data Schema</div>', unsafe_allow_html=True)
                st.dataframe(schema_df, use_container_width=True)
        else:
            st.warning("No article data available to explore.")

# Render footer component
render_footer()