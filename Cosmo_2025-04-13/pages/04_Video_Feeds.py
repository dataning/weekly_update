"""
Enhanced Streamlit Video Feeds Monitor with Premier Access
---------------------------------------
A Streamlit app that dynamically loads the latest data from a parquet file
and displays the complete dataframe. Includes
collapsible detailed views with text highlighting for important keywords.
With embedded thumbnails and video links.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import os
import glob
from io import BytesIO
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
import theme
# Import shared access control module (only keeping what's needed)
from services.access_control import (
    initialize_session_state, login_ui, admin_settings_ui,
    load_config, save_config
)

# Constants
CONFIG_FILE = "config.json"
# Keywords to highlight in the text
HIGHLIGHT_KEYWORDS = [
    "blackrock", "larry fink", "fink"
]

# Initialize session state for authentication
initialize_session_state()

theme.set_page_config()
theme.apply_full_theme()

# Render header
render_header()

# Custom CSS for highlighting, media display, and authentication
st.markdown("""
<style>
    .highlight {
        background-color: #FFFF00;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
    }
    .sentiment-positive {
        color: green;
        font-weight: bold;
    }
    .sentiment-negative {
        color: red;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: gray;
    }
    .entry-metadata {
        margin-bottom: 15px;
        border-left: 3px solid #ccc;
        padding-left: 10px;
    }
    .entry-content {
        line-height: 1.6;
        border-left: 3px solid #f0f0f0;
        padding-left: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .media-container {
        background-color: #f9f9f9;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .thumbnail-container img {
        transition: transform 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .thumbnail-container img:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .video-link {
        display: block;
        margin-bottom: 10px;
        padding: 10px;
        background-color: #f0f8ff;
        border-radius: 4px;
        text-decoration: none;
        color: #0366d6;
        border: 1px solid #c8e1ff;
        transition: background-color 0.2s ease;
    }
    .video-link:hover {
        background-color: #e1f0ff;
    }
    .media-links-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .error-box {
        background-color: #ffebee;
        color: #b71c1c;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 5px solid #f44336;
    }
    .warning-box {
        background-color: #fff8e1;
        color: #ff6f00;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 5px solid #ffa000;
    }
    .info-box {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 5px solid #2196f3;
    }
    .data-date-info {
        font-weight: bold;
        color: #1976d2;
        font-size: 0.9rem;
        margin-bottom: 15px;
        background-color: #f0f7ff;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 4px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_parquet_data():
    """
    Load data from the latest parquet file in the 'data' folder
    
    Returns:
    --------
    pandas.DataFrame, str
        DataFrame containing the mention data and the data date
    """
    try:
        # Find all CR_daily files in the data directory
        data_files = glob.glob('data/CR_daily_*.parquet')
        
        if not data_files:
            st.error("No CR_daily files found in the 'data' directory.")
            return None, None, None
            
        # Get the most recent file
        latest_file = max(data_files, key=os.path.getctime)
        
        # Extract date from filename (assuming format CR_daily_YYYY-MM-DD_HH.parquet)
        date_match = re.search(r'CR_daily_(\d{4}-\d{2}-\d{2})(?:_(\d{2}))?\.parquet', latest_file)
        
        # Get file modification time for more precise timestamp
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
        
        if date_match:
            data_date = date_match.group(1)
            hour = date_match.group(2) if date_match.group(2) else file_mod_time.strftime('%H')
            
            # Create a full timestamp using file modification time for minutes and seconds
            last_updated = f"{data_date} {hour}:{file_mod_time.strftime('%M:%S')}"
            
            # Save both the date and the full timestamp
            formatted_date = datetime.strptime(data_date, '%Y-%m-%d').strftime('%B %d, %Y')
        else:
            # Use file modification time if no date in filename
            data_date = file_mod_time.strftime('%Y-%m-%d')
            last_updated = file_mod_time.strftime('%Y-%m-%d %H:%M:%S')
            formatted_date = file_mod_time.strftime('%B %d, %Y')
         
        # Load the parquet file with a spinner for better UX
        with st.spinner(f"Loading video feed data from {formatted_date}..."):
            df = pd.read_parquet(latest_file)
            st.success(f"✅ Successfully loaded {len(df)} records from {formatted_date}.")
            return df, data_date, last_updated
            
    except Exception as e:
        st.error(f"Error loading parquet file: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        return None, None

def detect_media_fields(df):
    """
    Dynamically detect media-related fields in the dataframe
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the mention data
        
    Returns:
    --------
    tuple
        (thumbnail_fields, video_fields) - Lists of field names for thumbnails and videos
    """
    # Initialize empty lists
    thumbnail_fields = []
    video_fields = []
    
    # Check all columns to identify potential media fields
    for col in df.columns:
        col_lower = col.lower()
        
        # Check for thumbnail fields
        if 'thumbnail' in col_lower or ('image' in col_lower and 'url' in col_lower):
            # Verify that at least one non-null value is a URL
            if df[col].notna().any():
                sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else ''
                if isinstance(sample, str) and (sample.startswith('http://') or sample.startswith('https://')):
                    thumbnail_fields.append(col)
        
        # Check for video/media fields
        if (('media' in col_lower or 'video' in col_lower) and 'url' in col_lower) or \
           ('legacy_media' == col_lower) or ('media' == col_lower):
            # Verify that at least one non-null value is a URL
            if df[col].notna().any():
                sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else ''
                if isinstance(sample, str) and (sample.startswith('http://') or sample.startswith('https://')):
                    video_fields.append(col)
    
    # Add common known fields if they weren't detected but exist in the dataframe
    known_thumbnail_fields = ['thumbnailUrl', 'thumbnail']
    known_video_fields = ['media_url', 'media_url_no_highlight', 'relative_media_url', 'legacy_media', 'media']
    
    for field in known_thumbnail_fields:
        if field in df.columns and field not in thumbnail_fields:
            thumbnail_fields.append(field)
    
    for field in known_video_fields:
        if field in df.columns and field not in video_fields:
            video_fields.append(field)
    
    # Log the detected fields
    st.session_state['thumbnail_fields'] = thumbnail_fields
    st.session_state['video_fields'] = video_fields
    
    return thumbnail_fields, video_fields

def highlight_text(text, keywords=HIGHLIGHT_KEYWORDS):
    """
    Highlight specified keywords in text
    
    Parameters:
    -----------
    text : str
        Text to highlight
    keywords : list
        List of keywords to highlight
        
    Returns:
    --------
    str
        Text with highlighted keywords
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Escape any HTML in the original text
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # Create a regex pattern for all keywords (case insensitive)
    pattern = r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')'
    
    # Replace all occurrences with highlighted spans
    highlighted = re.sub(pattern, r'<span class="highlight">\1</span>', text, flags=re.IGNORECASE)
    
    return highlighted

def display_detailed_entries(df, num_entries=30, keywords=HIGHLIGHT_KEYWORDS, data_date=None):
    """
    Display detailed information for the most recent entries
    in collapsible markdown format with highlighted keywords,
    embedded thumbnails, and video links
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the mention data
    num_entries : int
        Number of entries to display (default: 30)
    keywords : list
        List of keywords to highlight
    data_date : str
        Date of the data being displayed
    """
    date_display = f" ({data_date})" if data_date else ""
    st.header(f"Latest Entries{date_display}")
    
    # Add keyword customization
    with st.expander("Customize Highlighted Keywords"):
        # Convert list to string for editing
        keywords_str = st.text_area(
            "Enter keywords to highlight (one per line)",
            "\n".join(keywords),
            height=150
        )
        
        # Update keywords from text area
        custom_keywords = [k.strip() for k in keywords_str.split("\n") if k.strip()]
        
        if st.button("Update Highlighting"):
            keywords = custom_keywords
            st.success(f"Updated {len(keywords)} keywords for highlighting")
    
    # Ensure we have a timestamp or time column for sorting
    sort_col = 'timestamp' if 'timestamp' in df.columns else 'time' if 'time' in df.columns else None
    
    if sort_col:
        # Sort by timestamp/time in descending order
        try:
            if sort_col == 'timestamp' and df[sort_col].dtype == 'object':
                # Try to convert to datetime if it's a string
                df['datetime'] = pd.to_datetime(df[sort_col], format='%Y%m%d%H%M%S', errors='coerce')
                sorted_df = df.sort_values(by='datetime', ascending=False)
            else:
                sorted_df = df.sort_values(by=sort_col, ascending=False)
        except Exception as e:
            st.warning(f"Could not sort by {sort_col}: {e}")
            sorted_df = df
    else:
        # If no timestamp/time column, use the dataframe as is
        sorted_df = df
    
    # Get the most recent entries
    recent_entries = sorted_df.head(num_entries)
    
    # Get media fields from session state
    thumbnail_fields = st.session_state.get('thumbnail_fields', [])
    video_fields = st.session_state.get('video_fields', [])
    
    # If media fields aren't in session state, detect them
    if not thumbnail_fields or not video_fields:
        thumbnail_fields, video_fields = detect_media_fields(df)
    
    # Display each entry in a collapsible section
    for i, (_, entry) in enumerate(recent_entries.iterrows()):
        # Get title for the expander
        title = entry.get('title', f'Entry {i+1}')
        
        # Create expander with title
        with st.expander(f"{title}"):
            # Create columns for layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Format entry details as markdown
                st.markdown(f"### {title}")
                
                # Channel and time info in a styled container
                st.markdown('<div class="entry-metadata">', unsafe_allow_html=True)
                
                channel = entry.get('channel_name', 'Unknown Channel')
                time = entry.get('time', 'Unknown Time')
                st.markdown(f"**Channel:** {channel}  \n**Time:** {time}")
                
                # Additional metadata
                if 'market_name' in entry and pd.notna(entry['market_name']):
                    st.markdown(f"**Market:** {entry['market_name']}")
                
                if 'program_type' in entry and pd.notna(entry['program_type']):
                    st.markdown(f"**Program Type:** {entry['program_type']}")
                
                # Sentiment with color coding
                if 'sentiment' in entry and pd.notna(entry['sentiment']):
                    sentiment = float(entry['sentiment'])
                    sentiment_class = "sentiment-positive" if sentiment > 0.2 else "sentiment-negative" if sentiment < -0.2 else "sentiment-neutral"
                    st.markdown(f"**Sentiment:** <span class='{sentiment_class}'>{sentiment:.2f}</span>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Content/text with highlighting
                if 'text' in entry and pd.notna(entry['text']):
                    st.markdown("### Content")
                    
                    # Apply highlighting to the text
                    highlighted_text = highlight_text(entry['text'], keywords)
                    
                    # Display the highlighted text
                    st.markdown(f'<div class="entry-content">{highlighted_text}</div>', unsafe_allow_html=True)
            
            with col2:
                # Thumbnail section
                st.markdown("### Media")
                
                # Find and display thumbnail
                thumbnail_url = None
                for field in thumbnail_fields:
                    if field in entry and pd.notna(entry[field]):
                        thumbnail_url = entry[field]
                        break
                
                if thumbnail_url:
                    st.image(thumbnail_url, caption="Thumbnail", use_container_width=True)
                else:
                    st.markdown("*No thumbnail available*")
                
                # Video links section
                st.markdown("### Video Links")
                
                # Check for all possible media/video URL fields
                media_links = []
                
                # Create descriptive labels for different video types
                video_type_labels = {
                    'media_url': 'Direct Video',
                    'media': 'Stream',
                    'media_url_no_highlight': 'Clean Video',
                    'legacy_media': 'Legacy Format',
                    'relative_media_url': 'Relative Path'
                }
                
                # Find all available video links
                for field in video_fields:
                    if field in entry and pd.notna(entry[field]):
                        label = video_type_labels.get(field, field.replace('_', ' ').title())
                        media_links.append((label, entry[field]))
                
                if media_links:
                    for label, url in media_links:
                        st.markdown(f"[{label}]({url})")
                else:
                    st.markdown("*No video links available*")
                
                # Direct link to CriticalMention
                if 'uuid' in entry and pd.notna(entry['uuid']):
                    st.markdown("### Direct Link")
                    uuid = entry['uuid']
                    cm_link = f"https://app.criticalmention.com/app/#/report/{uuid}/clip/search"
                    st.markdown(f"[View in CriticalMention]({cm_link})")
            
            # Additional details in a new row
            st.markdown("### Additional Details")
            detail_cols = ['uuid', 'author', 'audience', 'affiliate', 'market_country']
            details = []
            
            for col in detail_cols:
                if col in entry and pd.notna(entry[col]):
                    details.append(f"**{col.replace('_', ' ').title()}:** {entry[col]}")
            
            if details:
                st.markdown("\n".join(details))
            else:
                st.markdown("No additional details available.")

def display_data_stats(df, data_date=None):
    """
    Display basic statistics about the loaded data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the mention data
    data_date : str
        Date of the data being displayed
    """
    if df.empty:
        st.warning("No data available to display.")
        return
    
    date_display = f" ({data_date})" if data_date else ""
    st.header(f"Video Feed Data Overview{date_display}")
    
    # Create metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Mentions", f"{len(df):,}")
    
    with col2:
        # Count unique channels
        if 'channelName' in df.columns:
            channel_count = df['channelName'].nunique()
            st.metric("Unique Channels", f"{channel_count:,}")
        elif 'channel_name' in df.columns:
            channel_count = df['channel_name'].nunique()
            st.metric("Unique Channels", f"{channel_count:,}")
    
    with col3:
        # Count text mentions of keywords
        if 'text' in df.columns:
            keyword_pattern = '|'.join(HIGHLIGHT_KEYWORDS)
            keyword_mentions = df['text'].str.contains(keyword_pattern, case=False, na=False).sum()
            st.metric("Keyword Mentions", f"{keyword_mentions:,}")
    
    with col4:
        # Average sentiment if available
        if 'sentiment' in df.columns:
            avg_sentiment = df['sentiment'].mean()
            st.metric("Avg. Sentiment", f"{avg_sentiment:.2f}")

# Main function
def main():
    # Check for premier access login using the shared access_control module
    if not login_ui():
        # If not authenticated, stop execution here
        return
    
    # Main app title
    st.title("📊 Video Feeds Monitor")
    
    # Set default number of detailed entries
    num_detailed = 20
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Premier access settings (admin section)
        admin_settings_ui()
        
        # Add filtering options
        st.header("Filter Data")
        
        # Only show if data is loaded
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            
            # Date range filter if time column exists
            if 'time' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['time'])
                    min_date = df['date'].min().date()
                    max_date = df['date'].max().date()
                    
                    st.subheader("Date Range")
                    start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
                    end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
                    
                    # Apply date filter
                    if start_date and end_date:
                        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
                        st.session_state.filtered_df = df[mask]
                        st.success(f"Showing {len(st.session_state.filtered_df)} of {len(df)} records")
                    else:
                        st.session_state.filtered_df = df
                except Exception as e:
                    st.warning(f"Error setting up date filter: {e}")
            
            # Channel filter
            channel_col = 'channelName' if 'channelName' in df.columns else 'channel_name' if 'channel_name' in df.columns else None
            if channel_col:
                st.subheader("Channel Filter")
                
                # Get unique channels
                channels = sorted(df[channel_col].unique())
                
                # Multi-select for channels
                selected_channels = st.multiselect("Select Channels", channels)
                
                # Apply channel filter if any selected
                if selected_channels:
                    if 'filtered_df' in st.session_state:
                        st.session_state.filtered_df = st.session_state.filtered_df[
                            st.session_state.filtered_df[channel_col].isin(selected_channels)
                        ]
                    else:
                        st.session_state.filtered_df = df[df[channel_col].isin(selected_channels)]
                    
                    st.success(f"Showing {len(st.session_state.filtered_df)} of {len(df)} records")
            
            # Reset filters button
            if st.button("Reset Filters"):
                st.session_state.filtered_df = df
                st.success("Filters reset")
    
    # Main content
    # Automatically load data after login
    if 'df' not in st.session_state:
        df, data_date, last_updated = load_parquet_data()
        
        if df is not None:
            # Store in session state
            st.session_state.df = df
            st.session_state.data_date = data_date
            st.session_state.last_updated = last_updated
            st.session_state.num_detailed = num_detailed
    
    # Get the data and date from session state
    df = st.session_state.get('df')
    data_date = st.session_state.get('data_date')
    last_updated = st.session_state.get('last_updated')
    
    # Display data date at the top of the main content area
    if data_date:
        formatted_date = datetime.strptime(data_date, '%Y-%m-%d').strftime('%B %d, %Y')
        
        # Display the exact timestamp in the requested format
        st.markdown(f'<div class="data-date-info">📊 Data loaded from local files | Last updated: {last_updated}</div>', 
                   unsafe_allow_html=True)
    
    # Display overview stats
    if df is not None:
        # Use filtered dataframe if it exists, otherwise use the original
        if 'filtered_df' in st.session_state:
            display_df = st.session_state.filtered_df
        else:
            display_df = df
            # Initialize filtered_df
            st.session_state.filtered_df = df
        
        # Show data stats
        display_data_stats(display_df, data_date)
        
        num_detailed = st.session_state.get('num_detailed', 30)
        
        # Display tabs
        tabs = st.tabs(["Data Table", "Media Analysis", "Sentiment Analysis", "Channel Analysis", "Download"])
        
        # Data Table tab
        with tabs[0]:
            st.subheader(f"Data Table{' (' + formatted_date + ')' if data_date else ''}")
            st.dataframe(display_df)
        
        # Media Analysis tab 
        with tabs[1]:
            st.subheader(f"Media Coverage Timeline{' (' + formatted_date + ')' if data_date else ''}")
            
            # Convert timestamp to datetime if needed
            if 'time' in display_df.columns:
                # Try to ensure we have a datetime column
                try:
                    if 'date' not in display_df.columns:
                        display_df['date'] = pd.to_datetime(display_df['time'])
                    
                    # Use pandas to resample and count by day
                    df_by_date = display_df.groupby(display_df['date'].dt.date).size().reset_index(name='count')
                    df_by_date.columns = ['date', 'mentions']
                    
                    # Create bar chart with Plotly
                    fig = px.bar(df_by_date, x='date', y='mentions', 
                                 title=f'Media Mentions by Date{" (" + formatted_date + ")" if data_date else ""}',
                                 labels={'date': 'Date', 'mentions': 'Number of Mentions'},
                                 template='plotly_white')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Distribution by hour
                    st.subheader("Mentions by Hour of Day")
                    hour_counts = display_df.groupby(display_df['date'].dt.hour).size().reset_index(name='count')
                    hour_counts.columns = ['hour', 'mentions']
                    
                    fig = px.bar(hour_counts, x='hour', y='mentions',
                                 title='Media Mentions by Hour of Day',
                                 labels={'hour': 'Hour of Day', 'mentions': 'Number of Mentions'},
                                 template='plotly_white')
                    fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating media analysis charts: {e}")
        
        # Sentiment Analysis tab
        with tabs[2]:
            st.subheader(f"Sentiment Analysis{' (' + formatted_date + ')' if data_date else ''}")
            
            if 'sentiment' in display_df.columns:
                try:
                    # Average sentiment by channel
                    st.subheader("Average Sentiment by Channel")
                    channel_col = 'channelName' if 'channelName' in display_df.columns else 'channel_name'
                    
                    if channel_col in display_df.columns:
                        sentiment_by_channel = display_df.groupby(channel_col)['sentiment'].mean().sort_values(ascending=False).reset_index()
                        sentiment_by_channel.columns = ['Channel', 'Average Sentiment']
                        
                        # Only show top 15 channels
                        top_channels = sentiment_by_channel.head(15)
                        
                        # Create horizontal bar chart with Plotly
                        fig = px.bar(top_channels, 
                                     x='Average Sentiment', 
                                     y='Channel',
                                     orientation='h',
                                     title='Average Sentiment by Channel',
                                     color='Average Sentiment',
                                     color_continuous_scale='RdBu',
                                     template='plotly_white')
                        
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Sentiment distribution
                    st.subheader("Sentiment Distribution")
                    
                    # Create sentiment categories
                    display_df['sentiment_category'] = pd.cut(
                        display_df['sentiment'],
                        bins=[-1, -0.3, 0.3, 1],
                        labels=['Negative', 'Neutral', 'Positive']
                    )
                    
                    sentiment_counts = display_df['sentiment_category'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']
                    
                    # Create a pie chart with Plotly
                    fig = px.pie(sentiment_counts, 
                                 values='Count', 
                                 names='Sentiment',
                                 title='Sentiment Distribution',
                                 color='Sentiment',
                                 color_discrete_map={'Positive':'green', 'Neutral':'gray', 'Negative':'red'},
                                 template='plotly_white')
                    
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add a histogram of sentiment values
                    st.subheader("Sentiment Value Distribution")
                    fig = px.histogram(display_df, 
                                      x='sentiment',
                                      nbins=20,
                                      title='Distribution of Sentiment Values',
                                      labels={'sentiment': 'Sentiment Score'},
                                      template='plotly_white')
                    
                    fig.update_layout(bargap=0.1)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating sentiment analysis charts: {e}")
            else:
                st.warning("No sentiment data available in the dataset.")
        
        # Channel Analysis tab
        with tabs[3]:
            st.subheader(f"Channel Analysis{' (' + formatted_date + ')' if data_date else ''}")
            
            channel_col = 'channelName' if 'channelName' in display_df.columns else 'channel_name' if 'channel_name' in display_df.columns else None
            
            if channel_col:
                try:
                    # Distribution by channel
                    st.subheader("Mentions by Channel")
                    channel_counts = display_df[channel_col].value_counts().reset_index().head(10)
                    channel_counts.columns = ['Channel', 'Mentions']
                    
                    # Create horizontal bar chart with Plotly
                    fig = px.bar(channel_counts, 
                                 x='Mentions', 
                                 y='Channel',
                                 orientation='h',
                                 title='Top 10 Channels by Mention Count',
                                 color='Mentions',
                                 color_continuous_scale='Viridis',
                                 template='plotly_white')
                    
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating channel analysis charts: {e}")
            
            # Distribution by market
            if 'market_name' in display_df.columns:
                try:
                    st.subheader("Mentions by Market")
                    market_counts = display_df['market_name'].value_counts().reset_index().head(10)
                    market_counts.columns = ['Market', 'Mentions']
                    
                    # Create horizontal bar chart with Plotly
                    fig = px.bar(market_counts, 
                                 x='Mentions', 
                                 y='Market',
                                 orientation='h',
                                 title='Top 10 Markets by Mention Count',
                                 color='Mentions',
                                 color_continuous_scale='Viridis',
                                 template='plotly_white')
                    
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating market analysis charts: {e}")
            
            # Distribution by country
            if 'market_country' in display_df.columns:
                try:
                    st.subheader("Mentions by Country")
                    country_counts = display_df['market_country'].value_counts().reset_index()
                    country_counts.columns = ['Country', 'Mentions']
                    
                    # Create pie chart with Plotly
                    fig = px.pie(country_counts, 
                                 values='Mentions', 
                                 names='Country',
                                 title='Distribution of Mentions by Country',
                                 template='plotly_white')
                    
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating country analysis charts: {e}")
            
            # Keyword frequency analysis
            if 'text' in display_df.columns:
                try:
                    st.subheader("Keyword Frequency Analysis")
                    
                    # Process text to get most common words
                    from collections import Counter
                    import re
                    
                    # Combine all text
                    all_text = ' '.join(display_df['text'].dropna().astype(str).tolist())
                    
                    # Clean text (remove punctuation, convert to lowercase)
                    cleaned_text = re.sub(r'[^\w\s]', '', all_text.lower())
                    
                    # Split into words
                    words = cleaned_text.split()
                    
                    # Remove common English stopwords
                    stopwords = ['the', 'and', 'to', 'of', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 
                                'this', 'with', 'i', 'you', 'it', 'not', 'or', 'be', 'are', 'from',
                                'at', 'as', 'your', 'have', 'more', 'an', 'was', 'we', 'will', 'can',
                                'all', 'has', 'who', 'they', 'what', 'their', 'there', 'if', 'but',
                                'about', 'which', 'when', 'one', 'would', 'so', 'up', 'out', 'like',
                                'time', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'get',
                                'some', 'than']
                    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
                    
                    # Count words
                    word_counts = Counter(filtered_words).most_common(15)
                    
                    # Create DataFrame
                    word_df = pd.DataFrame(word_counts, columns=['Word', 'Count'])
                    
                    # Create horizontal bar chart with Plotly
                    fig = px.bar(word_df,
                                 x='Count',
                                 y='Word',
                                 orientation='h',
                                 title='Most Frequent Words in Mentions',
                                 color='Count',
                                 color_continuous_scale='Viridis',
                                 template='plotly_white')
                    
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating keyword frequency analysis: {e}")
        
        # Download tab
        with tabs[4]:
            st.subheader(f"Download Data{' (' + formatted_date + ')' if data_date else ''}")
            
            # Add a note about the data date
            if data_date:
                st.markdown(f"💡 **Note:** This data is from **{formatted_date}**.")
            
            # CSV download
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"video_feed_data_{data_date if data_date else datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Excel download
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    display_df.to_excel(writer, index=False, sheet_name='Mentions')
                
                excel_data = buffer.getvalue()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"video_feed_data_{data_date if data_date else datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Excel download not available: {e}")
        
        # Display detailed entries section with highlighting and media
        display_detailed_entries(display_df, num_detailed, HIGHLIGHT_KEYWORDS, data_date)
    else:
        st.error("No data available. Please check that the data files exist in the 'data' directory.")

if __name__ == "__main__":
    main()

# Render footer component
render_footer()