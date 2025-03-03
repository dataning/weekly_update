import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
from newsletter_generator import NewsletterGenerator
import re
from bs4 import BeautifulSoup

# Set page configuration as the very first Streamlit command
st.set_page_config(
    page_title="Newsletter Generator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add a navigation section at the top
st.markdown("""
<style>
    .nav-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.5rem 1rem;
        background-color: #f0f2f6;
        color: #262730;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 1rem;
        border: none;
        cursor: pointer;
    }
    .nav-button:hover {
        background-color: #e0e2e6;
    }
</style>
""", unsafe_allow_html=True)

# Navigation bar
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back to Home", key="back_to_home"):
        try:
            from streamlit.runtime.scriptrunner import RerunData, RerunException
            from streamlit.source_util import get_pages
            
            def switch_page(page_name):
                def standardize_name(name):
                    return name.lower().replace("_", " ")
                page_name = standardize_name(page_name)
                pages = get_pages("app.py")
                for page_hash, config in pages.items():
                    if standardize_name(config["page_name"]) == page_name:
                        raise RerunException(
                            RerunData(
                                page_script_hash=page_hash,
                                page_name=page_name,
                            )
                        )
            
            # Debug: print available pages to verify
            pages = get_pages("app.py")
            st.write(pages)
            
            switch_page("app")
        except Exception as e:
            # Fallback: set session state flag and rerun
            st.session_state.page = "home"
            st.rerun()

# App title (displayed only once)
st.title("📧 Newsletter Generator")

# ---- Function definitions below ----

def update_html_dimensions(html_content, width):
    """
    Updates all occurrences of width:800px and width="800" in HTML content,
    adjusting other related dimensions.
    """
    html_content = re.sub(r'width:800px', f'width:{width}px', html_content)
    html_content = re.sub(r'width="800"', f'width="{width}"', html_content)
    html_content = re.sub(r'width:800px !important;', f'width:{width}px !important;', html_content)
    html_content = re.sub(r'max-width:800px !important;', f'max-width:{width}px !important;', html_content)
    html_content = re.sub(
        r'style="(.*?)width:800px(.*?)"',
        f'style="\\1width:{width}px\\2"',
        html_content
    )
    html_content = re.sub(
        r'style="background-color:#ffffff; width:800px;"',
        f'style="background-color:#ffffff; width:{width}px;"', 
        html_content
    )
    return html_content

def generate_prompt(df, selected_indices):
    """
    Generate a prompt for summarization based on selected articles.
    """
    if not selected_indices:
        return ""
    
    prompt = """You're a 10-year experienced financial journalist and summarize the following financial information as a breakfast briefing.

"""
    for i, idx in enumerate(selected_indices):
        row = df.iloc[idx]
        prompt += f"Article {i+1}:\n"
        prompt += f"Title: {row.get('Article_Title', '')}\n"
        prompt += f"Company: {row.get('Company', '')}\n"
        prompt += f"Source: {row.get('Source', '')}\n"
        prompt += f"Date: {row.get('Date', '')}\n"
        prompt += f"Content: {row.get('Content', '')}\n\n"
    
    prompt += """
Please provide a concise but comprehensive summary of these articles. The summary should:
1. Capture the key information and trends
2. Be written in a professional journalistic style
3. Be formatted in Markdown with appropriate headings
4. Be suitable for inclusion in a financial newsletter
5. Be between 200-300 words
"""
    return prompt

def inject_summary(html_content, summary_html):
    """
    Injects summary HTML after the "Additional Information" section.
    """
    if not summary_html or not html_content:
        return html_content
    
    target_pattern = r'<div>Please submit any feedback.*?<\/div>'
    
    if not re.search(target_pattern, html_content):
        target_pattern = r'<div>Additional Information:.*?<\/div>'
        if not re.search(target_pattern, html_content):
            st.warning("Could not find the exact insertion point. Summary will be added at the top of the newsletter.")
            return html_content.replace('<table cellspacing="0" cellpadding="0" border="0" width="100%" align="center" class="full-width">', 
                                       f'<table cellspacing="0" cellpadding="0" border="0" width="100%" align="center" class="full-width">\n<tr><td colspan="3">{summary_html}</td></tr>')
    
    modified_html = re.sub(
        target_pattern, 
        lambda match: f"{match.group(0)}\n<div>{summary_html}</div>",
        html_content,
        count=1
    )
    return modified_html

# Default banner HTML templates
BANNER_HTML_TEMPLATES = {
    "blue": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #e6f2ff; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #0168b1;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #0168b1; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "green": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #F0F7F0; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #2C8B44;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #1A5D2B; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "purple": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #F5F0FF; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #673AB7;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #4A148C; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "corporate": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #1D2951; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #D74B4B;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #FFFFFF; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """
}

def extract_banner_from_html(html_file, content_width=800):
    """
    Extract banner HTML from an uploaded HTML file and adjust its width.
    Returns the banner HTML content and any CSS styles.
    
    Args:
        html_file: The uploaded HTML file
        content_width: The desired width for the banner (defaults to 800px)
    """
    if html_file is None:
        return None, None
    
    try:
        content = html_file.getvalue().decode('utf-8')
        
        # First try to parse with BeautifulSoup for reliable extraction
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract all styles
        style_content = ""
        style_tags = soup.find_all('style')
        for style in style_tags:
            style_content += style.string if style.string else ""
        
        # Extract banner div
        banner_div = soup.select_one('.banner')
        
        if banner_div:
            banner_html = str(banner_div)
        # If no specific banner class, try to get the body content
        elif soup.body and soup.body.div:
            banner_html = str(soup.body.div)
        else:
            # Last resort, try regex extraction
            if '<div class="banner"' in content:
                # Extract the banner div with possible nested content
                banner_match = re.search(r'<div class="banner".*?>(.*?</div>)\s*</div>', content, re.DOTALL)
                if banner_match:
                    banner_html = f'<div class="banner">{banner_match.group(1)}</div>'
                else:
                    return None, None
            else:
                return None, None
        
        # Preserve the original styles but adjust widths
        if style_content:
            # First convert all px values to use consistent format for easier regex
            style_content = re.sub(r'(\d+)px', r'\1px', style_content)
            
            # Modify the banner width in CSS
            style_content = re.sub(
                r'(\.banner\s*\{[^}]*?)width\s*:\s*\d+px', 
                f'\\1width: {content_width}px', 
                style_content
            )
            
            # Add responsive styles
            if '@media' not in style_content:
                style_content += f"""
                @media only screen and (max-width: 480px) {{
                    .banner {{
                        width: 100% !important;
                        max-width: 100% !important;
                    }}
                    .top-section, .middle-bar, .bottom-section, .top-bar, .middle-bar, .bottom-bar {{
                        width: 100% !important;
                    }}
                }}
                """
        
        # Adjust the HTML width attributes
        banner_html = re.sub(r'width\s*=\s*["\']\d+["\']', f'width="{content_width}"', banner_html)
        banner_html = re.sub(r'width\s*=\s*\d+', f'width="{content_width}"', banner_html)
        
        # Adjust inline styles
        banner_html = re.sub(
            r'style\s*=\s*(["\'])(.*?)width\s*:\s*\d+px(.*?)(["\'])', 
            f'style=\\1\\2width: {content_width}px\\3\\4', 
            banner_html
        )
        
        # Add class for responsive design if not present
        if 'class="banner"' in banner_html and 'content-width' not in banner_html:
            banner_html = banner_html.replace('class="banner"', 'class="banner content-width"')
        
        return banner_html, style_content
    
    except Exception as e:
        st.error(f"Error extracting banner from HTML: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None

def inject_banner_into_newsletter(html_content, banner_html, banner_styles=None, content_width=800):
    """
    Injects the custom banner HTML directly into the newsletter HTML.
    
    Args:
        html_content: The newsletter HTML content
        banner_html: The banner HTML to inject
        banner_styles: CSS styles for the banner
        content_width: The desired width for the banner
    """
    if not banner_html or not html_content:
        return html_content
    
    # Find the location to insert the banner
    banner_insertion_marker = "<!-- Custom Banner -->"
    if banner_insertion_marker not in html_content:
        st.warning("Could not find the banner insertion point in the template.")
        return html_content
    
    # Process banner styles to make them more specific and avoid conflicts
    if banner_styles:
        # Make banner styles more specific to avoid conflicts with newsletter styles
        processed_styles = banner_styles
        
        # Add a scoping selector to banner styles to avoid conflicts
        processed_styles = processed_styles.replace(
            ".banner {", 
            ".newsletter-custom-banner .banner {"
        )
        processed_styles = processed_styles.replace(
            ".top-section", 
            ".newsletter-custom-banner .top-section"
        )
        processed_styles = processed_styles.replace(
            ".middle-bar", 
            ".newsletter-custom-banner .middle-bar"
        )
        processed_styles = processed_styles.replace(
            ".bottom-section", 
            ".newsletter-custom-banner .bottom-section"
        )
        processed_styles = processed_styles.replace(
            ".top-bar", 
            ".newsletter-custom-banner .top-bar"
        )
        processed_styles = processed_styles.replace(
            ".bottom-bar", 
            ".newsletter-custom-banner .bottom-bar"
        )
        
        # Add responsive overrides
        processed_styles += f"""
        @media only screen and (max-width:480px) {{
            .newsletter-custom-banner .banner,
            .newsletter-custom-banner .top-section,
            .newsletter-custom-banner .bottom-section,
            .newsletter-custom-banner .top-bar,
            .newsletter-custom-banner .middle-bar,
            .newsletter-custom-banner .bottom-bar {{
                width: 100% !important;
                max-width: 100% !important;
            }}
        }}
        """
        
        # Wrap banner with a container div for scoped styles
        banner_html = f'<div class="newsletter-custom-banner">{banner_html}</div>'
    else:
        processed_styles = ""
    
    # Insert the banner HTML and styles
    style_insertion = f"""<style type="text/css">
    /* Custom Banner Styles */
    {processed_styles}
    </style>
    """ if processed_styles else ""
    
    # Wrap in a table structure that matches the newsletter format
    table_wrapped_banner = f"""
    <table cellspacing="0" cellpadding="0" border="0" width="{content_width}" align="center" class="content-width">
        <tr>
            <td align="center">
                {style_insertion}
                {banner_html}
            </td>
        </tr>
    </table>
    """
    
    # Replace the comment section with our banner
    modified_html = html_content.replace(
        banner_insertion_marker, 
        f"{banner_insertion_marker}\n{table_wrapped_banner}"
    )
    
    # Remove the default header image if it exists
    modified_html = modified_html.replace(
        '<img style="display:block; vertical-align:top; width:800px; height:auto;" vspace="0" hspace="0" border="0" height="auto" width="800" class="mobile-image" src="https://lbpscdn.lonebuffalo.com/clients/blackrockgif/assets/LB-BGIF-Header.jpg" alt="Newsletter Header">',
        '<!-- Header banner replaced by custom HTML banner -->'
    )
    
    return modified_html

def generate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_html_file=None, banner_type="blue", summary_html=""):
    generator = NewsletterGenerator('newsletter_template.html')
    output_path = os.path.join(TEMP_DIR, f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # Process banner HTML
    custom_banner_html = None
    custom_banner_styles = None
    if banner_html_file:
        # Extract and resize the banner to match content width
        custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_html_file, content_width)
        if not custom_banner_html:
            st.warning("Could not extract banner from HTML file. Using default banner.")
            custom_banner_html = BANNER_HTML_TEMPLATES.get(banner_type, BANNER_HTML_TEMPLATES["blue"])
            # Resize default banner too
            custom_banner_html = re.sub(r'width: 800px', f'width: {content_width}px', custom_banner_html)
    else:
        custom_banner_html = BANNER_HTML_TEMPLATES.get(banner_type, BANNER_HTML_TEMPLATES["blue"])
        # Resize default banner too
        custom_banner_html = re.sub(r'width: 800px', f'width: {content_width}px', custom_banner_html)
    
    # Create a default banner file for the initial generation
    # We'll replace this with our custom banner later
    banner_file_path = os.path.join(TEMP_DIR, f"temp_banner_{banner_type}.html")
    
    with open(banner_file_path, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
 <style>
/* Banner styles */
 </style>
</head>
<body>
<!-- This is a placeholder banner that will be replaced -->
</body>
</html>""")
    
    # Generate the initial newsletter
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path=output_path,
        preview_text=preview_text,
        column_mapping=column_mapping,
        colors=colors,
        banner_path=banner_file_path
    )
    
    # Read the generated newsletter
    with open(output_path, 'r', encoding='utf-8') as file:
        newsletter_html = file.read()
    
    # Inject our custom banner directly into the HTML
    newsletter_html = inject_banner_into_newsletter(
        newsletter_html, 
        custom_banner_html, 
        custom_banner_styles,
        content_width
    )
    
    # Add summary if provided
    if summary_html:
        newsletter_html = inject_summary(newsletter_html, summary_html)
    
    # Update dimensions
    newsletter_html = update_html_dimensions(newsletter_html, content_width)
    
    # Handle mobile responsiveness
    if not mobile_friendly:
        newsletter_html = newsletter_html.replace('@media only screen and (max-width:480px)', '@media only screen and (max-width:1px)')
    
    # Write the final HTML to file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(newsletter_html)
    
    # Clean up temporary banner file
    try:
        os.remove(banner_file_path)
    except:
        pass
        
    return newsletter_html, output_path

def get_download_link(html_content, filename):
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">Download HTML File</a>'
    return href

def create_column_mapping_interface(df):
    columns = list(df.columns)
    col1, col2 = st.columns(2)
    
    with col1:
        section_name_col = st.selectbox("Company/Section Name", options=columns, 
                                        index=columns.index("Company") if "Company" in columns else 0)
        news_type_col = st.selectbox("News Type", options=columns, 
                                      index=columns.index("News_Type") if "News_Type" in columns else 0)
        article_title_col = st.selectbox("Article Title", options=columns, 
                                         index=columns.index("Article_Title") if "Article_Title" in columns else 0)
    with col2:
        source_col = st.selectbox("Source", options=columns, 
                                  index=columns.index("Source") if "Source" in columns else 0)
        date_col = st.selectbox("Date", options=columns, 
                               index=columns.index("Date") if "Date" in columns else 0)
        content_col = st.selectbox("Content", options=columns, 
                                   index=columns.index("Content") if "Content" in columns else 0)
    
    column_mapping = {
        'section_name': section_name_col,
        'news_type': news_type_col,
        'article_title': article_title_col,
        'source': source_col,
        'date': date_col,
        'content': content_col
    }
    
    return column_mapping

# ---- End function definitions ----

# Create a temporary directory for files if it doesn't exist
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Main content area for file upload
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to get started.")
    
    st.subheader("How It Works")
    st.markdown("""
    1. **Upload CSV data** with your newsletter content
    2. **Select articles** from the data preview to summarize
    3. **Generate a prompt** for your preferred LLM tool
    4. **Paste the generated summary** back into the app
    5. **Customize appearance** with color themes, banner styles, and width options
    6. **Upload your custom HTML banner** to personalize the newsletter
    7. **Generate and preview** your newsletter
    8. **Download** the HTML file for use in your email platform
    """)
    
    st.subheader("CSV Format Example")
    sample_data = [
        {
            "Company": "FakeCorp",
            "News_Type": "Company News",
            "Article_Title": "FakeCorp Launches Revolutionary Product",
            "Source": "Tech Insider",
            "Date": "01 March 2025",
            "Content": "FakeCorp has unveiled a revolutionary product designed to disrupt the industry..."
        },
        {
            "Company": "FakeCorp",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "No news updates this week",
            "Source": None,
            "Date": None,
            "Content": None
        }
    ]
    
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df)
    
    csv = sample_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="sample_newsletter_data.csv">Download sample CSV file</a>'
    st.markdown(href, unsafe_allow_html=True)
else:
    try:
        df = pd.read_csv(uploaded_file)
        unnamed_cols = [col for col in df.columns if 'Unnamed:' in col]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        left_col, right_col = st.columns([6, 4])
        regenerate = False
        banner_html_file = None
        
        with left_col:
            st.subheader("Configuration")
            with st.expander("Data Preview & Summary Generator", expanded=True):
                st.caption("Select rows in the table below to include in the newsletter summary")
                if 'selected' not in df.columns:
                    df['selected'] = False
                
                desired_order = ['selected', 'Company', 'Source', 'Article_Title', 'Date', 'Content', 'News_Type']
                existing_cols = list(df.columns)
                ordered_cols = [col for col in desired_order if col in existing_cols]
                ordered_cols += [col for col in existing_cols if col not in desired_order and col != 'selected']
                df = df[ordered_cols]
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "selected": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select this row for summarization",
                            default=False,
                        ),
                        "Date": st.column_config.TextColumn(
                            "Date",
                            help="Publication date"
                        )
                    },
                    hide_index=True,
                    height=400,
                    use_container_width=True
                )
                
                selected_indices = edited_df.index[edited_df['selected'] == True].tolist()
                st.session_state.selected_rows = selected_indices
                
                if selected_indices:
                    st.info(f"{len(selected_indices)} articles selected for summarization.")
            
            if selected_indices:
                st.subheader("Generate Summary")
                prompt_tab, summary_tab = st.tabs(["1. Get Prompt for LLM", "2. Add Generated Summary"])
                
                with prompt_tab:
                    prompt = generate_prompt(df, selected_indices)
                    st.markdown("### Copy this prompt to your preferred LLM:")
                    copy_col1, copy_col2 = st.columns([5, 1])
                    with copy_col2:
                        if st.button("📋 Copy", use_container_width=True):
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
                    user_summary = st.text_area("Paste your generated summary here:", height=200)
                    
                    if user_summary:
                        formatted_summary = f"""
                        <div style="color: #333333; font-family: 'BLK Fort', 'Arial', Arial, sans-serif; font-size: 14px; line-height: 22px; padding: 15px 0;">
                            <h3 style="color: #000000; font-size: 18px; margin-bottom: 10px; border-bottom: 1px solid #cccccc; padding-bottom: 5px;">Weekly Summary</h3>
                            {user_summary.replace('\n', '<br>')}
                        </div>
                        """
                        
                        if st.button("Add Summary to Newsletter", use_container_width=True):
                            st.session_state.summary_html = formatted_summary
                            if 'newsletter_html' in st.session_state:
                                with st.spinner("Updating newsletter with summary..."):
                                    output_path = st.session_state.get('output_path', '')
                                    if output_path and os.path.exists(output_path):
                                        with open(output_path, 'r', encoding='utf-8') as file:
                                            current_html = file.read()
                                        updated_html = inject_summary(current_html, formatted_summary)
                                        with open(output_path, 'w', encoding='utf-8') as file:
                                            file.write(updated_html)
                                        st.session_state.newsletter_html = updated_html
                                    st.success("Summary added and newsletter updated! Check the preview.")
                                    st.balloons()
                            else:
                                st.success("Summary added! Now click 'Generate Newsletter' to see it included.")
                        
                        st.markdown("**Preview of formatted summary:**")
                        st.markdown(formatted_summary, unsafe_allow_html=True)
            
            column_mapping = {
                'section_name': "Company" if "Company" in df.columns else df.columns[0],
                'news_type': "News_Type" if "News_Type" in df.columns else df.columns[1],
                'article_title': "Article_Title" if "Article_Title" in df.columns else df.columns[2],
                'source': "Source" if "Source" in df.columns else df.columns[3],
                'date': "Date" if "Date" in df.columns else df.columns[4],
                'content': "Content" if "Content" in df.columns else df.columns[5]
            }
            
            with st.expander("Color Settings", expanded=True):
                color_theme = st.selectbox(
                    "Select a color theme",
                    ["Blue (Default)", "Green", "Purple", "Corporate", "Custom"]
                )
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
                elif color_theme == "Custom":
                    st.caption("Choose your custom colors")
                    colors = {
                        'primary': st.color_picker("Primary Color", '#0168b1'),
                        'secondary': st.color_picker("Secondary Color", '#333333'),
                        'background': st.color_picker("Background Color", '#e6e6e6'),
                        'header_bg': st.color_picker("Header Background", '#0168b1'),
                        'footer_bg': st.color_picker("Footer Background", '#000000'),
                        'highlight': st.color_picker("Highlight Color", '#0168b1')
                    }
                    default_banner = "blue"
                
                # Banner selection
                banner_options = ["Upload Custom HTML Banner", "Match with theme", "Blue", "Green", "Purple", "Corporate"]
                banner_selection = st.radio(
                    "Choose a banner style:",
                    banner_options,
                    horizontal=True,
                    index=0
                )
                
                if banner_selection == "Upload Custom HTML Banner":
                    banner_html_file = st.file_uploader("Upload your HTML banner file", type=["html", "htm"])
                    if banner_html_file:
                        banner_html, banner_styles = extract_banner_from_html(banner_html_file)
                        if banner_html:
                            st.success("HTML banner uploaded successfully!")
                            # Preview the banner HTML
                            st.markdown("**Banner Preview:**")
                            st.markdown(f'<div style="border: 1px solid #ccc; border-radius: 5px; overflow: hidden;">{banner_html}</div>', unsafe_allow_html=True)
                        else:
                            st.warning("Could not extract banner HTML from file. Check the structure of your HTML file.")
                    selected_banner = default_banner  # Fallback if HTML parsing fails
                elif banner_selection == "Match with theme":
                    selected_banner = default_banner
                else:
                    selected_banner = banner_selection.lower()
                
                # Debug checkbox for banner content
                debug_mode = st.checkbox("Debug Mode (Show extracted banner content)", value=False)
                if debug_mode and banner_html_file:
                    banner_html, banner_styles = extract_banner_from_html(banner_html_file)
                    if banner_html:
                        st.subheader("Extracted Banner HTML")
                        st.code(banner_html, language="html")
                        if banner_styles:
                            st.subheader("Extracted Banner Styles")
                            st.code(banner_styles, language="css")
                    else:
                        st.error("Failed to extract banner HTML from the file.")
            
            with st.expander("Layout Settings", expanded=True):
                content_width = st.slider("Content Width (px)", 600, 1000, 800)
                mobile_friendly = st.checkbox("Mobile-friendly design", value=True)
            
            with st.expander("Email Settings", expanded=True):
                preview_text = st.text_input("Preview Text", "Your newsletter preview text here")
            
            if st.button("Generate Newsletter", type="primary", use_container_width=True):
                regenerate = True
            
            if 'newsletter_html' in st.session_state:
                st.markdown("### Download Options")
                st.markdown(get_download_link(st.session_state.newsletter_html, "newsletter.html"), unsafe_allow_html=True)
                st.download_button(
                    "Download HTML Code",
                    st.session_state.newsletter_html,
                    file_name="newsletter.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        with right_col:
            st.subheader("Newsletter Preview")
            preview_controls_col1, preview_controls_col2 = st.columns([3, 1])
            with preview_controls_col1:
                preview_mode = st.radio("Preview Mode", ["Visual Preview", "HTML Code"], horizontal=True)
                device_preview = st.radio("Device", ["Desktop", "Mobile (Simulated)"], horizontal=True)
            with preview_controls_col2:
                preview_height = st.slider("Height", 600, 1200, 800)
            
            if regenerate or 'newsletter_html' not in st.session_state:
                with st.spinner("Generating newsletter..."):
                    summary_html = st.session_state.get('summary_html', "")
                    newsletter_html, output_path = generate_newsletter(
                        df,
                        column_mapping,
                        colors,
                        preview_text,
                        content_width,
                        mobile_friendly,
                        banner_html_file,
                        selected_banner,
                        summary_html
                    )
                    st.session_state.newsletter_html = newsletter_html
                    st.session_state.output_path = output_path
            
            preview_container = st.container()
            if preview_mode == "Visual Preview":
                with preview_container:
                    st.markdown(
                        f"""
                        <div style="border:1px solid #ddd; border-radius:5px;">
                            <div style="background-color:#f0f0f0; padding:8px; border-radius:5px 5px 0 0;">
                                <strong>{"📱 Mobile Preview" if device_preview=="Mobile (Simulated)" else "🖥️ Desktop Preview"}</strong>
                            </div>
                            <div style="{"max-width:480px; margin:0 auto;" if device_preview=="Mobile (Simulated)" else ""}">
                        """, unsafe_allow_html=True
                    )
                    iframe_height = preview_height
                    html_with_script = f"""
                    <iframe srcdoc="{st.session_state.newsletter_html.replace('"', '&quot;')}" 
                            width="100%" 
                            height="{iframe_height}px" 
                            style="border: none; overflow: auto;">
                    </iframe>
                    """
                    st.components.v1.html(html_with_script, height=iframe_height+50, scrolling=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                st.code(st.session_state.newsletter_html, language="html")
                
    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        
st.markdown("---")
st.markdown("Newsletter Generator App - Created with Streamlit 📧")