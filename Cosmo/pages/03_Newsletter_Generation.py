"""
Newsletter Generator page for the Gravity app
"""
import streamlit as st
import pandas as pd
import base64
import io
import os
from datetime import datetime
from PIL import Image
from jinja2 import Environment, FileSystemLoader
from utils.session_state import initialize_session_state, trigger_update
from utils.data_processing import clean_dataframe, create_column_mapping
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
from services.banner_service import (
    get_modified_banner_html, 
    COLOR_BANNER_TEMPLATES, 
    BANNER_FILENAMES,
    DEFAULT_BANNER_TEXTS
)
from utils.email_sender import EmailSender

# Set page config
st.set_page_config(
    page_title="Newsletter Generator - Gravity",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session_state()

# Ensure necessary directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("templates/banners", exist_ok=True)

# Render header
render_header()

# Global variables to be used by update function
df = None
column_mapping = None

# Import the NewsletterGenerator class
from modules.newsletter_generator import NewsletterGenerator

# Helper functions
def generate_prompt(df, selected_indices):
    """Generate a prompt for LLM summarization"""
    if not selected_indices or len(selected_indices) == 0:
        return ""
    
    prompt = """You are a senior news editor with 10+ years of experience distilling multiple news stories into concise briefings. Summarize the following table of news headlines, summaries, outlets, and themes in EXACTLY 3 paragraphs, no more and no less:

The first paragraph should provide an overview of the main theme or trend connecting most of the news stories in the table.
The second paragraph should highlight the most significant or impactful stories, including key details like company names and core developments.
The third paragraph should identify any secondary themes or patterns across multiple stories and note any outliers or unique stories that are still noteworthy.

Use professional journalistic language and include the most relevant details from the original sources. Focus on synthesizing information rather than simply listing stories. Maintain appropriate attribution to news outlets when necessary.

"""
    # Create a formatted table of the selected articles
    prompt += "| Title | Company | Source | Date | Content |\n"
    prompt += "| ----- | ------- | ------ | ---- | ------- |\n"
    
    # Get selected rows using boolean indexing for safety
    selected_rows = df.loc[selected_indices]
    
    for _, row in selected_rows.iterrows():
        # Safely handle values, converting to string and handling NaN/None
        def safe_value(value, default=''):
            if pd.isna(value) or value is None:
                return default
            return str(value).replace('|', '-')
        
        # Check for various column names to be flexible with different datasets
        # Title column variations
        title = ""
        for title_col in ['Article_Title', 'header_text', 'Title', 'Headline']:
            if title_col in row and not pd.isna(row.get(title_col)):
                title = safe_value(row.get(title_col))
                break
                
        # If no title found from known columns, use first text column as fallback
        if not title:
            for col in row.index:
                if isinstance(row[col], str) and col != 'selected':
                    title = safe_value(row[col])
                    break
        
        # Company column variations
        company = ""
        for company_col in ['Company', 'search_term', 'Theme']:
            if company_col in row and not pd.isna(row.get(company_col)):
                company = safe_value(row.get(company_col))
                break
        
        # Source column variations
        source = ""
        for source_col in ['Source', 'first_source_name', 'Publisher']:
            if source_col in row and not pd.isna(row.get(source_col)):
                source = safe_value(row.get(source_col))
                break
        
        # Date column variations
        date = ""
        for date_col in ['Date', 'local_time_text', 'Publication_Date']:
            if date_col in row and not pd.isna(row.get(date_col)):
                date = safe_value(row.get(date_col))
                break
        
        # Content column variations
        content = ""
        for content_col in ['Content', 'summary_text', 'body_text', 'Summary']:
            if content_col in row and not pd.isna(row.get(content_col)):
                content = safe_value(row.get(content_col))
                break
        
        # Truncate content for table readability
        if content and len(content) > 100:
            content = content[:97] + "..."
        
        prompt += f"| {title} | {company} | {source} | {date} | {content} |\n"
    
    return prompt

def update_preview_on_change():
    """
    Update the newsletter preview immediately after a change
    No need to rerun the app - directly update the preview
    """
    global df, column_mapping
    
    if df is None:
        return
        
    # Mark as updating to prevent multiple simultaneous updates
    st.session_state.preview_updating = True
    
    try:
        # Get current settings
        color_theme = st.session_state.get('color_theme_newsletter', "Blue (Default)")
        
        # Set colors based on theme
        if color_theme == "Blue (Default)":
            colors = {
                'primary': '#0168b1',
                'secondary': '#333333',
                'background': '#e6e6e6',
                'header_bg': '#0168b1',
                'footer_bg': '#000000',
                'highlight': '#0168b1'
            }
            default_banner = "blue"
        elif color_theme == "Green":
            colors = {
                'primary': '#2C8B44',
                'secondary': '#333333',
                'background': '#F0F7F0',
                'header_bg': '#1A5D2B',
                'footer_bg': '#333333',
                'highlight': '#2C8B44'
            }
            default_banner = "green"
        elif color_theme == "Purple":
            colors = {
                'primary': '#673AB7',
                'secondary': '#333333',
                'background': '#F5F0FF',
                'header_bg': '#4A148C',
                'footer_bg': '#333333',
                'highlight': '#9575CD'
            }
            default_banner = "purple"
        elif color_theme == "Corporate":
            colors = {
                'primary': '#D74B4B',
                'secondary': '#333333',
                'background': '#F5F5F5',
                'header_bg': '#1D2951',
                'footer_bg': '#1D2951',
                'highlight': '#D74B4B'
            }
            default_banner = "corporate"
        elif color_theme == "Red":
            colors = {
                'primary': '#D32F2F',
                'secondary': '#333333',
                'background': '#FFEBEE',
                'header_bg': '#B71C1C',
                'footer_bg': '#7F0000',
                'highlight': '#F44336'
            }
            default_banner = "red"
        elif color_theme == "Teal":
            colors = {
                'primary': '#00897B',
                'secondary': '#333333',
                'background': '#E0F2F1',
                'header_bg': '#004D40',
                'footer_bg': '#002B22',
                'highlight': '#26A69A'
            }
            default_banner = "teal"
        elif color_theme == "Amber":
            colors = {
                'primary': '#FFB300',
                'secondary': '#333333',
                'background': '#FFF8E1',
                'header_bg': '#FF6F00',
                'footer_bg': '#B23C00',
                'highlight': '#FFC107'
            }
            default_banner = "amber"
        elif color_theme == "Indigo":
            colors = {
                'primary': '#3949AB',
                'secondary': '#333333',
                'background': '#E8EAF6',
                'header_bg': '#1A237E',
                'footer_bg': '#0D1243',
                'highlight': '#3F51B5'
            }
            default_banner = "indigo"
        elif color_theme == "Cyan":
            colors = {
                'primary': '#00ACC1',
                'secondary': '#333333',
                'background': '#E0F7FA',
                'header_bg': '#006064',
                'footer_bg': '#00363A',
                'highlight': '#00BCD4'
            }
            default_banner = "cyan"
        elif color_theme == "Brown":
            colors = {
                'primary': '#795548',
                'secondary': '#333333',
                'background': '#EFEBE9',
                'header_bg': '#3E2723',
                'footer_bg': '#1B0000',
                'highlight': '#8D6E63'
            }
            default_banner = "brown"
        elif color_theme == "Custom":
            # Handle custom colors based on method
            custom_method = st.session_state.get('custom_method_newsletter', "Color Picker")
            
            if custom_method == "Color Picker":
                colors = {
                    'primary': st.session_state.get('primary_color_newsletter', '#0168b1'),
                    'secondary': st.session_state.get('secondary_color_newsletter', '#333333'),
                    'background': st.session_state.get('background_color_newsletter', '#e6e6e6'),
                    'header_bg': st.session_state.get('header_bg_color_newsletter', '#0168b1'),
                    'footer_bg': st.session_state.get('footer_bg_color_newsletter', '#000000'),
                    'highlight': st.session_state.get('highlight_color_newsletter', '#0168b1')
                }
            else:  # HEX Code input
                colors = {
                    'primary': st.session_state.get('primary_hex_newsletter', '#0168b1'),
                    'secondary': st.session_state.get('secondary_hex_newsletter', '#333333'),
                    'background': st.session_state.get('background_hex_newsletter', '#e6e6e6'),
                    'header_bg': st.session_state.get('header_bg_hex_newsletter', '#0168b1'),
                    'footer_bg': st.session_state.get('footer_bg_hex_newsletter', '#000000'),
                    'highlight': st.session_state.get('highlight_hex_newsletter', '#0168b1')
                }
            
            default_banner = "blue"
        else:
            # Default fallback
            colors = {
                'primary': '#0168b1',
                'secondary': '#333333',
                'background': '#e6e6e6',
                'header_bg': '#0168b1',
                'footer_bg': '#000000',
                'highlight': '#0168b1'
            }
            default_banner = "blue"
        
        # Get other settings
        banner_selection = st.session_state.get('banner_selection_newsletter', "BlackRock Corporate (Default)")
        content_width = st.session_state.get('content_width_newsletter', 800)
        mobile_friendly = st.session_state.get('mobile_friendly_newsletter', True)
        preview_text = st.session_state.get('preview_text_newsletter', "Your newsletter preview text here")
        
        # Handle banner file
        banner_html_file = None
        if 'custom_banner_newsletter' in st.session_state:
            banner_html_file = st.session_state.custom_banner_newsletter
        
        # Get additional content
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
        # Handle different banner types
        if banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
        elif banner_selection in BANNER_FILENAMES:
            # Use the modified HTML directly
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text)
        else:
            # Use the color template
            banner_input = COLOR_BANNER_TEMPLATES.get(default_banner, COLOR_BANNER_TEMPLATES["blue"])
            # Update the width
            banner_input = banner_input.replace('width: 800px', f'width: {content_width}px')
        
        # Create generator instance
        generator = NewsletterGenerator(template_path='templates/newsletter_template.html')
        
        # Generate the newsletter without saving to disk
        newsletter_html, _ = generator.generate_newsletter(
            df=df,
            output_path=None,  # No output path needed for preview
            preview_text=preview_text,
            column_mapping=column_mapping,
            colors=colors,
            banner_input=banner_input,
            summary_html=summary_html,
            image_html=image_html,
            content_width=content_width,
            mobile_friendly=mobile_friendly,
            save_to_disk=False  # Don't save to disk for preview
        )
        
        # Save in session state for display
        st.session_state.newsletter_html = newsletter_html
        st.session_state.needs_update = False
        
    except Exception as e:
        st.error(f"Error updating preview: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        st.session_state.newsletter_error = True
    finally:
        # Reset updating flag
        st.session_state.preview_updating = False

def save_newsletter_for_sending():
    """
    Save the current newsletter to a temporary file for sending or downloading
    Returns the path to the saved file
    """
    global df, column_mapping
    
    if df is None or 'newsletter_html' not in st.session_state:
        return None
    
    try:
        # Create generator instance
        generator = NewsletterGenerator(template_path='templates/newsletter_template.html')
        
        # Get current settings from session state
        color_theme = st.session_state.get('color_theme_newsletter', "Blue (Default)")
        banner_selection = st.session_state.get('banner_selection_newsletter', "BlackRock Corporate (Default)")
        content_width = st.session_state.get('content_width_newsletter', 800)
        mobile_friendly = st.session_state.get('mobile_friendly_newsletter', True)
        preview_text = st.session_state.get('preview_text_newsletter', "Your newsletter preview text here")
        
        # Get colors based on theme (simplified)
        colors = {
            'primary': '#0168b1',
            'secondary': '#333333',
            'background': '#e6e6e6',
            'header_bg': '#0168b1',
            'footer_bg': '#000000',
            'highlight': '#0168b1'
        }
        
        # Handle banner file
        banner_html_file = None
        if 'custom_banner_newsletter' in st.session_state:
            banner_html_file = st.session_state.custom_banner_newsletter
        
        # Get additional content
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
        # Handle different banner types
        if banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
        elif banner_selection in BANNER_FILENAMES:
            # Use the modified HTML directly
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text)
        else:
            # Use a default banner
            banner_input = COLOR_BANNER_TEMPLATES.get("blue", COLOR_BANNER_TEMPLATES["blue"])
        
        # Generate and save the newsletter
        _, output_path = generator.generate_newsletter(
            df=df,
            column_mapping=column_mapping,
            colors=colors,
            preview_text=preview_text,
            banner_input=banner_input,
            summary_html=summary_html,
            image_html=image_html,
            content_width=content_width,
            mobile_friendly=mobile_friendly,
            save_to_disk=True  # Save to disk for sending
        )
        
        return output_path
        
    except Exception as e:
        st.error(f"Error saving newsletter: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Main page content
st.title("📧 Newsletter Generator")
st.write("Create customized newsletters using your tagged articles or upload a CSV")

# First, let's check for data sources
has_tagged_data = (
    "tagged_news_df" in st.session_state 
    and st.session_state.tagged_news_df is not None
    and hasattr(st.session_state.tagged_news_df, 'empty')
    and not st.session_state.tagged_news_df.empty
)

# Source selection
st.subheader("Data Source")
data_source = st.radio(
    "Choose your data source:",
    options=["Tagged News Articles", "Upload CSV", "Use Demo Data"],
    index=0 if has_tagged_data else 2,
    key="data_source_radio_newsletter"
)

if data_source == "Tagged News Articles":
    if has_tagged_data:
        df = st.session_state.tagged_news_df.copy()
        st.success(f"Using {len(df)} tagged articles from previous step")
    else:
        st.error("No tagged articles available. Please tag some articles in the News Tagging tab or choose another data source.")

elif data_source == "Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload your CSV file", 
        type=["csv"], 
        key="csv_uploader_newsletter"
    )
    
    if uploaded_file is not None:
        # Process the uploaded file
        df = pd.read_csv(uploaded_file)
        df = clean_dataframe(df)
        st.success(f"Loaded {len(df)} articles from CSV")
    else:
        st.info("Please upload a CSV file with your news articles")

