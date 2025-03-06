import streamlit as st
import pandas as pd
import os
import base64
import uuid
import time
import shutil
import hashlib
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
from newsletter_generator import NewsletterGenerator

# Import banner templates from separate file - import all templates
from banner_templates import (
    CORPCOMM_BANNER, GIPS_BANNER, MODERN_BANNER, GRADIENT_BANNER,
    MINIMALIST_BANNER, SPLIT_BANNER, BORDERED_BANNER, GEOMETRIC_BANNER,
    WAVE_BANNER, BOXED_BANNER, BANNER_HTML_TEMPLATES, BANNER_HTML_CONTENT, 
    BANNER_FILENAMES
)

# Set page configuration as the very first Streamlit command
st.set_page_config(
    page_title="Newsletter Generator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Create a temporary directory for files if it doesn't exist
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Create banners directory if it doesn't exist
BANNERS_DIR = "banners"
if not os.path.exists(BANNERS_DIR):
    os.makedirs(BANNERS_DIR)

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

# ---- Temp File Management Functions ----

def get_session_id():
    """Get or create a unique session ID for this user session"""
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())
    return st.session_state['session_id']

def get_session_temp_path(file_type, extension="html"):
    """Create a session-specific temporary file path that can be reused"""
    session_id = get_session_id()
    return os.path.join(TEMP_DIR, f"{file_type}_{session_id}.{extension}")

def cleanup_temp_files(max_age_hours=24, force_cleanup=False):
    """Remove temporary files older than the specified age
    
    Args:
        max_age_hours: Maximum age of files to keep in hours. Set to 0 to delete all temp files.
        force_cleanup: If True, cleanup will be more aggressive, deleting duplicate content
        
    Returns:
        count: Number of files deleted
    """
    now = datetime.now()
    count = 0
    
    try:
        if not os.path.exists(TEMP_DIR):
            return 0
        
        # Get current session ID for protection
        current_session_id = get_session_id()
        
        # IMPROVED: Track file content hashes to find duplicates
        content_hashes = {}
        file_sizes = {}
        kept_files = {}
        
        # First pass: analyze all files
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
                
            try:
                # Get file size
                file_size = os.path.getsize(file_path)
                file_sizes[filename] = file_size
                
                # For small files, calculate content hash for duplicate detection
                if file_size < 10 * 1024 * 1024:  # Only hash files < 10MB for performance
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        content_hash = hash(content)
                        
                        # Track this hash
                        if content_hash not in content_hashes:
                            content_hashes[content_hash] = []
                        content_hashes[content_hash].append(filename)
            except:
                # If any error occurs during reading, ignore this file
                pass
        
        # Second pass: delete files based on rules
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if not os.path.isfile(file_path):
                continue
                
            # Determine file type
            file_type = "other"
            
            # IMPROVED: Better file type detection
            if "_" in filename:
                parts = filename.split("_")
                if len(parts) >= 2:
                    file_type = parts[0]
                    
                    # Special handling for banner and newsletter files that use UUID structure
                    if any(marker in filename for marker in ["temp_banner", "newsletter_output"]):
                        # Extract UUID from the filename if present
                        uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', filename)
                        if uuid_match:
                            uuid_str = uuid_match.group(0)
                            # Protect current session files
                            if current_session_id in filename:
                                # This is a current session file, keep newest version
                                continue
            
            # Calculate file age
            file_age = now - datetime.fromtimestamp(os.path.getmtime(file_path))
            age_hours = file_age.total_seconds() / 3600
            
            # Conditions for deletion
            delete_conditions = [
                # Condition 1: max_age_hours is 0 (force delete all)
                max_age_hours == 0 and (not filename.endswith(f"{current_session_id}.html")),
                
                # Condition 2: File exceeds age threshold and not from current session
                age_hours > max_age_hours and (not filename.endswith(f"{current_session_id}.html")),
                
                # Condition 3: Duplicated content with same hash (keep newest per session)
                force_cleanup and filename in file_sizes and file_sizes[filename] < 10 * 1024 * 1024 and 
                    any(content_hash for content_hash, files in content_hashes.items() 
                        if filename in files and len(files) > 1 and 
                        any(f != filename and (f.endswith(f"{current_session_id}.html") or 
                           (current_session_id not in filename and current_session_id not in f)) 
                           for f in files))
            ]
            
            # If any condition is met, delete the file
            if any(delete_conditions):
                try:
                    os.remove(file_path)
                    count += 1
                except:
                    pass
                    
        # Store the cleanup result in session state
        if count > 0:
            st.session_state['cleanup_message'] = f"Cleaned up {count} temporary files"
        return count
    except Exception as e:
        st.warning(f"Error during cleanup: {str(e)}")
        import traceback
        st.warning(traceback.format_exc())
        return 0

