import streamlit as st
import os
import re

# Global variables for customization
APP_NAME = "Gravity"  # Default name
APP_EMOJI = "👨‍🚀"      # Default emoji

def set_app_name(name):
    """Set a custom name for the app (replaces 'Gravity' in the header)"""
    global APP_NAME
    APP_NAME = name

def set_app_emoji(emoji):
    """Set a custom emoji for the app (replaces the '✨' in page_icon)"""
    global APP_EMOJI
    APP_EMOJI = emoji

def get_streamlit_page_names(pages_dir='pages'):
    """
    Extract page names from Streamlit pages directory.
    Converts filenames like '01_News_Search.py' to just 'News_Search'.
    """
    # Check if directory exists
    if not os.path.exists(pages_dir):
        print(f"Directory '{pages_dir}' not found.")
        return []
    
    # Get all .py files
    page_files = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
    page_files.sort()  # Sort to maintain order based on number prefix
    
    # Extract page names using regex
    page_names = []
    pattern = r'^\d+_(.+)\.py$'
    
    for file in page_files:
        match = re.search(pattern, file)
        if match:
            page_name = match.group(1)  # Get the part after number and underscore
            page_names.append(page_name)
    
    return page_names

def set_page_config():
    """Set the page configuration for all pages"""
    global APP_EMOJI
    st.set_page_config(
        page_title="Gravity",
        page_icon=APP_EMOJI,
        layout="wide",
        initial_sidebar_state="collapsed"  # Changed from "expanded" to "collapsed"
    )

