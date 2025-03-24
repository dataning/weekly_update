"""
CriticalMention Cookie Retriever
--------------------------------
This module provides functions to automate the retrieval of authentication cookies
from CriticalMention using various methods.
"""

import requests
import json
import time
import re
from urllib.parse import urlparse
import streamlit as st

def get_criticalmention_cookies(username, password, debug_output=None):
    """
    Automates the login process to CriticalMention and retrieves authentication cookies
    
    Parameters:
    -----------
    username : str
        CriticalMention username
    password : str
        CriticalMention password
    debug_output : function or None
        Function to handle debug output (default: print)
    
    Returns:
    --------
    str
        Cookie string if successful, None if failed
    """
    # Use the provided debug function or create a simple one
    debug = debug_output if debug_output else print
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # User agent to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Progress tracking
    debug("Step 1: Accessing CriticalMention login page...")
    
    # First, get the main login page
    login_page_url = "https://app.criticalmention.com/app/#user/login"
    login_page_response = session.get(login_page_url, headers=headers)
    
    if login_page_response.status_code != 200:
        debug(f"Failed to access login page: {login_page_response.status_code}")
        return None
    
    # Look for authentication endpoints
    debug("Step 2: Extracting authentication parameters...")
    
    # Try to find the auth API endpoint
    auth_endpoint = "https://app.criticalmention.com/api/v1/auth"
    
    # Try direct authentication
    debug("Step 3: Attempting direct API authentication...")
    
    auth_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://app.criticalmention.com",
        "Connection": "keep-alive",
        "Referer": "https://app.criticalmention.com/app/"
    }
    
    auth_data = {
        "username": username,
        "password": password
    }
    
    auth_response = session.post(auth_endpoint, json=auth_data, headers=auth_headers)
    
    # Check if the authentication was successful
    if auth_response.status_code != 200:
        debug(f"Direct API authentication failed: {auth_response.status_code}")
        debug(f"Response: {auth_response.text}")
        return None
    
    # Try to parse the JSON response
    try:
        auth_result = auth_response.json()
        debug(f"Authentication response: {auth_result}")
        
        # Check for errors in the response
        if "error" in auth_result or ("success" in auth_result and not auth_result["success"]):
            debug("Authentication rejected by server")
            return None
            
    except Exception as e:
        debug(f"Error parsing authentication response: {str(e)}")
        debug(f"Response content: {auth_response.text[:200]}...")
    
    # Step 4: Access a protected page to ensure we're fully authenticated
    debug("Step 4: Verifying authentication and retrieving final cookies...")
    
    # Wait briefly to allow any session initialization
    time.sleep(1)
    
    # Try to access user profile or dashboard
    verification_urls = [
        "https://app.criticalmention.com/api/v1/user/profile",
        "https://app.criticalmention.com/api/v1/dashboard"
    ]
    
    for verify_url in verification_urls:
        verify_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Referer": "https://app.criticalmention.com/app/"
        }
        
        verify_response = session.get(verify_url, headers=verify_headers)
        
        if verify_response.status_code == 200:
            debug(f"Successfully verified authentication using {verify_url}")
            break
        else:
            debug(f"Failed to verify with {verify_url}: {verify_response.status_code}")
    
    # Extract all cookies from the session
    debug("Step 5: Extracting cookies...")
    
    # Debug cookie information
    for cookie in session.cookies:
        debug(f"Cookie: {cookie.name}={cookie.value[:10]}...")
    
    # Convert cookies to string format
    cookie_string = "; ".join([f"{name}={value}" for name, value in session.cookies.items()])
    
    if not cookie_string:
        debug("No cookies obtained!")
        return None
    
    # Look specifically for the Authorization cookie
    has_auth = any(cookie.name == "Authorization" for cookie in session.cookies)
    if not has_auth:
        debug("Warning: No Authorization cookie found!")
    
    debug(f"Successfully extracted {len(session.cookies)} cookies")
    
    return cookie_string

