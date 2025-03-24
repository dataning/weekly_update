"""
Banner service for handling banner templates and customization
"""
import os
import re
from bs4 import BeautifulSoup

# Banner type to filename mapping
BANNER_FILENAMES = {
    "BlackRock Corporate (Default)": "corpcomm_banner.html",
    "GIPS Infrastructure": "gips_infra_banner.html",
    "Modern Design": "modern_banner.html",
    "Gradient Style": "gradient_banner.html",
    "Minimalist": "minimalist_banner.html",
    "Split Design": "split_banner.html",
    "Bordered": "bordered_banner.html",
    "Geometric": "geometric_banner.html",
    "Wave": "wave_banner.html",
    "Boxed": "boxed_banner.html"
}

# Color-themed simple banner templates 
COLOR_BANNER_TEMPLATES = {
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
    """,
    "red": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #FFEBEE; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #D32F2F;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #B71C1C; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "teal": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E0F2F1; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #00897B;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #004D40; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "amber": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #FFF8E1; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #FFB300;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #FF6F00; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "indigo": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E8EAF6; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #3949AB;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #1A237E; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "cyan": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E0F7FA; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #00ACC1;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #006064; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "brown": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #EFEBE9; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #795548;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #3E2723; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """
}

# Default banner texts
DEFAULT_BANNER_TEXTS = {
    # Existing values
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
    'gradient_edition': 'March 2025 Edition',
    
    # New values for other banner types
    'minimalist_title': 'Minimalist Newsletter',
    'minimalist_subtitle': 'Clean design for modern communications',
    'minimalist_date': 'March 2025',
    
    'split_brand': 'Split Design',
    'split_tagline': 'Distinctive newsletters that stand out',
    'split_title': 'Weekly Market Report',
    'split_description': 'Analysis and insights for financial professionals',
    
    'bordered_title': 'Bordered Newsletter Design',
    'bordered_subtitle': 'Elegant framing for your important communications',
    
    'geometric_title': 'Geometric Design',
    'geometric_subtitle': 'Modern patterns for creative communications',
    
    'wave_title': 'Wave Design Newsletter',
    'wave_subtitle': 'Flowing information with style',
    'wave_date': 'March 2025',
    
    'boxed_title': 'Boxed Newsletter Design',
    'boxed_subtitle': 'Structured content for professional communications',
    'boxed_badge': 'EXCLUSIVE'
}

def load_banner_html(banner_type):
    """
    Load the banner HTML content for a given banner type
    
    Args:
        banner_type: The type of banner to load
        
    Returns:
        str: HTML content
    """
    if banner_type in BANNER_FILENAMES:
        filename = BANNER_FILENAMES[banner_type]
        template_path = f"templates/banners/{filename}"
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    # If the template doesn't exist or banner_type is not recognized,
    # return a color template as fallback
    if banner_type.lower() in COLOR_BANNER_TEMPLATES:
        return COLOR_BANNER_TEMPLATES[banner_type.lower()]
    
    # Default fallback
    return COLOR_BANNER_TEMPLATES["blue"]

