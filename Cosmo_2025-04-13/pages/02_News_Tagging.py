"""
News Tagging page for the Gravity app
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime  # Add this import
from utils.session_state import initialize_session_state
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
import theme

# Initialize session state
initialize_session_state()

theme.set_page_config()
theme.apply_full_theme()


# Render header
render_header()

# Main page content
st.title("🏷️ News Tagging")
st.write("Add themes and subheaders to categorize your selected news articles")

# Check if we have selected news data in session state
if "selected_news_df" not in st.session_state or st.session_state.selected_news_df is None:
    st.error("⚠️ No selected news articles. Please select articles in the Search tab first.")
    
    # Add a button to go back to search page
    button_key = f"goto_search_btn_tagging_{int(time.time() * 1000)}"
    if st.button("← Go to News Search", type="primary", key=button_key):
        st.switch_page("pages/01_news_search.py")
else:
    # Get the selected dataframe directly from session state
    # Use copy to avoid modifying the original
    df = st.session_state.selected_news_df.copy()
    
    # Handle column mapping between news search and tagging pages
    column_mappings = {
        'title': 'header_text',           # Map title from search to header_text in tagging
        'summary': 'summary_text',        # Map summary from search to summary_text in tagging
        'source': 'source_name',          # Map source to source_name
    }
    
    # Create any mapped columns that don't exist
    for source_col, target_col in column_mappings.items():
        if source_col in df.columns and target_col not in df.columns:
            df[target_col] = df[source_col]
    
    # Create any missing columns needed by the tagging page
    required_cols = ['countryname', 'body_text']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    
    # Add Theme and Subheader columns if they don't exist
    if 'Theme' not in df.columns:
        df['Theme'] = ""
    
    if 'Subheader' not in df.columns:
        df['Subheader'] = ""
    
    # Main content
    # Display statistics
    st.header("📈 Tagging Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(df))
    
    with col2:
        # Count articles with any theme
        themed_count = df[df['Theme'] != ""].shape[0]
        st.metric("Themed Articles", themed_count)
    
    with col3:
        # Count selected articles
        selected_count = df['selected'].sum() if 'selected' in df.columns else 0
        st.metric("Checked Articles", int(selected_count))
    
    # Tag Management Section - Now in main panel instead of sidebar
    st.header("🏷️ Tag Management")
    st.write("Add themes and subheaders to checked articles in the table below")
    
    # Create a single row with 4 columns for theme and subheader inputs
    tag_col1, tag_col2, tag_col3, tag_col4 = st.columns([3, 1, 3, 1])

    with tag_col1:
        theme_options = st.text_input(
            "Enter themes (comma separated):",
            value="GenAI, Energy, Healthcare",
            help="Example: GenAI, Energy, Healthcare",
            key="theme_options_input_tagging"
        )

    with tag_col2:
        apply_theme = st.button("Apply", use_container_width=True, key="apply_theme_btn_tagging")

    with tag_col3:
        subheader_options = st.text_input(
            "Enter subheaders (comma separated):",
            value="Global, AMERS, EMERA, APAC",
            help="Example: Global, AMERS, EMERA, APAC",
            key="subheader_options_input_tagging"
        )

    with tag_col4:
        apply_subheader = st.button("Apply", use_container_width=True, key="apply_subheader_btn_tagging")  
        
    # Additional action buttons in a row
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        clear_selection = st.button("Clear Checks", use_container_width=True, key="clear_checks_btn_tagging")
    
    with btn_col2:
        reset_tags = st.button("Reset All Tags", use_container_width=True, key="reset_tags_btn_tagging")
    
    # Add a separator
    st.markdown("---")
    
    # Helper functions for batch operations
    def apply_theme_to_selected():
        theme_list = [theme.strip() for theme in theme_options.split(",")]
        mask = df['selected'] == True
        if mask.any():
            # For selected rows, append new themes (avoid duplicates)
            for idx in df[mask].index:
                current_themes = set([] if pd.isna(df.at[idx, 'Theme']) or df.at[idx, 'Theme'] == "" else 
                                    [t.strip() for t in df.at[idx, 'Theme'].split(",")])
                new_themes = current_themes.union(set(theme_list))
                df.at[idx, 'Theme'] = ", ".join(new_themes)
            st.success(f"Applied themes to {mask.sum()} checked articles")
        else:
            st.warning("No articles checked. Please check articles first.")
    
    def apply_subheader_to_selected():
        subheader_list = [subheader.strip() for subheader in subheader_options.split(",")]
        mask = df['selected'] == True
        if mask.any():
            # For selected rows, append new subheaders (avoid duplicates)
            for idx in df[mask].index:
                current_subheaders = set([] if pd.isna(df.at[idx, 'Subheader']) or df.at[idx, 'Subheader'] == "" else 
                                       [s.strip() for s in df.at[idx, 'Subheader'].split(",")])
                new_subheaders = current_subheaders.union(set(subheader_list))
                df.at[idx, 'Subheader'] = ", ".join(new_subheaders)
            st.success(f"Applied subheaders to {mask.sum()} checked articles")
        else:
            st.warning("No articles checked. Please check articles first.")
    
    # Execute batch operations based on button clicks
    if apply_theme:
        apply_theme_to_selected()
    
    if apply_subheader:
        apply_subheader_to_selected()
    
    if clear_selection:
        df['selected'] = False
        st.success("All checks cleared")
    
    if reset_tags:
        df['Theme'] = ""
        df['Subheader'] = ""
        st.success("All tags have been reset")
    
    # Data table section header
    st.header("📋 News Articles")
    
    # Create display columns - put selected first, then Theme/Subheader, then priority columns
    priority_cols = ['search_term', 'countryname', 'header_text', 'summary_text', 'body_text']
    display_cols = ['selected', 'Theme', 'Subheader']
    
    # Add available priority columns (only if they exist in the dataframe)
    for col in priority_cols:
        if col in df.columns:
            display_cols.append(col)
    
    # Ensure all display columns exist in the dataframe
    for col in display_cols:
        if col not in df.columns:
            df[col] = ""
            
    # Make sure there's a "selected" column if it doesn't exist
    if 'selected' not in df.columns:
        df['selected'] = False
    
    # Create column config with fallbacks for missing columns
    column_config = {
        "selected": st.column_config.CheckboxColumn("Select", help="Check articles for batch editing"),
        "Theme": st.column_config.TextColumn("Theme", help="Article themes (e.g., GenAI, Energy)", width="medium"),
        "Subheader": st.column_config.TextColumn("Subheader", help="Article region (e.g., Global, AMERS)", width="medium")
    }
    
    # Add column config for priority columns only if they exist
    if 'search_term' in df.columns:
        column_config["search_term"] = st.column_config.TextColumn("Company", help="Company name")
    
    if 'countryname' in df.columns:
        column_config["countryname"] = st.column_config.TextColumn("Country", help="Country of publication")
    
    if 'header_text' in df.columns:
        column_config["header_text"] = st.column_config.TextColumn("Headline", help="Article headline")
    elif 'title' in df.columns and 'title' in display_cols:
        column_config["title"] = st.column_config.TextColumn("Headline", help="Article headline")
        
    if 'summary_text' in df.columns:
        column_config["summary_text"] = st.column_config.TextColumn("Summary", help="Article summary")
    elif 'summary' in df.columns and 'summary' in display_cols:
        column_config["summary"] = st.column_config.TextColumn("Summary", help="Article summary")
        
    if 'body_text' in df.columns:
        column_config["body_text"] = st.column_config.TextColumn("Content", help="Article content")
    
    # Create the data editor for user interaction - ensure Theme and Subheader are editable
    edited_df = st.data_editor(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        num_rows="dynamic",
        key="analysis_data_editor_tagging",
        disabled=False  # Ensure nothing is disabled
    )
    
    # Update the displayed columns in the dataframe with edited values
    for col in display_cols:
        if col in edited_df.columns:
            df[col] = edited_df[col]
    
    # Update session state with the edited dataframe
    st.session_state.selected_news_df = df
    
    # Store the edited dataframe for the newsletter tab
    st.session_state.tagged_news_df = df.copy()
    
    # Add buttons to handle newsletter generation
    st.markdown("---")
    
    newsletter_col1, newsletter_col2 = st.columns(2)
    with newsletter_col1:
        st.subheader("Use Tagged Articles for Newsletter")
        st.write("Generate a newsletter using the articles you've tagged above.")
        
        if st.button("Generate Newsletter from Tagged Articles", type="primary", use_container_width=True, key="generate_newsletter_btn_tagging"):
            # Save the tagged data for newsletter generation
            st.session_state.tagged_news_df = df
            st.success("Articles are ready for newsletter generation!")
            st.switch_page("pages/03_newsletter.py")
    
    with newsletter_col2:
        st.subheader("Export Tagged Articles")
        st.write("Download your tagged articles as a CSV file.")
        
        # Download button
        st.download_button(
            label="📥 Download Tagged Articles as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"tagged_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_tagged_btn_tagging"
        )

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()