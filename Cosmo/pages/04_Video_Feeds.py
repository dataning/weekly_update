"""
Enhanced Streamlit Video Feeds Monitor with Premier Access Code
---------------------------------------
A Streamlit app that retrieves data from CriticalMention
without keywords and displays the complete dataframe. Includes
collapsible detailed views with text highlighting for important keywords.
Now with embedded thumbnails, video links, premier access control,
and proxy support.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import re
import traceback
from io import BytesIO
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

# Import shared access control module
from services.access_control import (
    initialize_session_state, login_ui, admin_settings_ui,
    load_config, save_config, get_auth_cookie, token_management_ui,
    token_info_ui, view_token_history_ui
)

# Import the CriticalMention client
from services.cr_service import CriticalMentionClient

# Constants
CONFIG_FILE = "config.json"
# Keywords to highlight in the text
HIGHLIGHT_KEYWORDS = [
    "blackrock", "larry fink", "fink"
]

# Set page configuration
st.set_page_config(
    page_title="Video Feeds Monitor",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for authentication
initialize_session_state()

# Render header
render_header()

# Pre-load configuration
config = load_config()
if not config or "premier_access" not in config:
    st.error("Error: Missing premier access configuration in config.json")
    st.stop()

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
    .cookie-instruction-img {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 5px;
        max-width: 100%;
    }
    .token-info {
        background-color: #f8f9fa;
        border-left: 3px solid #4CAF50;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 4px 4px 0;
    }
    /* Media display styles */
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
    /* Auth method tabs */
    .auth-method-tabs {
        display: flex;
        border-bottom: 1px solid #ccc;
        margin-bottom: 15px;
    }
    .auth-method-tab {
        padding: 10px 15px;
        cursor: pointer;
        border: 1px solid transparent;
        border-bottom: none;
        margin-right: 5px;
        border-radius: 5px 5px 0 0;
        background-color: #f8f9fa;
    }
    .auth-method-tab.active {
        background-color: white;
        border-color: #ccc;
        border-bottom-color: white;
        margin-bottom: -1px;
    }
</style>
""", unsafe_allow_html=True)

def verify_config():
    """Verify the configuration file has the necessary settings"""
    config = load_config()
    missing_sections = []
    
    # Check required sections
    required_sections = ["criticalmention", "premier_access"]
    for section in required_sections:
        if section not in config:
            missing_sections.append(section)
    
    if missing_sections:
        st.error(f"Missing required config sections: {', '.join(missing_sections)}")
        return False
    
    # Check premier access settings
    premier = config.get("premier_access", {})
    if "access_code" not in premier and "code_hash" not in premier:
        st.error("No access code found in premier_access section")
        return False
    
    # Check for credentials
    if "default_token" not in config.get("criticalmention", {}):
        st.warning("CriticalMention token not configured")
        return False
    
    # All checks passed
    st.success("Configuration verified successfully!")
    return True

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

