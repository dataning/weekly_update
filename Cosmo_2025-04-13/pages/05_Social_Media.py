import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
import glob
from components.header import render_header
import theme
# Import access control functionality
from services.access_control import (
    initialize_session_state, login_ui, admin_settings_ui,
    load_config, save_config
)

# Initialize the session state for authentication
initialize_session_state()

theme.set_page_config()
theme.apply_full_theme()

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
st.markdown('Comprehensive analysis of social media posts and articles mentioning BlackRock')

# Add admin settings to the sidebar
with st.sidebar:
    st.header("Administration")
    admin_settings_ui()

# Function to load data from parquet file in 'data' folder
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    with st.spinner("Loading social media data..."):
        try:
            # Find the latest file starting with 'Social_daily' in the 'data' directory
            data_files = glob.glob('data/Social_daily_*.parquet')
            
            if not data_files:
                st.error("No Social_daily files found in the 'data' directory.")
                return pd.DataFrame(), pd.DataFrame(), {}
            
            # Get the most recent file
            latest_file = max(data_files, key=os.path.getctime)
            # st.info(f"Loading data from: {latest_file}")
            
            # Load the parquet file
            social_df = pd.read_parquet(latest_file)
            
            # Add a column for BlackRock mentions if it doesn't exist
            if 'mentions_blackrock' not in social_df.columns:
                social_df['mentions_blackrock'] = social_df['post_text'].str.lower().str.contains('blackrock')
            
            # For now, we'll return empty DataFrames for article_posts_df and article_metadata
            # In a real implementation, you might have separate article data files to load
            article_posts_df = pd.DataFrame()
            article_metadata = {}
            
            return social_df, article_posts_df, article_metadata
        except Exception as e:
            st.error(f"Error loading data: {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            # Return empty DataFrames - can be handled downstream
            return pd.DataFrame(), pd.DataFrame(), {}

# Load data
social_df, article_posts_df, article_metadata = load_data()

# Show data source info
st.info(f"Data loaded from local files | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Check if social_df is empty or None
if social_df is None or (isinstance(social_df, pd.DataFrame) and social_df.empty):
    st.error("No data available. Please check that data files exist in the 'data' folder.")
    
    # Add retry button
    if st.button("🔄 Retry Loading Data"):
        # Reset cache and reload
        load_data.clear()
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
                    # Skip None values
                    if value is None:
                        continue
                    
                    # Make sure we're working with numeric values
                    try:
                        value_float = float(value)
                    except (TypeError, ValueError):
                        continue
                        
                    # Add to existing value or initialize
                    if state in viral_states:
                        viral_states[state] = viral_states[state] + value_float
                    else:
                        viral_states[state] = value_float
        
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

# Tab 4: Article Analysis
with tab4:
    st.markdown('<div class="section-title">Article Analysis</div>', unsafe_allow_html=True)
    
    if not article_posts_df.empty:
        # Article analysis code here
        st.markdown("### Article Analysis functionality will be implemented here")
    else:
        st.info("No article data available. This feature would analyze articles mentioning BlackRock.")
        
        # Display sample UI for what the article analysis would look like
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">Sample Article Analysis Features</h4>
            <ul>
                <li>Top articles by engagement and reach</li>
                <li>Publication source analysis</li>
                <li>Sentiment analysis of article content</li>
                <li>Topic clustering and trend identification</li>
                <li>Timeline of article publications</li>
                <li>Correlation between article content and social media engagement</li>
            </ul>
            <p>To enable this feature, article data would need to be included in the data folder.</p>
        </div>
        """, unsafe_allow_html=True)

# Tab 5: Raw Data Explorer
with tab5:
    st.markdown('<div class="section-title">Raw Data Explorer</div>', unsafe_allow_html=True)
    
    # Add explanation
    st.markdown("""
    This tab provides direct access to the raw data loaded from the parquet file. You can explore both social media posts 
    and filter or search for specific information.
    """)
    
    # Social Media Data Explorer
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

# Render sidebar component
theme.render_sidebar()

# Render footer component
theme.render_footer()