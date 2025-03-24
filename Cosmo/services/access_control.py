"""
Enhanced Authentication and Access Control Module
-----------------------------------------------
Handles authentication, access control, and token management for CriticalMention API.
Dark mode compatible version.
"""

import streamlit as st
import json
import os
import requests
import time
from datetime import datetime, timedelta
import hashlib
from services.cookie_retriever import get_criticalmention_cookies, try_alternative_auth, try_selenium_auth

# Constants
CONFIG_FILE = "config.json"

# Helper functions
def load_config():
    """Load configuration from config file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return {}
    else:
        st.error(f"Config file not found: {CONFIG_FILE}")
        return {}

def save_config(config):
    """Save configuration to config file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def initialize_session_state():
    """Initialize session state variables for authentication if they don't exist"""
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'auth_attempts' not in st.session_state:
        st.session_state.auth_attempts = 0
    if 'lockout_until' not in st.session_state:
        st.session_state.lockout_until = None
    if 'auth_method' not in st.session_state:
        st.session_state.auth_method = "manual"  # 'manual' or 'api'

def validate_access_code(input_code):
    """
    Validate the access code against the stored code in config.json
    
    Parameters:
    -----------
    input_code : str
        The access code entered by the user
        
    Returns:
    --------
    bool
        True if valid, False otherwise
    """
    config = load_config()
    
    # Check if premier_access configuration exists
    if "premier_access" not in config:
        st.error("Premier access configuration not found in config.json")
        return False
    
    # Get stored access code - checks for either code_hash or access_code
    if "code_hash" in config["premier_access"]:
        # Use hash-based validation for enhanced security
        stored_hash = config["premier_access"]["code_hash"]
        input_hash = hashlib.sha256(input_code.encode()).hexdigest()
        return input_hash == stored_hash
    elif "access_code" in config["premier_access"]:
        # Direct comparison with plaintext access code
        return input_code == config["premier_access"]["access_code"]
    else:
        st.error("No access code configuration found")
        return False

def check_lockout():
    """
    Check if the user is currently locked out
    
    Returns:
    --------
    bool
        True if locked out, False otherwise
    """
    if st.session_state.lockout_until is None:
        return False
    
    current_time = datetime.now()
    lockout_time = st.session_state.lockout_until
    
    if current_time > lockout_time:
        # Lockout period has expired
        st.session_state.lockout_until = None
        st.session_state.auth_attempts = 0
        return False
    
    # Still locked out
    return True

def check_expiration():
    """
    Check if the access code has expired
    
    Returns:
    --------
    bool
        True if expired, False otherwise
    """
    config = load_config()
    
    if "premier_access" not in config or "expiration_date" not in config["premier_access"]:
        return False
    
    try:
        expiration = datetime.fromisoformat(config["premier_access"]["expiration_date"])
        if datetime.now() > expiration:
            return True
    except (ValueError, TypeError):
        pass
    
    return False

