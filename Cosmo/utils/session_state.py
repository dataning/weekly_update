"""
Session state management utilities for the Gravity app
"""
import streamlit as st
from datetime import datetime

def initialize_session_state():
    """Initialize all session state variables needed across the application"""
    # Main data storage
    if "news_df" not in st.session_state:
        st.session_state.news_df = None
    if "filtered_news_df" not in st.session_state:
        st.session_state.filtered_news_df = None
    if "selected_news_df" not in st.session_state:
        st.session_state.selected_news_df = None
    if "tagged_news_df" not in st.session_state:
        st.session_state.tagged_news_df = None
        
    # Newsletter configuration
    if "last_config" not in st.session_state:
        st.session_state.last_config = {
            'color_theme': None,
            'banner_selection': None,
            'content_width': None,
            'mobile_friendly': None,
            'preview_text': None,
            'summary_html': None,
            'image_html': None,
            'banner_text': {}
        }
        
    # Newsletter generator state
    if "needs_update" not in st.session_state:
        st.session_state.needs_update = True
    if "newsletter_error" not in st.session_state:
        st.session_state.newsletter_error = False
    if "preview_updating" not in st.session_state:
        st.session_state.preview_updating = False
    if "newsletter_html" not in st.session_state:
        st.session_state.newsletter_html = ""
    if "output_path" not in st.session_state:
        st.session_state.output_path = ""
        
    # Content elements
    if "summary_html" not in st.session_state:
        st.session_state.summary_html = ""
    if "image_html" not in st.session_state:
        st.session_state.image_html = ""
    
    # Banner text defaults
    if "banner_text" not in st.session_state:
        st.session_state.banner_text = {
            'corporate_top': 'BlackRock',
            'corporate_middle': 'NEWSLETTER',
            'gips_brand': 'BlackRock',
            'gips_subtitle': 'GIPS Infrastructure',
            'gips_headline': 'Weekly Newsletter',
            'modern_brand': 'BlackRock News',
            'modern_date': datetime.now().strftime('%B %d, %Y'),
            'modern_tagline': 'Your weekly update on market insights',
            'gradient_title': 'Market Insights',
            'gradient_subtitle': 'Weekly Newsletter',
            'gradient_edition': f'Edition #{datetime.now().strftime("%W")} | {datetime.now().strftime("%B %Y")}'
        }
        
    # Email functionality
    if "email_history" not in st.session_state:
        st.session_state.email_history = []

def trigger_update():
    """Trigger update for newsletter preview"""
    st.session_state.needs_update = True
    st.session_state.newsletter_error = False