"""
Gravity - Footer Component
This component creates a consistent footer across all pages
"""
import streamlit as st
from datetime import datetime
from theme import apply_theme

def render_footer():
    """Renders the application footer with copyright and links"""
    # Make sure the theme is applied
    apply_theme()
    
    # Add some spacing before the footer
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Add a separator
    st.markdown("<hr style='margin: 0; padding: 0; height: 1px; border: none; background-color: #e0e0e0;'>", unsafe_allow_html=True)
    
    # Create a footer container
    footer_container = st.container()
    
    with footer_container:
        cols = st.columns([3, 1])
        
        with cols[0]:
            # Copyright and links
            current_year = datetime.now().year
            st.markdown(f"""
            <div style='font-size: 0.8rem; color: #666; padding: 1rem 0;'>
                © {current_year} Gravity | News Explorer & Newsletter Generator
                • <a href="#" target="_blank">Terms of Service</a>
                • <a href="#" target="_blank">Privacy Policy</a>
                • <a href="#" target="_blank">Contact Support</a>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            # Version info
            st.markdown("""
            <div style='font-size: 0.8rem; color: #666; padding: 1rem 0; text-align: right;'>
                Version 1.0.0
            </div>
            """, unsafe_allow_html=True)