"""
Sidebar component for the Gravity app
"""
import streamlit as st

def render_sidebar():
    """Render the sidebar with navigation and info"""
    with st.sidebar:
        # Add custom CSS for the sidebar brand
        st.markdown("""
        <style>
        /* Import a bold, fun font for the neon effect */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@700&display=swap');

        /* Neon Flicker Animation using black glow */
        @keyframes neonFlicker {
            0% {
                text-shadow:
                    0 0 5px #000000,
                    0 0 10px #000000,
                    0 0 20px #000000,
                    0 0 40px #000000,
                    0 0 80px #000000,
                    0 0 90px #000000,
                    0 0 100px #000000;
            }
            25% {
                text-shadow:
                    0 0 5px #000000,
                    0 0 10px #000000,
                    0 0 20px #000000,
                    0 0 40px #000000,
                    0 0 80px #000000,
                    0 0 90px #000000,
                    0 0 100px #000000;
                opacity: 0.8;
            }
            30% {
                text-shadow: none;
                opacity: 0.7;
            }
            70% {
                text-shadow:
                    0 0 5px #000000,
                    0 0 10px #000000,
                    0 0 20px #000000,
                    0 0 40px #000000,
                    0 0 80px #000000,
                    0 0 90px #000000,
                    0 0 100px #000000;
                opacity: 1;
            }
            100% {
                text-shadow:
                    0 0 5px #000000,
                    0 0 10px #000000,
                    0 0 20px #000000,
                    0 0 40px #000000,
                    0 0 80px #000000,
                    0 0 90px #000000,
                    0 0 100px #000000;
            }
        }

        .gravity-sidebar-brand {
            font-family: "Kanit", sans-serif;
            font-weight: 700;
            font-size: 40px;
            color: #ffffff;
            /* Black neon glow */
            text-shadow:
                0 0 5px #000000,
                0 0 10px #000000,
                0 0 20px #000000,
                0 0 40px #000000,
                0 0 80px #000000,
                0 0 90px #000000,
                0 0 100px #000000;
            
            /* Tilt the text slightly to mimic a billboard angle */
            transform: rotate(-5deg);

            /* Apply flicker animation */
            animation: neonFlicker 2.5s infinite;

            /* Center the text */
            margin: 20px auto;
            text-align: center;
            display: block;
        }

        /* Dark mode adjustments (optional) */
        @media (prefers-color-scheme: dark) {
            .gravity-sidebar-brand {
                /* Increase brightness in dark mode, if desired */
                opacity: 0.9;
            }
        }
        </style>
        
        <div class="gravity-sidebar-brand">Gravity</div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation links
        st.subheader("Navigation")
        
        # Main features buttons
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
            
        if st.button("🔍 News Search", use_container_width=True):
            st.switch_page("pages/01_news_search.py")
        
        if st.button("🏷️ News Tagging", use_container_width=True):
            st.switch_page("pages/02_news_tagging.py")
        
        if st.button("📧 Newsletter Generator", use_container_width=True):
            st.switch_page("pages/03_newsletter.py")
        
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