def api_login_criticalmention(username, password):
    """
    Authenticate with CriticalMention using direct API calls
    
    Parameters:
    -----------
    username : str
        CriticalMention username
    password : str
        CriticalMention password
        
    Returns:
    --------
    str or None
        Authentication cookie string if successful, None if failed
    """
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    debug_info = st.empty()
    
    try:
        # Update status
        status_text.text("Initializing authentication...")
        progress_bar.progress(10)
        
        # First request - Get the login page to obtain any CSRF tokens
        status_text.text("Retrieving login page...")
        progress_bar.progress(20)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        login_page_response = session.get("https://app.criticalmention.com/app/#user/login", headers=headers)
        
        if login_page_response.status_code != 200:
            status_text.text(f"Failed to access login page: {login_page_response.status_code}")
            debug_info.error(f"Login page response: {login_page_response.status_code} - {login_page_response.reason}")
            return None
        
        # Display how many cookies we got from the login page
        initial_cookies = len(session.cookies)
        debug_info.info(f"Got {initial_cookies} cookies from login page")
        
        # Update status
        status_text.text("Preparing login credentials...")
        progress_bar.progress(40)
        
        # Second request - Submit login credentials
        login_url = "https://app.criticalmention.com/api/v1/auth"
        
        login_data = {
            "username": username,
            "password": password
        }
        
        login_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://app.criticalmention.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://app.criticalmention.com/app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        status_text.text("Authenticating...")
        progress_bar.progress(60)
        
        login_response = session.post(login_url, json=login_data, headers=login_headers)
        
        # Show detailed login response for debugging
        debug_info.info(f"Login response status: {login_response.status_code} - {login_response.reason}")
        
        if login_response.status_code != 200:
            status_text.text(f"Login failed: {login_response.status_code}")
            debug_info.error(f"Login failed with status: {login_response.status_code} - {login_response.reason}")
            return None
        
        # Check the login response content
        try:
            login_result = login_response.json()
            debug_info.info(f"Login response content: {login_result}")
            
            # Check for success indicators in the response
            if "error" in login_result:
                status_text.text(f"Login failed: {login_result['error']}")
                debug_info.error(f"Login error: {login_result['error']}")
                return None
            elif "success" in login_result and not login_result["success"]:
                status_text.text("Login failed: Request rejected")
                debug_info.error("Login success flag is False")
                return None
        except Exception as e:
            debug_info.warning(f"Non-JSON login response or parsing error: {str(e)}")
            debug_info.info(f"Response content: {login_response.text[:200]}...")
            # Continue anyway as some APIs don't return JSON
        
        # Check how many cookies we have after login
        after_login_cookies = len(session.cookies)
        debug_info.info(f"Cookies after login: {after_login_cookies} (added {after_login_cookies - initial_cookies})")
        
        # Update status
        status_text.text("Verifying authentication...")
        progress_bar.progress(80)
        
        # Third request - Access a protected page to ensure we're logged in
        verify_url = "https://app.criticalmention.com/api/v1/user/profile"
        
        verify_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://app.criticalmention.com/app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        verify_response = session.get(verify_url, headers=verify_headers)
        
        # Show verification response for debugging
        debug_info.info(f"Verification response: {verify_response.status_code} - {verify_response.reason}")
        
        if verify_response.status_code != 200:
            status_text.text(f"Authentication verification failed: {verify_response.status_code}")
            debug_info.error(f"Verification failed: {verify_response.status_code} - {verify_response.reason}")
            try:
                debug_info.error(f"Response content: {verify_response.json()}")
            except:
                debug_info.error(f"Response content: {verify_response.text[:200]}...")
            return None
        
        # Extract all cookies from the session
        status_text.text("Extracting authentication cookies...")
        progress_bar.progress(90)
        
        # Show all cookies for debugging
        for cookie in session.cookies:
            debug_info.info(f"Cookie: {cookie.name}={cookie.value[:10]}...")
        
        # Convert cookies to string format
        cookie_string = "; ".join([f"{name}={value}" for name, value in session.cookies.items()])
        
        # Check if we actually got any cookies
        if not cookie_string or len(cookie_string) < 20:
            status_text.text("Authentication failed: No valid cookies obtained")
            debug_info.error(f"Empty or invalid cookie string: {cookie_string}")
            return None
        
        # Complete the progress
        status_text.text("Authentication completed successfully!")
        progress_bar.progress(100)
        
        debug_info.success(f"Extracted {len(session.cookies)} cookies")
        return cookie_string
        
    except Exception as e:
        # Handle any unexpected errors
        status_text.text(f"An error occurred: {str(e)}")
        debug_info.exception(f"Exception during authentication: {str(e)}")
        return None

# Alternative method to try - Direct manual request with minimal dependencies
def direct_login_criticalmention(username, password):
    """
    Alternative login approach with direct cookie extraction
    """
    status_text = st.empty()
    debug_text = st.empty()
    
    try:
        status_text.info("Attempting direct authentication...")
        
        # Create a session
        session = requests.Session()
        
        # First, get the login page
        login_page_url = "https://app.criticalmention.com/app/"
        login_page_response = session.get(login_page_url)
        debug_text.info(f"Login page status: {login_page_response.status_code}")
        
        # Now send login request
        login_url = "https://app.criticalmention.com/api/v1/auth"
        login_data = json.dumps({"username": username, "password": password})
        
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://app.criticalmention.com/app/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        login_response = session.post(login_url, data=login_data, headers=headers)
        debug_text.info(f"Login status: {login_response.status_code}")
        
        # Try to get the JSON response
        try:
            response_json = login_response.json()
            debug_text.info(f"Response: {response_json}")
        except:
            debug_text.warning("Not JSON response")
        
        # Extract cookies as string
        cookie_dict = requests.utils.dict_from_cookiejar(session.cookies)
        debug_text.info(f"Got {len(cookie_dict)} cookies")
        
        # Form the cookie string
        cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
        
        if cookie_string:
            debug_text.success("Authentication successful")
            return cookie_string
        else:
            debug_text.error("No cookies obtained")
            return None
            
    except Exception as e:
        debug_text.error(f"Error in direct login: {str(e)}")
        return None

