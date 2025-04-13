"""
Gravity - Sidebar Component
This component creates a consistent sidebar across all pages
"""
import streamlit as st
from theme import apply_theme  # Changed: import the function from theme module

def render_sidebar():
    """Renders the application sidebar with navigation and tools"""
    # Make sure the theme is applied
    apply_theme()
    
    with st.sidebar:
        # Rest of your sidebar code...
        # st.sidebar.markdown("---")
        st.sidebar.caption("© 2025 Gravity | All Rights Reserved")