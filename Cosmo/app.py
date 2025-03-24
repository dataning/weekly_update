"""
Gravity - News Explorer & Newsletter Generator
A comprehensive platform for news monitoring, content analysis, and media distribution
"""
import os
import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
from utils.session_state import initialize_session_state

# Set page configuration
st.set_page_config(
    page_title="Gravity",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure required directories exist
for directory in ["templates/banners", "static/data", "static/css", "temp"]:
    os.makedirs(directory, exist_ok=True)

# Initialize app state
initialize_session_state()

# Custom CSS for dark mode compatibility
st.markdown("""
<style>
    /* Dark mode styles */
    .stApp {
        color: #f0f2f6;
    }
    
    /* Cards styling with dark mode compatibility */
    .feature-card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        background-color: #2a2a2a;
        margin-bottom: 20px;
        height: 100%;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 36px;
        margin-bottom: 10px;
    }
    
    .feature-title {
        font-size: 22px;
        font-weight: 600;
        color: #80b3ff;
        margin-bottom: 10px;
    }
    
    .feature-desc {
        font-size: 16px;
        color: #d0d0d0;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Render header component
render_header()

# Main homepage content
st.title("Welcome to Gravity")
st.write("Your all-in-one platform for monitoring, analyzing, and distributing media and news content across diverse channels.")

# Feature overview section
st.header("Our Platform Features")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">News Search</div>
        <div class="feature-desc">
            Access real-time news about your target entities across thousands of global publications.
            Filter by company, industry, region, and timeframe to discover relevant content instantly.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to News Search", key="home_news_search", use_container_width=True):
        st.switch_page("pages/01_news_search.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📰</div>
        <div class="feature-title">Newsletter Generator</div>
        <div class="feature-desc">
            Transform curated news into polished, professional newsletters with just a few clicks.
            Customize templates, incorporate AI-generated summaries, and export ready-to-send HTML emails.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Newsletter Generator", key="home_newsletter", use_container_width=True):
        st.switch_page("pages/03_newsletter.py")

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📺</div>
        <div class="feature-title">Video Feeds</div>
        <div class="feature-desc">
            Monitor video content from major media outlets, industry channels, and streaming platforms.
            Track mentions, analyze sentiment, and capture key moments for comprehensive media intelligence.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Video Feeds", key="home_video_feeds", use_container_width=True):
        st.switch_page("pages/04_Video_Feeds.py")

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📱</div>
        <div class="feature-title">Social Media</div>
        <div class="feature-desc">
            Track conversations about your entity across all major social platforms in one unified dashboard.
            Measure engagement, identify trends, and respond to opportunities in real-time.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Social Media Feeds", key="home_social_media", use_container_width=True):
        st.switch_page("pages/05_Social_Media.py")

# Getting started section
st.subheader("Getting Started")
st.markdown("""
New to the platform? Here's how to make the most of Gravity:
1. **Explore News Search** to discover relevant articles about your target companies or topics
2. **Save and organize content** into custom collections for easy reference and collaboration
3. **Generate professional newsletters** to distribute insights to stakeholders and clients
4. **Set up automated monitoring** for continuous intelligence on your key topics
5. **Integrate media feeds** from news, video, and social sources for comprehensive coverage
""")

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()