import streamlit as st
import pandas as pd
import os
import base64
import io
from PIL import Image
from datetime import datetime, timedelta
import time
import re
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import uuid

# Import banner utilities from the banner_template module
from banner_templates import (
    ensure_banner_files,
    get_modified_banner_html,
    extract_banner_from_html,
    inject_banner_into_newsletter,
    update_html_dimensions,
    COLOR_BANNER_TEMPLATES,
    BANNER_FILENAMES,
    DEFAULT_BANNER_TEXTS
)

# Set up logging for email functionality
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EmailSender')

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
    
    /* Add CSS to make preview more responsive */
    .preview-container iframe {
        width: 100%;
        border: none;
        transition: all 0.3s ease;
    }
    
    /* Fix for components with on_change */
    div[data-testid="stForm"] {
        background-color: transparent;
        border: none;
        padding: 0;
    }
    
    /* Style for summary section */
    .summary-section {
        background-color: #f8f9fa;
        border-left: 3px solid #0168b1;
        padding: 10px 15px;
        margin: 10px 0;
    }
    
    /* Style for image preview */
    .image-preview {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Style for email form */
    .email-form {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Create banners directory if it doesn't exist
BANNERS_DIR = "banners"
if not os.path.exists(BANNERS_DIR):
    os.makedirs(BANNERS_DIR)

# Initialize session state for tracking changes
if 'last_config' not in st.session_state:
    st.session_state.last_config = {
        'color_theme': None,
        'banner_selection': None,
        'content_width': None,
        'mobile_friendly': None,
        'preview_text': None,
        'summary_html': None,
        'image_html': None,
        'banner_text': {}
    }
if 'needs_update' not in st.session_state:
    st.session_state.needs_update = True
if 'newsletter_error' not in st.session_state:
    st.session_state.newsletter_error = False
if 'banner_text' not in st.session_state:
    st.session_state.banner_text = DEFAULT_BANNER_TEXTS.copy()
if 'preview_updating' not in st.session_state:
    st.session_state.preview_updating = False
if 'summary_html' not in st.session_state:
    st.session_state.summary_html = ""
if 'image_html' not in st.session_state:
    st.session_state.image_html = ""
if 'email_history' not in st.session_state:
    st.session_state.email_history = []

# Ensure all banner files are present in the banners directory
ensure_banner_files(BANNERS_DIR)

# IMPROVED: Auto-update trigger function - centralized control
def trigger_update():
    st.session_state.needs_update = True
    st.session_state.newsletter_error = False

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

# Email Sender class for sending HTML emails
class EmailSender:
    """
    Class for sending HTML-templated emails via BlackRock's internal mail server.
    """
    
    def __init__(self, internal_mail_server='mailhub.blackrock.com'):
        """
        Initialize email sender with BlackRock's internal mail server
        """
        self.mail_server = internal_mail_server
        
    def _html_to_text(self, html):
        """
        Simple converter from HTML to plain text.
        """
        # Remove HTML tags
        text = re.sub(r'<.*?>', ' ', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Replace common HTML entities
        replacements = {
            '&nbsp;': ' ', 
            '&lt;': '<', 
            '&gt;': '>', 
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'",
            '&ndash;': '-',
            '&mdash;': '--'
        }
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
            
        return text.strip()
    
    def send_html_email(self, from_email, to_emails, subject, html_content, cc_emails=None, bcc_emails=None):
        """
        Send an HTML email via BlackRock's internal mail server
        
        Args:
            from_email (str): Sender's email address
            to_emails (str or list): Recipient email(s) - can be a string or list
            subject (str): Email subject
            html_content (str): HTML content as a string
            cc_emails (str or list): CC recipients - can be a string or list
            bcc_emails (str or list): BCC recipients - can be a string or list
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Convert email parameters to lists if they're strings
        if isinstance(to_emails, str):
            to_emails = [email.strip() for email in to_emails.split(',') if email.strip()]
            
        if cc_emails and isinstance(cc_emails, str):
            cc_emails = [email.strip() for email in cc_emails.split(',') if email.strip()]
            
        if bcc_emails and isinstance(bcc_emails, str):
            bcc_emails = [email.strip() for email in bcc_emails.split(',') if email.strip()]
            
        # Create message container
        msg_root = MIMEMultipart('related')
        msg_root['Subject'] = subject
        msg_root['From'] = from_email
        msg_root['To'] = ", ".join(to_emails)
        
        # Add CC if provided
        if cc_emails:
            msg_root['Cc'] = ", ".join(cc_emails)
            # Add CC emails to recipient list for sending
            to_emails.extend(cc_emails)
            
        # Add BCC if provided (only to recipient list, not headers)
        if bcc_emails:
            to_emails.extend(bcc_emails)
            
        msg_root.preamble = 'This is a multi-part message in MIME format.'
        
        # Create alternative part for HTML/plain text
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        
        try:
            # Create plain text version
            text_content = self._html_to_text(html_content)
            
            # Attach text part
            msg_text_plain = MIMEText(text_content, 'plain')
            msg_alternative.attach(msg_text_plain)
            
            # Attach HTML part
            msg_text_html = MIMEText(html_content, 'html')
            msg_alternative.attach(msg_text_html)
            
        except Exception as e:
            logger.error(f"Error processing HTML content: {e}")
            return False, f"Error processing HTML content: {e}"
        
        # Send the email
        try:
            with smtplib.SMTP(self.mail_server) as server:
                server.send_message(msg_root)
                recipients_count = len(to_emails)
                logger.info(f"Email sent successfully to {recipients_count} recipient(s)")
                return True, f"Email sent successfully to {recipients_count} recipient(s)"
                
        except Exception as e:
            error_msg = f"Failed to send email. Error: {e}"
            logger.error(error_msg)
            return False, error_msg

# Apply summary at a specific position 
def apply_summary_at_position(html_content, summary_html, position="after_banner"):
    """
    Apply the summary at a specific position in the newsletter.
    Works entirely in memory - no file operations.
    """
    if not summary_html or not html_content:
        return html_content
    
    # First priority: Always look for the Please submit any feedback section
    feedback_container_patterns = [
        r'(<div[^>]*>\s*Please submit any feedback:.*?<\/div>)',  # Standard pattern
        r'(<div[^>]*>\s*Please submit any feedback\s*:.*?<\/div>)',  # With spacing
        r'(<div[^>]*>\s*Additional\s+Information:.*?<\/div>)',  # With word spacing
        r'(<div[^>]*class=["\']footer-info["\'][^>]*>.*?Please submit any feedback.*?<\/div>)',  # With class
        r'(<tr[^>]*>\s*<td[^>]*>\s*Please submit any feedback:.*?<\/td>\s*<\/tr>)',  # Table-based footer
    ]
    
    # Try each pattern to find the Please submit any feedback section
    for pattern in feedback_container_patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            container = match.group(1)
            text_start = re.search(r'(Please submit any feedback)', container, re.IGNORECASE)
            if text_start:
                text_pos = text_start.start(1)
                new_container = container[:text_pos] + f"{summary_html} " + container[text_pos:]
                return html_content.replace(container, new_container)
            else:
                summary_div = f'{summary_html} '
                new_container = container.replace('>', '>' + summary_div, 1)
                return html_content.replace(container, new_container)
    
    # Simpler patterns if no match
    simpler_patterns = [
        r'(Please submit any feedback)',  # Just the text
        r'(Additional\s+Information:)',   # Just the section heading
    ]
    
    for pattern in simpler_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            text = match.group(1)
            summary_with_spacing = f'{summary_html} {text}'
            return html_content.replace(text, summary_with_spacing)
    
    # Position-based logic if no patterns match
    if position == "top" or position == "Top of newsletter":
        body_match = re.search(r'<body.*?>', html_content)
        if body_match:
            body_tag = body_match.group(0)
            return html_content.replace(
                body_tag,
                f"{body_tag}\n<div class='newsletter-summary'>{summary_html}</div>"
            )
    
    elif position == "after_banner" or position == "After banner":
        banner_patterns = [
            r'<!-- Custom Banner -->.*?</table>',  # After custom banner
            r'<img[^>]*Header\.jpg[^>]*>',         # After header image
            r'<div class="banner">.*?</div>'        # After banner div
        ]
        
        for pattern in banner_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                insertion_point = match.group(0)
                return html_content.replace(
                    insertion_point,
                    f"{insertion_point}\n<div class='newsletter-summary'>{summary_html}</div>"
                )
    
    elif position == "before_articles" or position == "Before articles":
        article_patterns = [
            r'<div class="articles-section">',     # Articles section
            r'<table[^>]*class="article-table"',   # Article table
            r'<h2[^>]*>Latest News</h2>'           # News heading
        ]
        
        for pattern in article_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                insertion_point = match.group(0)
                return html_content.replace(
                    insertion_point,
                    f"<div class='newsletter-summary'>{summary_html}</div>\n{insertion_point}"
                )
    
    # Fallback - add after BANNER_INSERTION_POINT marker
    banner_marker = "<!-- BANNER_INSERTION_POINT -->"
    if banner_marker in html_content:
        parts = html_content.split(banner_marker, 1)
        if len(parts) == 2:
            table_end_idx = parts[1].find("</table>")
            if table_end_idx > -1:
                insertion_point = table_end_idx + 8  # Length of "</table>"
                modified_html = parts[0] + banner_marker + parts[1][:insertion_point] + f"\n\n<!-- SUMMARY START -->\n{summary_html}\n<!-- SUMMARY END -->\n\n" + parts[1][insertion_point:]
                return modified_html
    
    # Ultimate fallback: append to beginning of HTML
    return f"<!-- SUMMARY START -->\n{summary_html}\n<!-- SUMMARY END -->\n\n{html_content}"

# Apply image at a specific position
def apply_image_content(html_content, image_html):
    """
    Apply the image and caption content below the summary section.
    """
    if not image_html or not html_content:
        return html_content
    
    # First approach: Look for the Weekly Summary heading and its container div
    weekly_summary_pattern = r'<h3[^>]*>Weekly Summary</h3>.*?</div>'
    match = re.search(weekly_summary_pattern, html_content, re.DOTALL)
    if match:
        # Insert the image right after the summary div
        summary_section = match.group(0)
        return html_content.replace(
            summary_section,
            f"{summary_section}\n{image_html}"
        )
    
    # Second approach: Try using BeautifulSoup for more reliable HTML parsing
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        summary_heading = soup.find('h3', string='Weekly Summary')
        if summary_heading:
            # Find the parent div containing the summary
            summary_div = summary_heading.find_parent('div')
            if summary_div:
                # Create a new tag from the image HTML
                img_soup = BeautifulSoup(image_html, 'html.parser')
                # Insert the image content after the summary div
                summary_div.insert_after(img_soup)
                return str(soup)
    except Exception as e:
        # Continue with fallback approaches if BeautifulSoup fails
        pass
    
    # Look for newsletter-summary class
    summary_class = 'newsletter-summary'
    if summary_class in html_content:
        pattern = f'<div class=[\'"]?{summary_class}[\'"]?.*?</div>'
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            insertion_point = match.group(0)
            return html_content.replace(
                insertion_point,
                f"{insertion_point}\n{image_html}"
            )
    
    # Try feedback section
    feedback_patterns = [
        r'(<div[^>]*>\s*Please submit any feedback:.*?<\/div>)',
        r'(<div[^>]*>\s*Please submit any feedback\s*:.*?<\/div>)'
    ]
    
    for pattern in feedback_patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            container = match.group(1)
            return html_content.replace(
                container,
                f"{image_html}\n{container}"
            )
    
    # Try after banner
    banner_patterns = [
        r'<!-- Custom Banner -->.*?</table>',
        r'<img[^>]*Header\.jpg[^>]*>',
        r'<div class="banner">.*?</div>'
    ]
    
    for pattern in banner_patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            insertion_point = match.group(0)
            return html_content.replace(
                insertion_point,
                f"{insertion_point}\n{image_html}"
            )
    
    # Fallback: add at beginning of body
    body_match = re.search(r'<body.*?>', html_content)
    if body_match:
        body_tag = body_match.group(0)
        return html_content.replace(
            body_tag,
            f"{body_tag}\n{image_html}"
        )
    
    return html_content

# ---- Function definitions ----

def generate_prompt(df, selected_indices):
    """
    Generate a prompt for summarization based on selected articles.
    """
    if not selected_indices:
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
    
    for idx in selected_indices:
        row = df.iloc[idx]
        
        # Safely handle values, converting to string and handling NaN/None
        def safe_value(value, default=''):
            import pandas as pd
            if pd.isna(value) or value is None:
                return default
            return str(value).replace('|', '-')
        
        title = safe_value(row.get('Article_Title', ''))
        company = safe_value(row.get('Company', ''))
        source = safe_value(row.get('Source', ''))
        date = safe_value(row.get('Date', ''))
        content = safe_value(row.get('Content', ''))
        
        # Truncate content for table readability
        if len(content) > 100:
            content = content[:97] + "..."
        
        prompt += f"| {title} | {company} | {source} | {date} | {content} |\n"
    
    return prompt

def generate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_input=None, banner_type="blue", summary_html="", image_html=""):
    """
    Generate a newsletter with all content including summary and images.
    """
    from newsletter_generator import NewsletterGenerator
    
    generator = NewsletterGenerator('newsletter_template.html')
    output_path = os.path.join(TEMP_DIR, f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # Process banner HTML
    custom_banner_html = None
    custom_banner_styles = None
    
    if banner_input:
        # Extract and resize the banner to match content width
        custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_input, content_width)
        
    if not custom_banner_html:
        custom_banner_html = COLOR_BANNER_TEMPLATES.get(banner_type, COLOR_BANNER_TEMPLATES["blue"])
        custom_banner_html = re.sub(r'width: 800px', f'width: {content_width}px', custom_banner_html)
    
    # Create temporary banner file
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
    
    # Generate the newsletter
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
    
    # Inject custom banner
    newsletter_html = inject_banner_into_newsletter(
        newsletter_html, 
        custom_banner_html, 
        custom_banner_styles,
        content_width
    )
    
    # Add summary if provided
    if summary_html:
        newsletter_html = apply_summary_at_position(newsletter_html, summary_html, "after_banner")
    
    # Add image if provided
    if image_html:
        newsletter_html = apply_image_content(newsletter_html, image_html)
    
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

# IMPROVED: Column mapping interface that works with existing columns
def create_column_mapping_interface(df):
    columns = list(df.columns)
    
    # Default to theme/Company for main categories
    theme_col_default = None
    if 'theme' in columns:
        theme_col_default = columns.index('theme')
    elif 'Company' in columns:
        theme_col_default = columns.index('Company')
    else:
        theme_col_default = 0
        
    # Default to subheader/News_Type for subcategories
    subheader_col_default = None
    if 'subheader' in columns:
        subheader_col_default = columns.index('subheader')
    elif 'News_Type' in columns:
        subheader_col_default = columns.index('News_Type')
    else:
        subheader_col_default = 0
    
    # Allow user to select which columns to use, with appropriate defaults
    theme_col = st.selectbox(
        "Theme Column", 
        options=columns, 
        index=theme_col_default,
        on_change=trigger_update
    )
    
    subheader_col = st.selectbox(
        "Subheader Column", 
        options=columns, 
        index=subheader_col_default,
        on_change=trigger_update
    )
    
    # Create mapping without modifying the dataframe
    column_mapping = {
        'theme': theme_col,
        'subheader': subheader_col,
        'article_title': 'Article_Title' if 'Article_Title' in columns else columns[0],
        'source': 'Source' if 'Source' in columns else columns[0],
        'date': 'Date' if 'Date' in columns else columns[0],
        'content': 'Content' if 'Content' in columns else columns[0]
    }
    
    return column_mapping

# Clean dataframe without adding columns
def clean_dataframe(df):
    # Make a clean copy of the dataframe
    df_clean = df.copy()
    
    # Remove unnamed columns
    unnamed_cols = [col for col in df_clean.columns if 'Unnamed:' in col]
    if unnamed_cols:
        df_clean = df_clean.drop(columns=unnamed_cols)
        
    # Add selection column if it doesn't exist (required for functionality)
    if 'selected' not in df_clean.columns:
        df_clean['selected'] = False
        
    # Handle date formatting if needed
    if 'Date' in df_clean.columns and df_clean['Date'].dtype == 'object':
        try:
            df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        except:
            pass  # Keep original if conversion fails
            
    return df_clean

# Add mapping explanation focused on theme and subheader
def add_mapping_explanation():
    with st.expander("About Theme & Subheader Structure", expanded=False):
        st.markdown("""
        ### Newsletter Organization Structure
        
        This newsletter generator organizes content using:
        
        - **Theme**: The main category for each section (select which column contains your themes)
        - **Subheader**: The subcategory within each theme (select which column contains your subheaders)
        
        #### Example Structure:
        ```
        Technology (Theme)
        ├── Product Updates (Subheader)
        │   ├── Article 1
        │   └── Article 2
        └── Industry News (Subheader)
            └── Article 3
        
        Finance (Theme)
        └── Market Analysis (Subheader)
            └── Article 4
        ```
        
        Common column names used for these purposes:
        - For themes: 'Company', 'theme', 'category', etc.
        - For subheaders: 'News_Type', 'subheader', 'subcategory', etc.
        
        The mapping you select here determines how your newsletter will be organized.
        """)

# IMPROVED: Function to auto-generate newsletter
def regenerate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_selection, banner_html_file, default_banner, force=False):
    """
    Regenerate the newsletter based on current configuration
    
    Parameters:
    - force: If True, will regenerate even if needs_update is False
    
    Returns:
    - success: Boolean indicating if generation was successful
    """
    if not (st.session_state.needs_update or force) or st.session_state.preview_updating:
        return True

    # Set flag to prevent concurrent updates
    st.session_state.preview_updating = True
    
    try:
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
        # Handle different banner types
        if banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
        elif banner_selection in BANNER_FILENAMES:
            # Use the modified HTML directly as HTML content, not as a file path
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text)
        else:
            # Default case
            banner_path = os.path.join(BANNERS_DIR, "corpcomm_banner.html")
            banner_input = banner_path
        
        newsletter_html, output_path = generate_newsletter(
            df,
            column_mapping,
            colors,
            preview_text,
            content_width,
            mobile_friendly,
            banner_input,
            default_banner,
            summary_html,
            image_html
        )
        st.session_state.newsletter_html = newsletter_html
        st.session_state.output_path = output_path
        st.session_state.needs_update = False
        st.session_state.newsletter_error = False
        
        # Reset the updating flag
        st.session_state.preview_updating = False
        return True
        
    except Exception as e:
        st.session_state.newsletter_error = True
        st.session_state.preview_updating = False
        st.error(f"Error generating newsletter: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

# ---- End function definitions ----

# Create a temporary directory for files if it doesn't exist
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Option to load the existing demo data
use_demo_data = st.checkbox("Load demo data", value=False, key="use_demo_data", on_change=trigger_update)

if use_demo_data:
    # Check if the demo file exists
    demo_file = "dummy_news.csv"
    
    if os.path.exists(demo_file):
        df = pd.read_csv(demo_file)
        df = clean_dataframe(df)  # Clean without adding columns
        st.success(f"Loaded demo dataset with {len(df)} articles")
    else:
        st.error(f"Demo file '{demo_file}' not found. Please upload a CSV file instead.")
        use_demo_data = False
else:
    # Regular file upload option
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"], on_change=trigger_update)

    if uploaded_file is None:
        st.info("Please upload a CSV file or use the demo data option to get started.")
        
        st.subheader("How It Works")
        st.markdown("""
        1. **Upload CSV data** with your newsletter content
        2. **Select articles** from the data preview to summarize
        3. **Generate a prompt** for your preferred LLM tool
        4. **Paste the generated summary** back into the app
        5. **Add an image** to enhance your newsletter (optional)
        6. **Customize appearance** with color themes, banner styles, and width options
        7. **Generate and preview** your newsletter
        8. **Email or download** the HTML file for your email platform
        """)
        
        st.subheader("CSV Format Example")
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
        
        # Exit the script since no data is loaded
        st.stop()
    else:
        # Process the uploaded file
        df = pd.read_csv(uploaded_file)
        df = clean_dataframe(df)  # Clean without adding columns

# At this point, we have a dataframe either from the uploaded file or demo data
try:
    # Data preview and editor
    st.subheader("Data Preview & Summary Generator")
    st.caption("Select rows in the table below to include in the newsletter summary")
    
    # Create data editor with just the selection column added if needed
    if 'selected' not in df.columns:
        df['selected'] = False
    
    # Use data editor - will trigger update when selection changes
    edited_df = st.data_editor(
        df,
        column_config={
            "selected": st.column_config.CheckboxColumn(
                "Select",
                help="Select this row for summarization",
                default=False,
            )
        },
        hide_index=True,
        height=500,
        use_container_width=True,
        key="data_editor",
        on_change=trigger_update
    )
    
    # Get selected rows and update dataframe with edits
    df = edited_df.copy()  # Preserve any edits made in the data editor
    selected_indices = df.index[df['selected'] == True].tolist()
    st.session_state.selected_rows = selected_indices
    
    if selected_indices:
        st.info(f"{len(selected_indices)} articles selected for summarization.")
    
    # Create columns for configuration and preview
    banner_html_file = None
    left_col, right_col = st.columns([6, 6])
    
    with left_col:
        st.subheader("Configuration")
        
        # Create tabs for different content sections
        content_tabs = st.tabs(["Summary", "Image", "Layout", "Banner"])
        
        with content_tabs[0]:  # Summary Tab
            st.subheader("Newsletter Summary")
            
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
                    user_summary = st.text_area("Paste your generated summary here:", height=200, key="user_summary", on_change=trigger_update)
                    
                    if user_summary:
                        # Format summary for display with proper HTML
                        formatted_summary = f"""
                        <div style="color: #333333; font-family: 'BLK Fort', 'Arial', Arial, sans-serif; font-size: 14px; line-height: 22px; padding: 15px 0;">
                            <h3 style="color: #000000; font-size: 18px; margin-bottom: 10px; border-bottom: 1px solid #cccccc; padding-bottom: 5px;">Weekly Summary</h3>
                            {user_summary.replace('\n', '<br>')}
                        </div>
                        """
                        
                        if st.button("Add Summary to Newsletter", use_container_width=True):
                            st.session_state.summary_html = formatted_summary
                            trigger_update()
                        
                        st.markdown("**Preview of formatted summary:**")
                        st.markdown(formatted_summary, unsafe_allow_html=True)
                        
                        # Button to remove summary if one exists
                        if 'summary_html' in st.session_state and st.session_state.summary_html:
                            if st.button("Remove Summary", use_container_width=True):
                                st.session_state.summary_html = ""
                                trigger_update()
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
            uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "gif"], key="image_upload", on_change=trigger_update)
            
            # Image caption
            image_caption = st.text_area("Image caption:", height=100, key="image_caption", on_change=trigger_update)
            
            if uploaded_image:
                # Display preview
                st.subheader("Image Preview")
                st.image(uploaded_image, width=400)
                
                # Add button to insert image
                if st.button("Add Image to Newsletter", use_container_width=True):
                    # Convert the image to base64 for embedding in HTML
                    try:
                        # Open the image using PIL
                        img = Image.open(uploaded_image)
                        
                        # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
                        if img.mode == 'RGBA':
                            # Create a white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            # Paste the image on the background using alpha as mask
                            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
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
                        img.save(buffered, format="JPEG")  # Force JPEG format
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
                        trigger_update()
                        st.success("Image added to newsletter")
                    except Exception as e:
                        st.error(f"Error processing image: {e}")
            
            # Remove image button if an image exists
            if 'image_html' in st.session_state and st.session_state.image_html:
                st.success("Image added to newsletter")
                if st.button("Remove Image", use_container_width=True):
                    st.session_state.image_html = ""
                    trigger_update()
        
        with content_tabs[2]:  # Layout Tab
            st.subheader("Layout Settings")
            
            # Column mapping for newsletter organization
            st.markdown("### Newsletter Organization")
            column_mapping = create_column_mapping_interface(df)
            
            # Add the mapping explanation
            add_mapping_explanation()
            
            # Layout dimensions and settings
            st.markdown("### Dimensions and Preview Text")
            
            # Color scheme selection
            color_theme = st.selectbox(
                "Select a color theme",
                ["Blue (Default)", "Green", "Purple", "Corporate", "Red", "Teal", "Amber", "Indigo", "Cyan", "Brown", "Custom"],
                key="color_theme",
                on_change=trigger_update
            )
            
            # Pre-determined color schemes (10 options)
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
                st.subheader("Custom Color Selection")
                # Allow both HEX code input and color picker
                custom_method = st.radio(
                    "Choose method for custom colors:",
                    ["Color Picker", "HEX Code"],
                    horizontal=True,
                    key="custom_method",
                    on_change=trigger_update
                )
                
                if custom_method == "Color Picker":
                    colors = {
                        'primary': st.color_picker("Primary Color", '#0168b1', key="primary_color", on_change=trigger_update),
                        'secondary': st.color_picker("Secondary Color", '#333333', key="secondary_color", on_change=trigger_update),
                        'background': st.color_picker("Background Color", '#e6e6e6', key="background_color", on_change=trigger_update),
                        'header_bg': st.color_picker("Header Background", '#0168b1', key="header_bg_color", on_change=trigger_update),
                        'footer_bg': st.color_picker("Footer Background", '#000000', key="footer_bg_color", on_change=trigger_update),
                        'highlight': st.color_picker("Highlight Color", '#0168b1', key="highlight_color", on_change=trigger_update)
                    }
                else:  # HEX Code input
                    col1, col2 = st.columns(2)
                    with col1:
                        primary = st.text_input("Primary Color (HEX)", "#0168b1", key="primary_hex", on_change=trigger_update)
                        secondary = st.text_input("Secondary Color (HEX)", "#333333", key="secondary_hex", on_change=trigger_update)
                        background = st.text_input("Background Color (HEX)", "#e6e6e6", key="background_hex", on_change=trigger_update)
                    with col2:
                        header_bg = st.text_input("Header Background (HEX)", "#0168b1", key="header_bg_hex", on_change=trigger_update)
                        footer_bg = st.text_input("Footer Background (HEX)", "#000000", key="footer_bg_hex", on_change=trigger_update)
                        highlight = st.text_input("Highlight Color (HEX)", "#0168b1", key="highlight_hex", on_change=trigger_update)
                    
                    colors = {
                        'primary': primary,
                        'secondary': secondary,
                        'background': background,
                        'header_bg': header_bg,
                        'footer_bg': footer_bg,
                        'highlight': highlight
                    }
                
                default_banner = "blue"
                
            # Common layout settings
            content_width = st.slider(
                "Content Width (px)", 
                600, 1000, 800,
                key="content_width",
                on_change=trigger_update
            )
            
            mobile_friendly = st.checkbox(
                "Mobile-friendly design", 
                value=True,
                key="mobile_friendly",
                on_change=trigger_update
            )
            
            preview_text = st.text_input(
                "Preview Text (shown in email clients)", 
                "Your newsletter preview text here",
                key="preview_text",
                on_change=trigger_update
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
                key="banner_selection",
                on_change=trigger_update
            )
            
            # Text editing fields for each banner type
            st.subheader("Edit Banner Text")
            
            if banner_selection == "BlackRock Corporate (Default)":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['corporate_top'] = st.text_input(
                        "Top Bar Text", 
                        st.session_state.banner_text['corporate_top'],
                        key="corporate_top_text",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['corporate_middle'] = st.text_input(
                        "Middle Bar Text", 
                        st.session_state.banner_text['corporate_middle'],
                        key="corporate_middle_text",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "GIPS Infrastructure":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gips_brand'] = st.text_input(
                        "Brand Name", 
                        st.session_state.banner_text['gips_brand'],
                        key="gips_brand_text",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['gips_subtitle'] = st.text_input(
                        "Brand Subtitle", 
                        st.session_state.banner_text['gips_subtitle'],
                        key="gips_subtitle_text",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['gips_headline'] = st.text_input(
                        "Headline Text", 
                        st.session_state.banner_text['gips_headline'],
                        key="gips_headline_text",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Modern Design":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['modern_brand'] = st.text_input(
                        "Brand Text", 
                        st.session_state.banner_text['modern_brand'],
                        key="modern_brand_text",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['modern_date'] = st.text_input(
                        "Date Text", 
                        st.session_state.banner_text['modern_date'],
                        key="modern_date_text",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['modern_tagline'] = st.text_input(
                        "Tagline Text", 
                        st.session_state.banner_text['modern_tagline'],
                        key="modern_tagline_text",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Gradient Style":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gradient_title'] = st.text_input(
                        "Title", 
                        st.session_state.banner_text['gradient_title'],
                        key="gradient_title_text",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['gradient_subtitle'] = st.text_input(
                        "Subtitle", 
                        st.session_state.banner_text['gradient_subtitle'],
                        key="gradient_subtitle_text",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['gradient_edition'] = st.text_input(
                        "Edition Text", 
                        st.session_state.banner_text['gradient_edition'],
                        key="gradient_edition_text",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Upload Custom HTML Banner":
                banner_html_file = st.file_uploader(
                    "Upload your HTML banner file", 
                    type=["html", "htm"],
                    key="custom_banner",
                    on_change=trigger_update
                )
                if banner_html_file:
                    st.success("HTML banner uploaded successfully!")
                    selected_banner = banner_html_file
                else:
                    # Default to corpcomm_banner if no upload
                    banner_path = os.path.join(BANNERS_DIR, "corpcomm_banner.html")
                    st.info("No custom banner uploaded. Using default BlackRock Corporate banner.")
                    selected_banner = banner_path
            
            # Debug checkbox for banner content
            debug_mode = st.checkbox("Debug Mode (Show HTML content)", value=False, key="debug_mode", on_change=trigger_update)
            if debug_mode:
                if banner_selection != "Upload Custom HTML Banner" or (banner_selection == "Upload Custom HTML Banner" and not banner_html_file):
                    # For preloaded banners, show their content
                    html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    
                    st.subheader(f"HTML Content for {banner_selection}")
                    st.code(html_content, language="html")
                elif banner_html_file:
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
            <div class="email-form">
                <h3>Send Newsletter</h3>
                <p>Send your newsletter directly via email to your recipients.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input(
                    "From Email", 
                    placeholder="your.name@company.com",
                    key="sender_email"
                )
            
            with col2:
                email_subject = st.text_input(
                    "Subject", 
                    f"Newsletter: {datetime.now().strftime('%B %d, %Y')}",
                    key="email_subject"
                )
            
            # Email recipients
            to_emails = st.text_area(
                "To Emails (comma separated)", 
                placeholder="recipient1@company.com, recipient2@company.com",
                key="to_emails"
            )
            
            # Optional CC and BCC
            col1, col2 = st.columns(2)
            with col1:
                cc_emails = st.text_area(
                    "CC", 
                    placeholder="cc1@company.com, cc2@company.com",
                    key="cc_emails",
                    height=80
                )
            
            with col2:
                bcc_emails = st.text_area(
                    "BCC", 
                    placeholder="bcc1@company.com, bcc2@company.com",
                    key="bcc_emails",
                    height=80
                )
            
            # Send button
            if st.button("Send Newsletter Email", use_container_width=True, key="send_email_btn"):
                if 'newsletter_html' not in st.session_state:
                    st.error("Please generate the newsletter first.")
                elif not sender_email:
                    st.error("Please enter your email address.")
                elif not to_emails:
                    st.error("Please enter at least one recipient email address.")
                else:
                    # Get the HTML content
                    newsletter_html = st.session_state.newsletter_html
                    
                    with st.spinner("Sending email ..."):
                        # Create email sender
                        email_sender = EmailSender()
                        
                        # Send the email
                        success, message = email_sender.send_html_email(
                            from_email=sender_email,
                            to_emails=to_emails,
                            subject=email_subject,
                            html_content=newsletter_html,
                            cc_emails=cc_emails,
                            bcc_emails=bcc_emails
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
            
            # Show email sending history
            if st.session_state.email_history:
                st.subheader("Email Sending History")
                
                # Convert history to DataFrame
                history_df = pd.DataFrame(st.session_state.email_history)
                st.dataframe(history_df, hide_index=True)
        
        # IMPROVED: Clearer manual generation button
        st.subheader("Manual Generation")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("If the preview doesn't update automatically, click this button.")
        with col2:
            if st.button("Force Regenerate", use_container_width=True):
                regenerate_newsletter(
                    df, 
                    column_mapping, 
                    colors, 
                    preview_text, 
                    content_width, 
                    mobile_friendly, 
                    banner_selection,
                    banner_html_file,
                    default_banner,
                    force=True
                )
                st.success("Newsletter regenerated successfully!")
    
    with right_col:
        st.subheader("Newsletter Preview")
        preview_controls_col1, preview_controls_col2 = st.columns([3, 1])
        with preview_controls_col1:
            # MODIFIED: Removed HTML Code option
            device_preview = st.radio(
                "Device", 
                ["Desktop", "Mobile (Simulated)"], 
                horizontal=True,
                key="device_preview",
                on_change=trigger_update
            )
        with preview_controls_col2:
            # MODIFIED: Default height set to 1600
            preview_height = st.slider(
                "Height", 
                600, 2000, 1600,
                key="preview_height"
            )
        
        # IMPROVED: Automatic regeneration when configuration changes
        if regenerate_newsletter(
            df, 
            column_mapping, 
            colors, 
            preview_text, 
            content_width, 
            mobile_friendly, 
            banner_selection,
            banner_html_file,
            default_banner
        ):
            # Only show preview if there's no error
            if not st.session_state.get('newsletter_error', False) and 'newsletter_html' in st.session_state:
                # Add preview update spinner
                with st.spinner("Updating preview..."):
                    preview_container = st.container()
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
                        
                        # IMPROVED: Use unique key for iframe to ensure refresh
                        iframe_height = preview_height
                        iframe_key = f"preview_{datetime.now().strftime('%H%M%S')}"
                        html_with_script = f"""
                        <iframe srcdoc="{st.session_state.newsletter_html.replace('"', '&quot;')}" 
                                width="100%" 
                                height="{iframe_height}px" 
                                style="border: none; overflow: auto;"
                                class="preview-iframe"
                                id="{iframe_key}">
                        </iframe>
                        <script>
                            // Force iframe refresh when content changes
                            document.getElementById("{iframe_key}").onload = function() {{
                                console.log("Iframe loaded");
                            }};
                        </script>
                        """
                        st.components.v1.html(html_with_script, height=iframe_height+50, scrolling=True)
                        st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Download button for the generated newsletter
                if 'output_path' in st.session_state:
                    download_col1, download_col2 = st.columns([3, 1])
                    with download_col1:
                        st.caption("Download the newsletter HTML to use in your email platform")
                    with download_col2:
                        with open(st.session_state.output_path, 'r', encoding='utf-8') as f:
                            newsletter_content = f.read()
                        st.download_button(
                            "Download HTML",
                            data=newsletter_content,
                            file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html",
                            use_container_width=True
                        )
            else:
                # Show error message if generation failed
                st.error("There was an error generating the preview. Please adjust your settings and try again.")
                st.button("Clear Error and Try Again", on_click=lambda: setattr(st.session_state, 'newsletter_error', False))
        
except Exception as e:
    st.error(f"Error processing the file: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    
st.markdown("---")
st.markdown("Newsletter Generator App - Created with Streamlit 📧")