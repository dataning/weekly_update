"""
Gravity - News Explorer & Newsletter Generator
Main application entry point for the Streamlit app
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

# Render header component
render_header()

# Main homepage content
st.title("Welcome to Gravity")
st.write("Your all-in-one platform for monitoring, analyzing, and distributing business news.")

# Feature overview section
st.header("Our Platform Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); background-color: white;">
        <div style="font-size: 36px; margin-bottom: 10px;">🔍</div>
        <div style="font-size: 22px; font-weight: 600; color: #1E3A8A; margin-bottom: 10px;">News Search</div>
        <div style="font-size: 16px; color: #4B5563; margin-bottom: 15px;">
            Search for latest news about your target entity across thousands of news outlets. 
            Filter by company, region, publication, and more to find exactly what you need.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to News Search", key="home_news_search", use_container_width=True):
        st.switch_page("pages/01_news_search.py")

with col2:
    st.markdown("""
    <div style="padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); background-color: white;">
        <div style="font-size: 36px; margin-bottom: 10px;">📧</div>
        <div style="font-size: 22px; font-weight: 600; color: #1E3A8A; margin-bottom: 10px;">Newsletter Generator</div>
        <div style="font-size: 16px; color: #4B5563; margin-bottom: 15px;">
            Create beautiful, professional newsletters from your news data. Customize themes, 
            include AI-generated summaries, and export ready-to-send HTML emails.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to Newsletter Generator", key="home_newsletter", use_container_width=True):
        st.switch_page("pages/03_newsletter.py")

# Getting started section
st.subheader("Getting Started")
st.markdown("""
New to the platform? Here's how to get started:

1. **Explore News Search** to find relevant articles about your target companies
2. **Save articles of interest** for later reference and sharing
3. **Generate newsletters** to distribute insights to your team or clients
4. **Set up regular reports** to maintain consistent communication
""")

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()