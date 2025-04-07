"""
Access Control Module
-----------------------------------
Authenticates users via passcode from existing config.json
"""

import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta

# Constants
CONFIG_FILE = "config.json"

def initialize_session_state():
    """Initialize session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "lockout_until" not in st.session_state:
        st.session_state.lockout_until = None
    if "config" not in st.session_state:
        st.session_state.config = load_config()

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
    config = st.session_state.config
    
    # Check if premier_access configuration exists
    if "premier_access" not in config:
        st.error("Access configuration not found in config.json")
        return False
    
    # Check if factiva_access_code is also valid (as an alternative)
    if "dow_jones" in config and "factiva_access_code" in config["dow_jones"]:
        if input_code == config["dow_jones"]["factiva_access_code"]:
            return True
    
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
        st.session_state.login_attempts = 0
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
    config = st.session_state.config
    
    if "premier_access" not in config or "expiration_date" not in config["premier_access"]:
        return False
    
    try:
        expiration = datetime.fromisoformat(config["premier_access"]["expiration_date"])
        if datetime.now() > expiration:
            return True
    except (ValueError, TypeError):
        pass
    
    return False

def login_ui():
    """
    Display the passcode login UI and handle authentication
    
    Returns:
    --------
    bool
        True if authenticated, False otherwise
    """
    # Check if already authenticated
    if st.session_state.authenticated:
        return True
    
    # Check if locked out
    if check_lockout():
        lockout_end = st.session_state.lockout_until
        minutes_left = int((lockout_end - datetime.now()).total_seconds() / 60) + 1
        
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
    
    # Get config for access settings
    config = st.session_state.config
    
    # Ensure premier_access section exists
    if "premier_access" not in config:
        # Create basic premier_access section
        config["premier_access"] = {
            "access_code": "CommComm",
            "max_attempts": 5,
            "lockout_minutes": 15,
            "expiration_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
        save_config(config)
    
    # Get max attempts and lockout duration
    max_attempts = config["premier_access"].get("max_attempts", 5)
    lockout_minutes = config["premier_access"].get("lockout_minutes", 15)
    
    # Display login form
    login_container = st.container(border=True)
    with login_container:
        st.header("🔒 Restricted Access", anchor=False)
        st.subheader("Corp Comms Access Only", anchor=False)
    
        # Show attempt counter if there have been attempts
        if st.session_state.login_attempts > 0:
            attempts_left = max_attempts - st.session_state.login_attempts
            st.warning(f"⚠️ {attempts_left} login attempts remaining")
        
        # Login form
        with st.form("login_form"):
            access_code = st.text_input("Enter Access Code", type="password")
            submitted = st.form_submit_button("Access Dashboard")
            
            if submitted:
                if validate_access_code(access_code):
                    st.session_state.authenticated = True
                    st.session_state.login_attempts = 0
                    st.success("✅ Access granted! Redirecting to dashboard...")
                    st.rerun()
                    return True
                else:
                    # Increment attempt counter
                    st.session_state.login_attempts += 1
                    
                    # Check if max attempts reached
                    if st.session_state.login_attempts >= max_attempts:
                        # Set lockout until time
                        st.session_state.lockout_until = datetime.now() + timedelta(minutes=lockout_minutes)
                        st.error(f"🔒 Too many failed attempts. Your access has been locked for {lockout_minutes} minutes.")
                    else:
                        st.error("❌ Invalid access code. Please try again.")
        
        st.caption("This is a restricted service. Unauthorized access is prohibited.")
    
    return False

def admin_settings_ui():
    """
    Admin settings UI for viewing access code settings
    """
    if not st.session_state.authenticated:
        return
    
    with st.expander("🔐 Access Settings", expanded=False):
        st.markdown("### Access Code Information")
        
        # Get current config
        config = st.session_state.config
        
        # Check for premier_access configuration
        if "premier_access" not in config:
            st.error("Access configuration not found in config.json")
            return
        
        # Show last updated time
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
        
        # Logout button
        if st.button("Logout"):
            logout()
            st.rerun()

def logout():
    """Log out the current user."""
    st.session_state.authenticated = False

def load_config():
    """Load configuration from config file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as config_file:
                return json.load(config_file)
        else:
            st.error(f"Config file not found: {CONFIG_FILE}")
            # Create a basic config with premier_access section
            default_config = {
                "premier_access": {
                    "access_code": "CommComm",
                    "max_attempts": 5,
                    "lockout_minutes": 15,
                    "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }
            with open(CONFIG_FILE, "w") as config_file:
                json.dump(default_config, config_file, indent=4)
            return default_config
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return {}

def save_config(config):
    """Save configuration to the config file."""
    try:
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file, indent=4)
        st.session_state.config = config
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

# Stub functions to maintain API compatibility with the previous version
def get_criticalmention_cookies(username, password, debug_output=None):
    """Stub function that returns None but maintains API compatibility"""
    debug = debug_output if debug_output else print
    debug("CriticalMention cookie retrieval not implemented")
    return None

def try_alternative_auth(username, password, debug_output=None):
    """Stub function that returns None but maintains API compatibility"""
    debug = debug_output if debug_output else print
    debug("Alternative authentication not implemented")
    return None

def try_selenium_auth(username, password, debug_output=None):
    """Stub function that returns None but maintains API compatibility"""
    debug = debug_output if debug_output else print
    debug("Selenium authentication not implemented")
    return None