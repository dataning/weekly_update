"""
Sidebar component for the Gravity app
"""
import streamlit as st

def render_sidebar():
    """Render the sidebar with navigation, user case info, and app details"""
    with st.sidebar:
        # Custom CSS for the user case box with adaptive theming
        st.markdown("""
        <style>
        /* User case box styling - Dark theme (default) */
        .stApp[data-theme="dark"] .user-case-box {
            background-color: #1E3A8A;
            border-left: 5px solid #60A5FA;
        }
        
        .stApp[data-theme="dark"] .case-title {
            color: #60A5FA;
        }
        
        .stApp[data-theme="dark"] .case-item {
            color: white;
        }
        
        .stApp[data-theme="dark"] .case-highlight {
            background-color: rgba(96, 165, 250, 0.2);
            color: #BFE0FF;
        }
        
        /* User case box styling - Light theme */
        .stApp[data-theme="light"] .user-case-box {
            background-color: #E3F2FD;
            border-left: 5px solid #1E88E5;
        }
        
        .stApp[data-theme="light"] .case-title {
            color: #1565C0;
        }
        
        .stApp[data-theme="light"] .case-item {
            color: #333333;
        }
        
        .stApp[data-theme="light"] .case-highlight {
            background-color: rgba(25, 118, 210, 0.1);
            color: #1565C0;
        }
        
        /* Common styling for both themes */
        .user-case-box {
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .case-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .case-item {
            margin-bottom: 5px;
        }
        
        .case-highlight {
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            display: inline-block;
            margin-top: 3px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # User case section with custom styling
        st.markdown('<div class="user-case-box">', unsafe_allow_html=True)
        st.markdown('<div class="case-title">Active User Cases</div>', unsafe_allow_html=True)
        user_case = st.session_state.get('current_user_case', {
            'stakeholders': 'Corp Comms',
            'industry': 'Corporate Affairs',
            'focus_areas': ['BlackRock'],
            'monitoring_since': 'March 26, 2025'
        })
        st.markdown(f'<div class="case-item">User Case: <strong>{user_case["stakeholders"]}</strong></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="case-item">Monitoring: {user_case["industry"]}</div>', unsafe_allow_html=True)
        
        focus_areas_html = ""
        for area in user_case['focus_areas']:
            focus_areas_html += f'<div class="case-highlight">{area}</div> '
        
        st.markdown(f'<div class="case-item">Target:</div>{focus_areas_html}', unsafe_allow_html=True)
        st.markdown(f'<div class="case-item">Since: {user_case["monitoring_since"]}</div>', unsafe_allow_html=True)
        
        # Add native Streamlit progress bar
        st.markdown('<div class="case-item">Monitoring Progress:</div>', unsafe_allow_html=True)
        
        # Use Streamlit's native progress bar which adapts to theme automatically
        progress_percentage = 0.75  # Example value (0-1 range) - replace with actual progress
        st.progress(progress_percentage)
        
        # Add label for the percentage
        st.markdown(f'<div style="font-size: 12px; text-align: right;">75% Complete</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close the user-case-box div
        
        st.markdown("---")
        
        # Navigation links
        st.subheader("Navigation")
        
        # Main features buttons
        if st.button("🏠 Home", use_container_width=True, key="sidebar_home_button"):
            st.switch_page("app.py")
        if st.button("🔍 News Search", use_container_width=True, key="sidebar_news_search_button"):
            st.switch_page("pages/01_News_Search.py")
        if st.button("🏷️ News Tagging", use_container_width=True, key="sidebar_news_tagging_button"):
            st.switch_page("pages/02_News_Tagging.py")
        if st.button("📰 Newsletter Generator", use_container_width=True, key="sidebar_newsletter_button"):
            st.switch_page("pages/03_Newsletter_Generation.py")
        if st.button("📺 Video Feeds", use_container_width=True, key="sidebar_video_feeds_button"):
            st.switch_page("pages/04_Video_Feeds.py")
        if st.button("📱 Social Media", use_container_width=True, key="sidebar_social_media_button"):
            st.switch_page("pages/05_Social_Media.py")
            
        st.markdown("---")
        st.caption("Gravity v0.1 - Released on 25 March 2025")
        st.caption("© 2025 Gravity ❤️ Made by PAG")