elif data_source == "Use Demo Data":
    # Check if the demo file exists
    demo_file = "static/data/dummy_news.csv"
    
    if os.path.exists(demo_file):
        df = pd.read_csv(demo_file)
        df = clean_dataframe(df)
        st.success(f"Loaded demo dataset with {len(df)} articles")
    else:
        # Create a simple demo dataset if file doesn't exist
        data = [
            {"Company": "Technology Corp", "News_Type": "Product Updates", "Article_Title": "New Product Launch", 
             "Source": "Tech Insider", "Date": "01 March 2025", 
             "Content": "A revolutionary product designed to disrupt the industry..."},
            {"Company": "Technology Corp", "News_Type": "Industry News", "Article_Title": "Market Trends", 
             "Source": "Business Journal", "Date": "02 March 2025", 
             "Content": "Industry analysis shows significant growth in tech sector..."},
            {"Company": "Finance Inc", "News_Type": "Market Analysis", "Article_Title": "Q1 Results",
             "Source": "Financial Times", "Date": "03 March 2025",
             "Content": "First quarter results show strong performance across all sectors..."}
        ]
        
        df = pd.DataFrame(data)
        # Save for future use
        os.makedirs(os.path.dirname(demo_file), exist_ok=True)
        df.to_csv(demo_file, index=False)
        
        st.success(f"Created sample dataset with {len(df)} articles")

