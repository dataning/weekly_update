import streamlit as st
import os
import re
from datetime import datetime

# App customization
APP_NAME = "Gravity"
APP_EMOJI = "👨‍🚀"

def set_app_name(name):
    """Set a custom name for the app"""
    global APP_NAME
    APP_NAME = name

def set_app_emoji(emoji):
    """Set a custom emoji for the app"""
    global APP_EMOJI
    APP_EMOJI = emoji

def get_streamlit_page_names(pages_dir='pages'):
    """Extract page names from Streamlit pages directory (01_Page_Name.py → Page_Name)"""
    if not os.path.exists(pages_dir):
        return []
    
    page_files = sorted([f for f in os.listdir(pages_dir) if f.endswith('.py')])
    page_names = []
    pattern = r'^\d+_(.+)\.py$'
    
    for file in page_files:
        match = re.search(pattern, file)
        if match:
            page_names.append(match.group(1))
    
    return page_names

def set_page_config():
    """Set the Streamlit page configuration"""
    st.set_page_config(
        page_title="Gravity",
        page_icon=APP_EMOJI,
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def apply_theme():
    """Apply custom CSS styling to the app"""
    st.markdown("""
    <style>
        /* Import Roboto font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');

        /* Global font settings */
        * {
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
            background-color: #f5f6f8;
        }

        a {
            text-decoration: none !important;
            color: #000000 !important;
        }

        /* Sidebar toggle button */
        .sidebar-toggle {
            position: fixed;
            top: 24px;
            right: -15px;
            width: 32.5px;
            height: 32.5px;
            background-color: #000000;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1100;
            font-weight: normal;
            font-size: 16px;
            border: none;
            transition: all 0.3s ease;
            border-radius: 4px;
            padding-right: 4px;
        }
        
        .sidebar-toggle.collapsed {
            background-color: #000000;
            left: 25px;
        }

        /* Top navbar */
        .app-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background-color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 0 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            z-index: 1000;
        }

        .app-title {
            position: relative;
            font-size: 20px;
            font-weight: 700;
            color: #000000;
            margin-left: 50px;
            margin-top: 20px;
            text-transform: uppercase;
            z-index: 1;
            line-height: 32px;
        }
        
        .app-name {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            font-size: 32px;
            font-weight: 800;
            color: #000000;
            z-index: 1;
            margin-left: 20px;
            margin-top: 22px;
            line-height: 60px;
        }
        
        .r-symbol {
            font-size: 8px;
            vertical-align: sub;
            margin-left: 2px;
            position: relative;
            bottom: 5px;
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
        }

        .nav-item:hover {
            background-color: #f5f8ff;
            border-bottom: 2px solid #0000f3;
        }

        .nav-item.active {
            background-color: #ffffff;
            font-weight: 500;
        }

        /* Main content area */
        .main-content {
            margin-top: 110px;
            padding: 0 20px 20px 20px;
            background-color: #f5f6f8;
            transition: margin-left 0.3s ease, width 0.3s ease;
            position: relative;
            width: 100%;
        }

        .stApp {
            background-color: #f5f6f8 !important;
        }

        .block-container {
            background-color: #f5f6f8 !important;
            padding-top: 0 !important;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            margin-top: 110px;
            background-color: white !important;
            max-width: 300px !important;
            transition: transform 0.3s ease, width 0.3s ease;
            position: fixed !important;
            height: calc(100vh - 100px) !important;
            z-index: 999;
        }

        .sidebar-expanded [data-testid="stSidebar"] {
            transform: translateX(0) !important;
        }

        .sidebar-expanded .main-content {
            margin-left: 300px !important;
            width: calc(100% - 300px) !important;
        }

        .sidebar-collapsed [data-testid="stSidebar"] {
            transform: translateX(-100%) !important;
        }

        .sidebar-collapsed .main-content {
            margin-left: 0 !important;
            width: 100% !important;
        }

        button[kind="headerButton"] {
            display: none !important;
        }

        .sidebar-menu-item {
            display: flex;
            align-items: center;
            height: 40px;
            padding: 0 15px;
            font-size: 14px;
            font-weight: 400;
            color: #000000;
            text-decoration: none;
            cursor: pointer;
        }

        .sidebar-menu-item:hover {
            background-color: #f5f8ff;
            border-left: 2px solid #0000f3;
        }

        .sidebar-menu-item.active {
            background-color: #ffffff;
            font-weight: 500;
            border-left: 2px solid #0000f3;
        }

        /* Button styling */
        .stButton > button {
            height: 36px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 0 15px !important;
            background-color: #ffffff !important;
            color: #0000f3 !important;
            border: 1px solid #0000f3 !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            transition: all 0.2s !important;
            box-shadow: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        .stButton > button:hover {
            background-color: #0000f3 !important;
            color: #ffffff !important;
        }

        /* Blue button style */
        .blue-button {
            background-color: #ffffff;
            color: #0000f3;
            border: 1px solid #0000f3;
            border-radius: 4px;
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
            background-color: #0000f3;
            color: #ffffff;
        }
        
        .blue-button .icon {
            margin-right: 5px;
            font-size: 16px;
            font-weight: bold;
        }

        /* Blue collar specific styles */
        .blue-collar-section {
            border-left: 4px solid #0000f3;
            padding-left: 15px;
        }
        
        .blue-collar-heading {
            color: #0000f3 !important;
            font-weight: 600 !important;
        }
        
        .blue-collar-tag {
            background-color: #0000f3;
            color: white !important;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px !important;
            font-weight: 500 !important;
            display: inline-block;
        }
        
        .blue-collar-link {
            color: #0000f3 !important;
            text-decoration: underline !important;
        }
        
        .blue-collar-table th {
            background-color: #0000f3 !important;
            color: white !important;
        }
        
        .blue-collar-table tr:hover {
            background-color: rgba(0, 0, 243, 0.05) !important;
        }

        /* Radio buttons styling */
        [data-testid="stRadio"] > div > div > label > div:first-child {
            background-color: #0000f3 !important;
            border-color: #0000f3 !important;
        }
        
        [data-testid="stRadio"] input:checked + div {
            border-color: #0000f3 !important;
            box-shadow: 0 0 0 1px #0000f3 !important;
        }
        
        /* Slider styling */
        [data-testid="stSlider"] .stSlider > div > div > div {
            background-color: #0000f3 !important;
        }
        
        [data-testid="stSlider"] .stSlider > div > div > div > div {
            background-color: #0000f3 !important;
        }
        
        /* Checkbox styling */
        [data-testid="stCheckbox"] > div > div > label > div:first-child {
            background-color: #0000f3 !important;
            border-color: #0000f3 !important;
        }

        /* Help Message Popup */
        #help-message-container {
            position: fixed;
            top: 120px;
            right: 20px;
            width: 350px;
            padding: 20px;
            background-color: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            border-radius: 4px;
            z-index: 1000;
            border: 1px solid #0000f3;
            display: none;
        }

        #help-message-container h3 {
            font-size: 18px;
            font-weight: 500;
            margin-top: 0;
            margin-bottom: 15px;
            color: #0000f3;
        }

        #help-message-container .help-close-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #666;
            padding: 0 5px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_navbar():
    """Render the navigation bar at the top of the page"""
    pages = get_streamlit_page_names()
    
    nav_links = '<a href="/" class="nav-item" target="_self">Home</a>'
    for page_name in pages:
        if page_name.lower() != "help":
            display_name = page_name.replace("_", " ")
            nav_links += f'<a href="/{page_name}" class="nav-item" target="_self">{display_name}</a>'
    
    navbar_html = f"""
    <button class="sidebar-toggle collapsed" id="sidebar-toggle">A</button>
    
    <div class="app-header">
        <div class="app-title">{APP_NAME}</div>
        <div class="app-name">Aladdin<span class="r-symbol">®</span></div>
    </div>
    <div class="sub-navbar">
        <div class="nav-items">
            {nav_links}
        </div>
        <div class="nav-actions">
            <a href="/Help" class="nav-item" id="help-button">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                Help
            </a>
        </div>
    </div>
    
    <div id="help-message-container">
        <button class="help-close-btn" id="help-close">×</button>
        <h3>Gravity Help Center</h3>
        
        <div class="help-section">
            <div class="help-section-title">Getting Started</div>
            <p>Welcome to Gravity! Here's how to get started with our application:</p>
            <ul>
                <li>Use the sidebar on the left to navigate between different tools</li>
                <li>Click on the navigation links above to access different pages</li>
                <li>Search for specific content using the search box</li>
            </ul>
        </div>
        
        <div class="help-section">
            <div class="help-section-title">Key Features</div>
            <ul>
                <li><strong>News Search:</strong> Find and analyze news articles</li>
                <li><strong>Newsletter Generator:</strong> Create professional newsletters</li>
                <li><strong>Content Analysis:</strong> Get insights from your content</li>
            </ul>
        </div>
        
        <div class="help-section">
            <div class="help-section-title">Need More Help?</div>
            <p>Contact our support team at <a href="mailto:support@gravity-app.com" style="color: #0000f3 !important; text-decoration: underline !important;">support@gravity-app.com</a></p>
        </div>
    </div>
    
    <div class="main-content">
        <!-- Streamlit content goes here -->
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)
    
    # JavaScript for help button functionality
    help_js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const helpButton = document.querySelector('#help-button');
        const helpContainer = document.querySelector('#help-message-container');
        const closeButton = document.querySelector('#help-close');
        
        if (helpButton && helpContainer && closeButton) {
            helpButton.addEventListener('click', function(e) {
                e.preventDefault();
                helpContainer.style.display = helpContainer.style.display === 'block' ? 'none' : 'block';
            });
            
            closeButton.addEventListener('click', function() {
                helpContainer.style.display = 'none';
            });
            
            document.addEventListener('click', function(e) {
                if (helpContainer.style.display === 'block' && 
                    !helpContainer.contains(e.target) && 
                    e.target !== helpButton) {
                    helpContainer.style.display = 'none';
                }
            });
        }
    });
    </script>
    """
    st.markdown(help_js, unsafe_allow_html=True)
    
def render_sidebar_js():
    """Inject JavaScript to handle sidebar toggle and navigation"""
    pages = get_streamlit_page_names()
    
    sidebar_links = '<a href="/" class="sidebar-menu-item" target="_self">Home</a>\n'
    for page_name in pages:
        display_name = page_name.replace("_", " ")
        sidebar_links += f'<a href="/{page_name}" class="sidebar-menu-item" target="_self">{display_name}</a>\n'
    
    sidebar_js = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Find Streamlit sidebar with retry
        function findSidebar(attempts = 0, maxAttempts = 10) {{
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) return sidebar;
            if (attempts < maxAttempts) {{
                setTimeout(() => findSidebar(attempts + 1, maxAttempts), 300);
                return null;
            }}
            return null;
        }}
        
        // Find main container
        function findMainContainer(attempts = 0, maxAttempts = 10) {{
            const main = window.parent.document.querySelector('.main');
            if (main) return main;
            if (attempts < maxAttempts) {{
                setTimeout(() => findMainContainer(attempts + 1, maxAttempts), 300);
                return null;
            }}
            return null;
        }}
        
        // Find elements
        const sidebar = findSidebar();
        if (!sidebar) return;
        const mainElement = findMainContainer();
        
        // Initial state
        document.body.classList.add('sidebar-collapsed');
        const sidebarWidth = '300px';
        
        // Style sidebar
        sidebar.style.transition = 'transform 0.3s ease, width 0.3s ease';
        sidebar.style.width = sidebarWidth;
        sidebar.style.maxWidth = sidebarWidth;
        sidebar.style.position = 'fixed';
        sidebar.style.height = 'calc(100vh - 100px)';
        sidebar.style.zIndex = '999';
        sidebar.style.transform = 'translateX(-100%)';
        
        // Track sidebar state
        let sidebarExpanded = false;

        // Create sidebar content
        const sidebarContent = document.createElement('div');
        sidebarContent.className = 'sidebar-content';
        sidebarContent.innerHTML = `
            <div class="sidebar-searchbox">Search</div>
            <div class="sidebar-menu">
                {sidebar_links}
            </div>
        `;
        
        // Apply font styles
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

        // Replace sidebar content
        setTimeout(function() {{
            const streamlitSidebarContent = sidebar.querySelector('.block-container');
            if (streamlitSidebarContent) {{
                streamlitSidebarContent.innerHTML = '';
                streamlitSidebarContent.appendChild(sidebarContent);
            }}
            
            highlightActivePage();
            setupToggleButton();
            setupNavigation();
        }}, 500);
        
        // Highlight active page
        function highlightActivePage() {{
            const currentPath = window.location.pathname;
            
            // Handle root path
            if (currentPath === '/' || currentPath === '') {{
                document.querySelectorAll('.nav-item, .sidebar-menu-item').forEach(item => {{
                    item.classList.toggle('active', item.getAttribute('href') === '/');
                }});
                return;
            }}
            
            // Handle other pages
            const pageName = currentPath.split('/').filter(Boolean).join('/');
            
            document.querySelectorAll('.nav-item, .sidebar-menu-item').forEach(item => {{
                const href = item.getAttribute('href');
                const itemPath = href.split('/').filter(Boolean).join('/');
                item.classList.toggle('active', itemPath === pageName);
            }});
        }}
        
        // Set up toggle button
        function setupToggleButton() {{
            const toggleButton = document.querySelector('#sidebar-toggle');
            if (!toggleButton) return;
            
            toggleButton.classList.add('collapsed');
            toggleButton.innerText = '>';
            
            toggleButton.addEventListener('click', function() {{
                if (sidebarExpanded) {{
                    // Close sidebar
                    sidebar.style.transform = 'translateX(-100%)';
                    toggleButton.classList.add('collapsed');
                    toggleButton.innerText = '>';
                    sidebarExpanded = false;
                    
                    document.body.classList.remove('sidebar-expanded');
                    document.body.classList.add('sidebar-collapsed');
                    
                    const mainContentEl = document.querySelector('.main-content');
                    if (mainContentEl) {{
                        mainContentEl.style.marginLeft = '0';
                        mainContentEl.style.width = '100%';
                    }}
                    
                    if (mainElement) {{
                        mainElement.style.marginLeft = '0';
                        mainElement.style.width = '100%';
                    }}
                }} else {{
                    // Open sidebar
                    sidebar.style.transform = 'translateX(0%)';
                    toggleButton.classList.remove('collapsed');
                    toggleButton.innerText = '×';
                    sidebarExpanded = true;
                    
                    document.body.classList.remove('sidebar-collapsed');
                    document.body.classList.add('sidebar-expanded');
                    
                    const mainContentEl = document.querySelector('.main-content');
                    if (mainContentEl) {{
                        mainContentEl.style.marginLeft = sidebarWidth;
                        mainContentEl.style.width = `calc(100% - ${{sidebarWidth}})`;
                    }}
                    
                    if (mainElement) {{
                        mainElement.style.marginLeft = sidebarWidth;
                        mainElement.style.width = `calc(100% - ${{sidebarWidth}})`;
                    }}
                }}
                
                window.dispatchEvent(new Event('resize'));
            }});
        }}
        
        // Setup navigation
        function setupNavigation() {{
            const navLinks = document.querySelectorAll('.nav-item, .sidebar-menu-item');
            
            navLinks.forEach(link => {{
                link.removeAttribute('target');
                link.setAttribute('target', '_self');
                
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const href = this.getAttribute('href');
                    window.parent.location.href = href;
                }});
            }});
        }}
        
        // Observer for DOM changes
        const observer = new MutationObserver(function(mutations) {{
            const toggleButton = document.querySelector('#sidebar-toggle');
            if (toggleButton && !toggleButton.hasAttribute('data-listener-attached')) {{
                setupToggleButton();
                toggleButton.setAttribute('data-listener-attached', 'true');
            }}
        }});
        
        observer.observe(document.body, {{ childList: true, subtree: true }});
        
        // Handle window resize
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

def render_sidebar():
    """Renders the application sidebar with navigation and tools"""
    with st.sidebar:
        # Add some space
        st.markdown("<br>" * 5, unsafe_allow_html=True)
        
        # Add a separator
        st.markdown("---")
        
        # Add copyright notice
        st.caption(f"© {datetime.now().year} Gravity | All Rights Reserved")

def render_footer():
    """Renders the application footer with copyright and links"""
    st.markdown("<br><hr style='margin: 0; padding: 0; height: 1px; border: none; background-color: #e0e0e0;'>", unsafe_allow_html=True)
    
    footer_container = st.container()
    with footer_container:
        cols = st.columns([3, 1])
        
        with cols[0]:
            current_year = datetime.now().year
            st.markdown(f"""
            <div style='font-size: 0.8rem; color: #666; padding: 1rem 0;'>
                © {current_year} Gravity | News Explorer & Newsletter Generator
                • <a href="#" target="_blank">Terms of Service</a>
                • <a href="#" target="_blank">Privacy Policy</a>
                • <a href="#" target="_blank">Contact Support</a>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[1]:
            st.markdown("""
            <div style='font-size: 0.8rem; color: #666; padding: 1rem 0; text-align: right;'>
                Made by PAG<br>
                Version 1.0.0
            </div>
            """, unsafe_allow_html=True)

def apply_full_theme():
    """Apply the complete theme including CSS, navbar and JavaScript"""
    apply_theme()
    render_navbar()
    render_sidebar_js()

# UI Components

def create_blue_button(text, icon="", key=None, url=None):
    """Create a button styled with the blue outline/filled style"""
    if url:
        onclick = f"window.location.href='{url}'"
    else:
        button_id = key if key else f"btn_{text.replace(' ', '_').lower()}"
        onclick = f"document.getElementById('{button_id}_clicked').value='true'; document.getElementById('{button_id}_form').submit();"
    
    form_html = "" if url else f"""
    <form id="{button_id}_form" method="post">
        <input type="hidden" id="{button_id}_clicked" name="{button_id}_clicked" value="false">
    </form>
    """
    
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
            border-left: 5px solid #0000f3;
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
    st.dataframe(df)