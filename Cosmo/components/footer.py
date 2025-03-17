"""
Footer component for the Gravity app
"""
import streamlit as st

def render_footer():
    """Render the page footer"""
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns([2,1,1])

    with footer_col1:
        st.markdown("© 2025 Gravity. Made by PAG.")

    with footer_col2:
        st.markdown("**Links**")
        st.markdown("[Documentation](#)")
        st.markdown("[Support](#)")

    with footer_col3:
        st.markdown("**Contact**")
        st.markdown("ning.lu@blackrock.com")