def apply_theme():
    """Apply custom theme and styling to the Gravity app"""
    # Inject CSS and HTML with consistent font styling across the entire app
    st.markdown("""
    <style>
        /* Import Roboto font with all needed weights */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');

        /* Global font settings - apply to everything */
        * {
            font-family: 'Roboto', sans-serif !important;
        }
        
        html, body, div, span, applet, object, iframe, h1, h2, h3, h4, h5, h6,
        p, blockquote, pre, a, abbr, acronym, address, big, cite, code, del,
        dfn, em, img, ins, kbd, q, s, samp, small, strike, strong, sub, sup,
        tt, var, b, u, i, center, dl, dt, dd, ol, ul, li, fieldset, form, label,
        legend, table, caption, tbody, tfoot, thead, tr, th, td {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Override Streamlit elements */
        .stTextInput input, .stTextArea textarea, .stNumberInput input, 
        .stDateInput input, .stTimeInput input, .stSelectbox, .stMultiselect,
        [data-testid="stWidgetLabel"], .stAlert, [data-baseweb="select"] {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Streamlit markdown text */
        [data-testid="stMarkdownContainer"] p, 
        [data-testid="stMarkdownContainer"] span, 
        [data-testid="stMarkdownContainer"] li, 
        [data-testid="stMarkdownContainer"] a, 
        [data-testid="stMarkdownContainer"] h1, 
        [data-testid="stMarkdownContainer"] h2, 
        [data-testid="stMarkdownContainer"] h3, 
        [data-testid="stMarkdownContainer"] h4, 
        [data-testid="stMarkdownContainer"] h5, 
        [data-testid="stMarkdownContainer"] h6 {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Buttons text */
        button, .stButton > button {
            font-family: 'Roboto', sans-serif !important;
        }

        /* All widgets */
        [data-testid="stWidgetLabel"] p {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Hide default Streamlit elements */
        MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* Base body styling */
        body {
            font-family: 'Roboto', sans-serif !important;
            font-size: 0.8125rem;
            margin: 0;
            padding: 0;
            background-color: #f5f6f8; /* Adding light gray background */
        }

        a {
            text-decoration: none !important;
            color: #000000 !important;
            font-family: 'Roboto', sans-serif !important;
        }

        /* Custom sidebar toggle button */
        .sidebar-toggle {
            position: fixed;
            top: 23px;
            right: 0px;
            width: 33px;
            height: 33px;
            background-color: #000000;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1100; /* Increased z-index to appear above the logo */
            font-weight: bold;
            font-size: 18px;
            font-family: 'Roboto', sans-serif !important;
            border: none;
            transition: all 0.3s ease;
            border-radius: 4px;
        }
        
        /* No A logo styling needed */
        
        /* Animated states for the toggle button */
        .sidebar-toggle.collapsed {
            background-color: #000000; /* Keep it black */
            left: 25px;
        }

        /* Top navbar styles */
        .app-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background-color: #ffffff;
            display: flex;
            align-items: center; /* Center items vertically */
            justify-content: flex-start;
            padding: 0 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            z-index: 1000;
        }

        /* Gravity title styling - next to sidebar button */
        .app-title {
            position: relative;
            font-size: 20px;
            font-weight: 700;
            color: #000000;
            font-family: 'Roboto', sans-serif !important;
            margin-left: 50px; /* Positioned to the right of sidebar toggle */
            margin-top: 20px; /* Remove top margin to allow center alignment */
            text-transform: uppercase;
            z-index: 1;
            line-height: 32px; /* Match height of hamburger icon */
        }
        
        /* Aladdin title - centered */
        .app-name {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            font-size: 32px;
            font-weight: 800;
            color: #000000;
            font-family: 'Roboto', sans-serif !important;
            z-index: 1;
            margin-left: 20px;
            margin-top: 22px; /* Remove top margin to allow center alignment */
            line-height: 60px; /* Center in header */
        }
        
        /* Trademark styling */
        .r-symbol {
            font-size: 8px;
            vertical-align: sub;
            margin-left: 2px;
            position: relative;
            bottom: 5px;
        }

        .app-name {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            font-size: 32px;
            font-weight: 800;
            color: #000000;
            font-family: 'Roboto', sans-serif !important;
            z-index: 1;
        }

        .sub-navbar {
            position: fixed;
            top: 70px;
            left: 0;
            right: 0;
            height: 40px;
            background-color: #f1f2f4;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 999;
            padding-left: 20px;
        }

        .nav-items {
            display: flex;
            height: 100%;
        }

        .nav-actions {
            display: flex;
            align-items: center;
            padding-right: 20px;
        }

        .nav-item {
            height: 40px;
            display: flex;
            align-items: center;
            padding: 0 15px;
            font-size: 14px;
            color: #000000;
            text-decoration: none;
            position: relative;
            font-family: 'Roboto', sans-serif !important;
        }

        .nav-item:hover {
            background-color: #f5f8ff;
            border-bottom: 2px solid #0000f3; /* Using our specific blue */
        }

        .nav-item.active {
            background-color: #ffffff;
            font-weight: 500;
        }

        .dropdown-arrow {
            margin-left: 5px;
            font-size: 10px;
        }

        .options-button {
            background: none;
            border: none;
            color: #000000;
            font-size: 14px;
            font-family: 'Roboto', sans-serif !important;
            cursor: pointer;
            display: flex;
            align-items: center;
            height: 40px;
            padding: 0 15px;
        }

        .options-button:hover {
            background-color: #f5f8ff;
            border-bottom: 2px solid #0000f3; /* Using our specific blue */
        }
        
        .top-right-buttons {
            position: absolute;
            right: 20px;
            top: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .icon-button {
            display: flex;
            align-items: center;
            font-size: 14px;
            color: #666;
            text-decoration: none;
            cursor: pointer;
            font-family: 'Roboto', sans-serif !important;
        }
        
        .icon-button svg {
            margin-right: 5px;
        }

        .search-box {
            display: flex;
            align-items: center;
            border: 1px solid #c0c4ca;
            border-radius: 4px;
            padding: 0 8px;
            height: 30px;
            margin-left: 15px;
        }

        .search-input {
            border: none;
            background: none;
            outline: none;
            font-size: 14px;
            width: 150px;
            font-family: 'Roboto', sans-serif !important;
        }

        .search-icon {
            color: #6d7581;
        }

        /* Main content area that will expand when sidebar collapses */
        .main-content {
            margin-top: 110px; /* Adjusted to account for header height and navbar */
            padding: 0 20px 20px 20px; /* Removed top padding since header has its own spacing */
            background-color: #f5f6f8; /* Added background color */
            font-family: 'Roboto', sans-serif !important;
            transition: margin-left 0.3s ease, width 0.3s ease; /* Add transition to margin changes */
            position: relative;
            width: 100%;
        }

        /* Override default Streamlit background as well */
        .stApp {
            background-color: #f5f6f8 !important;
            font-family: 'Roboto', sans-serif !important;
        }

        .block-container {
            background-color: #f5f6f8 !important;
            font-family: 'Roboto', sans-serif !important;
            /* Adjust padding to work well with header */
            padding-top: 0 !important;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            margin-top: 110px;
            background-color: white !important;
            max-width: 300px !important; /* Make sure Streamlit's own styling doesn't override our width */
            font-family: 'Roboto', sans-serif !important;
            transition: transform 0.3s ease, width 0.3s ease;
            position: fixed !important; /* Make sidebar positioned absolutely */
            height: calc(100vh - 100px) !important; /* Full height minus header */
            z-index: 999; /* High z-index to stay above content */
        }

        /* When sidebar is expanded, push main content */
        .sidebar-expanded [data-testid="stSidebar"] {
            transform: translateX(0) !important;
        }

        /* Main content adjustment when sidebar is visible */
        .sidebar-expanded .main-content {
            margin-left: 300px !important; /* Match sidebar width */
            width: calc(100% - 300px) !important;
        }

        /* When sidebar is collapsed, let main content take full width */
        .sidebar-collapsed [data-testid="stSidebar"] {
            transform: translateX(-100%) !important;
        }

        .sidebar-collapsed .main-content {
            margin-left: 0 !important;
            width: 100% !important;
        }

        /* Hide the default Streamlit sidebar button */
        button[kind="headerButton"] {
            display: none !important;
        }

        .sidebar-content {
            padding: 0;
            font-family: 'Roboto', sans-serif !important;
        }

        .sidebar-section {
            padding: 15px 0;
            border-bottom: 1px solid #e6e6e6;
            font-family: 'Roboto', sans-serif !important;
        }

        .sidebar-menu {
            padding: 0;
            margin: 0;
            list-style: none;
            font-family: 'Roboto', sans-serif !important;
        }

        .sidebar-menu-item {
            display: flex;
            align-items: center;
            height: 40px;
            padding: 0 15px;
            font-size: 14px;
            font-family: 'Roboto', sans-serif !important;
            font-weight: 400;
            color: #000000;
            text-decoration: none;
            cursor: pointer;
        }

        .sidebar-menu-item:hover {
            background-color: #f5f8ff;
            border-left: 2px solid #0000f3; /* Using our specific blue */
        }

        .sidebar-menu-item.active {
            background-color: #ffffff;
            font-weight: 500;
            border-left: 2px solid #0000f3; /* Using our specific blue */
        }

        .sidebar-searchbox {
            background-color: #f1f2f4;
            border-radius: 4px;
            margin: 15px;
            padding: 8px 12px;
            color: #666;
            font-family: 'Roboto', sans-serif !important;
        }

        .r-symbol {
            font-size: 8px;
            vertical-align: sub;
            margin-left: 2px;
            position: relative;
            bottom: 5px;
        }

        /* Make main content match menu bar font style */
        .main-content p, 
        .main-content li,
        .main-content button:not(.stButton button),
        .main-content div,
        .main-content span,
        .main-content a,
        .main-content label {
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
            color: #000000 !important;
        }
        
        /* Exception for navigation buttons */
        .stButton button {
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
        }

        /* Style for headings to be consistent */
        .main-content h1,
        .main-content h2,
        .main-content h3,
        .main-content h4,
        .main-content h5,
        .main-content h6,
        .main-content .stTitle,
        [data-testid="stHeader"] {
            font-family: 'Roboto', sans-serif !important;
            color: #000000 !important;
        }

        .main-content h1 {
            font-size: 24px !important;
            font-weight: 500 !important;
        }

        .main-content h2,
        .main-content h3 {
            font-size: 18px !important;
            font-weight: 500 !important;
        }

        /* Style for metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
        }

        [data-testid="stMetricLabel"] {
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
        }

        /* Bullet points styling */
        .main-content ul {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        .main-content ul li {
            font-family: 'Roboto', sans-serif !important;
        }

        .main-content ul li::marker {
            color: #000000 !important;
        }

        /* Button styling to match blue outline/filled style */
        .stButton > button {
            height: 36px !important;
            font-family: 'Roboto', sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 0 15px !important;
            background-color: #ffffff !important;
            color: #0000f3 !important; /* Using our specific blue */
            border: 1px solid #0000f3 !important; /* Using our specific blue */
            border-radius: 4px !important;
            cursor: pointer !important;
            transition: all 0.2s !important;
            box-shadow: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        .stButton > button:hover {
            background-color: #0000f3 !important; /* Using our specific blue */
            color: #ffffff !important;
        }

        /* Data editor and table styles */
        [data-testid="stTable"], 
        [data-testid="stDataFrame"] {
            font-family: 'Roboto', sans-serif !important;
        }

        [data-testid="stTable"] th, 
        [data-testid="stTable"] td, 
        [data-testid="stDataFrame"] th, 
        [data-testid="stDataFrame"] td {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Tabs text */
        [data-testid="stTabs"] button {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Radio buttons and checkboxes */
        [data-testid="stRadio"] label, 
        [data-testid="stCheckbox"] label {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Input fields */
        input, 
        select, 
        textarea, 
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stMultiselect > div > div {
            font-family: 'Roboto', sans-serif !important;
        }

        /* Create a custom function for blue outline buttons */
        .blue-button {
            background-color: #ffffff;
            color: #0000f3; /* Using our specific blue */
            border: 1px solid #0000f3; /* Using our specific blue */
            border-radius: 4px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 500;
            padding: 8px 16px;
            text-align: center;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            transition: all 0.2s;
            text-decoration: none;
        }
        
        .blue-button:hover {
            background-color: #0000f3; /* Using our specific blue */
            color: #ffffff;
        }
        
        .blue-button .icon {
            margin-right: 5px;
            font-size: 16px;
            font-weight: bold;
        }

        /* Blue collar specific styles */
        .blue-collar-section {
            border-left: 4px solid #0000f3; /* Using our specific blue */
            padding-left: 15px;
        }
        
        .blue-collar-heading {
            color: #0000f3 !important; /* Using our specific blue */
            font-weight: 600 !important;
        }
        
        .blue-collar-highlight {
            background-color: #0000f3; /* Using our specific blue without transparency */
            color: white !important;
            padding: 2px 5px;
            border-radius: 3px;
        }
        
        .blue-collar-tag {
            background-color: #0000f3; /* Using our specific blue */
            color: white !important;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px !important;
            font-weight: 500 !important;
            display: inline-block;
        }
        
        .blue-collar-link {
            color: #0000f3 !important; /* Using our specific blue */
            text-decoration: underline !important;
        }
        
        /* For any blue collar related tables */
        .blue-collar-table th {
            background-color: #0000f3 !important; /* Using our specific blue */
            color: white !important;
        }
        
        .blue-collar-table tr:hover {
            background-color: rgba(0, 0, 243, 0.05) !important; /* Using our specific blue with transparency */
        }

        /* NEW STYLES FOR RADIO BUTTONS */
        /* Target the radio button circles */
        [data-testid="stRadio"] > div > div > label > div:first-child {
            background-color: #0000f3 !important; /* Change from red to blue */
            border-color: #0000f3 !important;
        }
        
        /* Style for radio buttons when selected */
        [data-testid="stRadio"] input:checked + div {
            border-color: #0000f3 !important;
            box-shadow: 0 0 0 1px #0000f3 !important;
        }
        
        /* NEW STYLES FOR SLIDERS */
        /* Slider track */
        [data-testid="stSlider"] .stSlider > div > div > div {
            background-color: #0000f3 !important; /* Exact blue for track */
        }
        
        /* Slider thumb */
        [data-testid="stSlider"] .stSlider > div > div > div > div {
            background-color: #0000f3 !important; /* Blue for the thumb */
        }
        
        /* Active part of the slider */
        [data-testid="stSlider"] .stSlider > div > div > div:nth-child(1) {
            background-color: #0000f3 !important;
        }
        
        /* Ensure the slider handle is blue */
        [data-testid="stSlider"] .stThumbValue {
            background-color: #0000f3 !important;
        }
        
        /* Style for number input + and - buttons */
        .stNumberInput button {
            color: #0000f3 !important;
            border-color: #0000f3 !important;
        }
        
        .stNumberInput button:hover {
            background-color: rgba(0, 0, 243, 0.1) !important;
        }
        
        /* Checkbox styling */
        [data-testid="stCheckbox"] > div > div > label > div:first-child {
            background-color: #0000f3 !important;
            border-color: #0000f3 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_navbar():
    """Render the navigation bar at the top of the page with dynamically discovered pages"""
    global APP_NAME
    # Get page names from pages directory
    pages = get_streamlit_page_names()
    
    # Generate navigation links HTML - make sure we're building full HTML tags
    nav_links = '<a href="/" class="nav-item" target="_self">Home</a>'
    
    for page_name in pages:
        display_name = page_name.replace("_", " ")
        nav_links += f'<a href="/{page_name}" class="nav-item" target="_self">{display_name}</a>'
    
    # HTML for header with the sidebar toggle and dynamic navigation
    navbar_html = f"""
    <!-- Custom sidebar toggle button with hamburger icon -->
    <button class="sidebar-toggle collapsed" id="sidebar-toggle">></button>
    
    <div class="app-header">
        <div class="app-title">{APP_NAME}</div>
        <div class="app-name">Aladdin<span class="r-symbol">®</span></div>
    </div>
    <div class="sub-navbar">
        <div class="nav-items">
            {nav_links}
        </div>
    </div>
    
    <div class="main-content">
        <!-- Streamlit content goes here -->
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)
    
