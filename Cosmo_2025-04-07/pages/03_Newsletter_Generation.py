"""
Newsletter Generator page for the Gravity app with a single, unified "Regenerate" button
PLUS color pickers for banner, dividers, and subheader highlights,
PLUS a "Use custom preview text" vs. "Auto-generate from summary" option.
"""
import streamlit as st
import pandas as pd
import base64
import io
import os
import time
from datetime import datetime
from PIL import Image
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup

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
os.makedirs("static/images", exist_ok=True)

# Render header
render_header()

# Global variables to be used by update function
df = None
column_mapping = None

# Import the NewsletterGenerator class
from modules.newsletter_generator import NewsletterGenerator

def fix_dividers(html_content, divider_bottom_color):
    """
    Directly finds and modifies the divider elements in the HTML.
    Top divider is always black, bottom divider has customizable color and is doubled in thickness.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Clear any existing style tags that might be interfering with divider colors
    for style_tag in soup.find_all('style'):
        if '.black-divider' in style_tag.string or '.yellow-divider' in style_tag.string:
            style_content = style_tag.string
            style_content = style_content.replace('background-color: #000000;', 'background-color: #000000;')
            style_content = style_content.replace('height: 2px;', 'height: 2px;')  # Keep black divider at 2px
            
            # Make yellow divider 4px and update color
            style_content = style_content.replace('background-color: #ffce00;', f'background-color: {divider_bottom_color};')
            style_content = style_content.replace('.yellow-divider { height: 2px;', f'.yellow-divider {{ height: 4px;')
            style_tag.string = style_content
    
    # Find all black divider elements - keep them at 2px and always black
    black_dividers = soup.find_all('div', class_='black-divider')
    for div in black_dividers:
        div['style'] = "height: 2px; background-color: #000000; margin: 0;"
        if 'bgcolor' in div.attrs:
            div['bgcolor'] = "#000000"
    
    # Find all yellow divider elements - make them 4px and use the custom color
    yellow_dividers = soup.find_all('div', class_='yellow-divider')
    for div in yellow_dividers:
        div['style'] = f"height: 4px; background-color: {divider_bottom_color}; margin: 0;"
        if 'bgcolor' in div.attrs:
            div['bgcolor'] = divider_bottom_color
    
    # Also look for any CSS rules with these classes in the style tags
    css_style = soup.new_tag('style')
    css_style.string = f"""
    .black-divider {{
        height: 2px !important;
        background-color: #000000 !important;
        margin: 0 !important;
    }}
    .yellow-divider {{
        height: 4px !important;
        background-color: {divider_bottom_color} !important;
        margin: 0 !important;
    }}
    """
    head = soup.head
    if head:
        head.append(css_style)
    
    return str(soup)

def is_dark_color(hex_color):
    """
    Determines if a color is "dark" and should have white text.
    Returns True if the color is dark, False otherwise.
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return brightness < 128