def direct_auth_ui(key_suffix=""):
    """
    UI for direct API authentication with CriticalMention
    
    Parameters:
    -----------
    key_suffix : str
        Optional suffix to make keys unique when used multiple times on the same page
    """
    st.markdown("## Direct API Authentication")
    
    # Get credentials from config if available
    config = load_config()
    default_username = ""
    if "criticalmention" in config and "username" in config["criticalmention"]:
        default_username = config["criticalmention"]["username"]
    
    # Get credentials
    username = st.text_input("CriticalMention Username", value=default_username, key=f"api_username_{key_suffix}")
    password = st.text_input("CriticalMention Password", type="password", key=f"api_password_{key_suffix}")
    
    # Add option to try alternative login method
    use_alt_method = st.checkbox("Try alternative login method", key=f"alt_method_{key_suffix}")
    
    if st.button("Login with API", type="primary", key=f"api_login_{key_suffix}"):
        if not username or not password:
            st.error("Please enter both username and password")
            return
        
        with st.spinner("Authenticating with CriticalMention..."):
            # Use the selected login method
            if use_alt_method:
                st.info("Using alternative login method...")
                cookie_string = direct_login_criticalmention(username, password)
            else:
                cookie_string = api_login_criticalmention(username, password)
            
            if cookie_string:
                # Update config
                if "criticalmention" not in config:
                    config["criticalmention"] = {}
                
                # Save username for future use
                config["criticalmention"]["username"] = username
                
                # Save old token for reference if it exists
                if "default_token" in config["criticalmention"]:
                    old_token = config["criticalmention"]["default_token"]
                    if "token_history" not in config["criticalmention"]:
                        config["criticalmention"]["token_history"] = []
                    
                    config["criticalmention"]["token_history"].append({
                        "token": old_token,
                        "replaced_at": datetime.now().isoformat()
                    })
                    
                    # Limit history to last 5 tokens
                    if len(config["criticalmention"]["token_history"]) > 5:
                        config["criticalmention"]["token_history"] = config["criticalmention"]["token_history"][-5:]
                
                # Update token
                config["criticalmention"]["default_token"] = cookie_string
                config["criticalmention"]["last_updated"] = datetime.now().isoformat()
                
                # Save config
                if save_config(config):
                    st.success("✅ Authentication successful! Token updated.")
                    cookie_count = len(cookie_string.split(';'))
                    st.info(f"New token contains approximately {cookie_count} cookies.")
                    st.warning("Reloading page to use the new token...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to save token to config file.")
            else:
                st.error("Authentication failed. Please check your credentials and try again.")
                st.info("Try using the Manual Token Entry method instead if API login continues to fail.")