def get_modified_banner_html(banner_type, banner_text):
    """
    Modifies banner HTML based on banner type and user input text.
    
    Args:
        banner_type: Type of banner to modify
        banner_text: Dictionary containing user-provided text values
        
    Returns:
        str: Modified banner HTML content
    """
    # Load the original banner HTML
    html_content = load_banner_html(banner_type)
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if banner_type == "BlackRock Corporate (Default)":
        # Update top bar text
        top_bar = soup.select_one('.top-bar')
        if top_bar:
            top_bar.string = banner_text.get('corporate_top', DEFAULT_BANNER_TEXTS['corporate_top'])
        
        # Update middle bar text
        middle_bar = soup.select_one('.middle-bar')
        if middle_bar:
            middle_bar.string = banner_text.get('corporate_middle', DEFAULT_BANNER_TEXTS['corporate_middle'])
    
    elif banner_type == "GIPS Infrastructure":
        # Update brand text
        brand_text_elem = soup.select_one('.brand-text')
        if brand_text_elem:
            # Clear existing content
            brand_text_elem.clear()
            
            # Add main brand text
            brand_text_elem.append(banner_text.get('gips_brand', DEFAULT_BANNER_TEXTS['gips_brand']))
            
            # Add a line break
            brand_text_elem.append(soup.new_tag('br'))
            
            # Add subtitle in a span
            subtitle_span = soup.new_tag('span')
            subtitle_span['style'] = 'font-size: 12px; font-weight: normal;'
            subtitle_span.string = banner_text.get('gips_subtitle', DEFAULT_BANNER_TEXTS['gips_subtitle'])
            brand_text_elem.append(subtitle_span)
        
        # Update headline text
        headline = soup.select_one('.headline')
        if headline:
            headline.string = banner_text.get('gips_headline', DEFAULT_BANNER_TEXTS['gips_headline'])
    
    elif banner_type == "Modern Design":
        # Update brand text
        brand_text = soup.select_one('.brand-text')
        if brand_text:
            brand_text.string = banner_text.get('modern_brand', DEFAULT_BANNER_TEXTS['modern_brand'])
        
        # Update date text
        date_text = soup.select_one('.date-text')
        if date_text:
            date_text.string = banner_text.get('modern_date', DEFAULT_BANNER_TEXTS['modern_date'])
        
        # Update tagline
        tagline = soup.select_one('.tagline')
        if tagline:
            tagline.string = banner_text.get('modern_tagline', DEFAULT_BANNER_TEXTS['modern_tagline'])
    
    elif banner_type == "Gradient Style":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('gradient_title', DEFAULT_BANNER_TEXTS['gradient_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('gradient_subtitle', DEFAULT_BANNER_TEXTS['gradient_subtitle'])
        
        # Update right content (edition)
        right_content = soup.select_one('.right-content')
        if right_content:
            right_content.string = banner_text.get('gradient_edition', DEFAULT_BANNER_TEXTS['gradient_edition'])
    
    elif banner_type == "Minimalist":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('minimalist_title', DEFAULT_BANNER_TEXTS['minimalist_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('minimalist_subtitle', DEFAULT_BANNER_TEXTS['minimalist_subtitle'])
        
        # Update date
        date = soup.select_one('.date')
        if date:
            date.string = banner_text.get('minimalist_date', DEFAULT_BANNER_TEXTS['minimalist_date'])
    
    elif banner_type == "Split Design":
        # Update brand
        brand = soup.select_one('.brand')
        if brand:
            brand.string = banner_text.get('split_brand', DEFAULT_BANNER_TEXTS['split_brand'])
        
        # Update tagline
        tagline = soup.select_one('.tagline')
        if tagline:
            tagline.string = banner_text.get('split_tagline', DEFAULT_BANNER_TEXTS['split_tagline'])
        
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('split_title', DEFAULT_BANNER_TEXTS['split_title'])
        
        # Update description
        description = soup.select_one('.description')
        if description:
            description.string = banner_text.get('split_description', DEFAULT_BANNER_TEXTS['split_description'])
    
    elif banner_type == "Bordered":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('bordered_title', DEFAULT_BANNER_TEXTS['bordered_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('bordered_subtitle', DEFAULT_BANNER_TEXTS['bordered_subtitle'])
    
    elif banner_type == "Geometric":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('geometric_title', DEFAULT_BANNER_TEXTS['geometric_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('geometric_subtitle', DEFAULT_BANNER_TEXTS['geometric_subtitle'])
    
    elif banner_type == "Wave":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('wave_title', DEFAULT_BANNER_TEXTS['wave_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('wave_subtitle', DEFAULT_BANNER_TEXTS['wave_subtitle'])
        
        # Update date
        date = soup.select_one('.date')
        if date:
            date.string = banner_text.get('wave_date', DEFAULT_BANNER_TEXTS['wave_date'])
    
    elif banner_type == "Boxed":
        # Update title
        title = soup.select_one('.title')
        if title:
            title.string = banner_text.get('boxed_title', DEFAULT_BANNER_TEXTS['boxed_title'])
        
        # Update subtitle
        subtitle = soup.select_one('.subtitle')
        if subtitle:
            subtitle.string = banner_text.get('boxed_subtitle', DEFAULT_BANNER_TEXTS['boxed_subtitle'])
        
        # Update badge
        badge = soup.select_one('.badge')
        if badge:
            badge.string = banner_text.get('boxed_badge', DEFAULT_BANNER_TEXTS['boxed_badge'])
    
    # Return the modified HTML
    return str(soup)

def extract_banner_from_html(html_file_or_content, content_width=800):
    """
    Extract banner HTML from an uploaded HTML file, file path, or HTML content string
    and adjust its width.
    
    Args:
        html_file_or_content: The uploaded HTML file, file path, or HTML content
        content_width: The desired width for the banner (defaults to 800px)
        
    Returns:
        tuple: (banner_html, style_content) - The extracted banner HTML and CSS styles
    """
    if html_file_or_content is None:
        return None, None
    
    try:
        # Determine what type of input we have
        if isinstance(html_file_or_content, str):
            if html_file_or_content.strip().startswith('<!DOCTYPE') or html_file_or_content.strip().startswith('<html'):
                # This is already HTML content
                content = html_file_or_content
            elif os.path.exists(html_file_or_content):
                # This is a file path
                with open(html_file_or_content, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # Could be HTML content without common opening tags
                content = html_file_or_content
        else:
            # This is an uploaded file
            try:
                content = html_file_or_content.getvalue().decode('utf-8')
            except AttributeError:
                # Last resort - try to convert to string
                content = str(html_file_or_content)
        
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
        print(f"Error extracting banner from HTML: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None, None

def inject_banner_into_newsletter(html_content, banner_html, banner_styles=None, content_width=800):
    """
    Injects the custom banner HTML directly into the newsletter HTML.
    
    Args:
        html_content: The newsletter HTML content
        banner_html: The banner HTML to inject
        banner_styles: CSS styles for the banner
        content_width: The desired width for the banner
        
    Returns:
        str: Modified newsletter HTML with banner injected
    """
    if not banner_html or not html_content:
        return html_content
    
    # Find the location to insert the banner
    banner_insertion_marker = "<!-- Custom Banner -->"
    if banner_insertion_marker not in html_content:
        print("Could not find the banner insertion point in the template.")
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

def update_html_dimensions(html_content, width):
    """
    Updates all occurrences of width:800px and width="800" in HTML content,
    adjusting other related dimensions.
    
    Args:
        html_content: The HTML content to modify
        width: The new width to set
        
    Returns:
        str: Modified HTML content with updated dimensions
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