def try_alternative_auth(username, password, debug_output=None):
    """
    Alternative authentication method using requests with a more complex approach
    
    Parameters:
    -----------
    username : str
        CriticalMention username
    password : str
        CriticalMention password
    debug_output : function or None
        Function to handle debug output
        
    Returns:
    --------
    str
        Cookie string if successful, None if failed
    """
    debug = debug_output if debug_output else print
    debug("Starting alternative authentication method...")
    
    # Create a session
    session = requests.Session()
    
    try:
        # First load the main page to get initial cookies
        debug("Step 1: Loading main page...")
        main_page_url = "https://app.criticalmention.com/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        main_response = session.get(main_page_url, headers=headers)
        if main_response.status_code != 200:
            debug(f"Failed to load main page: {main_response.status_code}")
            return None
            
        debug(f"Initial cookies: {len(session.cookies)}")
        
        # Now load the login page
        debug("Step 2: Loading login page...")
        login_page_url = "https://app.criticalmention.com/app/#user/login"
        login_response = session.get(login_page_url, headers=headers)
        
        if login_response.status_code != 200:
            debug(f"Failed to load login page: {login_response.status_code}")
            return None
            
        # Try to find auth endpoint in the page
        auth_url = "https://app.criticalmention.com/api/v1/auth"
        
        # Perform login
        debug("Step 3: Sending login request...")
        login_data = json.dumps({"username": username, "password": password})
        login_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": "https://app.criticalmention.com",
            "Referer": "https://app.criticalmention.com/app/"
        }
        
        auth_response = session.post(auth_url, data=login_data, headers=login_headers)
        
        if auth_response.status_code != 200:
            debug(f"Login failed: {auth_response.status_code}")
            return None
        
        # Get cookies after login
        debug(f"Cookies after login: {len(session.cookies)}")
        
        # Now try to access the dashboard or profile to ensure we're logged in
        debug("Step 4: Accessing protected page...")
        dashboard_url = "https://app.criticalmention.com/api/v1/user/profile"
        dashboard_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://app.criticalmention.com/app/"
        }
        
        dashboard_response = session.get(dashboard_url, headers=dashboard_headers)
        
        if dashboard_response.status_code != 200:
            debug(f"Failed to access protected page: {dashboard_response.status_code}")
            return None
            
        # Extract cookies as string
        cookie_string = "; ".join([f"{name}={value}" for name, value in session.cookies.items()])
        
        if cookie_string:
            debug("Successfully obtained cookies.")
            return cookie_string
        else:
            debug("No cookies obtained.")
            return None
        
    except Exception as e:
        debug(f"Error during authentication: {str(e)}")
        return None

def try_selenium_auth(username, password, debug_output=None):
    """
    Try to authenticate using Selenium (requires selenium package and webdriver)
    
    Note: This function requires additional setup, so it's optional.
    """
    debug = debug_output if debug_output else print
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        debug("Starting Selenium-based authentication...")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Create a new Chrome browser instance
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to the login page
            driver.get("https://app.criticalmention.com/app/#user/login")
            
            # Wait for the page to load and find the login form
            wait = WebDriverWait(driver, 10)
            
            # Find and fill the username field
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.send_keys(username)
            
            # Find and fill the password field
            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            
            # Find and click the login button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for authentication to complete
            wait.until(EC.url_contains("dashboard"))
            
            debug("Login successful!")
            
            # Extract all cookies
            cookies = driver.get_cookies()
            cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            debug(f"Extracted {len(cookies)} cookies")
            
            return cookie_string
            
        finally:
            # Always close the browser
            driver.quit()
            
    except ImportError:
        debug("Selenium not available. Cannot use selenium authentication method.")
        return None
    except Exception as e:
        debug(f"Error in Selenium authentication: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="CriticalMention Cookie Retriever")
    parser.add_argument("username", help="CriticalMention username")
    parser.add_argument("password", help="CriticalMention password")
    parser.add_argument("--method", choices=["standard", "alternative", "selenium"], 
                        default="standard", help="Authentication method to use")
    args = parser.parse_args()
    
    if args.method == "standard":
        cookie_string = get_criticalmention_cookies(args.username, args.password)
    elif args.method == "alternative":
        cookie_string = try_alternative_auth(args.username, args.password)
    else:  # selenium
        cookie_string = try_selenium_auth(args.username, args.password)
    
    if cookie_string:
        print("\nSuccessfully obtained cookies:")
        print(cookie_string)
    else:
        print("\nFailed to retrieve cookies!")