def manual_token_ui(key_suffix=""):
    """
    UI for manually entering a CriticalMention authentication token
    
    Parameters:
    -----------
    key_suffix : str
        Optional suffix to make keys unique when used multiple times on the same page
    """
    st.markdown("""
    ### Manual Token Entry
    
    Enter a token you've obtained from CriticalMention:
    
    1. **Log in to CriticalMention** in your browser
    2. **Use browser developer tools** to capture the token:
       - Open Chrome or Firefox and go to [CriticalMention](https://app.criticalmention.com/app/#user/login)
       - Log in with your credentials
       - Press F12 to open developer tools
       - Go to the Network tab
       - Reload the page (F5)
       - Click on any request to criticalmention.com 
       - Find the "Cookie" header in the Request Headers section
       - Copy the entire cookie string (right-click → Copy Value)
    
    3. **Paste the token below and click "Update Token"**
    """)
    
    # Add an example tip in a container that works with both light and dark modes
    st.container(border=True).markdown("""
    **Pro Tip:** The Cookie header looks like a long string starting with something like:
    
    `intercom-id-xdecp5g2=af349d30-7a57-4424-9c96-12d4bef7f620; intercom-device-id-xdecp5g2=973b5458-fc8d-4b72-a049-8b749114ef2b; *legacy*auth0...`
    """)
    
    # Cookie input
    cookie_input = st.text_area(
        "Paste the complete cookie string below:", 
        height=150,
        help="Copy the entire cookie header value from the developer tools",
        key=f"cookie_input_{key_suffix}"
    )
    
    if st.button("Update Token", key=f"update_token_{key_suffix}", type="primary"):
        if not cookie_input:
            st.error("Please paste the cookie string before updating.")
        else:
            # Add some basic validation
            if len(cookie_input) < 50 or "=" not in cookie_input or ";" not in cookie_input:
                st.error("This doesn't look like a valid cookie string. Please make sure you copied the entire Cookie header value.")
                return
                
            # Update config
            config = load_config()
            if "criticalmention" not in config:
                config["criticalmention"] = {}
            
            # Save old token for reference if it exists
            if "default_token" in config["criticalmention"]:
                old_token = config["criticalmention"]["default_token"]
                if "token_history" not in config["criticalmention"]:
                    config["criticalmention"]["token_history"] = []
                
                config["criticalmention"]["token_history"].append({
                    "token": old_token,
                    "replaced_at": datetime.now().isoformat()
                })
                
                # Limit history to last 5 tokens
                if len(config["criticalmention"]["token_history"]) > 5:
                    config["criticalmention"]["token_history"] = config["criticalmention"]["token_history"][-5:]
            
            # Update token
            config["criticalmention"]["default_token"] = cookie_input
            config["criticalmention"]["last_updated"] = datetime.now().isoformat()
            
            # Save config
            if save_config(config):
                st.success("✅ Token updated successfully!")
                
                # Show token info
                cookie_count = len(cookie_input.split(';'))
                st.info(f"New token contains approximately {cookie_count} cookies.")
                
                st.warning("Reloading page to use the new token...")
                st.rerun()  # Reload the page to use the new token
            else:
                st.error("Failed to save token to config file.")

def automatic_auth_ui(key_suffix=""):
    """UI for automatic cookie retrieval"""
    st.markdown("## Automatic Cookie Retrieval")
    
    # Display explanation
    st.markdown("""
    This option will attempt to automatically retrieve your CriticalMention authentication
    cookies by simulating the login process.
    """)
    
    # Get credentials from config if available
    config = load_config()
    default_username = ""
    if "criticalmention" in config and "username" in config["criticalmention"]:
        default_username = config["criticalmention"]["username"]
    
    # Get credentials
    username = st.text_input("CriticalMention Username", value=default_username, key=f"auto_username_{key_suffix}")
    password = st.text_input("CriticalMention Password", type="password", key=f"auto_password_{key_suffix}")
    
    auth_method = st.radio(
        "Authentication Method",
        ["Standard", "Alternative", "Selenium (if available)"],
        key=f"auto_method_{key_suffix}"
    )
    
    show_debug = st.checkbox("Show detailed debug output", value=True, key=f"debug_{key_suffix}")
    
    if st.button("Retrieve Cookies Automatically", key=f"auto_retrieve_{key_suffix}", type="primary"):
        if not username or not password:
            st.error("Please enter both username and password")
            return
        
        debug_container = st.empty()
        debug_output = []
        
        # Custom debug output function that displays updates in real-time
        def debug_print(msg):
            debug_output.append(msg)
            if show_debug:
                debug_container.code("\n".join(debug_output))
        
        with st.spinner("Authenticating with CriticalMention..."):
            if auth_method == "Standard":
                cookie_string = get_criticalmention_cookies(username, password, debug_print)
            elif auth_method == "Alternative":
                cookie_string = try_alternative_auth(username, password, debug_print)
            else:  # Selenium
                cookie_string = try_selenium_auth(username, password, debug_print)
            
            if cookie_string:
                # Update config
                if "criticalmention" not in config:
                    config["criticalmention"] = {}
                
                # Save username for future use
                config["criticalmention"]["username"] = username
                
                # Save old token for reference if it exists
                if "default_token" in config["criticalmention"]:
                    old_token = config["criticalmention"]["default_token"]
                    if "token_history" not in config["criticalmention"]:
                        config["criticalmention"]["token_history"] = []
                    
                    config["criticalmention"]["token_history"].append({
                        "token": old_token,
                        "replaced_at": datetime.now().isoformat()
                    })
                    
                    # Limit history to last 5 tokens
                    if len(config["criticalmention"]["token_history"]) > 5:
                        config["criticalmention"]["token_history"] = config["criticalmention"]["token_history"][-5:]
                
                # Update token
                config["criticalmention"]["default_token"] = cookie_string
                config["criticalmention"]["last_updated"] = datetime.now().isoformat()
                
                # Save config
                if save_config(config):
                    st.success("✅ Authentication successful! Token updated.")
                    cookie_count = len(cookie_string.split(';'))
                    st.info(f"New token contains approximately {cookie_count} cookies.")
                    st.warning("Reloading page to use the new token...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to save token to config file.")
            else:
                st.error("Authentication failed. Please check your credentials and try another method.")
                