# Run cleanup on EVERY app refresh with more aggressive cleanup
# Create a session counter to track refreshes
if 'refresh_counter' not in st.session_state:
    st.session_state['refresh_counter'] = 0
st.session_state['refresh_counter'] += 1

# Define what files to clean on refresh
# Current session files are protected by default
current_session_id = get_session_id()

# IMPROVED: Find and track output files with same content 
all_newsletters = []
newsletter_sizes = {}
related_files = {}

if os.path.exists(TEMP_DIR):
    # Get all newsletter files
    for filename in os.listdir(TEMP_DIR):
        if "newsletter" in filename and filename.endswith(".html"):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                file_size = os.path.getsize(file_path)
                newsletter_sizes[filename] = file_size
                all_newsletters.append(filename)
                
                # Extract UUID from filename if present
                uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', filename)
                if uuid_match:
                    uuid_str = uuid_match.group(0)
                    # Find related banner and temp files
                    for temp_file in os.listdir(TEMP_DIR):
                        if uuid_str in temp_file and temp_file != filename:
                            if uuid_str not in related_files:
                                related_files[uuid_str] = []
                            related_files[uuid_str].append(temp_file)
            except:
                pass

# Cleanup based on different strategies
cleanup_strategy = {
    'protect_current_session': True,  # Don't delete files from current session
    'age_threshold_hours': 1,         # Delete files older than this many hours
    'max_files_per_type': 3,          # Keep only this many files per type (template, newsletter, etc.)
    'clean_duplicate_content': True   # Clean duplicate content (files with same hash)
}

# Run cleanup with improved detection for newsletter and related temp files
cleanup_temp_files(cleanup_strategy['age_threshold_hours'], 
                  force_cleanup=cleanup_strategy['clean_duplicate_content'])

# Initialize session state for tracking changes
if 'last_config' not in st.session_state:
    st.session_state.last_config = {
        'color_theme': None,
        'banner_selection': None,
        'content_width': None,
        'mobile_friendly': None,
        'preview_text': None,
        'summary_html': None,
        'banner_text': {}
    }
if 'needs_update' not in st.session_state:
    st.session_state.needs_update = True
if 'banner_text' not in st.session_state:
    st.session_state.banner_text = {
        'corporate_top': 'BlackRock',
        'corporate_middle': 'BlackRock Daily News',
        'gips_brand': 'Global Infrastructure Partners',
        'gips_subtitle': 'a part of BlackRock',
        'gips_headline': 'BGIF EMEA + Asia Weekly News',
        'modern_brand': 'BlackRock Insights',
        'modern_date': 'Weekly Digest',
        'modern_tagline': 'Market Analysis & Investment Strategy',
        'gradient_title': 'BlackRock Newsletter',
        'gradient_subtitle': 'Weekly Market Updates & Analysis',
        'gradient_edition': 'March 2025 Edition'
    }

# Function to ensure all banner files are present in the banners directory
def ensure_banner_files():
    """Ensure all banner files are present in the banners directory"""
    # Make sure the banners directory exists
    if not os.path.exists(BANNERS_DIR):
        os.makedirs(BANNERS_DIR)
    
    # Write each banner to the banners directory
    for filename, content in BANNER_HTML_CONTENT.items():
        filepath = os.path.join(BANNERS_DIR, filename)
        # Always write the file to ensure it's up-to-date
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

# Call the function to ensure banner files exist
ensure_banner_files()

