"""
Banner templates and utilities for the Newsletter Generator app.
Contains HTML templates for different banner styles and utility functions for
managing, customizing, and embedding banners in newsletters.
"""

import os
import re
from bs4 import BeautifulSoup

# Corporate Communication Banner
CORPCOMM_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            /* We use flex-column so each "bar" stacks vertically */
            display: flex;
            flex-direction: column;
            margin: 0 auto;
        }
        
        /* Top black bar */
        .top-bar {
            background-color: #000000; /* black */
            color: #ffffff;           /* white text */
            display: flex;
            align-items: center;
            padding: 0 20px;
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            /* This portion takes up 40% of total height */
            height: 30%;
        }
        
        /* Middle white bar */
        .middle-bar {
            background-color: #ffffff; /* white */
            color: #000000;           /* black text */
            display: flex;
            align-items: center;
            padding: 0 20px;
            font-family: Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
            /* This portion also takes up 40% of total height */
            height: 60%;
        }
        
        /* Bottom colored strip */
        .bottom-bar {
            background-color: #FF4433; /* adjust to match your exact red/orange */
            /* This portion takes up the remaining 20% of total height */
            height: 10%;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="top-bar">BlackRock</div>
        <div class="middle-bar">BlackRock Daily News</div>
        <div class="bottom-bar"></div>
    </div>
</body>
</html>"""

# GIPS Infrastructure Banner
GIPS_BANNER = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* Overall banner container: 800x100 */
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            flex-direction: column;
            margin: 0 auto;
            font-family: Arial, sans-serif;
        }

        /* Top section: logo/brand on left, curated text on right */
        .top-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #ffffff; /* White background */
            height: 70%;              /* ~70px tall */
            padding: 0 10px;
            border-bottom: 2px solid #E45B2F; /* Orange divider line */
        }

        /* Brand area (logo + text) */
        .brand-area {
            display: flex;
            align-items: center;
        }

        /* Placeholder logo box—replace with an actual <img> if you have a file */
        .logo {
            width: 40px;
            height: 40px;
            background-color: #ccc; /* Temporary gray background */
            margin-right: 10px;
        }

        /* Main brand text */
        .brand-text {
            font-size: 14px;
            color: #000000;
        }

        /* Curated text on the right */
        .curated-text {
            text-align: right;
            font-size: 12px;
            font-weight: bold;
            color: #000000;
        }

        /* Bottom section: headline area */
        .bottom-section {
            background-color: #F3F2EC; /* Light gray/beige background */
            height: 30%;              /* ~30px tall */
            display: flex;
            align-items: center;
            padding: 0 10px;
        }

        .headline {
            font-size: 16px;
            font-weight: bold;
            color: #000000;
            margin: 0; /* Remove default <h1>/<h2> spacing if using those tags */
        }
    </style>
</head>
<body>
    <div class="banner">
        <!-- Top Section -->
        <div class="top-section">
            <div class="brand-area">
                <!-- Replace this .logo div with an <img> tag if you have a logo file -->
                <div class="logo"></div>
                <div class="brand-text">
                    Global Infrastructure Partners<br>
                    <span style="font-size: 12px; font-weight: normal;">
                        a part of BlackRock
                    </span>
                </div>
            </div>
        </div>

        <!-- Bottom Section -->
        <div class="bottom-section">
            <div class="headline">BGIF EMEA + Asia Weekly News</div>
        </div>
    </div>
</body>
</html>"""

# Modern Design Banner
MODERN_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            flex-direction: column;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Top part */
        .top-section {
            background-color: #0D1D41; /* Dark blue */
            color: #ffffff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 70%;
            padding: 0 20px;
        }
        
        .brand-text {
            font-size: 22px;
            font-weight: bold;
        }
        
        .date-text {
            font-size: 14px;
            opacity: 0.8;
        }
        
        /* Bottom part */
        .bottom-section {
            background-color: #E6E6E6; /* Light gray */
            height: 30%;
            display: flex;
            align-items: center;
            padding: 0 20px;
            border-bottom: 3px solid #00A9E0; /* Cyan accent */
        }
        
        .tagline {
            font-size: 14px;
            font-weight: 600;
            color: #333333;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="top-section">
            <div class="brand-text">BlackRock Insights</div>
            <div class="date-text">Weekly Digest</div>
        </div>
        <div class="bottom-section">
            <div class="tagline">Market Analysis & Investment Strategy</div>
        </div>
    </div>
</body>
</html>"""

# Gradient Style Banner
GRADIENT_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            flex-direction: column;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
        }
        
        .main-section {
            background: linear-gradient(135deg, #2C3E50, #4CA1AF);
            height: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 30px;
            color: white;
        }
        
        .left-content {
            display: flex;
            flex-direction: column;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .right-content {
            font-size: 16px;
            background: rgba(255,255,255,0.2);
            padding: 8px 15px;
            border-radius: 20px;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="main-section">
            <div class="left-content">
                <div class="title">BlackRock Newsletter</div>
                <div class="subtitle">Weekly Market Updates & Analysis</div>
            </div>
            <div class="right-content">March 2025 Edition</div>
        </div>
    </div>
</body>
</html>"""

# Minimalist Banner - Black and white with accent color
MINIMALIST_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            align-items: center;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            background-color: #FFFFFF;
            border-left: 8px solid #FF4713;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .content {
            padding: 0 30px;
        }
        
        .title {
            font-size: 28px;
            font-weight: bold;
            color: #000000;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666666;
        }
        
        .date {
            position: absolute;
            right: 30px;
            font-size: 14px;
            color: #FF4713;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="content">
            <div class="title">Minimalist Newsletter</div>
            <div class="subtitle">Clean design for modern communications</div>
        </div>
        <div class="date">March 2025</div>
    </div>
</body>
</html>"""

# Split Banner - Two-tone design with contrasting colors
SPLIT_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
        }
        
        .left-section {
            width: 40%;
            background-color: #6E3FA3;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0 20px;
        }
        
        .right-section {
            width: 60%;
            background-color: #FFFFFF;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0 20px;
            position: relative;
        }
        
        .right-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 6px;
            background-color: #FC9BB3;
        }
        
        .brand {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .tagline {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 5px;
        }
        
        .description {
            font-size: 13px;
            color: #666666;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="left-section">
            <div class="brand">Split Design</div>
            <div class="tagline">Distinctive newsletters that stand out</div>
        </div>
        <div class="right-section">
            <div class="title">Weekly Market Report</div>
            <div class="description">Analysis and insights for financial professionals</div>
        </div>
    </div>
</body>
</html>"""

# Bordered Banner - Simple border design with vibrant colors
BORDERED_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            background-color: #FFFFFF;
            border: 3px solid #FFCE00;
            box-sizing: border-box;
            position: relative;
        }
        
        .content {
            text-align: center;
        }
        
        .title {
            font-size: 28px;
            font-weight: bold;
            color: #008B5C;
            margin-bottom: 8px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666666;
        }
        
        .corner {
            position: absolute;
            width: 15px;
            height: 15px;
            background-color: #FFCE00;
        }
        
        .top-left {
            top: -3px;
            left: -3px;
        }
        
        .top-right {
            top: -3px;
            right: -3px;
        }
        
        .bottom-left {
            bottom: -3px;
            left: -3px;
        }
        
        .bottom-right {
            bottom: -3px;
            right: -3px;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="corner top-left"></div>
        <div class="corner top-right"></div>
        <div class="corner bottom-left"></div>
        <div class="corner bottom-right"></div>
        <div class="content">
            <div class="title">Bordered Newsletter Design</div>
            <div class="subtitle">Elegant framing for your important communications</div>
        </div>
    </div>
</body>
</html>"""

# Geometric Banner - Shapes and patterns using multiple colors
GEOMETRIC_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            position: relative;
            display: flex;
            align-items: center;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            background-color: #FFFFFF;
            overflow: hidden;
        }
        
        .shapes {
            position: absolute;
            width: 100%;
            height: 100%;
            z-index: 1;
        }
        
        .circle {
            position: absolute;
            width: 80px;
            height: 80px;
            border-radius: 50%;
        }
        
        .circle-1 {
            background-color: rgba(156, 121, 217, 0.3);
            top: -30px;
            left: 10%;
        }
        
        .circle-2 {
            background-color: rgba(200, 0, 88, 0.2);
            bottom: -40px;
            left: 30%;
            width: 100px;
            height: 100px;
        }
        
        .triangle {
            position: absolute;
            width: 0;
            height: 0;
            border-style: solid;
        }
        
        .triangle-1 {
            border-width: 0 50px 86.6px 50px;
            border-color: transparent transparent rgba(255, 206, 0, 0.3) transparent;
            right: 20%;
            top: -40px;
        }
        
        .rectangle {
            position: absolute;
            background-color: rgba(0, 87, 60, 0.2);
            width: 120px;
            height: 40px;
            right: 5%;
            bottom: 10px;
            transform: rotate(-15deg);
        }
        
        .content {
            position: relative;
            z-index: 2;
            padding: 0 30px;
            width: 100%;
        }
        
        .title {
            font-size: 28px;
            font-weight: bold;
            color: #000000;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666666;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="shapes">
            <div class="circle circle-1"></div>
            <div class="circle circle-2"></div>
            <div class="triangle triangle-1"></div>
            <div class="rectangle"></div>
        </div>
        <div class="content">
            <div class="title">Geometric Design</div>
            <div class="subtitle">Modern patterns for creative communications</div>
        </div>
    </div>
</body>
</html>"""

# Wave Banner - Curved wave design using gradient colors
WAVE_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            position: relative;
            display: flex;
            align-items: center;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            background-color: #FFFFFF;
            overflow: hidden;
        }
        
        .wave {
            position: absolute;
            height: 60px;
            width: 1200px;
            top: 70px;
            left: -200px;
            background: linear-gradient(90deg, #FFB194, #FC9BB3, #9E79D9);
            border-radius: 50% 50% 0 0;
        }
        
        .wave-2 {
            top: 45px;
            opacity: 0.3;
            background: linear-gradient(90deg, #9E79D9, #FC9BB3, #FFB194);
        }
        
        .content {
            position: relative;
            z-index: 2;
            padding: 0 30px;
        }
        
        .title {
            font-size: 28px;
            font-weight: bold;
            color: #000000;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666666;
        }
        
        .date {
            position: absolute;
            right: 30px;
            top: 38px;
            font-size: 14px;
            color: #6E3FA3;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="wave"></div>
        <div class="wave wave-2"></div>
        <div class="content">
            <div class="title">Wave Design Newsletter</div>
            <div class="subtitle">Flowing information with style</div>
        </div>
        <div class="date">March 2025</div>
    </div>
</body>
</html>"""

# Boxed Banner - Content in a bordered box with background colors
BOXED_BANNER = """<!DOCTYPE html>
<html>
<head>
    <style>
        .banner {
            width: 800px;
            height: 100px;
            display: flex;
            align-items: center;
            margin: 0 auto;
            font-family: 'Arial', sans-serif;
            background-color: #00573C;
            padding: 0 20px;
        }
        
        .box {
            border: 2px solid #9BD7BE;
            background-color: rgba(255, 255, 255, 0.1);
            padding: 15px 25px;
            display: flex;
            width: 100%;
        }
        
        .left-content {
            flex: 1;
        }
        
        .right-content {
            display: flex;
            align-items: center;
            justify-content: flex-end;
        }
        
        .title {
            font-size: 26px;
            font-weight: bold;
            color: #FFFFFF;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 13px;
            color: #9BD7BE;
        }
        
        .badge {
            background-color: #990012;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            letter-spacing: 1px;
        }
    </style>
</head>
<body>
    <div class="banner">
        <div class="box">
            <div class="left-content">
                <div class="title">Boxed Newsletter Design</div>
                <div class="subtitle">Structured content for professional communications</div>
            </div>
            <div class="right-content">
                <div class="badge">EXCLUSIVE</div>
            </div>
        </div>
    </div>
</body>
</html>"""

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

# Filename to content mapping
BANNER_HTML_CONTENT = {
    "corpcomm_banner.html": CORPCOMM_BANNER,
    "gips_infra_banner.html": GIPS_BANNER,
    "modern_banner.html": MODERN_BANNER,
    "gradient_banner.html": GRADIENT_BANNER,
    "minimalist_banner.html": MINIMALIST_BANNER,
    "split_banner.html": SPLIT_BANNER,
    "bordered_banner.html": BORDERED_BANNER,
    "geometric_banner.html": GEOMETRIC_BANNER,
    "wave_banner.html": WAVE_BANNER,
    "boxed_banner.html": BOXED_BANNER
}

# Default banner texts
DEFAULT_BANNER_TEXTS = {
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

def ensure_banner_files(banners_dir):
    """
    Ensures all banner files are present in the banners directory.
    Creates them if they don't exist.
    
    Args:
        banners_dir: Directory path where banner files should be stored
    """
    # Create the directory if it doesn't exist
    if not os.path.exists(banners_dir):
        os.makedirs(banners_dir)
    
    # Write each banner to the banners directory
    for filename, content in BANNER_HTML_CONTENT.items():
        filepath = os.path.join(banners_dir, filename)
        # Only write if the file doesn't already exist
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

def load_banner_file(filename, banners_dir):
    """
    Loads a banner file from the banners directory.
    
    Args:
        filename: Name of the banner file to load
        banners_dir: Directory where banner files are stored
        
    Returns:
        str: The HTML content of the banner file, or None if file not found
    """
    filepath = os.path.join(banners_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def get_modified_banner_html(banner_type, banner_text):
    """
    Modifies banner HTML based on banner type and user input text.
    
    Args:
        banner_type: Type of banner to modify
        banner_text: Dictionary containing user-provided text values
        
    Returns:
        str: Modified banner HTML content
    """
    if banner_type == "BlackRock Corporate (Default)":
        html_content = CORPCOMM_BANNER
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update top bar text
        top_bar = soup.select_one('.top-bar')
        if top_bar:
            top_bar.string = banner_text.get('corporate_top', DEFAULT_BANNER_TEXTS['corporate_top'])
        
        # Update middle bar text
        middle_bar = soup.select_one('.middle-bar')
        if middle_bar:
            middle_bar.string = banner_text.get('corporate_middle', DEFAULT_BANNER_TEXTS['corporate_middle'])
            
        return str(soup)
        
    elif banner_type == "GIPS Infrastructure":
        html_content = GIPS_BANNER
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
            
        return str(soup)
        
    elif banner_type == "Modern Design":
        html_content = MODERN_BANNER
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
            
        return str(soup)
        
    elif banner_type == "Gradient Style":
        html_content = GRADIENT_BANNER
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
            
        return str(soup)
    
    # Return original template if banner type not found
    return BANNER_HTML_CONTENT.get(BANNER_FILENAMES.get(banner_type, "corpcomm_banner.html"), "")

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

def inject_summary(html_content, summary_html):
    """
    Injects summary HTML after the "Additional Information" section.
    
    Args:
        html_content: The newsletter HTML content
        summary_html: The HTML content of the summary to inject
        
    Returns:
        str: Modified newsletter HTML with summary injected
    """
    if not summary_html or not html_content:
        return html_content
    
    target_pattern = r'<div>Please submit any feedback.*?<\/div>'
    
    if not re.search(target_pattern, html_content):
        target_pattern = r'<div>Additional Information:.*?<\/div>'
        if not re.search(target_pattern, html_content):
            # Fallback insertion point
            return html_content.replace('<table cellspacing="0" cellpadding="0" border="0" width="100%" align="center" class="full-width">', 
                                       f'<table cellspacing="0" cellpadding="0" border="0" width="100%" align="center" class="full-width">\n<tr><td colspan="3">{summary_html}</td></tr>')
    
    modified_html = re.sub(
        target_pattern, 
        lambda match: f"{match.group(0)}\n<div>{summary_html}</div>",
        html_content,
        count=1
    )
    return modified_html

def get_banner_template(banner_type, default_fallback="blue"):
    """
    Gets the banner template HTML for a given banner type.
    
    Args:
        banner_type: The type of banner to retrieve
        default_fallback: Fallback color if banner_type is not found
        
    Returns:
        str: The banner HTML template
    """
    if banner_type in BANNER_FILENAMES:
        filename = BANNER_FILENAMES[banner_type]
        return BANNER_HTML_CONTENT.get(filename, COLOR_BANNER_TEMPLATES.get(default_fallback))
    else:
        return COLOR_BANNER_TEMPLATES.get(banner_type, COLOR_BANNER_TEMPLATES.get(default_fallback))

# Test function - can be used to verify the module is working correctly
def test():
    print("Banner templates module - test output:")
    print(f"Number of banner templates: {len(BANNER_HTML_CONTENT)}")
    print(f"Number of color templates: {len(COLOR_BANNER_TEMPLATES)}")
    
    # Test a banner modification
    test_banner_text = {
        'corporate_top': 'Test Company',
        'corporate_middle': 'Daily Newsletter'
    }
    modified = get_modified_banner_html("BlackRock Corporate (Default)", test_banner_text)
    
    print(f"Modified banner contains 'Test Company': {'Test Company' in modified}")
    print(f"Modified banner contains 'Daily Newsletter': {'Daily Newsletter' in modified}")
    
    return "Tests completed successfully"

if __name__ == "__main__":
    test()