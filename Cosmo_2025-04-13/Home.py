"""
Gravity - News Explorer & Newsletter Generator
A comprehensive platform for news monitoring, content analysis, and media distribution
"""
import os
import streamlit as st
from components.header import render_header
import theme
from components.ui_helpers import create_info_banner, create_feature_card  # Add this line
from utils.session_state import initialize_session_state
# from utils.data_access import login

# Ensure required directories exist
for directory in ["templates/banners", "static/data", "static/css", "temp"]:
    os.makedirs(directory, exist_ok=True)

if "analytics" in st.query_params and "on" in st.query_params["analytics"]:
    st.subheader('User Stats')
    from utils.user_tracking import UserTracking
    UserTracking.display_analytics()

else:
    
    # Ensure required directories exist
    for directory in ["templates/banners", "static/data", "static/css", "temp"]:
        os.makedirs(directory, exist_ok=True)
        
    # Initialize app state
    initialize_session_state()

    theme.set_page_config()

    theme.apply_full_theme()
    
    # Render header component
    render_header()
    
    # login(stop_run=False)
    
    # Feature overview section
    # st.header("Our Platform Features")
    col1, col2 = st.columns(2)
    
    with col1:
        news_search_clicked = create_feature_card(
            icon="🔍",
            title="News Search",
            description="Access real-time news about your target entities across thousands of global publications. Filter by company, industry, region, and timeframe to discover relevant content instantly.",
            button_text="Go to News Search",
            button_key="home_news_search"
        )
        if news_search_clicked:
            st.switch_page("pages/01_News_Search.py")
    
    with col2:
        newsletter_clicked = create_feature_card(
            icon="📰",
            title="Newsletter Generator",
            description="Transform curated news into polished, professional newsletters with just a few clicks. Customize templates, incorporate AI-generated summaries, and export ready-to-send HTML emails.",
            button_text="Go to Newsletter Generator",
            button_key="home_newsletter"
        )
        if newsletter_clicked:
            st.switch_page("pages/03_Newsletter_Generation.py")
    
    col3, col4 = st.columns(2)
    
    with col3:
        video_clicked = create_feature_card(
            icon="📺",
            title="Video Feeds",
            description="Monitor video content from major media outlets, industry channels, and streaming platforms. Track mentions, analyze sentiment, and capture key moments for comprehensive media intelligence.",
            button_text="Go to Video Feeds",
            button_key="home_video_feeds"
        )
        if video_clicked:
            st.switch_page("pages/04_Video_Feeds.py")
    
    with col4:
        social_clicked = create_feature_card(
            icon="📱",
            title="Social Media",
            description="Track conversations about your entity across all major social platforms in one unified dashboard. Measure engagement, identify trends, and respond to opportunities in real-time.",
            button_text="Go to Social Media Feeds",
            button_key="home_social_media"
        )
        if social_clicked:
            st.switch_page("pages/05_Social_Media.py")
    
    # Render sidebar component
    theme.render_sidebar()
    
    # Render footer component
    theme.render_footer()