# Function to load a banner file from the banners directory
def load_banner_file(filename):
    filepath = os.path.join(BANNERS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None

# Function to modify banner text based on selection and user input
def get_modified_banner_html(banner_type, banner_text):
    if banner_type == "BlackRock Corporate (Default)":
        html_content = load_banner_file("corpcomm_banner.html")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update top bar text
        top_bar = soup.select_one('.top-bar')
        if top_bar:
            top_bar.string = banner_text['corporate_top']
        
        # Update middle bar text
        middle_bar = soup.select_one('.middle-bar')
        if middle_bar:
            middle_bar.string = banner_text['corporate_middle']
            
        return str(soup)
        
    elif banner_type == "GIPS Infrastructure":
        html_content = load_banner_file("gips_infra_banner.html")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update brand text
        brand_text_elem = soup.select_one('.brand-text')
        if brand_text_elem:
            # Clear existing content
            brand_text_elem.clear()
            
            # Add main brand text
            brand_text_elem.append(banner_text['gips_brand'])
            
            # Add a line break
            brand_text_elem.append(soup.new_tag('br'))
            
            # Add subtitle in a span
            subtitle_span = soup.new_tag('span')
            subtitle_span['style'] = 'font-size: 12px; font-weight: normal;'
            subtitle_span.string = banner_text['gips_subtitle']
            brand_text_elem.append(subtitle_span)
        
        # Update headline text
        headline = soup.select_one('.headline')
        if headline:
            headline.string = banner_text['gips_headline']
            
        return str(soup)
        
    elif banner_type == "Modern Design":
        html_content = load_banner_file("modern_banner.html")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update brand text
        brand_text = soup.select_one('.brand-text')
        if brand_text:
            brand_text.string = banner_text['modern_brand']
        
        # Update date text
        date_text = soup.select_one('.date-text')
        if date_text:
            date_text.string = banner_text['modern_date']
        
        # Update tagline
        tagline = soup.select_one('.tagline')
        if tagline:
            tagline.string = banner_text['modern_tagline']
            
        return str(soup)
        
    elif banner_type == "Gradient Style":
        html_content = load_banner_file("gradient_banner.html")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text['gradient_title']
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text['gradient_subtitle']
        
        # Update right content (edition)
        right_content = soup.select_one('.right-content')
        if right_content:
            right_content.string = banner_text['gradient_edition']
            
        return str(soup)
    elif banner_type == "Minimalist":
        return MINIMALIST_BANNER
    elif banner_type == "Split Design":
        return SPLIT_BANNER
    elif banner_type == "Bordered":
        return BORDERED_BANNER
    elif banner_type == "Geometric":
        return GEOMETRIC_BANNER
    elif banner_type == "Wave":
        return WAVE_BANNER
    elif banner_type == "Boxed":
        return BOXED_BANNER
    
    return None

# IMPROVED: Create template copy - now uses session-based file paths
def create_template_copy(original_template_path):
    """
    Create a session-specific copy of the original template file.
    Reuses the same file for this session rather than creating a new one each time.
    
    Args:
        original_template_path: Path to the original template file
        
    Returns:
        Path to the copied template file
    """
    # Generate a unique file path for this session
    template_copy_path = get_session_temp_path("template_copy")
    
    # Make sure the TEMP_DIR exists
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    # Make sure the original template exists
    if not os.path.exists(original_template_path):
        raise FileNotFoundError(f"Original template file not found: {original_template_path}")
    
    # Copy the original template to the new path
    shutil.copy2(original_template_path, template_copy_path)
    
    return template_copy_path

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
    
    prompt = """You are a senior news editor with 10+ years of experience distilling multiple news stories into concise briefings. Summarize the following table of news headlines, summaries, outlets, and themes in EXACTLY 3 sentences, no more and no less:

The first sentence should provide an overview of the main theme or trend connecting most of the news stories in the table.
The second sentence should highlight the most significant or impactful story from the table, including key details like company name and core development.
The third sentence should identify any secondary themes or patterns across multiple stories (such as industry sectors, geographical regions, or business activities like funding, expansion, or product launches).
The fourth sentence should note any outliers or unique stories that stand apart from the main trends but are still noteworthy.
The final sentence should offer a brief conclusion about what these collective stories suggest about current market conditions, industry direction, or potential future developments.

Use professional journalistic language and include the most relevant details from the original sources. Focus on synthesizing information rather than simply listing stories. Maintain appropriate attribution to news outlets when necessary.

"""
    # Create a formatted table of the selected articles
    prompt += "| Title | Company | Source | Date | Content |\n"
    prompt += "| ----- | ------- | ------ | ---- | ------- |\n"
    
    for idx in selected_indices:
        row = df.iloc[idx]
        title = row.get('Article_Title', '').replace('|', '-')
        company = row.get('Company', '').replace('|', '-')
        source = row.get('Source', '').replace('|', '-')
        date = row.get('Date', '').replace('|', '-')
        # Truncate content for table readability
        content = row.get('Content', '').replace('|', '-')
        if len(content) > 100:
            content = content[:97] + "..."
        
        prompt += f"| {title} | {company} | {source} | {date} | {content} |\n"
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
BANNER_HTML_TEMPLATES = BANNER_HTML_TEMPLATES

def extract_banner_from_html(html_file_or_content, content_width=800):
    """
    Extract banner HTML from an uploaded HTML file, file path, or HTML content string
    and adjust its width.
    Returns the banner HTML content and any CSS styles.
    
    Args:
        html_file_or_content: The uploaded HTML file, file path, or HTML content
        content_width: The desired width for the banner (defaults to 800px)
    """
    if html_file_or_content is None:
        return None, None
    
    try:
        # Determine what type of input we have
        if isinstance(html_file_or_content, str):
            # Check if it's HTML content directly
            if html_file_or_content.strip().startswith('<!DOCTYPE') or html_file_or_content.strip().startswith('<html'):
                content = html_file_or_content
            elif os.path.exists(html_file_or_content):
                # It's a file path, read the file
                with open(html_file_or_content, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # It's probably HTML content without standard opening tags
                content = html_file_or_content
        else:
            # Try to handle it as a file-like object (e.g., from st.file_uploader)
            try:
                content = html_file_or_content.getvalue().decode('utf-8')
            except (AttributeError, ValueError):
                # Last resort - convert to string
                content = str(html_file_or_content)
        
        # Parse with BeautifulSoup
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
            # Try looking for a div with class containing 'banner'
            banner_divs = soup.select('div[class*="banner"]')
            if banner_divs:
                banner_html = str(banner_divs[0])
            else:
                # Last resort, try regex extraction
                banner_match = re.search(r'<div[^>]*(?:class|id)=["\'][^"\']*?banner[^"\']*["\'][^>]*>.*?</div>', content, re.DOTALL | re.IGNORECASE)
                if banner_match:
                    banner_html = banner_match.group(0)
                else:
                    return None, None
        
        # Modify banner width in HTML
        banner_html = re.sub(r'width\s*=\s*["\']\d+["\']', f'width="{content_width}"', banner_html)
        banner_html = re.sub(r'width\s*=\s*\d+', f'width="{content_width}"', banner_html)
        
        # Modify inline styles
        banner_html = re.sub(
            r'style\s*=\s*(["\'])(.*?)width\s*:\s*\d+px(.*?)(["\'])', 
            f'style=\\1\\2width: {content_width}px\\3\\4', 
            banner_html
        )
        
        # Modify styles
        if style_content:
            style_content = re.sub(
                r'(\.banner\s*\{[^}]*?)width\s*:\s*\d+px', 
                f'\\1width: {content_width}px', 
                style_content
            )
            
            # Add responsive styles if needed
            if '@media' not in style_content:
                style_content += f"""
                @media only screen and (max-width: 480px) {{
                    .banner {{
                        width: 100% !important;
                        max-width: 100% !important;
                    }}
                }}
                """
        
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

# Modify generate_newsletter to handle related files more efficiently
def generate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_input=None, banner_type="blue", summary_html=""):
    # IMPROVED: Create a session-specific template copy
    original_template_path = 'newsletter_template.html'
    template_copy_path = create_template_copy(original_template_path)
    
    # Initialize the generator with the copy instead of the original
    generator = NewsletterGenerator(template_copy_path)
    
    # IMPROVED: Generate a deterministic session-specific output path 
    # Use fixed name pattern for better file tracking
    session_id = get_session_id()
    output_path = os.path.join(TEMP_DIR, f"newsletter_output_{session_id}.html")
    
    # Process banner HTML
    custom_banner_html = None
    custom_banner_styles = None
    
    if banner_input:
        # Extract and resize the banner to match content width
        custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_input, content_width)
        
    if not custom_banner_html:
        st.warning("Could not extract banner from HTML. Using default banner.")
        custom_banner_html = BANNER_HTML_TEMPLATES.get(banner_type, BANNER_HTML_TEMPLATES["blue"])
        # Resize default banner too
        custom_banner_html = re.sub(r'width: 800px', f'width: {content_width}px', custom_banner_html)
    
    # IMPROVED: Use deterministic naming for the banner file
    banner_file_path = os.path.join(TEMP_DIR, f"temp_banner_{banner_type}_{session_id}.html")
    
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
    
    # Generate the initial newsletter using the template copy
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
    
    # Write the final HTML to file - this file can be used for emailing
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(newsletter_html)
        
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