def fetch_all_mentions(days_back=7, limit=500, use_proxy=False):
    """
    Fetch all mentions from the past X days without any keyword filtering
    with improved error handling and proxy support
    
    Parameters:
    -----------
    days_back : int
        Number of days to look back (default: 7)
    limit : int
        Maximum number of results to return (default: 500)
    use_proxy : bool, default False
        Whether to use a proxy for API requests
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing all mention data
    """
    # Get auth cookie
    auth_cookie = get_auth_cookie()
    
    if not auth_cookie:
        st.error("Error: No authentication token found in config.json")
        return None
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates for API
    start_str = start_date.strftime("%Y-%m-%d 00:00:00")
    end_str = end_date.strftime("%Y-%m-%d 23:59:59")
    
    # Try a smaller date range if you're having issues
    # start_str = end_date.strftime("%Y-%m-%d 00:00:00")  # Just today
    
    st.info(f"Searching from {start_str} to {end_str}")
    
    # Log proxy usage
    if use_proxy:
        st.info("Using proxy: http://webproxy.blackrock.com:8080")
    
    with st.spinner(f"Fetching mentions from {start_str} to {end_str}..."):
        try:
            # Initialize client with proxy setting
            client = CriticalMentionClient(auth_cookie, use_proxy=use_proxy)
            
            # Fetch mentions without keywords
            st.info("Calling API to fetch mentions...")
            mentions = client.fetch_mentions(start_str, end_str, limit)
            
            if not mentions:
                st.error("API returned empty or null response")
                return None
                
            if isinstance(mentions, list):
                st.success(f"Retrieved {len(mentions)} mentions")
                
                # Convert to DataFrame
                st.info("Converting to DataFrame...")
                df = client.to_dataframe()
                
                if df is None or df.empty:
                    st.warning("Conversion to DataFrame resulted in empty data")
                    return None
                
                # Detect media fields
                thumbnail_fields, video_fields = detect_media_fields(df)
                
                # Log detected fields
                st.info(f"Detected {len(thumbnail_fields)} thumbnail fields and {len(video_fields)} video fields")
                
                return df
            else:
                st.error(f"Unexpected response type: {type(mentions)}")
                return None
        except Exception as e:
            st.error(f"Error fetching mentions: {str(e)}")
            st.code(traceback.format_exc(), language="python")
            return None

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

