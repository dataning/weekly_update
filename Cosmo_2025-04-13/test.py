import streamlit as st

# Set page config
st.set_page_config(
    page_title="Aladdin",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject CSS and HTML
css = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    body {
        font-family: 'Roboto', sans-serif;
        font-size: 0.8125rem;
        margin: 0;
        padding: 0;
        background-color: #f5f6f8; /* Adding light gray background to match screenshot */
    }

    a {
        text-decoration: none !important;
        color: #000000 !important;
    }

    /* Top navbar styles */
    .app-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
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
        font-size: 14px;
        font-weight: 500;
        color: #000000;
        font-family: 'Roboto', sans-serif;
        margin-left: 50px; /* ~5cm from left (sidebar button) */
        margin-top: 20px;
        text-transform: uppercase;
        z-index: 2;
    }

    .app-name {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        font-size: 32px;
        font-weight: 800;
        color: #000000;
        font-family: 'Roboto', sans-serif;
        z-index: 1;
    }

    .sub-navbar {
        position: fixed;
        top: 60px;
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

    .dropdown-arrow {
        margin-left: 5px;
        font-size: 10px;
    }

    .options-button {
        background: none;
        border: none;
        color: #000000;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        height: 40px;
        padding: 0 15px;
    }

    .options-button:hover {
        background-color: #f5f8ff;
        border-bottom: 2px solid #0000f3;
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
    }

    .search-icon {
        color: #6d7581;
    }

    .main-content {
        margin-top: 110px;
        padding: 20px;
        background-color: #f5f6f8; /* Added background color to match screenshot */
    }

    /* Override default Streamlit background as well */
    .stApp {
        background-color: #f5f6f8 !important;
    }

    .block-container {
        background-color: #f5f6f8 !important;
    }

    [data-testid="stSidebar"] {
        margin-top: 100px;
        background-color: white !important;
        max-width: 300px !important; /* Make sure Streamlit's own styling doesn't override our width */
    }

    button[kind="headerButton"] {
        display: none !important;
    }

    .sidebar-content {
        padding: 0;
    }

    .sidebar-section {
        padding: 15px 0;
        border-bottom: 1px solid #e6e6e6;
    }

    .sidebar-menu {
        padding: 0;
        margin: 0;
        list-style: none;
    }

    .sidebar-menu-item {
        display: flex;
        align-items: center;
        height: 40px;
        padding: 0 15px;
        font-size: 14px;
        font-family: 'Roboto', sans-serif;
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

    .sidebar-searchbox {
        background-color: #f1f2f4;
        border-radius: 4px;
        margin: 15px;
        padding: 8px 12px;
        color: #666;
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
    .main-content button,
    .stButton button,
    .main-content div {
        font-family: 'Roboto', sans-serif !important;
        font-size: 14px !important;
        color: #000000 !important;
    }

    /* Style for headings to be consistent */
    .main-content h1,
    .main-content h2,
    .main-content h3,
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

    .main-content ul li::marker {
        color: #000000 !important;
    }

    /* Button styling to match */
    .stButton > button {
        height: 36px !important;
        font-family: 'Roboto', sans-serif !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        padding: 0 15px !important;
        border-radius: 4px !important;
    }

</style>
"""

# HTML for header
navbar_html = """
<div class="app-header">
    <div class="app-title">APPLICATION NAME</div>
    <div class="app-name">Aladdin<span class="r-symbol">®</span></div>
    <div class="top-right-buttons">
        <a href="#" class="icon-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            Help
        </a>
        <a href="#" class="icon-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            Settings
        </a>
    </div>
</div>
<div class="sub-navbar">
    <div class="nav-items">
        <a href="/" class="nav-item">Home</a>
        <a href="/News_Search" class="nav-item">News Search</a>
        <a href="/News_Tagging" class="nav-item">News Tagging</a>
        <a href="/Newsletter_Generation" class="nav-item">Newsletter Generation</a>
        <a href="/Video_Feeds" class="nav-item">Video Feeds</a>
        <a href="/Social_Media" class="nav-item">Social Media</a>
    </div>
    <div class="nav-actions">
        <button class="options-button">Options ▼</button>
        <div class="search-box">
            <input type="text" class="search-input" placeholder="Search">
            <span class="search-icon">🔍</span>
        </div>
    </div>
</div>
<div class="main-content">
    <!-- Streamlit content goes here -->
</div>
"""

# JavaScript to override Streamlit sidebar and handle page navigation with multi-page app structure
sidebar_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    if (!sidebar) return;

    // Control the sidebar width here - change this value to adjust width
    const sidebarWidth = '300px'; // You can change this value as needed
    
    sidebar.style.transition = 'transform 0.3s ease';
    sidebar.style.width = sidebarWidth;
    sidebar.style.transform = 'translateX(0%)';

    const sidebarContent = document.createElement('div');
    sidebarContent.className = 'sidebar-content';
    sidebarContent.innerHTML = `
        <div class="sidebar-searchbox">Search</div>
        <div class="sidebar-menu">
            <a href="/" class="sidebar-menu-item">Home</a>
            <a href="/News_Search" class="sidebar-menu-item">News Search</a>
            <a href="/News_Tagging" class="sidebar-menu-item">News Tagging</a>
            <a href="/Newsletter_Generation" class="sidebar-menu-item">Newsletter Generation</a>
            <a href="/Video_Feeds" class="sidebar-menu-item">Video Feeds</a>
            <a href="/Social_Media" class="sidebar-menu-item">Social Media</a>
        </div>
    `;
    
    // Apply font styles directly to ensure they're applied
    setTimeout(function() {
        const sidebarItems = document.querySelectorAll('.sidebar-menu-item');
        sidebarItems.forEach(item => {
            item.style.fontSize = '13px';
            item.style.fontFamily = 'Roboto, sans-serif';
            item.style.fontWeight = '400';
            item.style.letterSpacing = 'normal';
        });
        
        const searchBox = document.querySelector('.sidebar-searchbox');
        if (searchBox) {
            searchBox.style.fontSize = '13px';
            searchBox.style.fontFamily = 'Roboto, sans-serif';
            searchBox.style.fontWeight = '400';
        }
    }, 600);

    setTimeout(function() {
        const streamlitSidebarContent = sidebar.querySelector('.block-container');
        if (streamlitSidebarContent) {
            streamlitSidebarContent.innerHTML = '';
            streamlitSidebarContent.appendChild(sidebarContent);
        }
        
        // Set active state based on current page
        highlightActivePage();
    }, 500);
    
    // Highlight active page in navbar and sidebar
    function highlightActivePage() {
        const currentPath = window.location.pathname;
        
        // Handle root path
        if (currentPath === '/' || currentPath === '') {
            document.querySelectorAll('.nav-item').forEach(item => {
                if (item.getAttribute('href') === '/') {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            
            document.querySelectorAll('.sidebar-menu-item').forEach(item => {
                if (item.getAttribute('href') === '/') {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            return;
        }
        
        // Handle other pages
        const pageName = currentPath.split('/').filter(Boolean).join('/');
        
        document.querySelectorAll('.nav-item').forEach(item => {
            const href = item.getAttribute('href');
            const itemPath = href.split('/').filter(Boolean).join('/');
            
            if (itemPath === pageName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        document.querySelectorAll('.sidebar-menu-item').forEach(item => {
            const href = item.getAttribute('href');
            const itemPath = href.split('/').filter(Boolean).join('/');
            
            if (itemPath === pageName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
});
</script>
"""

# Inject everything
st.markdown(css + navbar_html + sidebar_js, unsafe_allow_html=True)

# Main content area - for Home page only
# The pages in the pages/ directory will handle their own content
with st.container():
    st.title("Welcome to the Aladdin App")
    st.write("This is a Streamlit application with a fixed sidebar.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Main Features")
        st.write("""
        - **News Search**: Search for news articles 
        - **News Tagging**: Tag and categorize news articles
        - **Newsletter Generation**: Create newsletters from selected news
        - **Video Feeds**: Manage video content
        - **Social Media**: Track social media posts
        """)
        st.button("Get Started")
    
    with col2:
        st.subheader("Recent Updates")
        st.write("Latest system updates and improvements.")
        st.metric(label="System Performance", value="92%", delta="4%")