# Add this function to manually clean up related files
def cleanup_related_files(pattern=None):
    """
    Manually clean up related temporary files.
    Args:
        pattern: String pattern to match files (e.g., UUID)
    """
    if not os.path.exists(TEMP_DIR):
        return 0
    
    count = 0
    current_session_id = get_session_id()
    
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
                
            # Skip current session files
            if current_session_id in filename:
                continue
                
            # If pattern is provided, only delete matching files
            if pattern and pattern not in filename:
                continue
                
            try:
                os.remove(file_path)
                count += 1
            except:
                pass
                
        return count
    except Exception as e:
        st.warning(f"Error cleaning up related files: {str(e)}")
        return 0

# Function to check if configuration has changed
def config_changed(current_config):
    changed = False
    for key, value in current_config.items():
        if key in st.session_state.last_config and st.session_state.last_config[key] != value:
            changed = True
            break
    
    # Update last_config with current values
    for key, value in current_config.items():
        st.session_state.last_config[key] = value
    
    return changed

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

# IMPROVED: Add a sidebar with cleanup option
with st.sidebar:
    st.header("Temp File Management")
    
    # Show temp file info
    total_files = len([f for f in os.listdir(TEMP_DIR) if os.path.isfile(os.path.join(TEMP_DIR, f))]) if os.path.exists(TEMP_DIR) else 0
    
    st.metric("Temporary Files", total_files)
    
    # Add columns for cleanup options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clean All Files"):
            num_deleted = cleanup_temp_files(max_age_hours=0)  # Delete all temp files
            st.success(f"Removed {num_deleted} files")
            time.sleep(1)  # Short pause before refresh
            st.rerun()
    
    with col2:
        if st.button("Clean Duplicates"):
            # Find and clean duplicate files
            num_deleted = cleanup_temp_files(max_age_hours=24, force_cleanup=True)
            st.success(f"Removed {num_deleted} duplicate files")
            time.sleep(1)  # Short pause before refresh
            st.rerun()
    
    # Advanced cleanup option
    with st.expander("Advanced Cleanup", expanded=False):
        # Show pattern-based cleanup option
        pattern = st.text_input("File Pattern or UUID", placeholder="Enter pattern to match filenames")
        if pattern and st.button("Delete Matching Files"):
            num_deleted = cleanup_related_files(pattern)
            st.success(f"Removed {num_deleted} matching files")
            time.sleep(1)  # Short pause before refresh
            st.rerun()
    
    st.caption("Automatic cleanup runs on every app refresh")
    
    # Display cleanup message if it exists
    if 'cleanup_message' in st.session_state:
        st.info(st.session_state['cleanup_message'])
        # Clear the message after displaying
        st.session_state.pop('cleanup_message', None)
        
    # Display refresh counter
    st.caption(f"App refreshes: {st.session_state.get('refresh_counter', 1)}")

