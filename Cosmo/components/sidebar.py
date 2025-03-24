"""
Sidebar component for the Gravity app
"""
import streamlit as st

def render_sidebar():
    """Render the sidebar with navigation, user case info, and app details"""
    with st.sidebar:
        # Custom CSS for the user case box
        st.markdown("""
        <style>
        .user-case-box {
            background-color: #1E3A8A;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 5px solid #60A5FA;
        }
        .case-title {
            color: #60A5FA;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .case-item {
            color: white;
            margin-bottom: 5px;
        }
        .case-highlight {
            background-color: rgba(96, 165, 250, 0.2);
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            color: #BFE0FF;
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
                
        st.markdown("---")
        
        # Navigation links
        st.subheader("Navigation")
        # Main features buttons
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        if st.button("🔍 News Search", use_container_width=True):
            st.switch_page("pages/01_News_Search.py")
        if st.button("🏷️ News Tagging", use_container_width=True):
            st.switch_page("pages/02_News_Tagging.py")
        if st.button("📰 Newsletter Generator", use_container_width=True):
            st.switch_page("pages/03_Newsletter_Generation.py")
        if st.button("📺 Video Feeds", use_container_width=True):
            st.switch_page("pages/04_Video_Feeds.py")
        if st.button("📱 Social Media", use_container_width=True):
            st.switch_page("pages/05_Social_Media.py")
        
        st.markdown("---")
        st.caption("Gravity v0.1 - Released on 25 March 2025")
        st.caption("© 2025 Gravity ❤️ Made by PAG")