def render_sidebar_js():
    """JavaScript to override Streamlit sidebar and handle page navigation with dynamic pages"""
    # Get page names for sidebar links
    pages = get_streamlit_page_names()
    
    # Generate sidebar links HTML
    sidebar_links = '<a href="/" class="sidebar-menu-item" target="_self">Home</a>\n'
    for page_name in pages:
        display_name = page_name.replace("_", " ")
        sidebar_links += f'<a href="/{page_name}" class="sidebar-menu-item" target="_self">{display_name}</a>\n'
    
    sidebar_js = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Debug: Check if listener is attached
        console.log("DOM Content Loaded - Setting up sidebar");
        
        // Function to find Streamlit sidebar with retry
        function findSidebar(attempts = 0, maxAttempts = 10) {{
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            
            if (sidebar) {{
                console.log("Sidebar found on attempt:", attempts);
                return sidebar;
            }} else if (attempts < maxAttempts) {{
                console.log("Sidebar not found, retrying... (Attempt " + (attempts + 1) + "/" + maxAttempts + ")");
                setTimeout(() => findSidebar(attempts + 1, maxAttempts), 300);
                return null;
            }} else {{
                console.error("Failed to find sidebar after " + maxAttempts + " attempts");
                return null;
            }}
        }}
        
        // Function to find main container
        function findMainContainer(attempts = 0, maxAttempts = 10) {{
            const main = window.parent.document.querySelector('.main');
            
            if (main) {{
                console.log("Main container found on attempt:", attempts);
                return main;
            }} else if (attempts < maxAttempts) {{
                console.log("Main container not found, retrying... (Attempt " + (attempts + 1) + "/" + maxAttempts + ")");
                setTimeout(() => findMainContainer(attempts + 1, maxAttempts), 300);
                return null;
            }} else {{
                console.error("Failed to find main container after " + maxAttempts + " attempts");
                return null;
            }}
        }}
        
        // Find the sidebar with retry mechanism
        const sidebarElement = findSidebar();
        if (!sidebarElement) return;
        
        const sidebar = sidebarElement;
        
        // Find the main container
        const mainElement = findMainContainer();
        
        // Add body classes to track sidebar state (initially collapsed)
        document.body.classList.add('sidebar-collapsed');
        
        // Control the sidebar width here - change this value to adjust width
        const sidebarWidth = '300px'; 
        
        // Add custom styling to sidebar
        sidebar.style.transition = 'transform 0.3s ease, width 0.3s ease';
        sidebar.style.width = sidebarWidth;
        sidebar.style.maxWidth = sidebarWidth;
        sidebar.style.position = 'fixed';
        sidebar.style.height = 'calc(100vh - 100px)';
        sidebar.style.zIndex = '999';
        
        // Set sidebar to be initially closed
        sidebar.style.transform = 'translateX(-100%)';
        
        // Track sidebar state - set to collapsed by default
        let sidebarExpanded = false;
        
        // Debug: log sidebar properties
        console.log("Sidebar initial properties:", {{
            width: sidebar.style.width,
            transform: sidebar.style.transform,
            transition: sidebar.style.transition
        }});

        const sidebarContent = document.createElement('div');
        sidebarContent.className = 'sidebar-content';
        sidebarContent.innerHTML = `
            <div class="sidebar-searchbox">Search</div>
            <div class="sidebar-menu">
                {sidebar_links}
            </div>
        `;
        
        // Apply font styles after a delay
        setTimeout(function() {{
            const sidebarItems = document.querySelectorAll('.sidebar-menu-item');
            sidebarItems.forEach(item => {{
                item.style.fontSize = '13px';
                item.style.fontFamily = 'Roboto, sans-serif';
                item.style.fontWeight = '400';
                item.style.letterSpacing = 'normal';
            }});
            
            const searchBox = document.querySelector('.sidebar-searchbox');
            if (searchBox) {{
                searchBox.style.fontSize = '13px';
                searchBox.style.fontFamily = 'Roboto, sans-serif';
                searchBox.style.fontWeight = '400';
            }}
        }}, 600);

        setTimeout(function() {{
            const streamlitSidebarContent = sidebar.querySelector('.block-container');
            if (streamlitSidebarContent) {{
                // Debug: Log found content
                console.log("Found sidebar content to replace");
                streamlitSidebarContent.innerHTML = '';
                streamlitSidebarContent.appendChild(sidebarContent);
            }} else {{
                console.error("Could not find .block-container inside sidebar");
            }}
            
            // Set active state based on current page
            highlightActivePage();
            
            // Find and setup the toggle button
            setupToggleButton();
            
            // Setup navigation to use current tab
            setupNavigation();
        }}, 500);
        
        // Highlight active page in navbar and sidebar
        function highlightActivePage() {{
            const currentPath = window.location.pathname;
            
            // Handle root path
            if (currentPath === '/' || currentPath === '') {{
                document.querySelectorAll('.nav-item').forEach(item => {{
                    if (item.getAttribute('href') === '/') {{
                        item.classList.add('active');
                    }} else {{
                        item.classList.remove('active');
                    }}
                }});
                
                document.querySelectorAll('.sidebar-menu-item').forEach(item => {{
                    if (item.getAttribute('href') === '/') {{
                        item.classList.add('active');
                    }} else {{
                        item.classList.remove('active');
                    }}
                }});
                return;
            }}
            
            // Handle other pages
            const pageName = currentPath.split('/').filter(Boolean).join('/');
            
            document.querySelectorAll('.nav-item').forEach(item => {{
                const href = item.getAttribute('href');
                const itemPath = href.split('/').filter(Boolean).join('/');
                
                if (itemPath === pageName) {{
                    item.classList.add('active');
                }} else {{
                    item.classList.remove('active');
                }}
            }});
            
            document.querySelectorAll('.sidebar-menu-item').forEach(item => {{
                const href = item.getAttribute('href');
                const itemPath = href.split('/').filter(Boolean).join('/');
                
                if (itemPath === pageName) {{
                    item.classList.add('active');
                }} else {{
                    item.classList.remove('active');
                }}
            }});
        }}
        
        // Set up the toggle button with animation
        function setupToggleButton() {{
            // Add event listener for the sidebar toggle button
            const toggleButton = document.querySelector('#sidebar-toggle');
            if (!toggleButton) {{
                console.error("Toggle button not found!");
                return;
            }}
            
            console.log("Toggle button found and being set up");
            
            // Add collapsed class to toggle button initially
            toggleButton.classList.add('collapsed');
            toggleButton.innerText = '>';
            
            toggleButton.addEventListener('click', function() {{
                console.log("Toggle button clicked, current state:", sidebarExpanded);
                
                if (sidebarExpanded) {{
                    // Close sidebar
                    sidebar.style.transform = 'translateX(-100%)';
                    toggleButton.classList.add('collapsed');
                    toggleButton.innerText = '>';
                    sidebarExpanded = false;
                    
                    // Update body class for sidebar state
                    document.body.classList.remove('sidebar-expanded');
                    document.body.classList.add('sidebar-collapsed');
                    
                    // Reset main content margin
                    const mainContentEl = document.querySelector('.main-content');
                    if (mainContentEl) {{
                        mainContentEl.style.marginLeft = '0';
                        mainContentEl.style.width = '100%';
                    }}
                    
                    // Adjust Streamlit's main content container if available
                    if (mainElement) {{
                        mainElement.style.marginLeft = '0';
                        mainElement.style.width = '100%';
                    }}
                    
                    // Debug logging
                    console.log("Sidebar closed: ", {{
                        transform: sidebar.style.transform,
                        expanded: sidebarExpanded
                    }});
                }} else {{
                    // Open sidebar
                    sidebar.style.transform = 'translateX(0%)';
                    toggleButton.classList.remove('collapsed');
                    toggleButton.innerText = '×';  // Changed to X for close icon
                    sidebarExpanded = true;
                    
                    // Update body class for sidebar state
                    document.body.classList.remove('sidebar-collapsed');
                    document.body.classList.add('sidebar-expanded');
                    
                    // Add main content margin to accommodate sidebar
                    const mainContentEl = document.querySelector('.main-content');
                    if (mainContentEl) {{
                        mainContentEl.style.marginLeft = sidebarWidth;
                        mainContentEl.style.width = `calc(100% - ${{sidebarWidth}})`;
                    }}
                    
                    // Adjust Streamlit's main content container if available
                    if (mainElement) {{
                        mainElement.style.marginLeft = sidebarWidth;
                        mainElement.style.width = `calc(100% - ${{sidebarWidth}})`;
                    }}
                    
                    // Debug logging
                    console.log("Sidebar opened: ", {{
                        transform: sidebar.style.transform,
                        expanded: sidebarExpanded
                    }});
                }}
                
                // Trigger window resize to help Streamlit recalculate layouts
                window.dispatchEvent(new Event('resize'));
            }});
        }}
        
        // Setup navigation to prevent opening in new tabs
        function setupNavigation() {{
            // Get all navigation links from both navbar and sidebar
            const navLinks = document.querySelectorAll('.nav-item, .sidebar-menu-item');
            
            navLinks.forEach(link => {{
                // Remove any target attributes that might be set elsewhere
                link.removeAttribute('target');
                // Add target="_self" explicitly 
                link.setAttribute('target', '_self');
                
                link.addEventListener('click', function(e) {{
                    e.preventDefault(); // Prevent the default link behavior
                    
                    const href = this.getAttribute('href');
                    // Navigate within the current tab, using parent to break out of iframe if needed
                    window.parent.location.href = href;
                }});
            }});
            
            // Add direct click handlers to each link separately as a fallback
            document.querySelectorAll('.nav-item').forEach(navItem => {{
                navItem.onclick = function(e) {{
                    e.preventDefault();
                    const href = this.getAttribute('href');
                    window.parent.location.href = href;
                    return false;
                }};
            }});
            
            document.querySelectorAll('.sidebar-menu-item').forEach(sidebarItem => {{
                sidebarItem.onclick = function(e) {{
                    e.preventDefault();
                    const href = this.getAttribute('href');
                    window.parent.location.href = href;
                    return false;
                }};
            }});
        }}
        
        // Ensure sidebar toggle works by monitoring DOM mutations
        const observer = new MutationObserver(function(mutations) {{
            const toggleButton = document.querySelector('#sidebar-toggle');
            if (toggleButton && !toggleButton.hasAttribute('data-listener-attached')) {{
                setupToggleButton();
                toggleButton.setAttribute('data-listener-attached', 'true');
            }}
        }});
        
        observer.observe(document.body, {{ childList: true, subtree: true }});
        
        // Make sure to adjust layout on window resize
        window.addEventListener('resize', function() {{
            if (sidebarExpanded) {{
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {{
                    mainContentEl.style.marginLeft = sidebarWidth;
                    mainContentEl.style.width = `calc(100% - ${{sidebarWidth}})`;
                }}
                
                if (mainElement) {{
                    mainElement.style.marginLeft = sidebarWidth;
                    mainElement.style.width = `calc(100% - ${{sidebarWidth}})`;
                }}
            }} else {{
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {{
                    mainContentEl.style.marginLeft = '0';
                    mainContentEl.style.width = '100%';
                }}
                
                if (mainElement) {{
                    mainElement.style.marginLeft = '0';
                    mainElement.style.width = '100%';
                }}
            }}
        }});
    }});
    </script>
    """
    st.markdown(sidebar_js, unsafe_allow_html=True)

def apply_full_theme():
    """Apply the complete theme including CSS, navbar, and JavaScript"""
    apply_theme()
    render_navbar()
    render_sidebar_js()

# UI component functions

def create_blue_button(text, icon="", key=None, url=None):
    """Create a button styled like the blue outline/filled button"""
    if url:
        onclick = f"window.location.href='{url}'"
    else:
        # Use a unique key for the button interaction
        button_id = key if key else f"btn_{text.replace(' ', '_').lower()}"
        onclick = f"document.getElementById('{button_id}_clicked').value='true'; document.getElementById('{button_id}_form').submit();"
    
    # Hidden form and input to track button clicks
    form_html = ""
    if not url:
        form_html = f"""
        <form id="{button_id}_form" method="post">
            <input type="hidden" id="{button_id}_clicked" name="{button_id}_clicked" value="false">
        </form>
        """
    
    # Only add icon span if an icon is provided
    icon_html = f'<span class="icon">{icon}</span> ' if icon else ''
    
    button_html = f"""
    {form_html}
    <button class="blue-button" onclick="{onclick}">
        {icon_html}{text}
    </button>
    """
    
    return st.markdown(button_html, unsafe_allow_html=True)

def create_info_banner(message):
    """Create an information banner with a styled message"""
    st.markdown(
        f"""
        <div style="
            background-color: #f0f7ff;
            border-left: 5px solid #0000f3; /* Using our specific blue */
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-family: 'Roboto', sans-serif;
            font-size: 16px;
            line-height: 1.5;
        ">
            {message}
        </div>
        """, 
        unsafe_allow_html=True
    )

def create_feature_card(icon, title, description, button_text, button_key):
    """Create a feature card with icon, title, description and a button"""
    # Card container with styling
    with st.container():
        st.markdown(
            f"""
            <div style="
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                height: 100%;
            ">
                <div style="font-size: 36px; margin-bottom: 10px;">{icon}</div>
                <h3 style="font-family: 'Roboto', sans-serif; font-size: 18px; font-weight: 500; margin-bottom: 10px;">{title}</h3>
                <p style="font-family: 'Roboto', sans-serif; font-size: 14px; color: #666; margin-bottom: 10px; line-height: 1.5;">{description}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Button below the card with matching style to sidebar toggle
        return st.button(button_text, key=button_key)

def create_blue_collar_section(title, content):
    """Create a styled section for blue collar related content"""
    st.markdown(
        f"""
        <div class="blue-collar-section">
            <h2 class="blue-collar-heading">{title}</h2>
            <div>{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_blue_collar_tag(text):
    """Create a tag with the blue collar style"""
    return f'<span class="blue-collar-tag">{text}</span>'

def create_blue_collar_table(df):
    """Display a dataframe with blue collar styling"""
    st.markdown(
        """
        <style>
        /* Apply blue-collar-table class to the next table */
        .stDataFrame table {
            border-collapse: collapse;
            width: 100%;
        }
        
        .stDataFrame thead tr th {
            background-color: #0000f3 !important;
            color: white !important;
        }
        
        .stDataFrame tbody tr:hover {
            background-color: rgba(0, 0, 243, 0.05) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Display the dataframe
    st.dataframe(df)