def display_detailed_entries(df, num_entries=30, keywords=HIGHLIGHT_KEYWORDS):
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
    """
    st.header("Latest Entries")
    
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
                    st.image(thumbnail_url, caption="Thumbnail", use_column_width=True)
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

# Main function
def main():
    # Check for premier access login using the shared access_control module
    if not login_ui():
        # If not authenticated, stop execution here
        return
    
    # Main app title
    st.title("📊 Video Feeds Monitor")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Add config verification button
        if st.button("Verify Configuration"):
            verify_config()
        
        # Premier access settings (admin section) using the shared access_control module
        admin_settings_ui()
        
        # Authentication section
        st.header("Authentication")
        
        # Check for auth cookie
        auth_cookie = get_auth_cookie()
        if auth_cookie:
            st.success("Authentication token found in config.json")
            # Display token information
            token_info_ui()
            
            # Add a button to refresh/update token
            if st.button("Update Authentication Token"):
                st.session_state.show_token_management = True
        else:
            st.error("No authentication token found in config.json")
            # Always show token updater if no token exists
            st.session_state.show_token_management = True
        
        # Show token management UI if needed
        if st.session_state.get('show_token_management', False):
            with st.expander("🔑 Authentication Management", expanded=True):
                # Use a unique suffix for sidebar token management
                token_management_ui("sidebar")
        
        # Display token history if available
        config = load_config()
        if "criticalmention" in config and "token_history" in config["criticalmention"] and config["criticalmention"]["token_history"]:
            view_token_history_ui()
        
        # Data retrieval options
        st.header("Data Retrieval Options")
        
        days_back = st.slider(
            "Days to look back",
            min_value=1,
            max_value=90,
            value=7,  # Reduced default to 7 days to avoid large queries
            help="Number of days to fetch data from"
        )
        
        result_limit = st.slider(
            "Maximum results",
            min_value=10,
            max_value=1000,
            value=100,  # Reduced default to 100 to avoid large queries
            step=10,
            help="Maximum number of results to fetch"
        )
        
        # Number of detailed entries to show
        num_detailed = st.slider(
            "Detailed entries to show",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Number of recent entries to show in detailed view"
        )
        
        # Add proxy option
        use_proxy = st.checkbox(
            "BLK N@twork",
            value=True,
            help="Use BLK N@twork for API requests"
        )
        
        # if use_proxy:
        #     st.info("Using proxy: http://webproxy.blackrock.com:8080")
    
    # Main content
    st.header("Data Retrieval")
    
    # Check for authentication issues and display token updater in main content area if needed
    auth_cookie = get_auth_cookie()
    if not auth_cookie:
        st.markdown("""
        <div class="error-box">
            <h3>🔑 Authentication Error</h3>
            <p>No CriticalMention token found. Please update your authentication token to continue.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔄 Update CriticalMention Authentication", expanded=True):
            token_management_ui("main")
        return
        
    # Add a test connection button
    if st.button("Test Connection", type="primary"):
        # Try with a small date range and limit
        with st.spinner("Testing connection to CriticalMention..."):
            try:
                # Initialize client with proxy setting
                client = CriticalMentionClient(auth_cookie, use_proxy=use_proxy)
                
                # Get today's date
                today = datetime.now()
                start_str = today.strftime("%Y-%m-%d 00:00:00")
                end_str = today.strftime("%Y-%m-%d 23:59:59")
                
                # Try a minimal fetch
                st.info(f"Testing API connection with date range: {start_str} to {end_str}")
                test_result = client.fetch_mentions(start_str, end_str, 5)
                
                if test_result:
                    st.success(f"✅ Connection successful! Found {len(test_result)} mentions today.")
                else:
                    st.warning("Connection successful but no mentions found today.")
            except Exception as e:
                # Display authentication error message
                st.markdown(f"""
                <div class="error-box">
                    <h3>❌ Authentication Failed</h3>
                    <p>Your CriticalMention authentication token appears to be expired or invalid.</p>
                    <p>Error: {str(e)}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show token updater with a unique key suffix
                with st.expander("🔄 Update CriticalMention Authentication", expanded=True):
                    token_management_ui("test_conn")
    
    # Fetch data button
    if st.button("Fetch Data (No Keywords)", type="primary"):
        # Fetch all mentions with proxy option
        df = fetch_all_mentions(days_back=days_back, limit=result_limit, use_proxy=use_proxy)
        
        if df is not None:
            # Store in session state
            st.session_state.df = df
            st.session_state.num_detailed = num_detailed
        else:
            # If fetch failed, show token updater
            st.markdown("""
            <div class="error-box">
                <h3>⚠️ Data Fetch Failed</h3>
                <p>Failed to fetch data from CriticalMention. Your authentication token may be expired.</p>
                <p>Please update your token below.</p>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("🔄 Update CriticalMention Authentication", expanded=True):
                token_management_ui("fetch_failed")
    
    # Display results
    if 'df' in st.session_state and st.session_state.df is not None:
        df = st.session_state.df
        num_detailed = st.session_state.get('num_detailed', 30)
        
        # Display tabs
        tabs = st.tabs(["Data Table", "Column Information", "Download"])
        
        # Data Table tab
        with tabs[0]:
            st.subheader("Data Table")
            st.dataframe(df)
        
        # Column Information tab 
        with tabs[1]:
            st.subheader("Column Information")
            
            # Display column information
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Data Type': [str(df[col].dtype) for col in df.columns],
                'Non-Null Count': [df[col].count() for col in df.columns],
                'Null Count': [df[col].isna().sum() for col in df.columns],
                'Sample Values': [str(df[col].dropna().sample(min(3, len(df[col].dropna()))).tolist())[:100] + '...' if len(df[col].dropna()) > 0 else 'No non-null values' for col in df.columns]
            })
            
            st.dataframe(col_info)
            
            # Display media field information
            if 'thumbnail_fields' in st.session_state and 'video_fields' in st.session_state:
                st.subheader("Media Fields Detected")
                
                # Create columns for layout
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Thumbnail Fields")
                    for field in st.session_state['thumbnail_fields']:
                        st.markdown(f"- {field}")
                
                with col2:
                    st.markdown("#### Video Fields")
                    for field in st.session_state['video_fields']:
                        st.markdown(f"- {field}")
        
        # Download tab
        with tabs[2]:
            st.subheader("Download Data")
            
            # CSV download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"criticalmention_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Excel download
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Mentions')
                
                excel_data = buffer.getvalue()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"criticalmention_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Excel download not available: {e}")
        
        # Display detailed entries section with highlighting and media
        display_detailed_entries(df, num_detailed)

if __name__ == "__main__":
    main()

# Render footer component
render_footer()