def inject_direct_styles(html_content, colors):
    """
    Inject CSS directly into the head of the HTML to force color application
    regardless of template structure.

    UPDATED: Black divider is always black, yellow divider is 4px thick
    Also adjusts text color based on background darkness
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    head = soup.head
    
    # Determine text colors based on background darkness
    banner_bg_color = colors.get('banner_bg', '#ffce00')
    subheader_bg_color = colors.get('subheader_bg', '#ffce00')
    
    banner_text_color = '#ffffff' if is_dark_color(banner_bg_color) else '#000000'
    subheader_text_color = '#ffffff' if is_dark_color(subheader_bg_color) else '#000000'
    
    if head:
        style_tag = soup.new_tag('style')
        style_tag['type'] = 'text/css'
        
        custom_css = f"""
        /* Direct style injection for newsletter colors */
        .nav-container, 
        table[class*="nav-container"], 
        td[bgcolor="#ffce00"], 
        td[style*="background-color:#ffce00"], 
        td[style*="background-color: #ffce00"] {{ 
            background-color: {colors.get('banner_bg', '#ffce00')} !important; 
            color: {banner_text_color} !important;
        }}
        
        .nav-link, .nav-link a {{
            color: {banner_text_color} !important;
        }}
        
        div.black-divider {{ 
            background-color: #000000 !important; 
            height: 2px !important;
            margin: 0 !important;
        }}
        
        div.yellow-divider {{ 
            background-color: {colors.get('divider_color_2', '#ffce00')} !important; 
            height: 4px !important;
            margin: 0 !important;
        }}
        
        .subheader-text, 
        span[class*="subheader-text"] {{
            background-color: {colors.get('subheader_bg', '#ffce00')} !important;
            color: {subheader_text_color} !important;
        }}

        tr td[style*="#ffce00"] {{ background-color: {colors.get('banner_bg', '#ffce00')} !important; }}
        table.banner-container {{ background-color: {colors.get('banner_bg', '#ffce00')} !important; }}
        """
        
        style_tag.string = custom_css
        head.append(style_tag)
        
        # Modify inline styles for the nav container
        for td in soup.find_all('td', attrs={'bgcolor': '#ffce00'}):
            td['bgcolor'] = colors.get('banner_bg', '#ffce00')
        for td in soup.find_all('td', style=lambda s: s and 'background-color:#ffce00' in s):
            td['style'] = td['style'].replace('background-color:#ffce00', f'background-color:{colors.get("banner_bg", "#ffce00")}')
        
        for span in soup.find_all('span', class_='subheader-text'):
            span['style'] = f"background-color:{colors.get('subheader_bg', '#ffce00')}; color:{subheader_text_color};"
        
        return str(soup)
    return html_content

def apply_colors_to_html(html, colors):
    """
    Directly apply color settings to the HTML by replacing color codes.
    UPDATED: Black divider is always black, yellow divider is 4px thick
    """
    import re
    updated_html = html

    replacements = [
        # Headers
        (r'background-color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*header.*?\*\/', 
         f'background-color: {colors["header_color_1"]}; /* header */'),
        
        (r'background-color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*header.*?2.*?\*\/', 
         f'background-color: {colors["header_color_2"]}; /* header2 */'),
        
        # Footer
        (r'background-color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*footer.*?\*\/', 
         f'background-color: {colors["footer_color"]}; /* footer */'),
        
        # Dividers - keep top divider black
        (r'border-top:\s*\d+px\s+solid\s+#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*divider.*?\*\/', 
         f'border-top: 2px solid #000000; /* divider */'),
        
        # Yellow divider - double thickness
        (r'border-bottom:\s*\d+px\s+solid\s+#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*divider.*?\*\/', 
         f'border-bottom: 4px solid {colors["divider_color_2"]}; /* divider */'),
        
        # Subheaders
        (r'color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*subheader.*?\*\/', 
         f'color: {colors["subheader_color"]}; /* subheader */'),
        
        # Background
        (r'background-color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*email.*?background.*?\*\/', 
         f'background-color: {colors["background"]}; /* email background */'),
        
        (r'background-color:\s*#[0-9a-fA-F]{3,6}[^;]*?;\s*/\*\s*content.*?background.*?\*\/', 
         f'background-color: {colors["content_background"]}; /* content background */'),
    ]
    for pattern, replacement in replacements:
        updated_html = re.sub(pattern, replacement, updated_html)
    
    # Fallback: look for style attributes with known IDs
    updated_html = re.sub(r'(<td[^>]*?id=["\'](header|header-container|header-wrapper)["\'][^>]*?style=["|\'])([^"\']*?)(["|\'])', 
                          r'\1background-color: ' + colors["header_color_1"] + '; \3\4', 
                          updated_html)
    updated_html = re.sub(r'(<td[^>]*?id=["\'](footer|footer-container|footer-wrapper)["\'][^>]*?style=["|\'])([^"\']*?)(["|\'])', 
                          r'\1background-color: ' + colors["footer_color"] + '; \3\4', 
                          updated_html)
    updated_html = re.sub(r'(<h[2-4][^>]*?style=["|\'])([^"\']*?)(["|\'])', 
                          r'\1color: ' + colors["subheader_color"] + '; \2\3', 
                          updated_html)
    updated_html = re.sub(r'(<body[^>]*?style=["|\'])([^"\']*?)(["|\'])', 
                          r'\1background-color: ' + colors["background"] + '; \2\3', 
                          updated_html)
    updated_html = re.sub(r'(<td[^>]*?id=["\'](content|main-content|content-container)["\'][^>]*?style=["|\'])([^"\']*?)(["|\'])', 
                          r'\1background-color: ' + colors["content_background"] + '; \3\4', 
                          updated_html)
    
    # Special patterns
    special_patterns = [
        # nav container
        (r'(background-color:\s*#ffce00;\s*/\*\s*banner-bg\s*\*/)',
         f'background-color: {colors.get("banner_bg","#ffce00")}; /* banner-bg */'),
        (r'background-color:#ffce00;', f'background-color:{colors.get("banner_bg","#ffce00")};'),
        (r'bgcolor="#ffce00"', f'bgcolor="{colors.get("banner_bg","#ffce00")}"'),
        
        # keep top divider black
        (r'(background-color:\s*#000000;\s*/\*\s*divider-color-1\s*\*/)',
         f'background-color: #000000; /* divider-color-1 */'),
        
        # bottom divider
        (r'(background-color:\s*#ffce00;\s*/\*\s*divider-color-2\s*\*/)',
         f'background-color: {colors.get("divider_color_2","#ffce00")}; /* divider-color-2 */'),
        
        # subheader background
        (r'(background-color:\s*#ffce00;\s*/\*\s*subheader-bg\s*\*/)',
         f'background-color: {colors.get("subheader_bg","#ffce00")}; /* subheader-bg */'),
        
        # direct class targeting for thickness
        (r'\.black-divider\s*{[^}]*?background-color:\s*#[0-9A-Fa-f]{3,6}',
         f'.black-divider {{background-color: #000000'),
        (r'\.yellow-divider\s*{[^}]*?background-color:\s*#[0-9A-Fa-f]{3,6}',
         f'.yellow-divider {{background-color: {colors.get("divider_color_2","#ffce00")}'),
        (r'\.yellow-divider\s*{[^}]*?height:\s*2px',
         f'.yellow-divider {{height: 4px'),
        
        (r'\.nav-container\s*{[^}]*?background-color:\s*#[0-9A-Fa-f]{3,6}',
         f'.nav-container {{background-color: {colors.get("banner_bg","#ffce00")}'),
    ]
    for pat, repl in special_patterns:
        updated_html = re.sub(pat, repl, updated_html)
    
    # Replace inline styles for background-color #ffce00
    updated_html = re.sub(
        r'<td[^>]*?style="[^"]*?background-color:#ffce00[^"]*?"',
        lambda m: m.group(0).replace('background-color:#ffce00', f'background-color:{colors.get("banner_bg","#ffce00")}'),
        updated_html
    )
    
    # Hard-coded black divider & custom color yellow divider
    updated_html = re.sub(
        r'<div\s+class=(["\'])black-divider\1[^>]*>',
        f'<div class="black-divider" style="height: 2px; background-color: #000000; margin: 0;">',
        updated_html
    )
    updated_html = re.sub(
        r'<div\s+class=(["\'])yellow-divider\1[^>]*>',
        f'<div class="yellow-divider" style="height: 4px; background-color: {colors.get("divider_color_2","#ffce00")}; margin: 0;">',
        updated_html
    )
    
    return updated_html

def generate_prompt(df, selected_indices):
    """
    Generate a prompt for LLM summarization.
    """
    if not selected_indices:
        return ""
    
    prompt = """You are a senior news editor with 10+ years of experience distilling multiple news stories into concise briefings. Summarize the following table of news headlines, summaries, outlets, and themes in EXACTLY 3 paragraphs, no more and no less:

The first paragraph should provide an overview of the main theme or trend connecting most of the news stories in the table.
The second paragraph should highlight the most significant or impactful stories, including key details like company names and core developments.
The third paragraph should identify any secondary themes or patterns across multiple stories and note any outliers or unique stories that are still noteworthy.

Use professional journalistic language and include the most relevant details from the original sources. Focus on synthesizing information rather than simply listing stories. Maintain appropriate attribution to news outlets when necessary.