# Add the dataframe preview 
if df is not None:
    st.subheader("Imported Data Preview")
    
    # Define priority columns to display with both lowercase and capitalized versions
    priority_cols = [
        'selected', 'Selected',
        'theme', 'Theme', 
        'subheader', 'Subheader',
        'company', 'Company', 
        'search_term', 
        'first_source_name', 'Source',
        'countryname', 
        'header_text', 'Article_Title',
        'summary_text', 'Content',
        'body_text', 
        'url', 'Url'
    ]
    
    # Debug available columns
    with st.expander("Debug Available Columns"):
        st.write("Available columns in dataframe:", df.columns.tolist())
    
    # Filter to only include columns that actually exist in the dataframe
    display_cols = [col for col in priority_cols if col in df.columns]
    
    # If none of the priority columns exist, show all columns
    if not display_cols:
        display_cols = df.columns.tolist()
    
    # Show filtered columns
    st.dataframe(df[display_cols], use_container_width=True)
    
    # IMPORTANT: Create column_mapping here so it's available throughout
    column_mapping = create_column_mapping(df)
    
    # Add column mapping information to help users understand
    st.info("Note: Columns like 'Theme' and 'Subheader' from the tagging page will be shown here if available.")

# Show explanation if no data is available
if df is None:
    st.warning("Please select a valid data source to continue")
    
    # Show explanation for CSV format
    with st.expander("CSV Format Example"):
        st.write("Your CSV should include the following columns:")
        sample_data = [
            {
                "Company": "Technology Corp",
                "News_Type": "Product Updates",
                "Article_Title": "New Product Launch",
                "Source": "Tech Insider",
                "Date": "01 March 2025",
                "Content": "A revolutionary product designed to disrupt the industry..."
            },
            {
                "Company": "Technology Corp",
                "News_Type": "Industry News",
                "Article_Title": "Market Trends",
                "Source": "Business Journal",
                "Date": "02 March 2025",
                "Content": "Industry analysis shows significant growth in tech sector..."
            }
        ]
        
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df)
        
        csv = sample_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="sample_newsletter_data.csv">Download sample CSV file</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    st.stop()

