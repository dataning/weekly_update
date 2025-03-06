import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="Skywalker",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enhance the appearance
st.markdown("""
<style>
    /* Skywalker Branding Header Styles */
    .skywalker-header {
        display: flex;
        align-items: center;
        padding: 30px;
        background: #000000;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
        width: 100%;
        height: 160px;
    }
    
    .stars {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 40px 70px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 50px 160px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 90px 40px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 130px 80px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 160px 120px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0));
    }
    
    .skywalker-icon {
        position: relative;
        width: 60px;
        height: 60px;
        margin-right: 20px;
    }
    
    .icon-circle {
        position: absolute;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%);
        box-shadow: 0 0 20px rgba(255, 235, 59, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .icon-silhouette {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 30px;
        height: 40px;
    }
    
    .skywalker-title {
        font-family: 'Segoe UI', Arial, sans-serif;
        position: relative;
        z-index: 2;
    }
    
    .brand-name {
        color: #ffffff !important;
        font-size: 48px;
        font-weight: 700;
        letter-spacing: 3px;
        margin: 0;
        text-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
    }
            
    .skywalker-brand {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    .tagline {
        color: #ffffff;
        font-size: 18px;
        font-weight: 400;
        margin: 5px 0 0 0;
        letter-spacing: 1px;
    }
    
    /* Light beam effect */
    .light-beam {
        position: absolute;
        width: 150px;
        height: 100%;
        background: linear-gradient(90deg, 
                                  rgba(255, 255, 255, 0) 0%, 
                                  rgba(255, 255, 255, 0.1) 50%, 
                                  rgba(255, 255, 255, 0) 100%);
        transform: skewX(-20deg);
        animation: beam 8s infinite;
        opacity: 0.7;
    }
    
    @keyframes beam {
        0% { left: -150px; }
        30% { left: 100%; }
        100% { left: 100%; }
    }
    
    /* Spaceman styling */
    .spaceman {
        position: absolute;
        height: 80px;
        z-index: 2;
        opacity: 0.9;
        /* Combine multiple animations with slower timing */
        animation: 
            drift-x 40s linear infinite alternate, 
            drift-y 35s ease-in-out infinite alternate,
            spin 60s linear infinite;
        /* Start the spaceman in the middle-right area */
        top: 40px;
        right: 100px;
    }
    
    /* Horizontal drifting across the banner */
    @keyframes drift-x {
        0% { right: 30%; }
        20% { right: 80%; }
        40% { right: 20%; }
        60% { right: 65%; }
        80% { right: 40%; }
        100% { right: 70%; }
    }
    
    /* Vertical drifting */
    @keyframes drift-y {
        0% { top: 20px; }
        15% { top: 70px; }
        30% { top: 40px; }
        45% { top: 90px; }
        60% { top: 30px; }
        75% { top: 60px; }
        100% { top: 50px; }
    }
    
    /* Full rotation, including upside down */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        20% { transform: rotate(180deg); }
        40% { transform: rotate(90deg); }
        60% { transform: rotate(360deg); }
        80% { transform: rotate(270deg); }
        100% { transform: rotate(720deg); }
    }

    /* Original styles */
    .main-header {
        font-size: 42px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: 400;
        color: #64748B;
        margin-top: 0px;
    }
    .feature-card {
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 20px;
        background-color: white;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }
    .feature-icon {
        font-size: 36px;
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 22px;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 10px;
    }
    .feature-description {
        font-size: 16px;
        color: #4B5563;
        margin-bottom: 15px;
    }
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
    .page-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .stats-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stats-number {
        font-size: 28px;
        font-weight: 700;
        color: #1E3A8A;
    }
    .stats-label {
        font-size: 16px;
        color: #64748B;
    }
    .testimonial {
        font-style: italic;
        color: #4B5563;
        padding: 15px;
        border-left: 4px solid #1E3A8A;
        background-color: #F8FAFC;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation and quick links
with st.sidebar:
    st.title("Skywalker")
    st.markdown("---")
    
    # Navigation links
    st.subheader("Navigation")
    
    # Use switch_page for navigation in multi-page app
    if st.button("🔍 News Search", use_container_width=True):
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
            import threading
            
            def switch_page(page_name):
                from streamlit.runtime.scriptrunner import RerunData, RerunException
                from streamlit.source_util import get_pages
                
                def standardize_name(name):
                    return name.lower().replace("_", " ")
                
                page_name = standardize_name(page_name)
                
                pages = get_pages("streamlit_app.py")  # OR whatever your main page is called
                
                for page_hash, config in pages.items():
                    if standardize_name(config["page_name"]) == page_name:
                        raise RerunException(
                            RerunData(
                                page_script_hash=page_hash,
                                page_name=page_name,
                            )
                        )
            
            # Navigate to the news search page
            switch_page("News_Search")
            
        except Exception as e:
            st.error(f"Error navigating to News Search: {e}")
            st.info("As a fallback, we'll use session state navigation")
            st.session_state.page = "news_search"
            st.rerun()
    
    if st.button("📧 Newsletter Generator", use_container_width=True):
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
            import threading
            
            def switch_page(page_name):
                from streamlit.runtime.scriptrunner import RerunData, RerunException
                from streamlit.source_util import get_pages
                
                def standardize_name(name):
                    return name.lower().replace("_", " ")
                
                page_name = standardize_name(page_name)
                
                pages = get_pages("streamlit_app.py")  # OR whatever your main page is called
                
                for page_hash, config in pages.items():
                    if standardize_name(config["page_name"]) == page_name:
                        raise RerunException(
                            RerunData(
                                page_script_hash=page_hash,
                                page_name=page_name,
                            )
                        )
            
            # Navigate to the newsletter page
            switch_page("Newsletter_Generator")
            
        except Exception as e:
            st.error(f"Error navigating to Newsletter Generator: {e}")
            st.info("As a fallback, we'll use session state navigation")
            st.session_state.page = "newsletter"
            st.rerun()
    
    st.markdown("---")
    
    # Quick stats in sidebar
    st.subheader("Platform Stats")
    st.markdown("**Companies Tracked:** 5,000+")
    st.markdown("**News Sources:** 25,000+")
    st.markdown("**Daily Updates:** ~500,000")
    
    st.markdown("---")
    
    # Add a simulated recent activity feed
    st.subheader("Recent Activity")
    activities = [
        "Tesla news report generated",
        "BlackRock news analysis completed",
        "Microsoft newsletter sent",
        "Apple news alert triggered",
        "Custom dashboard updated"
    ]
    
    for activity in activities:
        st.markdown(f"• {activity}")

# Main content
def main_page():
    # Skywalker branding header at the top of main content
    st.markdown("""
    <div class="skywalker-header">
      <div class="stars"></div>
      <div class="light-beam"></div>
      
      <!-- Simple spaceman icon -->
      <div class="spaceman">
        <svg width="100" height="120" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
          <!-- Helmet -->
          <circle cx="50" cy="20" r="15" fill="white" opacity="0.9"/>
          <!-- Visor -->
          <circle cx="50" cy="20" r="10" fill="#0088ff" opacity="0.7"/>
          <!-- Body -->
          <rect x="35" y="30" width="30" height="45" rx="8" fill="white" opacity="0.8"/>
          <!-- Arms -->
          <rect x="20" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
          <rect x="60" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
          <!-- Legs -->
          <rect x="38" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
          <rect x="52" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
        </svg>
      </div>
      
      <div class="skywalker-icon">
        <div class="icon-circle">
          <svg class="icon-silhouette" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L9 9H3L8 14L6 21L12 17L18 21L16 14L21 9H15L12 2Z" fill="white"/>
          </svg>
        </div>
      </div>
      
      <div class="skywalker-title">
        <h1 class="brand-name">Skywalker</h1>
        <p class="tagline">News as power</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Brief introduction
    st.markdown("""
    Welcome to Skywalker, your all-in-one platform for monitoring, analyzing, and distributing 
    business news. Stay ahead of market trends, track competitors, and deliver polished communications with our 
    powerful suite of tools.
    """)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="stats-card"><p class="stats-number">5K+</p><p class="stats-label">Companies Tracked</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-card"><p class="stats-number">25K+</p><p class="stats-label">News Sources</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stats-card"><p class="stats-number">500K</p><p class="stats-label">Daily Updates</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="stats-card"><p class="stats-number">99.8%</p><p class="stats-label">Accuracy</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main features section
    st.subheader("Our Platform Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Company News Search</div>
            <div class="feature-description">
                Search for latest news about your target companies across thousands of sources. 
                Filter by company, region, publication, and more to find exactly what you need.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go to News Search", key="home_news_search", use_container_width=True):
            try:
                st.switch_page("pages/1_News_Search.py")
            except Exception as e:
                st.error(f"Error navigating: {e}")
                st.session_state.page = "news_search"
                st.rerun()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📧</div>
            <div class="feature-title">Newsletter Generator</div>
            <div class="feature-description">
                Create beautiful, professional newsletters from your news data. Customize themes, 
                include AI-generated summaries, and export ready-to-send HTML emails.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go to Newsletter Generator", key="home_newsletter", use_container_width=True):
            try:
                st.switch_page("pages/2_Newsletter_Generator.py")
            except Exception as e:
                st.error(f"Error navigating: {e}")
                st.session_state.page = "newsletter"
                st.rerun()
    
    # Second row of features (for future expansion)
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Analytics Dashboard</div>
            <div class="feature-description">
                Track sentiment trends, media coverage volume, and competitive intelligence through 
                interactive dashboards. Export data for your own analysis.
                <div style="color: #9333EA; background-color: #F3E8FF; padding: 5px; border-radius: 4px; display: inline-block; margin-top: 10px;">Coming Soon</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Learn More", key="analytics", use_container_width=True):
            st.toast("Analytics Dashboard coming soon! Stay tuned for updates.", icon="🚧")
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔔</div>
            <div class="feature-title">Alerts & Notifications</div>
            <div class="feature-description">
                Set up custom alerts for important news events, competitor mentions, or industry developments.
                Receive notifications via email, Slack, or within the platform.
                <div style="color: #9333EA; background-color: #F3E8FF; padding: 5px; border-radius: 4px; display: inline-block; margin-top: 10px;">Coming Soon</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Learn More", key="alerts", use_container_width=True):
            st.toast("Alerts & Notifications feature coming soon! Stay tuned for updates.", icon="🚧")
    
    st.markdown("---")
    
    # Testimonial section
    st.subheader("What Our Users Say")
    
    st.markdown("""
    <div class="testimonial">
        "Skywalker has transformed how our team monitors industry news. The newsletter generator saves us hours every week, and the search functionality helps us stay on top of competitor movements."
        <br><br>
        <strong>— Sarah Johnson, Director of Market Intelligence at Global Investments Ltd.</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Getting started section
    st.subheader("Getting Started")
    st.markdown("""
    New to the platform? Here's how to get started:
    
    1. **Explore Company News Search** to find relevant articles about your target companies
    2. **Save articles of interest** for later reference and sharing
    3. **Generate newsletters** to distribute insights to your team or clients
    4. **Set up regular reports** to maintain consistent communication
    """)
    
    # Call to action
    st.markdown("### Ready to get started?")
    cta_col1, cta_col2, cta_col3 = st.columns([2,2,2])
    
    with cta_col1:
        if st.button("🔍 Try News Search", use_container_width=True, key="cta_search"):
            try:
                st.switch_page("pages/1_News_Search.py")
            except Exception as e:
                st.error(f"Error navigating: {e}")
                st.session_state.page = "news_search"
                st.rerun()
    
    with cta_col2:
        if st.button("📧 Create Newsletter", use_container_width=True, key="cta_newsletter"):
            try:
                st.switch_page("pages/2_Newsletter_Generator.py")
            except Exception as e:
                st.error(f"Error navigating: {e}")
                st.session_state.page = "newsletter"
                st.rerun()
    
    with cta_col3:
        if st.button("📚 View Documentation", use_container_width=True, key="cta_docs"):
            st.toast("Documentation will be available soon!", icon="📚")

# Initialize session state for page navigation if it doesn't exist
if 'page' not in st.session_state:
    st.session_state.page = "home"

# Fall back to the old router logic if st.switch_page() doesn't work
# This ensures compatibility with older Streamlit versions
if st.session_state.page == "home":
    main_page()
elif st.session_state.page == "news_search":
    st.info("Redirecting to Company News Search page...")
    try:
        st.switch_page("pages/1_News_Search.py")
    except Exception:
        # In a real app, you might use st.switch_page() for multi-page apps
        # Here we'll just show a placeholder
        st.success("Company News Search would load here")
        
        # Add button to return to home
        if st.button("← Back to Home", key="back_from_search"):
            st.session_state.page = "home"
            st.rerun()
elif st.session_state.page == "newsletter":
    st.info("Redirecting to Newsletter Generator page...")
    try:
        st.switch_page("pages/2_Newsletter_Generator.py")
    except Exception:
        # In a real app, you might use st.switch_page() for multi-page apps
        # Here we'll just show a placeholder
        st.success("Newsletter Generator would load here")
        
        # Add button to return to home
        if st.button("← Back to Home", key="back_from_newsletter"):
            st.session_state.page = "home"
            st.rerun()

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2,1,1])

with footer_col1:
    st.markdown("© 2025 Skywalker. All rights reserved.")

with footer_col2:
    st.markdown("**Links**")
    st.markdown("[Documentation](#)")
    st.markdown("[Support](#)")

with footer_col3:
    st.markdown("**Contact**")
    st.markdown("contact@skywalker.com")
    st.markdown("+1 (800) 555-0123")

# Check if the pages directory exists, if not, create it
if not os.path.exists("pages"):
    os.makedirs("pages")
    st.toast("Created 'pages' directory for multi-page app structure", icon="📁")