"""
    prompt += "| Title | Company | Source | Date | Content |\n"
    prompt += "| ----- | ------- | ------ | ---- | ------- |\n"
    
    selected_rows = df.loc[selected_indices]
    
    for _, row in selected_rows.iterrows():
        def safe_value(value, default=''):
            if pd.isna(value) or value is None:
                return default
            return str(value).replace('|', '-')
        
        # Gather columns in a safe way
        title = ""
        for title_col in ['Article_Title','header_text','Title','Headline']:
            if title_col in row and not pd.isna(row.get(title_col)):
                title = safe_value(row.get(title_col))
                break
        if not title:
            # fallback: first textual column
            for col in row.index:
                if isinstance(row[col], str) and col != 'selected':
                    title = safe_value(row[col])
                    break
        
        company = ""
        for company_col in ['Company','search_term','Theme']:
            if company_col in row and not pd.isna(row.get(company_col)):
                company = safe_value(row.get(company_col))
                break
        
        source = ""
        for source_col in ['Source','first_source_name','Publisher']:
            if source_col in row and not pd.isna(row.get(source_col)):
                source = safe_value(row.get(source_col))
                break
        
        date = ""
        for date_col in ['Date','local_time_text','Publication_Date']:
            if date_col in row and not pd.isna(row.get(date_col)):
                date = safe_value(row.get(date_col))
                break
        
        content = ""
        for content_col in ['Content','summary_text','body_text','Summary']:
            if content_col in row and not pd.isna(row.get(content_col)):
                content = safe_value(row.get(content_col))
                break
        if content and len(content) > 100:
            content = content[:97] + "..."
        
        prompt += f"| {title} | {company} | {source} | {date} | {content} |\n"
    return prompt

def update_preview_on_change():
    """
    Update the newsletter preview immediately after a change.
    """
    global df, column_mapping
    if df is None:
        return
    
    st.session_state.preview_updating = True
    update_time = datetime.now()
    st.session_state.last_update_time = update_time.strftime("%H:%M:%S.%f")
    
    try:
        # Check if user selected "Auto-generate from summary"
        if st.session_state.get('preview_text_option') == "Auto-generate from summary":
            # If there's a summary available, extract first 150 chars
            if 'summary_html' in st.session_state and st.session_state.summary_html:
                soup = BeautifulSoup(st.session_state.summary_html, 'html.parser')
                raw_text = soup.get_text()
                short_preview = raw_text[:150].strip()
                if len(raw_text) > 150:
                    short_preview += "..."
                st.session_state.preview_text_newsletter = short_preview
        
        # Use the final preview text from session state
        preview_text = st.session_state.get("preview_text_newsletter", "Your newsletter preview text here")
        
        # Colors & skip banner injection
        skip_banner_injection = False
        colors = {
            'header_color_1': st.session_state.get('header_color_1_hex_newsletter', 
                st.session_state.get('header_color_1_newsletter', '#0168b1')),
            'header_color_2': st.session_state.get('header_color_2_hex_newsletter', 
                st.session_state.get('header_color_2_newsletter', '#333333')),
            'footer_color': st.session_state.get('footer_color_hex_newsletter',
                st.session_state.get('footer_color_newsletter', '#000000')),
            'divider_color_1': '#000000', # ALWAYS BLACK
            'divider_color_2': st.session_state.get('divider_bottom_pick', '#ffce00'),
            'subheader_color': st.session_state.get('subheader_color_hex_newsletter',
                st.session_state.get('subheader_color_newsletter', '#0168b1')),
            'background': st.session_state.get('background_hex_newsletter',
                st.session_state.get('background_color_newsletter', '#e6e6e6')),
            'content_background': st.session_state.get('content_background_hex_newsletter',
                st.session_state.get('content_background_color_newsletter', '#ffffff')),
            
            # Legacy
            'primary': st.session_state.get('header_color_1_newsletter', '#0168b1'),
            'secondary': st.session_state.get('header_color_2_newsletter', '#333333'),
            'header_bg': st.session_state.get('header_color_1_newsletter', '#0168b1'),
            'footer_bg': st.session_state.get('footer_color_newsletter', '#000000'),
            'highlight': st.session_state.get('subheader_color_newsletter', '#0168b1'),
            
            # ADDED FOR COLOR PICKERS
            'banner_bg': st.session_state.get('banner_bg_pick', '#ffce00'),
            'divider_color_2': st.session_state.get('divider_bottom_pick', '#ffce00'),
            'subheader_bg': st.session_state.get('subheader_bg_pick', '#ffce00'),
        }
        
        # If user used the color pickers, override with st.session_state.current_colors
        if 'current_colors' in st.session_state:
            for k,v in st.session_state.current_colors.items():
                colors[k] = v
        
        banner_selection = st.session_state.get('banner_selection_newsletter', "BlackRock Classic")
        content_width = st.session_state.get('content_width_newsletter', 800)
        mobile_friendly = st.session_state.get('mobile_friendly_newsletter', True)
        
        # Check banner
        banner_html_file = st.session_state.get("custom_banner_newsletter")
        if banner_selection == "Default (Original Template)":
            banner_input = None
            skip_banner_injection = True
        elif banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
        elif banner_selection in [
            "BlackRock Classic", "BlackRock Modern", "Yellow Accent", "Gradient Header", 
            "Minimalist", "Two-Column", "Bold Header", "Split Design",
            "Boxed Design", "Double Border", "Corner Accent", "Stacked Elements", "Executive Style"
        ]:
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text, content_width)
        else:
            banner_input = get_modified_banner_html("BlackRock Classic", st.session_state.banner_text, content_width)
        
        st.session_state.skip_banner_injection = skip_banner_injection
        
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
        generator = NewsletterGenerator(template_type="default")
        
        newsletter_html, _ = generator.generate_newsletter(
            df=df,
            output_path=None,
            preview_text=preview_text,
            column_mapping=column_mapping,
            colors=colors,
            banner_input=banner_input,
            summary_html=summary_html,
            image_html=image_html,
            content_width=content_width,
            mobile_friendly=mobile_friendly,
            save_to_disk=False,
            template_type="default",
            skip_banner_injection=skip_banner_injection
        )
        
        # Apply direct color replacements
        newsletter_html = apply_colors_to_html(newsletter_html, colors)
        # More aggressive style injection
        newsletter_html = inject_direct_styles(newsletter_html, colors)
        # Fix dividers
        divider_bottom_color = colors.get('divider_color_2', '#ffce00')
        newsletter_html = fix_dividers(newsletter_html, divider_bottom_color)

        newsletter_html += f"\n<!-- Update timestamp: {update_time.timestamp()} -->\n"
        st.session_state.newsletter_html = newsletter_html
        st.session_state.needs_update = False
    
    except Exception as e:
        error_msg = f"Error updating preview: {str(e)}"
        print(f"[ERROR] {error_msg}")
        st.session_state.newsletter_error = True
        st.session_state.newsletter_error_msg = error_msg
    finally:
        st.session_state.preview_updating = False

def save_newsletter_for_sending():
    """
    Save the current newsletter to a temporary file for sending or downloading.
    Returns the path to the saved file.
    """
    global df, column_mapping
    if df is None or 'newsletter_html' not in st.session_state:
        return None
    try:
        generator = NewsletterGenerator(template_type="default")
        
        banner_selection = st.session_state.get('banner_selection_newsletter', "BlackRock Classic")
        content_width = st.session_state.get('content_width_newsletter', 800)
        mobile_friendly = st.session_state.get('mobile_friendly_newsletter', True)
        preview_text = st.session_state.get('preview_text_newsletter', "Your newsletter preview text here")
        
        skip_banner_injection = (banner_selection == "Default (Original Template)")
        
        # Gather colors
        colors = {
            'header_color_1': st.session_state.get('header_color_1_hex_newsletter', 
                st.session_state.get('header_color_1_newsletter', '#0168b1')),
            'header_color_2': st.session_state.get('header_color_2_hex_newsletter', 
                st.session_state.get('header_color_2_newsletter', '#333333')),
            'footer_color': st.session_state.get('footer_color_hex_newsletter',
                st.session_state.get('footer_color_newsletter', '#000000')),
            'divider_color_1': '#000000',
            'divider_color_2': st.session_state.get('divider_bottom_pick', '#ffce00'),
            'subheader_color': st.session_state.get('subheader_color_hex_newsletter',
                st.session_state.get('subheader_color_newsletter', '#0168b1')),
            'background': st.session_state.get('background_hex_newsletter',
                st.session_state.get('background_color_newsletter', '#e6e6e6')),
            'content_background': st.session_state.get('content_background_hex_newsletter',
                st.session_state.get('content_background_color_newsletter', '#ffffff')),
            
            'primary': st.session_state.get('header_color_1_newsletter', '#0168b1'),
            'secondary': st.session_state.get('header_color_2_newsletter', '#333333'),
            'header_bg': st.session_state.get('header_color_1_newsletter', '#0168b1'),
            'footer_bg': st.session_state.get('footer_color_newsletter', '#000000'),
            'highlight': st.session_state.get('subheader_color_newsletter', '#0168b1'),
            'banner_bg': st.session_state.get('banner_bg_pick', '#ffce00'),
            'subheader_bg': st.session_state.get('subheader_bg_pick', '#ffce00'),
        }
        if 'current_colors' in st.session_state:
            for k,v in st.session_state.current_colors.items():
                colors[k] = v
        
        banner_html_file = st.session_state.get('custom_banner_newsletter')
        if banner_selection == "Default (Original Template)":
            banner_input = None
        elif banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
            skip_banner_injection = False
        elif banner_selection in [
            "BlackRock Classic", "BlackRock Modern", "Yellow Accent", "Gradient Header", 
            "Minimalist", "Two-Column", "Bold Header", "Split Design",
            "Boxed Design", "Double Border", "Corner Accent", "Stacked Elements", "Executive Style"
        ]:
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text, content_width)
            skip_banner_injection = False
        else:
            banner_input = get_modified_banner_html("BlackRock Classic", st.session_state.banner_text, content_width)
            skip_banner_injection = False
        
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
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
            save_to_disk=True,
            template_type="default",
            skip_banner_injection=skip_banner_injection
        )
        
        if output_path:
            with open(output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            html_content = apply_colors_to_html(html_content, colors)
            html_content = inject_direct_styles(html_content, colors)
            divider_bottom_color = colors.get('divider_color_2', '#ffce00')
            html_content = fix_dividers(html_content, divider_bottom_color)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return output_path
    except Exception as e:
        error_msg = f"Error saving newsletter: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return None

# Main page content
st.title("📧 Newsletter Generator")
st.write("Create customized newsletters using your tagged articles or upload a CSV.")

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
        st.error("No tagged articles available. Please tag some articles or select another data source.")
elif data_source == "Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload your CSV file", 
        type=["csv"], 
        key="csv_uploader_newsletter"
    )
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df = clean_dataframe(df)
        st.success(f"Loaded {len(df)} articles from CSV")
    else:
        st.info("Please upload a CSV file with your news articles.")
elif data_source == "Use Demo Data":
    demo_file = "static/data/dummy_news.csv"
    if os.path.exists(demo_file):
        df = pd.read_csv(demo_file)
        df = clean_dataframe(df)
        st.success(f"Loaded demo dataset with {len(df)} articles")
    else:
        data = [
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
            },
            {
                "Company": "Finance Inc", 
                "News_Type": "Market Analysis", 
                "Article_Title": "Q1 Results",
                "Source": "Financial Times", 
                "Date": "03 March 2025",
                "Content": "First quarter results show strong performance across all sectors..."
            }
        ]
        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(demo_file), exist_ok=True)
        df.to_csv(demo_file, index=False)
        st.success(f"Created sample dataset with {len(df)} articles")

if df is None:
    st.warning("Please select a valid data source to continue.")
    with st.expander("CSV Format Example"):
        st.write("Your CSV could include columns like:")
        sample_data = [
            {
                "Company": "Technology Corp",
                "News_Type": "Product Updates",
                "Article_Title": "New Product Launch",
                "Source": "Tech Insider",
                "Date": "01 March 2025",
                "Content": "A revolutionary product..."
            },
            {
                "Company": "Technology Corp",
                "News_Type": "Industry News",
                "Article_Title": "Market Trends",
                "Source": "Business Journal",
                "Date": "02 March 2025",
                "Content": "Industry analysis shows significant growth..."
            }
        ]
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df)
        
        csv = sample_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="sample_newsletter_data.csv">Download sample CSV file</a>'
        st.markdown(href, unsafe_allow_html=True)
    st.stop()

st.subheader("Imported Data Preview")
if df is not None:
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
    display_cols = [c for c in priority_cols if c in df.columns]
    if not display_cols:
        display_cols = df.columns.tolist()
    
    st.dataframe(df[display_cols], use_container_width=True)
    column_mapping = create_column_mapping(df)
    st.info("Columns like 'Theme' or 'Subheader' from your tagging step will appear here if present.")

left_col, right_col = st.columns([6, 6])

# ------------------------------
# LEFT COLUMN: CONFIG / CONTENT
# ------------------------------
with left_col:
    st.subheader("Configuration")
    content_tabs = st.tabs(["Summary", "Image", "Layout", "Email Your Newsletter"])
    
    # -- SUMMARY TAB --
    with content_tabs[0]:
        st.subheader("Newsletter Summary")
        
        if 'selected' not in df.columns:
            df['selected'] = False
        
        st.write("Select articles to include in summary.")
        
        title_col = next((c for c in ['Article_Title','header_text','Title','Headline'] if c in df.columns), df.columns[0])
        source_col = next((c for c in ['Source','first_source_name','Publisher'] if c in df.columns), None)
        
        sel_cols = ['selected', title_col]
        if source_col:
            sel_cols.append(source_col)
        
        extra_info_cols = []
        for possible_info in ['Date','Theme','Subheader','Company','search_term']:
            if possible_info in df.columns and possible_info not in sel_cols:
                extra_info_cols.append(possible_info)
        if extra_info_cols:
            sel_cols.extend(extra_info_cols[:2])
        
        column_config = {
            "selected": st.column_config.CheckboxColumn("Select", help="Check to include in summary")
        }
        if title_col:
            column_config[title_col] = st.column_config.TextColumn("Article Title", help="Title of the article")
        if source_col:
            column_config[source_col] = st.column_config.TextColumn("Source", help="Source of the article")
        
        edited_df = st.data_editor(
            df[sel_cols],
            hide_index=True,
            use_container_width=True,
            key="summary_selector_newsletter",
            column_config=column_config
        )
        df['selected'] = edited_df['selected']
        selected_rows = df[df['selected']==True]
        selected_indices = selected_rows.index.tolist()
        
        if selected_indices:
            st.subheader("Generate Summary")
            prompt_tab, summary_tab = st.tabs(["1. Get Prompt for LLM", "2. Add Generated Summary"])
            
            with prompt_tab:
                prompt = generate_prompt(df, selected_indices)
                st.markdown("### Copy this prompt to your preferred LLM:")
                c1, c2 = st.columns([5,1])
                with c2:
                    if st.button("📋 Copy Prompt", use_container_width=True, key="copy_prompt_btn_newsletter"):
                        st.toast("Prompt copied to clipboard!", icon="✅")
                st.code(prompt, language="text")
                st.caption("**Two ways to copy:**\n1. Click the \"📋 Copy Prompt\" button\n2. Use the copy icon in the code block")
            
            with summary_tab:
                st.markdown("**After using the prompt, paste your generated summary here:**")
                user_summary = st.text_area("Paste your generated summary here:", height=200, key="user_summary_newsletter")
                
                if st.button("Add Summary to Newsletter", use_container_width=True, key="add_summary_btn_newsletter"):
                    st.session_state.summary_html = user_summary
                    update_preview_on_change()
                    st.success("Summary added to newsletter and preview updated!")
                
                st.markdown("**Preview of how the summary will appear:**")
                st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-top: 10px;">
                        <div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px;">
                            <span style="font-weight: bold; font-size: 20px;">Daily Summary</span>
                        </div>
                        <div style="font-size: 14px; line-height: 22px;">
                            {user_summary.replace('\n','<br>') if user_summary else "No summary provided."}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if 'summary_html' in st.session_state and st.session_state.summary_html:
                    if st.button("Remove Summary", use_container_width=True, key="remove_summary_btn_newsletter"):
                        st.session_state.summary_html = ""
                        update_preview_on_change()
                        st.success("Summary removed from newsletter.")
        else:
            st.info("Select articles above to generate a summary prompt.")
        
        if 'summary_html' in st.session_state and st.session_state.summary_html:
            st.success("Summary is currently included in newsletter.")
            with st.expander("View Current Summary"):
                st.markdown(st.session_state.summary_html, unsafe_allow_html=True)
    
    # -- IMAGE TAB --
    with content_tabs[1]:
        st.subheader("Add Image to Daily Summary")
        uploaded_image = st.file_uploader("Upload an image", type=["jpg","jpeg","png","gif"], key="image_upload_newsletter")
        image_caption = st.text_area("Image caption:", height=100, key="image_caption_newsletter")
        
        if uploaded_image:
            st.subheader("Image Preview")
            st.image(uploaded_image, width=400)
            if st.button("Add Image to Newsletter", use_container_width=True, key="add_image_btn_newsletter"):
                try:
                    img = Image.open(uploaded_image)
                    # Convert RGBA -> RGB
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255,255,255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    # Resize if necessary
                    max_width = 600
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_width = max_width
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height))
                    
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    formatted_image_html = f"""
                    <div style="padding: 5px 0; margin-top: 20px;">
                        <img src="data:image/jpeg;base64,{img_str}"
                             alt="Newsletter Image"
                             style="max-width:100%; height:auto; display:block; margin:0 auto; border:1px solid #ddd;">
                        <p style="color: #666666; font-family: 'Arial', sans-serif; font-size: 12px; 
                                line-height: 16px; font-style:italic; padding: 5px 0; text-align: center;">
                            {image_caption}
                        </p>
                    </div>
                    """
                    st.session_state.image_html = formatted_image_html
                    update_preview_on_change()
                    st.success("Image added to newsletter and preview updated!")
                except Exception as e:
                    st.error(f"Error processing image: {e}")
            
            if 'image_html' in st.session_state and st.session_state.image_html:
                st.success("Image is currently included in newsletter.")
                if st.button("Remove Image", use_container_width=True, key="remove_image_btn_newsletter"):
                    st.session_state.image_html = ""
                    update_preview_on_change()
                    st.success("Image removed from newsletter.")
    
    # -- LAYOUT TAB --
    with content_tabs[2]:
        st.subheader("Layout and Banner Settings")

        st.markdown("### Dimensions & Preview Text")
        content_width = st.slider("Content Width (px)", 600, 1000, 800, key="content_width_newsletter")
        mobile_friendly = st.checkbox("Mobile-friendly design", value=True, key="mobile_friendly_newsletter")
        
        # Radio to select how to fill preview text
        preview_text_option = st.radio(
            "Preview Text Options",
            ["Use custom preview text","Auto-generate from summary"],
            key="preview_text_option"
        )
        
        if preview_text_option == "Use custom preview text":
            preview_text = st.text_input(
                "Preview Text (shown in email clients)", 
                "Your newsletter preview text here",
                key="preview_text_newsletter"
            )
        else:
            st.info("Preview text will be auto-generated from the first 150 characters of your summary (if available).")
            # We do not store a preview_text here—it's done in update_preview_on_change()
        
        st.markdown("### Banner Selection")
        banner_options = [
            "Default (Original Template)",
            "BlackRock Classic", 
            "BlackRock Modern", 
            "Yellow Accent", 
            "Gradient Header", 
            "Minimalist", 
            "Two-Column", 
            "Bold Header", 
            "Split Design",
            "Boxed Design",
            "Double Border",
            "Corner Accent",
            "Stacked Elements",
            "Executive Style",
            "Upload Custom HTML Banner"
        ]
        
        banner_selection = st.radio(
            "Choose a banner style:",
            banner_options,
            horizontal=True,
            index=0,
            key="banner_selection_newsletter"
        )
        
        st.markdown("### Edit Banner Text")
        banner_html_file = None
        
        if banner_selection == "Default (Original Template)":
            st.info("Using the original template banner without modifications.")
        elif banner_selection == "BlackRock Classic":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['classic_title'] = st.text_input(
                    "Newsletter Title",
                    st.session_state.banner_text.get('classic_title', DEFAULT_BANNER_TEXTS['classic_title']),
                    key="classic_title_text_newsletter"
                )
                st.session_state.banner_text['classic_subtitle'] = st.text_input(
                    "Newsletter Subtitle",
                    st.session_state.banner_text.get('classic_subtitle', DEFAULT_BANNER_TEXTS['classic_subtitle']),
                    key="classic_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['classic_date'] = st.text_input(
                    "Date Text",
                    st.session_state.banner_text.get('classic_date', DEFAULT_BANNER_TEXTS['classic_date']),
                    key="classic_date_text_newsletter"
                )
        elif banner_selection == "BlackRock Modern":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['modern_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('modern_title', DEFAULT_BANNER_TEXTS['modern_title']),
                    key="modern_title_text_newsletter"
                )
                st.session_state.banner_text['modern_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('modern_subtitle', DEFAULT_BANNER_TEXTS['modern_subtitle']),
                    key="modern_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['modern_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('modern_date', DEFAULT_BANNER_TEXTS['modern_date']),
                    key="modern_date_text_newsletter"
                )
        elif banner_selection == "Yellow Accent":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['accent_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('accent_title', DEFAULT_BANNER_TEXTS['accent_title']),
                    key="accent_title_text_newsletter"
                )
                st.session_state.banner_text['accent_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('accent_subtitle', DEFAULT_BANNER_TEXTS['accent_subtitle']),
                    key="accent_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['accent_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('accent_date', DEFAULT_BANNER_TEXTS['accent_date']),
                    key="accent_date_text_newsletter"
                )
        elif banner_selection == "Gradient Header":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['gradient_title'] = st.text_input(
                    "Title", 
                    st.session_state.banner_text.get('gradient_title', DEFAULT_BANNER_TEXTS['gradient_title']),
                    key="gradient_title_text_newsletter"
                )
                st.session_state.banner_text['gradient_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('gradient_subtitle', DEFAULT_BANNER_TEXTS['gradient_subtitle']),
                    key="gradient_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['gradient_date'] = st.text_input(
                    "Date/Edition",
                    st.session_state.banner_text.get('gradient_date', DEFAULT_BANNER_TEXTS['gradient_date']),
                    key="gradient_date_text_newsletter"
                )
        elif banner_selection == "Minimalist":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['minimalist_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('minimalist_title', DEFAULT_BANNER_TEXTS['minimalist_title']),
                    key="minimalist_title_text_newsletter"
                )
                st.session_state.banner_text['minimalist_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('minimalist_subtitle', DEFAULT_BANNER_TEXTS['minimalist_subtitle']),
                    key="minimalist_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['minimalist_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('minimalist_date', DEFAULT_BANNER_TEXTS['minimalist_date']),
                    key="minimalist_date_text_newsletter"
                )
        elif banner_selection == "Two-Column":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['two_column_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('two_column_title', DEFAULT_BANNER_TEXTS['two_column_title']),
                    key="two_column_title_text_newsletter"
                )
                st.session_state.banner_text['two_column_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('two_column_subtitle', DEFAULT_BANNER_TEXTS['two_column_subtitle']),
                    key="two_column_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['two_column_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('two_column_date', DEFAULT_BANNER_TEXTS['two_column_date']),
                    key="two_column_date_text_newsletter"
                )
        elif banner_selection == "Bold Header":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['bold_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('bold_title', DEFAULT_BANNER_TEXTS['bold_title']),
                    key="bold_title_text_newsletter"
                )
                st.session_state.banner_text['bold_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('bold_subtitle', DEFAULT_BANNER_TEXTS['bold_subtitle']),
                    key="bold_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['bold_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('bold_date', DEFAULT_BANNER_TEXTS['bold_date']),
                    key="bold_date_text_newsletter"
                )
        elif banner_selection == "Split Design":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['split_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('split_title', DEFAULT_BANNER_TEXTS['split_title']),
                    key="split_title_text_newsletter"
                )
                st.session_state.banner_text['split_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('split_subtitle', DEFAULT_BANNER_TEXTS['split_subtitle']),
                    key="split_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['split_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('split_date', DEFAULT_BANNER_TEXTS['split_date']),
                    key="split_date_text_newsletter"
                )
        elif banner_selection == "Boxed Design":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['boxed_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('boxed_title', DEFAULT_BANNER_TEXTS['boxed_title']),
                    key="boxed_title_text_newsletter"
                )
                st.session_state.banner_text['boxed_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('boxed_subtitle', DEFAULT_BANNER_TEXTS['boxed_subtitle']),
                    key="boxed_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['boxed_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('boxed_date', DEFAULT_BANNER_TEXTS['boxed_date']),
                    key="boxed_date_text_newsletter"
                )
        elif banner_selection == "Double Border":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['double_border_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('double_border_title', DEFAULT_BANNER_TEXTS['double_border_title']),
                    key="double_border_title_text_newsletter"
                )
                st.session_state.banner_text['double_border_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('double_border_subtitle', DEFAULT_BANNER_TEXTS['double_border_subtitle']),
                    key="double_border_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['double_border_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('double_border_date', DEFAULT_BANNER_TEXTS['double_border_date']),
                    key="double_border_date_text_newsletter"
                )
        elif banner_selection == "Corner Accent":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['corner_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('corner_title', DEFAULT_BANNER_TEXTS['corner_title']),
                    key="corner_title_text_newsletter"
                )
                st.session_state.banner_text['corner_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('corner_subtitle', DEFAULT_BANNER_TEXTS['corner_subtitle']),
                    key="corner_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['corner_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('corner_date', DEFAULT_BANNER_TEXTS['corner_date']),
                    key="corner_date_text_newsletter"
                )
        elif banner_selection == "Stacked Elements":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['stacked_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('stacked_title', DEFAULT_BANNER_TEXTS['stacked_title']),
                    key="stacked_title_text_newsletter"
                )
                st.session_state.banner_text['stacked_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('stacked_subtitle', DEFAULT_BANNER_TEXTS['stacked_subtitle']),
                    key="stacked_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['stacked_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('stacked_date', DEFAULT_BANNER_TEXTS['stacked_date']),
                    key="stacked_date_text_newsletter"
                )
        elif banner_selection == "Executive Style":
            c1,c2 = st.columns(2)
            with c1:
                st.session_state.banner_text['executive_title'] = st.text_input(
                    "Title",
                    st.session_state.banner_text.get('executive_title', DEFAULT_BANNER_TEXTS['executive_title']),
                    key="executive_title_text_newsletter"
                )
                st.session_state.banner_text['executive_subtitle'] = st.text_input(
                    "Subtitle",
                    st.session_state.banner_text.get('executive_subtitle', DEFAULT_BANNER_TEXTS['executive_subtitle']),
                    key="executive_subtitle_text_newsletter"
                )
            with c2:
                st.session_state.banner_text['executive_date'] = st.text_input(
                    "Date",
                    st.session_state.banner_text.get('executive_date', DEFAULT_BANNER_TEXTS['executive_date']),
                    key="executive_date_text_newsletter"
                )
        elif banner_selection == "Upload Custom HTML Banner":
            banner_html_file = st.file_uploader(
                "Upload your HTML banner file",
                type=["html","htm"],
                key="custom_banner_newsletter"
            )
            if banner_html_file:
                st.success("HTML banner uploaded!")
            else:
                st.info("No custom banner uploaded yet.")
        
        st.markdown("### Extra Color Settings")
        cA, cB, cC, cD = st.columns(4)
        with cA:
            st.text("Banner Bottom")
            st.session_state.banner_bg_pick = st.color_picker("##banner", "#ffce00", label_visibility="collapsed")
        with cB:
            st.text("Divider Bottom")
            st.session_state.divider_bottom_pick = st.color_picker("##divider", "#ffce00", label_visibility="collapsed")
        with cC:
            st.text("Subheader Tag")
            st.session_state.subheader_bg_pick = st.color_picker("##subheader", "#ffce00", label_visibility="collapsed")
        with cD:
            st.text("Set All Colors")
            all_color = st.color_picker("##all", "#0000ff", label_visibility="collapsed")
            apply_all = st.checkbox("Apply to all", help="Use this color for all elements")
        
        st.markdown("Click 'Apply Changes' to generate a new preview.")
        if st.button("Apply Changes", use_container_width=True, key="apply_changes_btn"):
            with st.spinner("Applying changes..."):
                if apply_all:
                    st.session_state.banner_bg_pick = all_color
                    st.session_state.divider_bottom_pick = all_color
                    st.session_state.subheader_bg_pick = all_color
                
                for key_ in ["newsletter_html","needs_update","preview_updating"]:
                    if key_ in st.session_state:
                        del st.session_state[key_]
                        
                # Force regeneration
                update_preview_on_change()
                st.success("Changes applied, preview updated!")
                time.sleep(0.5)
                st.rerun()
    
    # -- EMAIL YOUR NEWSLETTER TAB --
    with content_tabs[3]:
        st.subheader("Send Newsletter via Email")
        
        c1,c2 = st.columns(2)
        with c1:
            sender_email = st.text_input(
                "From Email", 
                placeholder="your.name@company.com",
                key="sender_email_newsletter"
            )
        with c2:
            email_subject = st.text_input(
                "Subject", 
                f"Newsletter: {datetime.now().strftime('%B %d, %Y')}",
                key="email_subject_newsletter"
            )
        
        to_emails = st.text_area(
            "To Emails (comma separated)", 
            placeholder="recipient1@company.com, recipient2@company.com",
            key="to_emails_newsletter"
        )
        
        cc_col,bcc_col = st.columns(2)
        with cc_col:
            cc_emails = st.text_area(
                "CC",
                placeholder="cc1@company.com, cc2@company.com",
                key="cc_emails_newsletter",
                height=80
            )
        with bcc_col:
            bcc_emails = st.text_area(
                "BCC",
                placeholder="bcc1@company.com, bcc2@company.com",
                key="bcc_emails_newsletter",
                height=80
            )
        
        attach_newsletter = st.checkbox("Attach newsletter as HTML file", value=False, key="attach_newsletter_checkbox")
        
        if st.button("Send Newsletter Email", use_container_width=True, key="send_email_btn_newsletter"):
            if 'newsletter_html' not in st.session_state:
                st.error("Please generate the newsletter first.")
            elif not sender_email:
                st.error("Please enter the sender email address.")
            elif not to_emails:
                st.error("Please enter at least one recipient email address.")
            else:
                newsletter_html = st.session_state.newsletter_html
                output_path = None
                if attach_newsletter:
                    output_path = save_newsletter_for_sending()
                with st.spinner("Sending email ..."):
                    email_sender = EmailSender()
                    attachments = [output_path] if output_path else None
                    
                    success, msg = email_sender.send_html_email(
                        from_email=sender_email,
                        to_emails=to_emails,
                        subject=email_subject,
                        html_content=newsletter_html,
                        cc_emails=cc_emails,
                        bcc_emails=bcc_emails,
                        attachments=attachments
                    )
                    
                    if success:
                        st.success(msg)
                        to_count = len([e.strip() for e in to_emails.split(',') if e.strip()])
                        cc_count = len([e.strip() for e in cc_emails.split(',') if e.strip()]) if cc_emails else 0
                        bcc_count = len([e.strip() for e in bcc_emails.split(',') if e.strip()]) if bcc_emails else 0
                        st.session_state.email_history.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'recipients': to_count+cc_count+bcc_count,
                            'subject': email_subject
                        })
                    else:
                        st.error(f"Failed to send email: {msg}")
                    if output_path and os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except:
                            pass

# -------------------------
# RIGHT COLUMN: PREVIEW
# -------------------------
with right_col:
    st.subheader("Newsletter Preview")
    if df is not None and 'newsletter_html' not in st.session_state:
        update_preview_on_change()
    if st.session_state.get('newsletter_error', False):
        st.error(f"Error in preview generation: {st.session_state.get('newsletter_error_msg','Unknown error')}")
        if st.button("Clear Error", key="clear_error_btn"):
            st.session_state.newsletter_error = False
            st.session_state.newsletter_error_msg = ""
    
    update_timestamp = st.session_state.get('last_update_time', 'Not updated yet')
    st.caption(f"Last updated: {update_timestamp}")
    
    c1,c2 = st.columns([3,1])
    with c1:
        preview_height = st.slider(
            "Preview Height (px)", 
            400, 2000, 800, 100, 
            key="preview_height_slider"
        )
    
    # SINGLE, UNIFIED "Regenerate" button
    with c2:
        if st.button("Regenerate", type="primary", use_container_width=True, key="force_regenerate_btn"):
            with st.spinner("Completely regenerating newsletter..."):
                for key_ in ['newsletter_html','needs_update','preview_updating','preview_force_update']:
                    if key_ in st.session_state:
                        del st.session_state[key_]
                
                generator = NewsletterGenerator(template_type="default")
                
                banner_selection = st.session_state.get('banner_selection_newsletter', "Default (Original Template)")
                content_width = st.session_state.get('content_width_newsletter', 800)
                mobile_friendly = st.session_state.get('mobile_friendly_newsletter', True)
                # Check if user wants auto or custom preview text
                if st.session_state.get('preview_text_option') == "Auto-generate from summary":
                    if 'summary_html' in st.session_state and st.session_state.summary_html:
                        soup = BeautifulSoup(st.session_state.summary_html, 'html.parser')
                        raw_text = soup.get_text()
                        short_preview = raw_text[:150].strip()
                        if len(raw_text)>150:
                            short_preview += "..."
                        st.session_state.preview_text_newsletter = short_preview
                preview_text = st.session_state.get('preview_text_newsletter', "Your newsletter preview text here")
                
                summary_html = st.session_state.get('summary_html','')
                image_html = st.session_state.get('image_html','')
                
                skip_banner_injection = (banner_selection=="Default (Original Template)")
                
                banner_html_file = st.session_state.get("custom_banner_newsletter")
                if banner_selection=="Default (Original Template)":
                    banner_input = None
                elif banner_selection=="Upload Custom HTML Banner" and banner_html_file:
                    banner_input = banner_html_file
                    skip_banner_injection=False
                elif banner_selection in [
                    "BlackRock Classic","BlackRock Modern","Yellow Accent","Gradient Header",
                    "Minimalist","Two-Column","Bold Header","Split Design",
                    "Boxed Design","Double Border","Corner Accent","Stacked Elements","Executive Style"
                ]:
                    banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text, content_width)
                    skip_banner_injection=False
                else:
                    banner_input = get_modified_banner_html("BlackRock Classic", st.session_state.banner_text, content_width)
                    skip_banner_injection=False
                
                # Colors
                colors = {
                    'header_color_1': st.session_state.get('header_color_1_newsletter','#0168b1'),
                    'header_color_2': st.session_state.get('header_color_2_newsletter','#333333'),
                    'footer_color': st.session_state.get('footer_color_newsletter','#000000'),
                    'divider_color_1': '#000000',
                    'divider_color_2': st.session_state.get('divider_bottom_pick','#ffce00'),
                    'subheader_color': st.session_state.get('subheader_color_newsletter','#0168b1'),
                    'background': st.session_state.get('background_color_newsletter','#e6e6e6'),
                    'content_background': st.session_state.get('content_background_color_newsletter','#ffffff'),
                    'primary': st.session_state.get('header_color_1_newsletter','#0168b1'),
                    'secondary': st.session_state.get('header_color_2_newsletter','#333333'),
                    'header_bg': st.session_state.get('header_color_1_newsletter','#0168b1'),
                    'footer_bg': st.session_state.get('footer_color_newsletter','#000000'),
                    'highlight': st.session_state.get('subheader_color_newsletter','#0168b1'),
                    'banner_bg': st.session_state.get('banner_bg_pick','#ffce00'),
                    'divider_color_2': st.session_state.get('divider_bottom_pick','#ffce00'),
                    'subheader_bg': st.session_state.get('subheader_bg_pick','#ffce00'),
                }
                if 'current_colors' in st.session_state:
                    for k,v in st.session_state.current_colors.items():
                        colors[k] = v
                
                newsletter_html, _ = generator.generate_newsletter(
                    df=df,
                    output_path=None,
                    preview_text=preview_text,
                    column_mapping=column_mapping,
                    colors=colors,
                    banner_input=banner_input,
                    summary_html=summary_html,
                    image_html=image_html,
                    content_width=content_width,
                    mobile_friendly=mobile_friendly,
                    save_to_disk=False,
                    template_type="default",
                    skip_banner_injection=skip_banner_injection
                )
                
                # Force color updates
                newsletter_html = apply_colors_to_html(newsletter_html, colors)
                newsletter_html = inject_direct_styles(newsletter_html, colors)
                divider_bottom_color = colors.get('divider_color_2','#ffce00')
                newsletter_html = fix_dividers(newsletter_html, divider_bottom_color)
                
                newsletter_html += f"\n<!-- Regeneration timestamp: {int(time.time()*1000)} -->\n"
                st.session_state.newsletter_html = newsletter_html
                st.success(f"Newsletter regenerated with '{banner_selection}' banner!")
                time.sleep(0.5)
                st.rerun()
    
    # Show preview
    if 'newsletter_html' in st.session_state and st.session_state.newsletter_html:
        try:
            import streamlit.components.v1 as components
            html_with_timestamp = st.session_state.newsletter_html
            components.html(html_with_timestamp, height=preview_height, scrolling=True)
            st.caption("Scroll to see the full content.")
            
            if st.button("Download HTML", use_container_width=True):
                output_path = save_newsletter_for_sending()
                if output_path:
                    with open(output_path, "r", encoding='utf-8') as file:
                        html_content = file.read()
                    b64 = base64.b64encode(html_content.encode()).decode()
                    download_filename = f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    href = f'<a href="data:text/html;base64,{b64}" download="{download_filename}">Click to download</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    try:
                        os.remove(output_path)
                    except:
                        pass
        except ImportError:
            st.error("Unable to import streamlit.components for HTML preview.")
            with st.expander("View Newsletter HTML Code"):
                st.code(st.session_state.newsletter_html, language='html')
    else:
        if df is not None:
            st.info("Generating preview...")
            if 'newsletter_html' in st.session_state:
                del st.session_state['newsletter_html']
            update_preview_on_change()
            st.rerun()
        else:
            st.info("No newsletter generated yet.")

# Render sidebar and footer
render_sidebar()
render_footer()