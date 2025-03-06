"""
Banner templates for the Newsletter Generator app.
Contains HTML templates for different banner styles.
"""

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

# NEW BANNERS:

# 1. Minimalist Banner - Black and white with accent color
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

# 2. Split Banner - Two-tone design with contrasting colors
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

# 3. Bordered Banner - Simple border design with vibrant colors
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

# 4. Geometric Banner - Shapes and patterns using multiple colors
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

# 5. Wave Banner - Curved wave design using gradient colors
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

# 6. Boxed Banner - Content in a bordered box with background colors
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

# Default banner HTML templates - used as fallbacks or color templates
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

# Mapping of banner types to filenames for consistency
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

# Banner HTML content mapping
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