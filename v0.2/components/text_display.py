# text_display.py

import streamlit as st
import pandas as pd

def display_styled_text(content_dict, styles=None):
    """
    Display text content with exact HTML structure
    """
    default_styles = {
        'border_color': "#e51ec7",
        'bg_color': "#f0f7ff",
        'text_color': "#000000",
        'font_size': "16px",
        'padding': "20px",
        'border_radius': "10px",
        'border_width': "6px"
    }
    
    if styles:
        default_styles.update(styles)
    
    # Create content with specified HTML structure
    content_html = ""
    for label, value in content_dict.items():
        content_html += f'''
        <div style="margin-bottom: 8px;">
            <span style="font-weight: bold; color: {default_styles['border_color']}; min-width: 140px; display: inline-block;">{label}:</span>
            <span style="color: #333333; display: inline-block; font-weight: 600;">{value}</span>
        </div>
        '''
    
    st.markdown(
        f'''
        <div style="
            background-color: {default_styles['bg_color']};
            padding: {default_styles['padding']};
            border-radius: {default_styles['border_radius']};
            border-left: {default_styles['border_width']} solid {default_styles['border_color']};
            margin: 10px 0;">
            {content_html}
        </div>
        ''',
        unsafe_allow_html=True
    )

def display_multi_column_content(content_list, styles_list=None):
    """
    Display multiple content blocks in columns
    """
    if styles_list is None:
        styles_list = [None] * len(content_list)
    
    cols = st.columns(len(content_list))
    
    for content, col, styles in zip(content_list, cols, styles_list):
        with col:
            if content:
                display_styled_text(content, styles)
            else:
                error_styles = {
                    'border_color': '#ff0000',
                    'bg_color': '#fff0f0',
                }
                display_styled_text({"Error": "No data available"}, error_styles)

def format_profile_content(df, ein):
    """
    Format profile data for display, with fallback options for organization names
    """
    if not df.empty:
        # Initialize org_name with a default value
        org_name = "Organization Name Not Available"
        
        # Try to get organization name with fallback logic
        if 'DoingBusinessAsName_BusinessNameLine1Txt' in df.columns:
            dba_name = df['DoingBusinessAsName_BusinessNameLine1Txt'].iloc[0]
            if pd.notna(dba_name):
                org_name = dba_name
        elif 'Filer_BusinessName_BusinessNameLine1Txt' in df.columns:
            filer_name = df['Filer_BusinessName_BusinessNameLine1Txt'].iloc[0]
            if pd.notna(filer_name):
                org_name = filer_name
        
        return {
            # "Organization": org_name,
            "EIN": ein,
            "Formation Year": df['FormationYr'].iloc[0] 
                if 'FormationYr' in df.columns and pd.notna(df['FormationYr'].iloc[0]) 
                else 'N/A',
            "Total Employees": "{:,}".format(int(df['TotalEmployeeCnt'].iloc[0]))
                if 'TotalEmployeeCnt' in df.columns and pd.notna(df['TotalEmployeeCnt'].iloc[0])
                else 'N/A'
        }
    
    return None