import streamlit as st

def create_info_banner(message):
    """Create an information banner with a styled message"""
    st.markdown(
        f"""
        <div style="
            background-color: #f0f7ff;
            border-left: 5px solid #0068c9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-family: 'Roboto', sans-serif;
            font-size: 16px;
            line-height: 1.5;
        ">
            {message}
        </div>
        """, 
        unsafe_allow_html=True
    )

def create_feature_card(icon, title, description, button_text, button_key):
    """Create a feature card with icon, title, description and a button"""
    # Card container with styling
    with st.container():
        st.markdown(
            f"""
            <div style="
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                height: 100%;
            ">
                <div style="font-size: 36px; margin-bottom: 10px;">{icon}</div>
                <h3 style="font-family: 'Roboto', sans-serif; font-size: 18px; font-weight: 500; margin-bottom: 10px;">{title}</h3>
                <p style="font-family: 'Roboto', sans-serif; font-size: 14px; color: #666; margin-bottom: 10px; line-height: 1.5;">{description}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Button below the card
        return st.button(button_text, key=button_key)