def token_management_ui(key_suffix=""):
    """
    Enhanced token management UI with automatic, API and manual options
    
    Parameters:
    -----------
    key_suffix : str
        Optional suffix to make keys unique when used multiple times on the same page
    """
    # Radio button to select authentication method
    auth_method = st.radio(
        "Authentication Method", 
        ["Automatic Retrieval", "API Login", "Manual Token Entry"],
        horizontal=True,
        index=0,
        key=f"auth_method_selector_{key_suffix}"
    )
    
    # Display the appropriate UI based on selection
    if auth_method == "Automatic Retrieval":
        automatic_auth_ui(key_suffix)
    elif auth_method == "API Login":
        direct_auth_ui(key_suffix)
    else:
        manual_token_ui(key_suffix)

def get_auth_cookie():
    """Get authentication cookie from config with better error handling"""
    config = load_config()
    if "criticalmention" in config and "default_token" in config["criticalmention"]:
        token = config["criticalmention"]["default_token"]
        if token:
            # Print the first and last 20 characters of the token for debugging
            if len(token) > 40:
                print(f"Token preview: {token[:20]}...{token[-20:]}")
            return token
        else:
            print("Token exists in config but is empty")
            return None
    else:
        print("No criticalmention or default_token found in config")
        return None

def token_info_ui():
    """Display information about the current token"""
    config = load_config()
    if "criticalmention" in config and "default_token" in config["criticalmention"]:
        # Show last updated time
        if "last_updated" in config["criticalmention"]:
            try:
                last_updated = datetime.fromisoformat(config["criticalmention"]["last_updated"])
                st.info(f"Token last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Calculate token age
                age = datetime.now() - last_updated
                if age.days > 0:
                    st.warning(f"Token age: {age.days} days, {age.seconds // 3600} hours")
                else:
                    hours = age.seconds // 3600
                    minutes = (age.seconds % 3600) // 60
                    st.success(f"Token age: {hours} hours, {minutes} minutes")
            except (ValueError, TypeError):
                pass
        
        # Show token size
        token = config["criticalmention"]["default_token"]
        token_size = len(token)
        cookie_count = len(token.split(';'))
        st.info(f"Current token: {token_size} characters, {cookie_count} cookies")

def view_token_history_ui():
    """Display token update history"""
    config = load_config()
    if "criticalmention" in config and "token_history" in config["criticalmention"] and config["criticalmention"]["token_history"]:
        with st.expander("📜 Token Update History"):
            st.markdown("### Previous Token Updates")
            
            for i, entry in enumerate(reversed(config["criticalmention"]["token_history"])):
                try:
                    replaced_at = datetime.fromisoformat(entry["replaced_at"])
                    st.markdown(f"**{i+1}.** Updated on {replaced_at.strftime('%Y-%m-%d')} at {replaced_at.strftime('%H:%M:%S')}")
                except (ValueError, TypeError):
                    st.markdown(f"**{i+1}.** Updated at unknown time")

def login_ui():
    """
    Display the login UI and handle authentication
    
    Returns:
    --------
    bool
        True if authenticated, False otherwise
    """
    # Check if already authenticated
    if st.session_state.is_authenticated:
        return True
    
    # Check if locked out
    if check_lockout():
        lockout_end = st.session_state.lockout_until
        minutes_left = int((lockout_end - datetime.now()).total_seconds() / 60) + 1
        
        # Use Streamlit container instead of custom HTML for dark mode compatibility
        container = st.container(border=True)
        with container:
            st.header("🔒 Access Restricted", anchor=False)
            st.subheader("Account Temporarily Locked", anchor=False)
            
            error_container = st.container(border=True)
            with error_container:
                st.error("Too many failed login attempts")
                st.write(f"Please try again in {minutes_left} minutes.")
            
            st.caption("For assistance, please contact your administrator.")
        
        return False
    
    # Check for expired access code
    if check_expiration():
        # Use Streamlit container instead of custom HTML for dark mode compatibility
        container = st.container(border=True)
        with container:
            st.header("🔒 Access Restricted", anchor=False)
            st.subheader("Access Code Expired", anchor=False)
            
            error_container = st.container(border=True)
            with error_container:
                st.error("Your access code has expired")
                st.write("Please contact your administrator for a new access code.")
            
            st.caption("For assistance, please contact your administrator.")
        
        return False
    
    # Load config for access settings
    config = load_config()
    
    # Use existing premier access settings from config
    if "premier_access" not in config:
        st.error("Premier access configuration not found in config.json")
        return False
    
    # Get max attempts and lockout duration
    max_attempts = config["premier_access"].get("max_attempts", 5)
    lockout_minutes = config["premier_access"].get("lockout_minutes", 15)
    
    # Display login form with nice styling using Streamlit components
    login_container = st.container(border=True)
    with login_container:
        st.header("🔒 Restricted Access", anchor=False)
        st.subheader("Corp Comms Access Only", anchor=False)
    
        # Show attempt counter if there have been attempts
        if st.session_state.auth_attempts > 0:
            attempts_left = max_attempts - st.session_state.auth_attempts
            st.warning(f"⚠️ {attempts_left} login attempts remaining")
        
        # Login form
        with st.form("login_form"):
            access_code = st.text_input("Enter Access Code", type="password")
            submitted = st.form_submit_button("Access Dashboard")
            
            if submitted:
                if validate_access_code(access_code):
                    st.session_state.is_authenticated = True
                    st.session_state.auth_attempts = 0
                    st.success("✅ Access granted! Redirecting to dashboard...")
                    st.rerun()
                    return True
                else:
                    # Increment attempt counter
                    st.session_state.auth_attempts += 1
                    
                    # Check if max attempts reached
                    if st.session_state.auth_attempts >= max_attempts:
                        # Set lockout until time
                        st.session_state.lockout_until = datetime.now() + timedelta(minutes=lockout_minutes)
                        st.error(f"🔒 Too many failed attempts. Your access has been locked for {lockout_minutes} minutes.")
                    else:
                        st.error("❌ Invalid access code. Please try again.")
        
        st.caption("This is a restricted service. Unauthorized access is prohibited. For assistance, please contact your administrator.")
    
    return False

def admin_settings_ui():
    """
    Admin settings UI for viewing access code settings (simplified version)
    """
    with st.expander("🔐 Access Settings", expanded=False):
        st.markdown("### Premier Access Information")
        
        # Get current config
        config = load_config()
        
        # Check for premier_access configuration
        if "premier_access" not in config:
            st.error("Premier access configuration not found in config.json")
            if st.button("Create Premier Access Configuration"):
                config["premier_access"] = {
                    "access_code": "CommComm",
                    "code_hash": hashlib.sha256("CommComm".encode()).hexdigest(),
                    "max_attempts": 5,
                    "lockout_minutes": 15,
                    "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
                if save_config(config):
                    st.success("Created default premier access configuration")
                    st.rerun()
                else:
                    st.error("Failed to create configuration")
            return
        
        # Show current settings
        if "last_updated" in config["premier_access"]:
            try:
                last_updated = datetime.fromisoformat(config["premier_access"]["last_updated"])
                st.info(f"Access code last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, TypeError):
                pass
        
        # Show expiration date
        if "expiration_date" in config["premier_access"]:
            try:
                expiration = datetime.fromisoformat(config["premier_access"]["expiration_date"])
                days_left = (expiration - datetime.now()).days
                
                if days_left > 30:
                    st.success(f"Access code valid until: {expiration.strftime('%Y-%m-%d')} ({days_left} days left)")
                elif days_left > 0:
                    st.warning(f"Access code expires soon: {expiration.strftime('%Y-%m-%d')} ({days_left} days left)")
                else:
                    st.error(f"Access code expired on: {expiration.strftime('%Y-%m-%d')}")
            except (ValueError, TypeError):
                pass
            
        # Show security settings
        st.markdown("### Security Settings")
        st.info(f"Maximum login attempts: {config['premier_access'].get('max_attempts', 5)}")
        st.info(f"Lockout duration: {config['premier_access'].get('lockout_minutes', 15)} minutes")