# Create columns for configuration and preview
left_col, right_col = st.columns([6, 6])

with left_col:
    st.subheader("Configuration")
    
    # Create tabs for different content sections
    content_tabs = st.tabs(["Summary", "Image", "Layout", "Banner"])
    
    with content_tabs[0]:  # Summary Tab
        st.subheader("Newsletter Summary")
        
        # Add select for articles
        if 'selected' not in df.columns:
            df['selected'] = False
        
        # Display dataframe for selection
        st.write("Select articles to include in summary")
        
        # Determine which columns to show for article selection
        title_column = next((col for col in ['Article_Title', 'header_text', 'Title', 'Headline'] 
                            if col in df.columns), df.columns[0])
        
        source_column = next((col for col in ['Source', 'first_source_name', 'Publisher'] 
                             if col in df.columns), None)
        
        # Create display columns list
        display_cols = ['selected', title_column]
        if source_column:
            display_cols.append(source_column)
            
        # Display more columns if available
        extra_info_cols = []
        for possible_info in ['Date', 'Theme', 'Subheader', 'Company', 'search_term']:
            if possible_info in df.columns and possible_info not in display_cols:
                extra_info_cols.append(possible_info)
        
        # Add up to 2 extra info columns if available
        if extra_info_cols:
            display_cols.extend(extra_info_cols[:2])
        
        # Create column config for better display
        column_config = {
            "selected": st.column_config.CheckboxColumn("Select", help="Check to include in summary")
        }
        
        # Better labels for the columns
        if title_column:
            column_config[title_column] = st.column_config.TextColumn("Article Title", help="Title of the article")
        if source_column:
            column_config[source_column] = st.column_config.TextColumn("Source", help="Source of the article")
        
        edited_df = st.data_editor(
            df[display_cols],
            hide_index=True,
            use_container_width=True,
            key="summary_selector_newsletter",
            column_config=column_config
        )
        
        # Update selection
        df['selected'] = edited_df['selected']
        
        # Get indices of selected rows - use boolean indexing to ensure safety
        selected_rows = df[df['selected'] == True]
        selected_indices = selected_rows.index.tolist()
        
        if selected_indices:
            st.subheader("Generate Summary")
            prompt_tab, summary_tab = st.tabs(["1. Get Prompt for LLM", "2. Add Generated Summary"])
            
            with prompt_tab:
                prompt = generate_prompt(df, selected_indices)
                st.markdown("### Copy this prompt to your preferred LLM:")
                copy_col1, copy_col2 = st.columns([5, 1])
                with copy_col2:
                    if st.button("📋 Copy", use_container_width=True, key="copy_prompt_btn_newsletter"):
                        st.toast("Prompt copied to clipboard!", icon="✅")
                st.code(prompt, language="text")
                st.caption("""
                **Two ways to copy:**
                1. Click the "📋 Copy" button above, or
                2. Use the copy icon in the top-right corner of the code block
                """)
                with st.expander("How to use this prompt"):
                    st.markdown("""
                    1. Copy the entire prompt using one of the copy buttons
                    2. Paste it into ChatGPT, Claude, or your preferred AI tool
                    3. Get the generated summary
                    4. Come back to the "Add Generated Summary" tab to paste your results
                    """)
            
            with summary_tab:
                st.markdown("**After generating your summary with an external LLM, paste it here:**")
                user_summary = st.text_area("Paste your generated summary here:", height=200, key="user_summary_newsletter")
                
                # Format summary for display with proper HTML
                formatted_summary = f"""
                <div style="color: #333333; font-family: 'BLK Fort', 'Arial', Arial, sans-serif; font-size: 14px; line-height: 22px; padding: 15px 0;">
                    <h3 style="color: #000000; font-size: 18px; margin-bottom: 10px; border-bottom: 1px solid #cccccc; padding-bottom: 5px;">Weekly Summary</h3>
                    {user_summary.replace('\n', '<br>') if user_summary else "No summary provided yet."}
                </div>
                """
                
                # Always show the Add Summary button
                if st.button("Add Summary to Newsletter", use_container_width=True, key="add_summary_btn_newsletter"):
                    st.session_state.summary_html = formatted_summary
                    update_preview_on_change()
                    st.success("Summary added to newsletter and preview updated!")
                
                st.markdown("**Preview of formatted summary:**")
                st.markdown(formatted_summary, unsafe_allow_html=True)
                
                # Button to remove summary if one exists
                if 'summary_html' in st.session_state and st.session_state.summary_html:
                    if st.button("Remove Summary", use_container_width=True, key="remove_summary_btn_newsletter"):
                        st.session_state.summary_html = ""
                        update_preview_on_change()
                        st.success("Summary removed from newsletter")
        else:
            st.info("Select articles in the table above to generate a summary prompt.")
            
        # Show current summary if it exists
        if 'summary_html' in st.session_state and st.session_state.summary_html:
            st.success("Summary added to newsletter")
            with st.expander("View current summary"):
                st.markdown(st.session_state.summary_html, unsafe_allow_html=True)
                
    with content_tabs[1]:  # Image Tab
        st.subheader("Add Image to Newsletter")
        
        # Image upload widget
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "gif"], key="image_upload_newsletter")
        
        # Image caption
        image_caption = st.text_area("Image caption:", height=100, key="image_caption_newsletter")
        
        if uploaded_image:
            # Display preview
            st.subheader("Image Preview")
            st.image(uploaded_image, width=400)
            
            # Add button to insert image
            if st.button("Add Image to Newsletter", use_container_width=True, key="add_image_btn_newsletter"):
                # Convert the image to base64 for embedding in HTML
                try:
                    # Open the image using PIL
                    img = Image.open(uploaded_image)
                    
                    # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
                    if img.mode == 'RGBA':
                        # Create a white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        # Paste the image on the background using alpha as mask
                        background.paste(img, mask=img.split()[3])
                        img = background
                    
                    # Resize to reasonable dimensions for email
                    max_width = 600
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_width = max_width
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height))
                    
                    # Save to buffer
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Format the image HTML with caption - centered with margin
                    formatted_image_html = f"""
                    <div style="padding: 15px 0; text-align: center;">
                        <img src="data:image/jpeg;base64,{img_str}" 
                            alt="Newsletter Image" 
                            style="max-width:100%; height:auto; display:block; margin:0 auto; border:1px solid #ddd;">
                        <p style="color: #333333; font-family: 'Arial', sans-serif; font-size: 14px; 
                                line-height: 22px; font-style:italic; padding: 10px 0; text-align: center;">{image_caption}</p>
                        <hr style="border:0; border-top:1px solid #ddd; margin:15px 0; width: 80%; margin: 15px auto;">
                    </div>
                    """
                    
                    # Store in session state
                    st.session_state.image_html = formatted_image_html
                    update_preview_on_change()
                    st.success("Image added to newsletter and preview updated!")
                    
                except Exception as e:
                    st.error(f"Error processing image: {e}")
        
            # Remove image button if an image exists
            if 'image_html' in st.session_state and st.session_state.image_html:
                st.success("Image added to newsletter")
                if st.button("Remove Image", use_container_width=True, key="remove_image_btn_newsletter"):
                    st.session_state.image_html = ""
                    update_preview_on_change()
                    st.success("Image removed from newsletter")
    
    with content_tabs[2]:  # Layout Tab
        st.subheader("Layout Settings")
        
        # Layout dimensions and settings
        st.markdown("### Dimensions and Preview Text")
        
        # Color scheme selection
        color_theme = st.selectbox(
            "Select a color theme",
            ["Blue (Default)", "Green", "Purple", "Corporate", "Red", "Teal", "Amber", "Indigo", "Cyan", "Brown", "Custom"],
            key="color_theme_newsletter",
            on_change=update_preview_on_change  # Direct update on change
        )
        
        # Pre-determined color schemes are handled in update_preview_on_change
        # Just provide default values for display purposes
        default_banner = "blue"
        
        # Common layout settings
        content_width = st.slider(
            "Content Width (px)", 
            600, 1000, 800,
            key="content_width_newsletter",
            on_change=update_preview_on_change  # Direct update on change
        )
        
        mobile_friendly = st.checkbox(
            "Mobile-friendly design", 
            value=True,
            key="mobile_friendly_newsletter",
            on_change=update_preview_on_change  # Direct update on change
        )
        
        preview_text = st.text_input(
            "Preview Text (shown in email clients)", 
            "Your newsletter preview text here",
            key="preview_text_newsletter",
            on_change=update_preview_on_change  # Direct update on change
        )
    
    with content_tabs[3]:  # Banner Tab
        st.subheader("Banner Selection")
        
        # Banner options now include preloaded banners from the banners directory
        banner_options = list(BANNER_FILENAMES.keys()) + ["Upload Custom HTML Banner"]
        
        banner_selection = st.radio(
            "Choose a banner style:",
            banner_options,
            horizontal=True,
            index=0,  # Default to the corpcomm_banner
            key="banner_selection_newsletter",
            on_change=update_preview_on_change  # Direct update on change
        )
        
        # Text editing fields for each banner type
        st.subheader("Edit Banner Text")
        
        banner_html_file = None
        
        if banner_selection == "BlackRock Corporate (Default)":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['corporate_top'] = st.text_input(
                    "Top Bar Text", 
                    st.session_state.banner_text['corporate_top'],
                    key="corporate_top_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['corporate_middle'] = st.text_input(
                    "Middle Bar Text", 
                    st.session_state.banner_text['corporate_middle'],
                    key="corporate_middle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            
        elif banner_selection == "GIPS Infrastructure":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['gips_brand'] = st.text_input(
                    "Brand Name", 
                    st.session_state.banner_text['gips_brand'],
                    key="gips_brand_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['gips_subtitle'] = st.text_input(
                    "Brand Subtitle", 
                    st.session_state.banner_text['gips_subtitle'],
                    key="gips_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['gips_headline'] = st.text_input(
                    "Headline Text", 
                    st.session_state.banner_text['gips_headline'],
                    key="gips_headline_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            
        elif banner_selection == "Modern Design":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['modern_brand'] = st.text_input(
                    "Brand Text", 
                    st.session_state.banner_text['modern_brand'],
                    key="modern_brand_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['modern_date'] = st.text_input(
                    "Date Text", 
                    st.session_state.banner_text['modern_date'],
                    key="modern_date_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['modern_tagline'] = st.text_input(
                    "Tagline Text", 
                    st.session_state.banner_text['modern_tagline'],
                    key="modern_tagline_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            
        elif banner_selection == "Gradient Style":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['gradient_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text['gradient_title'],
                    key="gradient_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['gradient_subtitle'] = st.text_input(
                    "Subtitle", 
                    st.session_state.banner_text['gradient_subtitle'],
                    key="gradient_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['gradient_edition'] = st.text_input(
                    "Edition Text", 
                    st.session_state.banner_text['gradient_edition'],
                    key="gradient_edition_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            
        elif banner_selection == "Minimalist":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['minimalist_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('minimalist_title', DEFAULT_BANNER_TEXTS['minimalist_title']),
                    key="minimalist_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['minimalist_subtitle'] = st.text_input(
                    "Subtitle", 
                    st.session_state.banner_text.get('minimalist_subtitle', DEFAULT_BANNER_TEXTS['minimalist_subtitle']),
                    key="minimalist_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['minimalist_date'] = st.text_input(
                    "Date", 
                    st.session_state.banner_text.get('minimalist_date', DEFAULT_BANNER_TEXTS['minimalist_date']),
                    key="minimalist_date_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )

        elif banner_selection == "Split Design":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['split_brand'] = st.text_input(
                    "Brand Text", 
                    st.session_state.banner_text.get('split_brand', DEFAULT_BANNER_TEXTS['split_brand']),
                    key="split_brand_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['split_tagline'] = st.text_input(
                    "Tagline", 
                    st.session_state.banner_text.get('split_tagline', DEFAULT_BANNER_TEXTS['split_tagline']),
                    key="split_tagline_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['split_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('split_title', DEFAULT_BANNER_TEXTS['split_title']),
                    key="split_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['split_description'] = st.text_input(
                    "Description", 
                    st.session_state.banner_text.get('split_description', DEFAULT_BANNER_TEXTS['split_description']),
                    key="split_description_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )

        elif banner_selection == "Bordered":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['bordered_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('bordered_title', DEFAULT_BANNER_TEXTS['bordered_title']),
                    key="bordered_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['bordered_subtitle'] = st.text_input(
                    "Subtitle", 
                    st.session_state.banner_text.get('bordered_subtitle', DEFAULT_BANNER_TEXTS['bordered_subtitle']),
                    key="bordered_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )

        elif banner_selection == "Geometric":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['geometric_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('geometric_title', DEFAULT_BANNER_TEXTS['geometric_title']),
                    key="geometric_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['geometric_subtitle'] = st.text_input(
                    "Subtitle", 
                    st.session_state.banner_text.get('geometric_subtitle', DEFAULT_BANNER_TEXTS['geometric_subtitle']),
                    key="geometric_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )

        elif banner_selection == "Wave":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['wave_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('wave_title', DEFAULT_BANNER_TEXTS['wave_title']),
                    key="wave_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['wave_subtitle'] = st.text_input(
                    "Subtitle", 
                    st.session_state.banner_text.get('wave_subtitle', DEFAULT_BANNER_TEXTS['wave_subtitle']),
                    key="wave_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['wave_date'] = st.text_input(
                    "Date", 
                    st.session_state.banner_text.get('wave_date', DEFAULT_BANNER_TEXTS['wave_date']),
                    key="wave_date_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )

        elif banner_selection == "Boxed":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.banner_text['boxed_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('boxed_title', DEFAULT_BANNER_TEXTS['boxed_title']),
                    key="boxed_title_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
                st.session_state.banner_text['boxed_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('boxed_subtitle', DEFAULT_BANNER_TEXTS['boxed_subtitle']),
                    key="boxed_subtitle_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
            with col2:
                st.session_state.banner_text['boxed_badge'] = st.text_input(
                    "Badge Text", 
                    st.session_state.banner_text.get('boxed_badge', DEFAULT_BANNER_TEXTS['boxed_badge']),
                    key="boxed_badge_text_newsletter",
                    on_change=update_preview_on_change  # Direct update on change
                )
        
        elif banner_selection == "Upload Custom HTML Banner":
            banner_html_file = st.file_uploader(
                "Upload your HTML banner file", 
                type=["html", "htm"],
                key="custom_banner_newsletter",
                on_change=update_preview_on_change  # Direct update on change
            )
            
            if banner_html_file:
                st.success("HTML banner uploaded successfully!")
            else:
                # Default to corpcomm_banner if no upload
                st.info("No custom banner uploaded. Using default BlackRock Corporate banner.")
        
        # Debug checkbox for banner content
        debug_mode = st.checkbox("Debug Mode (Show HTML content)", value=False, key="debug_mode_newsletter")
        if debug_mode:
            if banner_selection != "Upload Custom HTML Banner" or (banner_selection == "Upload Custom HTML Banner" and not banner_html_file):
                # For preloaded banners, show their content
                html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
                st.subheader(f"HTML Content for {banner_selection}")
                st.code(html_content, language="html")
            elif banner_html_file:
                from services.banner_service import extract_banner_from_html
                banner_html, banner_styles = extract_banner_from_html(banner_html_file)
                if banner_html:
                    st.subheader("Extracted Banner HTML")
                    st.code(banner_html, language="html")
                    if banner_styles:
                        st.subheader("Extracted Banner Styles")
                        st.code(banner_styles, language="css")
                else:
                    st.error("Failed to extract banner HTML from the file.")
    
    # Email functionality
    st.subheader("Email Your Newsletter")
    with st.expander("Send Newsletter via Email", expanded=False):
        st.markdown("""
        <div style="background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin-top: 20px;">
            <h3>Send Newsletter</h3>
            <p>Send your newsletter directly via email to your recipients.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            sender_email = st.text_input(
                "From Email", 
                placeholder="your.name@company.com",
                key="sender_email_newsletter"
            )
        
        with col2:
            email_subject = st.text_input(
                "Subject", 
                f"Newsletter: {datetime.now().strftime('%B %d, %Y')}",
                key="email_subject_newsletter"
            )
        
        # Email recipients
        to_emails = st.text_area(
            "To Emails (comma separated)", 
            placeholder="recipient1@company.com, recipient2@company.com",
            key="to_emails_newsletter"
        )
        
        # Optional CC and BCC
        col1, col2 = st.columns(2)
        with col1:
            cc_emails = st.text_area(
                "CC", 
                placeholder="cc1@company.com, cc2@company.com",
                key="cc_emails_newsletter",
                height=80
            )
        
        with col2:
            bcc_emails = st.text_area(
                "BCC", 
                placeholder="bcc1@company.com, bcc2@company.com",
                key="bcc_emails_newsletter",
                height=80
            )
        
        # Attachment options
        attach_newsletter = st.checkbox("Attach newsletter as HTML file", value=False, key="attach_newsletter_checkbox")
        
        # Send button
        if st.button("Send Newsletter Email", use_container_width=True, key="send_email_btn_newsletter"):
            if 'newsletter_html' not in st.session_state:
                st.error("Please generate the newsletter first.")
            elif not sender_email:
                st.error("Please enter your email address.")
            elif not to_emails:
                st.error("Please enter at least one recipient email address.")
            else:
                # Get the HTML content from session state
                newsletter_html = st.session_state.newsletter_html
                
                # Only save to disk if needed for attachment
                output_path = None
                if attach_newsletter:
                    output_path = save_newsletter_for_sending()
                
                with st.spinner("Sending email ..."):
                    # Create email sender
                    email_sender = EmailSender()
                    
                    # Prepare attachments if needed
                    attachments = [output_path] if output_path else None
                    
                    # Send the email using the in-memory HTML
                    success, message = email_sender.send_html_email(
                        from_email=sender_email,
                        to_emails=to_emails,
                        subject=email_subject,
                        html_content=newsletter_html,  # Use the in-memory HTML
                        cc_emails=cc_emails,
                        bcc_emails=bcc_emails,
                        attachments=attachments
                    )
                    
                    if success:
                        st.success(message)
                        # Add to history
                        to_count = len([email.strip() for email in to_emails.split(',') if email.strip()])
                        cc_count = len([email.strip() for email in cc_emails.split(',') if email.strip()]) if cc_emails else 0
                        bcc_count = len([email.strip() for email in bcc_emails.split(',') if email.strip()]) if bcc_emails else 0
                        
                        st.session_state.email_history.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'recipients': to_count + cc_count + bcc_count,
                            'subject': email_subject
                        })
                    else:
                        st.error(f"Failed to send email: {message}")
                        
                    # Clean up temporary file if it was created
                    if output_path and os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except Exception:
                            pass  # Ignore cleanup errors
    
    # Manual generation button
    st.subheader("Manual Generation")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("If the preview doesn't update automatically, click this button.")
    with col2:
        if st.button("Force Regenerate", use_container_width=True, key="force_regenerate_btn_manual"):
            update_preview_on_change()
            st.success("Newsletter regenerated successfully!")

# Add the newsletter preview on the right column
with right_col:
    st.subheader("Newsletter Preview")
    
    # Force update at the beginning to ensure preview is up-to-date
    if df is not None and 'newsletter_html' not in st.session_state:
        update_preview_on_change()
    
    # Add controls for preview
    preview_controls_col1, preview_controls_col2 = st.columns([3, 1])
    
    with preview_controls_col1:
        # Add slider to adjust preview height
        preview_height = st.slider(
            "Preview Height (px)",
            min_value=400,
            max_value=2000,
            value=800,
            step=100,
            key="preview_height_slider"
        )
    
    with preview_controls_col2:
        # Force regenerate button
        if st.button("Force Regenerate", type="primary", use_container_width=True, key="force_regenerate_btn_preview"):
            update_preview_on_change()
            st.success("Newsletter regenerated successfully!")
    
    # Display the newsletter preview
    if 'newsletter_html' in st.session_state and st.session_state.newsletter_html:
        preview_container = st.container()
        with preview_container:
            try:
                import streamlit.components.v1 as components
                
                # Use the user-defined preview height
                components.html(
                    st.session_state.newsletter_html, 
                    height=preview_height,
                    scrolling=True
                )
                
            except ImportError:
                st.error("Unable to import streamlit.components.v1 for HTML preview.")
                with st.expander("View Newsletter HTML Code"):
                    st.code(st.session_state.newsletter_html, language='html')
                
            st.caption("Note: The preview above shows how your newsletter will look. You can scroll to see the entire content.")
            
            # Add download button for the current preview
            if st.button("Download HTML", use_container_width=True):
                # Save current version to disk
                output_path = save_newsletter_for_sending()
                if output_path:
                    with open(output_path, "r", encoding="utf-8") as file:
                        html_content = file.read()
                        
                    # Create download link
                    b64 = base64.b64encode(html_content.encode()).decode()
                    download_filename = f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    href = f'<a href="data:text/html;base64,{b64}" download="{download_filename}">Click to download</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Clean up
                    try:
                        os.remove(output_path)
                    except:
                        pass
    else:
        # If no newsletter has been generated yet but we have data, trigger the update function
        if df is not None:
            st.info("Generating preview...")
            update_preview_on_change()
            st.rerun()  # Force a refresh to show the updated preview
        else:
            st.info("Configure your newsletter using the options on the left to see a preview here.")

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()