# Option to load the existing demo data
use_demo_data = st.checkbox("Load demo data", value=False, key="use_demo_data")

if use_demo_data:
    # Check if the demo file exists
    demo_file = "dummy_news.csv"
    
    if os.path.exists(demo_file):
        df = pd.read_csv(demo_file)
        st.success(f"Loaded demo dataset with {len(df)} articles")
    else:
        st.error(f"Demo file '{demo_file}' not found. Please upload a CSV file instead.")
        use_demo_data = False
else:
    # Regular file upload option
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is None:
        st.info("Please upload a CSV file or use the demo data option to get started.")
        
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
        
        # Exit the script since no data is loaded
        st.stop()
    else:
        # Process the uploaded file
        df = pd.read_csv(uploaded_file)
        unnamed_cols = [col for col in df.columns if 'Unnamed:' in col]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

# At this point, we have a dataframe either from the uploaded file or demo data
try:
    # MODIFIED CODE: Move data preview outside columns for full width
    st.subheader("Data Preview & Summary Generator")
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
        height=500,  # Increased height for better visibility
        use_container_width=True
    )
    
    selected_indices = edited_df.index[edited_df['selected'] == True].tolist()
    st.session_state.selected_rows = selected_indices
    
    if selected_indices:
        st.info(f"{len(selected_indices)} articles selected for summarization.")
    
    # Now create the columns for configuration and preview
    banner_html_file = None
    left_col, right_col = st.columns([5, 5])
    
    with left_col:
        st.subheader("Configuration")
        
        if selected_indices:
            st.subheader("Generate Summary")
            prompt_tab, summary_tab = st.tabs(["1. Get Prompt for LLM", "2. Add Generated Summary"])
            
            with prompt_tab:
                prompt = generate_prompt(df, selected_indices)
                st.markdown("### Generated prompt for your preferred LLM:")
                
                # Add styles for code block but without the copy button
                st.markdown('''
                <style>
                .stCodeBlock {
                    margin-top: 25px !important;
                    position: relative;
                }
                </style>
                ''', unsafe_allow_html=True)
                
                # Add the code block with the prompt (without custom copy button)
                st.code(prompt, language="text")
                
                # Add helpful instructions
                st.info("You can use the copy icon in the top-right corner of the code block to copy the prompt.")
                with st.expander("How to use this prompt"):
                    st.markdown("""
                    1. Copy the entire prompt using the copy icon in the top right
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
                        st.session_state.needs_update = True
                        st.rerun()
                    
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
        
        # MODIFIED: Separate color schemes and banner sections into different expanders
        current_config = {}
        
        with st.expander("Color Scheme Settings", expanded=True):
            color_theme = st.selectbox(
                "Select a color theme",
                ["Blue (Default)", "Green", "Purple", "Corporate", "Red", "Teal", "Amber", "Indigo", "Cyan", "Brown", "Custom"],
                key="color_theme",
                on_change=lambda: setattr(st.session_state, 'needs_update', True)
            )
            current_config['color_theme'] = color_theme
            
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
                    on_change=lambda: setattr(st.session_state, 'needs_update', True)
                )
                
                if custom_method == "Color Picker":
                    colors = {
                        'primary': st.color_picker("Primary Color", '#0168b1', key="primary_color", on_change=lambda: setattr(st.session_state, 'needs_update', True)),
                        'secondary': st.color_picker("Secondary Color", '#333333', key="secondary_color", on_change=lambda: setattr(st.session_state, 'needs_update', True)),
                        'background': st.color_picker("Background Color", '#e6e6e6', key="background_color", on_change=lambda: setattr(st.session_state, 'needs_update', True)),
                        'header_bg': st.color_picker("Header Background", '#0168b1', key="header_bg_color", on_change=lambda: setattr(st.session_state, 'needs_update', True)),
                        'footer_bg': st.color_picker("Footer Background", '#000000', key="footer_bg_color", on_change=lambda: setattr(st.session_state, 'needs_update', True)),
                        'highlight': st.color_picker("Highlight Color", '#0168b1', key="highlight_color", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                    }
                else:  # HEX Code input
                    col1, col2 = st.columns(2)
                    with col1:
                        primary = st.text_input("Primary Color (HEX)", "#0168b1", key="primary_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                        secondary = st.text_input("Secondary Color (HEX)", "#333333", key="secondary_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                        background = st.text_input("Background Color (HEX)", "#e6e6e6", key="background_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                    with col2:
                        header_bg = st.text_input("Header Background (HEX)", "#0168b1", key="header_bg_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                        footer_bg = st.text_input("Footer Background (HEX)", "#000000", key="footer_bg_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                        highlight = st.text_input("Highlight Color (HEX)", "#0168b1", key="highlight_hex", on_change=lambda: setattr(st.session_state, 'needs_update', True))
                    
                    colors = {
                        'primary': primary,
                        'secondary': secondary,
                        'background': background,
                        'header_bg': header_bg,
                        'footer_bg': footer_bg,
                        'highlight': highlight
                    }
                
                default_banner = "blue"
        
        # MODIFIED: Updated banner section to include editable text fields instead of preview
        with st.expander("Banner Settings", expanded=True):
            # Banner selection
            st.subheader("Banner Selection")
            
            # Banner options now include preloaded banners from the banners directory
            banner_options = [
                "BlackRock Corporate (Default)",
                "GIPS Infrastructure",
                "Modern Design",
                "Gradient Style",
                "Minimalist",
                "Split Design",
                "Bordered",
                "Geometric",
                "Wave",
                "Boxed",
                "Upload Custom HTML Banner"
            ]
            
            banner_selection = st.radio(
                "Choose a banner style:",
                banner_options,
                horizontal=True,
                index=0,  # Default to the corpcomm_banner
                key="banner_selection",
                on_change=lambda: setattr(st.session_state, 'needs_update', True)
            )
            current_config['banner_selection'] = banner_selection
            
            # NEW: Text editing fields for each banner type
            st.subheader("Edit Banner Text")
            
            if banner_selection == "BlackRock Corporate (Default)":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['corporate_top'] = st.text_input(
                        "Top Bar Text", 
                        st.session_state.banner_text['corporate_top'],
                        key="corporate_top_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                with col2:
                    st.session_state.banner_text['corporate_middle'] = st.text_input(
                        "Middle Bar Text", 
                        st.session_state.banner_text['corporate_middle'],
                        key="corporate_middle_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "GIPS Infrastructure":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gips_brand'] = st.text_input(
                        "Brand Name", 
                        st.session_state.banner_text['gips_brand'],
                        key="gips_brand_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                    st.session_state.banner_text['gips_subtitle'] = st.text_input(
                        "Brand Subtitle", 
                        st.session_state.banner_text['gips_subtitle'],
                        key="gips_subtitle_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                with col2:
                    st.session_state.banner_text['gips_headline'] = st.text_input(
                        "Headline Text", 
                        st.session_state.banner_text['gips_headline'],
                        key="gips_headline_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Modern Design":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['modern_brand'] = st.text_input(
                        "Brand Text", 
                        st.session_state.banner_text['modern_brand'],
                        key="modern_brand_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                    st.session_state.banner_text['modern_date'] = st.text_input(
                        "Date Text", 
                        st.session_state.banner_text['modern_date'],
                        key="modern_date_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                with col2:
                    st.session_state.banner_text['modern_tagline'] = st.text_input(
                        "Tagline Text", 
                        st.session_state.banner_text['modern_tagline'],
                        key="modern_tagline_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Gradient Style":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gradient_title'] = st.text_input(
                        "Title", 
                        st.session_state.banner_text['gradient_title'],
                        key="gradient_title_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                    st.session_state.banner_text['gradient_subtitle'] = st.text_input(
                        "Subtitle", 
                        st.session_state.banner_text['gradient_subtitle'],
                        key="gradient_subtitle_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                with col2:
                    st.session_state.banner_text['gradient_edition'] = st.text_input(
                        "Edition Text", 
                        st.session_state.banner_text['gradient_edition'],
                        key="gradient_edition_text",
                        on_change=lambda: setattr(st.session_state, 'needs_update', True)
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
            
            elif banner_selection in ["Minimalist", "Split Design", "Bordered", "Geometric", "Wave", "Boxed"]:
                # Get the HTML content directly
                if banner_selection == "Minimalist":
                    selected_banner = MINIMALIST_BANNER
                elif banner_selection == "Split Design":
                    selected_banner = SPLIT_BANNER
                elif banner_selection == "Bordered":
                    selected_banner = BORDERED_BANNER
                elif banner_selection == "Geometric":
                    selected_banner = GEOMETRIC_BANNER
                elif banner_selection == "Wave":
                    selected_banner = WAVE_BANNER
                elif banner_selection == "Boxed":
                    selected_banner = BOXED_BANNER
                
                st.info(f"Using {banner_selection} banner style for your newsletter.")
                
            elif banner_selection == "Upload Custom HTML Banner":
                banner_html_file = st.file_uploader(
                    "Upload your HTML banner file", 
                    type=["html", "htm"],
                    key="custom_banner",
                    on_change=lambda: setattr(st.session_state, 'needs_update', True)
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
            debug_mode = st.checkbox("Debug Mode (Show HTML content)", value=False, key="debug_mode")
            if debug_mode:
                if banner_selection != "Upload Custom HTML Banner" or (banner_selection == "Upload Custom HTML Banner" and not banner_html_file):
                    # For preloaded banners, show their content
                    if banner_selection == "BlackRock Corporate (Default)":
                        html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    elif banner_selection == "GIPS Infrastructure":
                        html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    elif banner_selection == "Modern Design":
                        html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    elif banner_selection == "Gradient Style":
                        html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    elif banner_selection == "Minimalist":
                        html_content = MINIMALIST_BANNER
                    elif banner_selection == "Split Design":
                        html_content = SPLIT_BANNER
                    elif banner_selection == "Bordered":
                        html_content = BORDERED_BANNER
                    elif banner_selection == "Geometric":
                        html_content = GEOMETRIC_BANNER
                    elif banner_selection == "Wave":
                        html_content = WAVE_BANNER
                    elif banner_selection == "Boxed":
                        html_content = BOXED_BANNER
                        
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
        
        with st.expander("Layout Settings", expanded=True):
            content_width = st.slider(
                "Content Width (px)", 
                600, 1000, 800,
                key="content_width",
                on_change=lambda: setattr(st.session_state, 'needs_update', True)
            )
            current_config['content_width'] = content_width
            
            mobile_friendly = st.checkbox(
                "Mobile-friendly design", 
                value=True,
                key="mobile_friendly",
                on_change=lambda: setattr(st.session_state, 'needs_update', True)
            )
            current_config['mobile_friendly'] = mobile_friendly
        
        with st.expander("Email Settings", expanded=True):
            preview_text = st.text_input(
                "Preview Text", 
                "Your newsletter preview text here",
                key="preview_text",
                on_change=lambda: setattr(st.session_state, 'needs_update', True)
            )
            current_config['preview_text'] = preview_text
        
        # Check if configuration has changed
        current_config['summary_html'] = st.session_state.get('summary_html', "")
        current_config['banner_text'] = st.session_state.banner_text
    
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
                on_change=lambda: st.session_state.update({'needs_update': True})
            )
        with preview_controls_col2:
            # MODIFIED: Default height set to 1600
            preview_height = st.slider(
                "Height", 
                600, 2000, 1600,
                key="preview_height"
            )
        
        # MODIFIED: Regenerate newsletter on configuration change
        if st.session_state.needs_update or 'newsletter_html' not in st.session_state:
            with st.spinner("Generating newsletter..."):
                summary_html = st.session_state.get('summary_html', "")
                
                try:
                    # Handle different banner types
                    if banner_selection == "Upload Custom HTML Banner" and banner_html_file:
                        banner_input = banner_html_file
                    elif banner_selection in ["BlackRock Corporate (Default)", "GIPS Infrastructure", "Modern Design", "Gradient Style"]:
                        # Use the modified HTML directly as HTML content
                        banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    elif banner_selection in ["Minimalist", "Split Design", "Bordered", "Geometric", "Wave", "Boxed"]:
                        # Get the HTML content directly from the constants
                        if banner_selection == "Minimalist":
                            banner_input = MINIMALIST_BANNER
                        elif banner_selection == "Split Design":
                            banner_input = SPLIT_BANNER
                        elif banner_selection == "Bordered":
                            banner_input = BORDERED_BANNER
                        elif banner_selection == "Geometric":
                            banner_input = GEOMETRIC_BANNER
                        elif banner_selection == "Wave":
                            banner_input = WAVE_BANNER
                        elif banner_selection == "Boxed":
                            banner_input = BOXED_BANNER
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
                        banner_input,  # This could be a file, a path string, or HTML content
                        default_banner,  # Fallback banner type
                        summary_html
                    )
                    st.session_state.newsletter_html = newsletter_html
                    st.session_state.output_path = output_path
                    st.session_state.needs_update = False
                except Exception as e:
                    st.error(f"Error generating newsletter: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
                    # Set a flag to prevent further errors
                    st.session_state.newsletter_error = True
        
        # Only show preview if there's no error
        if not st.session_state.get('newsletter_error', False) and 'newsletter_html' in st.session_state:
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
                
            # Added hidden download button after preview for user convenience
            if st.session_state.get('newsletter_html'):
                st.download_button(
                    "Download Newsletter HTML",
                    st.session_state.newsletter_html,
                    file_name="newsletter.html",
                    mime="text/html",
                    use_container_width=True
                )
            
except Exception as e:
    st.error(f"Error processing the file: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    
st.markdown("---")
st.markdown("Newsletter Generator App - Created with Streamlit 📧")
