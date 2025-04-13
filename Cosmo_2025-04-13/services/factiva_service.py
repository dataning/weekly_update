"""
Dow Jones API Module
-------------------
This module contains functions for interacting with the Dow Jones API
and managing authentication tokens.
"""

import requests
import json
import pandas as pd
import base64
import os
import pickle
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

# Load configuration from config.json
def load_config():
    """
    Load configuration from config.json file
    
    Returns:
    --------
    dict
        Configuration dictionary or empty dict if file doesn't exist
    """
    import os
    
    try:
        # Try using __file__ if we're in a script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(script_dir), "config.json")
    except NameError:
        # If __file__ is not available (interactive environment), try current directory
        current_dir = os.getcwd()
        config_path = os.path.join(current_dir, "config.json")
        
        # If not found, try parent directory
        if not os.path.exists(config_path):
            parent_dir = os.path.dirname(current_dir)
            config_path = os.path.join(parent_dir, "config.json")
    
    if not os.path.exists(config_path):
        print(f"Warning: config.json not found at {config_path}. API functionality may be limited.")
        return {}
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        print(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}

def get_token_path():
    import os
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(os.path.dirname(script_dir), "dow_jones_token.pkl")
    except NameError:
        current_dir = os.getcwd()
        token_path = os.path.join(current_dir, "dow_jones_token.pkl")
        
        if not os.path.exists(token_path):
            parent_dir = os.path.dirname(current_dir)
            token_path = os.path.join(parent_dir, "dow_jones_token.pkl")
        
        return token_path

# Load configuration
CONFIG = load_config()

# Constants
TOKEN_FILE = get_token_path()

DEFAULT_TOKEN = CONFIG.get("dow_jones", {}).get("default_token", "YOUR_DEFAULT_TOKEN_HERE")

# Company code mapping
COMPANY_CODES = {
    # Asset Management
    "BlackRock": "BLAMAN",
    "Vanguard": "VNGD",
    "State Street": "SSBT",
    
    # Technology
    "Palantir": "PTLZAT",
    
    # Crypto/Fintech
    "Coinbase": "CNYC",
    
    # Add other companies as needed
}

# Token Management Functions
def save_token(token_data):
    """
    Save token data to a local file
    
    Parameters:
    -----------
    token_data : dict
        Dictionary containing 'token' and 'expires_at' fields
    """
    try:
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(token_data, f)
        print(f"Token saved successfully to {TOKEN_FILE}")
        return True
    except Exception as e:
        print(f"Error saving token: {e}")
        return False

def load_token():
    """
    Load token data from local file
    
    Returns:
    --------
    dict
        Dictionary containing token information or None if file doesn't exist
    """
    if not os.path.exists(TOKEN_FILE):
        print(f"Token file not found. Using default token.")
        # Create a basic token object with the default token
        token_data = {
            'token': DEFAULT_TOKEN,
            'expires_at': datetime.now() + timedelta(days=30)  # Assume valid for 30 days
        }
        save_token(token_data)
        return token_data
        
    try:
        with open(TOKEN_FILE, 'rb') as f:
            token_data = pickle.load(f)
        print(f"Token loaded from {TOKEN_FILE}")
        return token_data
    except Exception as e:
        print(f"Error loading token: {e}")
        return None

def extend_token_expiry(days=14):
    """
    Extend the current token's expiry date by the specified number of days
    
    Parameters:
    -----------
    days : int, optional
        Number of days to extend token validity (default: 14)
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        # Load current token
        token_data = load_token()
        if not token_data:
            print("No token data to extend")
            return False
            
        # Get current expiry
        current_expires_at = token_data.get('expires_at')
        if not current_expires_at:
            print("Token data doesn't have an expiry date")
            return False
            
        # Calculate new expiry
        new_expires_at = current_expires_at + timedelta(days=days)
        
        # Log before and after
        print(f"Current expiry: {current_expires_at}")
        print(f"New expiry:     {new_expires_at}")
        
        # Create a new token data dictionary to ensure it's not just a reference
        new_token_data = {
            'token': token_data.get('token'),
            'expires_at': new_expires_at,
            'email': token_data.get('email'),
            'issued_at': token_data.get('issued_at', datetime.now())
        }
        
        # Save updated token data
        success = save_token(new_token_data)
        
        # Verify the change
        if success:
            # Reload the token to make sure it was saved
            reloaded_token = load_token()
            if reloaded_token and reloaded_token.get('expires_at'):
                print(f"Verified new expiry: {reloaded_token['expires_at']}")
                return True
            else:
                print("Failed to reload token after save")
        
        return success
    except Exception as e:
        print(f"Error extending token expiry: {e}")
        return False

def get_valid_token():
    """
    Get a valid token - either from storage or by updating if expired
    
    Returns:
    --------
    str
        A valid authentication token
    """
    token_data = load_token()
    
    if not token_data:
        # If we couldn't load a token, use the default
        return DEFAULT_TOKEN
    
    # Check if token is expired
    now = datetime.now()
    if now >= token_data.get('expires_at', now):
        # Token is expired, try to update it automatically
        if auto_refresh_token():
            print("Token automatically refreshed!")
            # Load the newly refreshed token
            token_data = load_token()
            
            # Double-check that the token is now valid
            token_info = get_dow_jones_token_info(token_data.get('token'))
            if token_info.get('status') != 'Valid':
                print("WARNING: Token is still expired after refresh!")
                # Try using the token from cURL logs
                try:
                    direct_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJEN0IwQTFERkJCNzlDRDFBQjM4NzNCMTcyODMyRjkxMENEQkRBREIiLCJ0eXAiOiJKV1QifQ.eyJwaWIiOnsiYWNjb3VudF9pZCI6IjlCTEEwMDQ2MDAiLCJhbGxvd19hdXRvX2xvZ2luIjoidHJ1ZSIsImFwYyI6IkZIIiwiY3RjIjoiRCIsIm1hc3Rlcl9hcHBfaWQiOiJaY01JZGlaajNmWDhtOU5JMWY4dGMxbDNDc0pFRGdjayIsInNlc3Npb25faWQiOiJwYnZpNFd3V19NRlJES09CWE1VMkRRWkJXSEU0VElNREdHSTRXQ01ERU1RWVRHWlJWTUpURE1NREZHTlNBIiwiZW1haWwiOiJKb2FubmEuWWF1QGJsYWNrcm9jay5jb20iLCJlaWQiOiJFNk9PMkhWQ1FIVlBFSExRMjdUNkJQTFNRQSJ9LCJpc3MiOiJodHRwczovL2FjY291bnRzLmRvd2pvbmVzLmNvbS9vYXV0aDIvdjIiLCJlbWFpbCI6IkpvYW5uYS5ZYXVAYmxhY2tyb2NrLmNvbSIsInN1YiI6ImIzMmMwMGIyLTI3Y2YtNGRkYi1hOGIyLTIxZDUzNDEwMGJjYyIsImF1ZCI6IlpjTUlkaVpqM2ZYOG05TkkxZjh0YzFsM0NzSkVEZ2NrIiwiYXpwIjoiWmNNSWRpWmozZlg4bTlOSTFmOHRjMWwzQ3NKRURnY2siLCJpYXQiOjE3NDQ1NTI4OTksImV4cCI6MTc0NDgxMjA5OX0.d4VJ7VKUmJ_MuNbbNFD9zdCf3zwl7mSTuyGoaXlziozA4sD9UrxRufNEEmAEquWpiuP6aWewLBcGx_BU9VZ-eGTzNlC3DaaAs7ESDdqoFQb1TNdLK0zZiJ5ID8Qxu525iA4rsDdbT6SQtI9PBrLpLBvE8tWl3Tk8BS4gwBuPaA4ka5uLiM95MFF7Uk6oTQ-j_nHCYxSPh4WlWYVLF6UpSQOhe_oM0xobx45nqy4AR-HHuKFnlM6wgLILzQEYFKsXpyMBCfsj_ViQKkFxjW9QRF37IFyru0TXayXgriRtasxg_CJk8oHf24fsLRCsfvzvON2odky_spW4K3PHYxRPMw"
                    # Check if this hardcoded token is valid
                    direct_token_info = get_dow_jones_token_info(direct_token)
                    if direct_token_info.get('status') == 'Valid':
                        return direct_token
                except:
                    pass
            
            return token_data.get('token', DEFAULT_TOKEN)
        else:
            print("Auto-refresh failed. Please update token manually through the app.")
            
            # As a last resort, try to use the token from your cURL logs
            try:
                direct_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJEN0IwQTFERkJCNzlDRDFBQjM4NzNCMTcyODMyRjkxMENEQkRBREIiLCJ0eXAiOiJKV1QifQ.eyJwaWIiOnsiYWNjb3VudF9pZCI6IjlCTEEwMDQ2MDAiLCJhbGxvd19hdXRvX2xvZ2luIjoidHJ1ZSIsImFwYyI6IkZIIiwiY3RjIjoiRCIsIm1hc3Rlcl9hcHBfaWQiOiJaY01JZGlaajNmWDhtOU5JMWY4dGMxbDNDc0pFRGdjayIsInNlc3Npb25faWQiOiJwYnZpNFd3V19NRlJES09CWE1VMkRRWkJXSEU0VElNREdHSTRXQ01ERU1RWVRHWlJWTUpURE1NREZHTlNBIiwiZW1haWwiOiJKb2FubmEuWWF1QGJsYWNrcm9jay5jb20iLCJlaWQiOiJFNk9PMkhWQ1FIVlBFSExRMjdUNkJQTFNRQSJ9LCJpc3MiOiJodHRwczovL2FjY291bnRzLmRvd2pvbmVzLmNvbS9vYXV0aDIvdjIiLCJlbWFpbCI6IkpvYW5uYS5ZYXVAYmxhY2tyb2NrLmNvbSIsInN1YiI6ImIzMmMwMGIyLTI3Y2YtNGRkYi1hOGIyLTIxZDUzNDEwMGJjYyIsImF1ZCI6IlpjTUlkaVpqM2ZYOG05TkkxZjh0YzFsM0NzSkVEZ2NrIiwiYXpwIjoiWmNNSWRpWmozZlg4bTlOSTFmOHRjMWwzQ3NKRURnY2siLCJpYXQiOjE3NDQ1NTI4OTksImV4cCI6MTc0NDgxMjA5OX0.d4VJ7VKUmJ_MuNbbNFD9zdCf3zwl7mSTuyGoaXlziozA4sD9UrxRufNEEmAEquWpiuP6aWewLBcGx_BU9VZ-eGTzNlC3DaaAs7ESDdqoFQb1TNdLK0zZiJ5ID8Qxu525iA4rsDdbT6SQtI9PBrLpLBvE8tWl3Tk8BS4gwBuPaA4ka5uLiM95MFF7Uk6oTQ-j_nHCYxSPh4WlWYVLF6UpSQOhe_oM0xobx45nqy4AR-HHuKFnlM6wgLILzQEYFKsXpyMBCfsj_ViQKkFxjW9QRF37IFyru0TXayXgriRtasxg_CJk8oHf24fsLRCsfvzvON2odky_spW4K3PHYxRPMw"
                # Check if this hardcoded token is valid
                direct_token_info = get_dow_jones_token_info(direct_token)
                if direct_token_info.get('status') == 'Valid':
                    return direct_token
            except:
                pass
            
            return token_data.get('token', DEFAULT_TOKEN)
    
    # Token is valid
    return token_data.get('token', DEFAULT_TOKEN)

def get_credentials():
    """
    Get Dow Jones API credentials from config.json
    
    Returns:
    --------
    tuple
        (username, password)
    """
    # Get credentials from config.json
    dow_jones_config = CONFIG.get("dow_jones", {})
    username = dow_jones_config.get("username")
    password = dow_jones_config.get("password")
    
    # If credentials are not available in config.json, use hardcoded ones (temporary!)
    if not username or not password:
        print("Warning: Credentials not found in config.json")
        print("Using fallback hardcoded credentials - SECURITY RISK")
        username = "username@example.com"  # Replace with your username
        password = "password123"  # Replace with your password
    
    return username, password

def get_dow_jones_token_info(auth_token=None):
    """
    Extract and display information about the Dow Jones authentication token
    
    Parameters:
    -----------
    auth_token : str, optional
        The JWT token to analyze. If None, uses the stored token.
        
    Returns:
    --------
    dict
        Information about the token including expiration
    """
    if auth_token is None:
        auth_token = get_valid_token()
        
    try:
        # Split the token into its parts
        parts = auth_token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        # Decode the payload (middle part)
        # Add padding if needed
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
        
        # Decode from base64
        decoded_bytes = base64.b64decode(payload)
        decoded_payload = json.loads(decoded_bytes)
        
        # Extract expiration time
        if 'exp' in decoded_payload:
            exp_timestamp = decoded_payload['exp']
            exp_date = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            
            # Check if token is expired
            is_expired = now > exp_date
            
            # Calculate time remaining or time since expiration
            if is_expired:
                time_diff = now - exp_date
                time_status = f"Expired {time_diff.days} days, {time_diff.seconds // 3600} hours ago"
            else:
                time_diff = exp_date - now
                time_status = f"Expires in {time_diff.days} days, {time_diff.seconds // 3600} hours"
            
            return {
                "email": decoded_payload.get('email', 'Not found'),
                "issued_at": datetime.fromtimestamp(decoded_payload.get('iat', 0)),
                "expires_at": exp_date,
                "status": "Expired" if is_expired else "Valid",
                "time_status": time_status
            }
        else:
            return {"error": "No expiration found in token"}
            
    except Exception as e:
        return {"error": f"Error analyzing token: {str(e)}"}

def update_token(new_token):
    """
    Update the stored token with a new one
    
    Parameters:
    -----------
    new_token : str
        The new token to store
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    # Validate the token first
    token_info = get_dow_jones_token_info(new_token)
    
    if token_info.get('status') != 'Valid':
        print(f"Cannot update token: {token_info.get('error', 'Invalid token')}")
        return False
    
    # Create token data and save it
    token_data = {
        'token': new_token,
        'expires_at': token_info.get('expires_at'),
        'email': token_info.get('email'),
        'issued_at': token_info.get('issued_at')
    }
    
    return save_token(token_data)

def check_token_validity(auth_token=None):
    """
    Check if the authentication token is valid by making a small test request
    
    Parameters:
    -----------
    auth_token : str, optional
        The authentication token to check. If None, uses the stored token.
        
    Returns:
    --------
    bool
        True if token is valid, False otherwise
    """
    if auth_token is None:
        auth_token = get_valid_token()
    
    # URL - same as main API
    url = "https://api.dowjones.com/content/search"
    
    # Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/vnd.dowjones.dna.content.v_1.0",
        "Accept-Language": "en",
        "Content-Type": "application/json",
        "authorization": f"Bearer {auth_token}",
        "Origin": "https://dj.factiva.com",
        "Referer": "https://dj.factiva.com/",
    }
    
    # Use a payload with a proper positive search term to avoid errors
    payload = {"data": {
        "attributes": {
            "page_limit": 1,
            "page_offset": 0,
            "query": {
                "content_collection": ["Publications"],
                "search_string": [
                    {
                        "mode": "Unified",
                        "value": "BlackRock"  # A positive search term
                    }
                ],
                "date": {
                    "days_range": "LastDay"
                }
            }
        },
        "id": "Search",
        "type": "content"
    }}
    
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("Authentication token has expired or is invalid.")
            print(f"Error details: {response.text}")
            return False
        else:
            print(f"Error checking token: Status code {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"Error checking token: {e}")
        return False

def auto_refresh_token():
    """
    Automatically refresh the Dow Jones API token using Auth0 authentication
    
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        print("Attempting to automatically refresh token via Auth0...")
        
        # Create a session to maintain cookies
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5"
        })
        
        # Handle proxy configuration
        proxy_config = CONFIG.get('proxy', {})
        if proxy_config.get('use_proxy', False) and proxy_config.get('proxy_url'):
            session.proxies = {
                'http': proxy_config.get('proxy_url'),
                'https': proxy_config.get('proxy_url')
            }
            print(f"Using proxy: {proxy_config.get('proxy_url')}")
        
        # Step 1: Access the login page to get CSRF token
        auth0_login_url = "https://auth.accounts.dowjones.com/login-page"
        login_params = {
            "client_id": "zgQkNiR9DBqamZBqIi6D0NaIvzLKkh3q",
            "scope": "openid pib email",
            "response_type": "code",
            "redirect_uri": "https://global.factiva.com/factivalogin/callback.aspx",
            "connection": "DJPIB",
            "protocol": "oauth2"
        }
        
        login_page_response = session.get(auth0_login_url, params=login_params)
        print(f"Login page accessed. Status: {login_page_response.status_code}")
        print(f"Cookies received: {session.cookies.get_dict()}")
        
        # Step 2: Extract CSRF token and state parameter
        csrf_token = session.cookies.get('csrf')
        if not csrf_token:
            print("No CSRF token found in cookies")
            return False
        
        print(f"CSRF token found: {csrf_token[:10]}...")
        
        state_param = None
        if "state=" in login_page_response.url:
            state_param = login_page_response.url.split("state=")[1].split("&")[0]
        
        # Step 3: Submit login credentials
        username, password = get_credentials()
        auth0_submit_url = "https://auth.accounts.dowjones.com/usernamepassword/login"
        
        login_data = {
            "client_id": "zgQkNiR9DBqamZBqIi6D0NaIvzLKkh3q",
            "redirect_uri": "https://global.factiva.com/factivalogin/callback.aspx",
            "tenant": "dowjones",
            "response_type": "code",
            "scope": "openid pib email",
            "username": username,
            "password": password,
            "_csrf": csrf_token,
            "connection": "DJPIB",
            "state": state_param
        }
        
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://auth.accounts.dowjones.com",
            "Referer": login_page_response.url
        }
        
        print("Submitting login credentials...")
        login_response = session.post(
            auth0_submit_url,
            data=login_data,
            headers=login_headers,
            allow_redirects=False
        )
        
        # Step 4: Handle the Auth0 form response and follow redirects manually
        if login_response.status_code == 200:
            soup = BeautifulSoup(login_response.text, 'html.parser')
            auth0_form = soup.find('form', {'name': 'hiddenform'})
            
            if auth0_form:
                form_action_url = auth0_form.get('action')
                form_data = {}
                for input_field in auth0_form.find_all('input'):
                    field_name = input_field.get('name')
                    field_value = input_field.get('value', '')
                    if field_name:
                        form_data[field_name] = field_value
                
                print(f"Submitting form to {form_action_url}...")
                form_response = session.post(
                    form_action_url,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    allow_redirects=True
                )
                
                # Step 5: Now access the Factiva main page to get the actual token
                factiva_url = "https://snapshot.factiva.com/du/Index?sa_from=GL"
                print(f"Accessing Factiva main page to get token...")
                factiva_response = session.get(factiva_url, allow_redirects=True)
                
                # Step 6: After login, access a protected endpoint to ensure all cookies are set
                search_url = "https://snapshot.factiva.com/Search/SSResults"
                search_data = {
                    "xsrftoken": session.cookies.get('xsrftoken', ''),
                    "searchModel": json.dumps({
                        "searchFilter": {
                            "dt": "LastDay"
                        }
                    })
                }
                
                search_headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://snapshot.factiva.com/Pages/Index"
                }
                
                print("Accessing search page to finalize authentication...")
                search_response = session.post(
                    search_url,
                    data=search_data,
                    headers=search_headers
                )
                
                # Step 7: Look for the token in cookies, especially the GSLogin cookie
                gslogin_cookie = session.cookies.get('GSLogin')
                if gslogin_cookie and "GL%5FI=" in gslogin_cookie:
                    # Extract the JWT token part from the cookie
                    token_parts = gslogin_cookie.split("GL%5FI=")[1].split("&")[0]
                    
                    # URL-decode the token
                    import urllib.parse
                    jwt_token = urllib.parse.unquote(token_parts)
                    
                    print(f"Found JWT token in GSLogin cookie!")
                    
                    # Validate and save the token
                    token_info = get_dow_jones_token_info(jwt_token)
                    if token_info.get('status') == 'Valid':
                        token_data = {
                            'token': jwt_token,
                            'expires_at': token_info.get('expires_at'),
                            'email': token_info.get('email'),
                            'issued_at': token_info.get('issued_at', datetime.now())
                        }
                        
                        if save_token(token_data):
                            print("Token successfully saved!")
                            return True
                    else:
                        print(f"Token validation failed: {token_info}")
                
                # Alternative: Look for authorization header in requests
                for response in [factiva_response, search_response]:
                    # Check if we received any token in response headers or embedded in the HTML
                    jwt_pattern = r'Bearer\s+(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)'
                    if response.text:
                        jwt_matches = re.findall(jwt_pattern, response.text)
                        if jwt_matches:
                            jwt_token = jwt_matches[0]
                            print(f"Found JWT token in response body!")
                            
                            # Validate and save the token
                            token_info = get_dow_jones_token_info(jwt_token)
                            if token_info.get('status') == 'Valid':
                                token_data = {
                                    'token': jwt_token,
                                    'expires_at': token_info.get('expires_at'),
                                    'email': token_info.get('email'),
                                    'issued_at': token_info.get('issued_at', datetime.now())
                                }
                                
                                if save_token(token_data):
                                    print("Token successfully saved!")
                                    return True
                
                # Try to find the token by making an API request that would receive it
                api_url = "https://api.dowjones.com/content/search"
                api_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
                    "Accept": "application/vnd.dowjones.dna.content.v_1.0",
                    "Origin": "https://snapshot.factiva.com",
                    "Referer": "https://snapshot.factiva.com/"
                }
                
                print("Making API request to see if token is in response...")
                api_response = session.get(api_url, headers=api_headers)
                
                # Check for Authorization header in the request
                if 'Authorization' in api_response.request.headers:
                    auth_header = api_response.request.headers['Authorization']
                    if auth_header.startswith('Bearer '):
                        jwt_token = auth_header.split('Bearer ')[1]
                        print(f"Found JWT token in Authorization header!")
                        
                        # Validate and save the token
                        token_info = get_dow_jones_token_info(jwt_token)
                        if token_info.get('status') == 'Valid':
                            token_data = {
                                'token': jwt_token,
                                'expires_at': token_info.get('expires_at'),
                                'email': token_info.get('email'),
                                'issued_at': token_info.get('issued_at', datetime.now())
                            }
                            
                            if save_token(token_data):
                                print("Token successfully saved!")
                                return True
                
        # If we couldn't get a new token through the web flow, 
        # try to extract it from the GSLogin cookie value in your cURL logs
        print("Looking for token in cURL logs...")
        # This is a fallback that uses the token from your cURL logs
        try:
            # Using the working token from your example
            token_from_logs = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJEN0IwQTFERkJCNzlDRDFBQjM4NzNCMTcyODMyRjkxMENEQkRBREIiLCJ0eXAiOiJKV1QifQ.eyJwaWIiOnsiYWNjb3VudF9pZCI6IjlCTEEwMDQ2MDAiLCJhbGxvd19hdXRvX2xvZ2luIjoidHJ1ZSIsImFwYyI6IkZIIiwiY3RjIjoiRCIsIm1hc3Rlcl9hcHBfaWQiOiJaY01JZGlaajNmWDhtOU5JMWY4dGMxbDNDc0pFRGdjayIsInNlc3Npb25faWQiOiJwYnZpNFd3V19NRlJES09CWE1VMkRRWkJXSEU0VElNREdHSTRXQ01ERU1RWVRHWlJWTUpURE1NREZHTlNBIiwiZW1haWwiOiJKb2FubmEuWWF1QGJsYWNrcm9jay5jb20iLCJlaWQiOiJFNk9PMkhWQ1FIVlBFSExRMjdUNkJQTFNRQSJ9LCJpc3MiOiJodHRwczovL2FjY291bnRzLmRvd2pvbmVzLmNvbS9vYXV0aDIvdjIiLCJlbWFpbCI6IkpvYW5uYS5ZYXVAYmxhY2tyb2NrLmNvbSIsInN1YiI6ImIzMmMwMGIyLTI3Y2YtNGRkYi1hOGIyLTIxZDUzNDEwMGJjYyIsImF1ZCI6IlpjTUlkaVpqM2ZYOG05TkkxZjh0YzFsM0NzSkVEZ2NrIiwiYXpwIjoiWmNNSWRpWmozZlg4bTlOSTFmOHRjMWwzQ3NKRURnY2siLCJpYXQiOjE3NDQ1NTI4OTksImV4cCI6MTc0NDgxMjA5OX0.d4VJ7VKUmJ_MuNbbNFD9zdCf3zwl7mSTuyGoaXlziozA4sD9UrxRufNEEmAEquWpiuP6aWewLBcGx_BU9VZ-eGTzNlC3DaaAs7ESDdqoFQb1TNdLK0zZiJ5ID8Qxu525iA4rsDdbT6SQtI9PBrLpLBvE8tWl3Tk8BS4gwBuPaA4ka5uLiM95MFF7Uk6oTQ-j_nHCYxSPh4WlWYVLF6UpSQOhe_oM0xobx45nqy4AR-HHuKFnlM6wgLILzQEYFKsXpyMBCfsj_ViQKkFxjW9QRF37IFyru0TXayXgriRtasxg_CJk8oHf24fsLRCsfvzvON2odky_spW4K3PHYxRPMw"
            
            # Check if this token is still valid
            token_info = get_dow_jones_token_info(token_from_logs)
            
            # If token is valid or can be validated, save it
            if token_info.get('status') == 'Valid':
                print("Token from logs is valid, saving it")
                token_data = {
                    'token': token_from_logs,
                    'expires_at': token_info.get('expires_at'),
                    'email': token_info.get('email'),
                    'issued_at': token_info.get('issued_at', datetime.now())
                }
                
                if save_token(token_data):
                    print("Token successfully saved!")
                    return True
        except Exception as e:
            print(f"Error using token from logs: {e}")
        
        # If all else fails, extend the current token
        print("Could not obtain a new token. Extending current token as fallback.")
        return extend_token_expiry(days=7)
        
    except Exception as e:
        print(f"Error during token refresh: {e}")
        import traceback
        traceback.print_exc()
        return False
        
def create_article_url(article_id):
    """
    Create a URL for the article based on its ID
    
    Parameters:
    -----------
    article_id : str
        The article ID from the API
        
    Returns:
    --------
    str
        A URL to access the article, or None if it can't be created
    """
    if not article_id:
        return None
    
    try:
        # Extract the document ID part from the full ID
        # Format examples: 
        # - drn:archive.newsarticle.ROCHDL0020250322el3m0001c
        # - drn:archive.newsarticle.DAMONL0020250321el3l003xp
        
        doc_id = article_id
        if '.' in article_id:
            parts = article_id.split('.')
            if len(parts) >= 3:
                doc_id = parts[-1]
        
        # Different URL formats based on source code patterns
        if 'SAEXC' in doc_id:  # SEC filings
            return f"https://www.sec.gov/Archives/edgar/data/{doc_id}"
        elif 'LBA' in doc_id:  # Reuters News
            return f"https://www.reuters.com/article/{doc_id}"
        elif 'DAMONL' in doc_id:  # Mail Online
            return f"https://www.dailymail.co.uk/news/article-{doc_id.split('el')[0]}"
        else:
            # General factiva URL with document ID as query parameter
            return f"https://professional.dowjones.com/factiva/gateway/default.asp?mod=Search&docID={doc_id}"
        
    except Exception as e:
        print(f"Error creating URL for {article_id}: {e}")
        # Return a generic Factiva search URL as fallback
        return f"https://professional.dowjones.com/factiva/gateway/default.asp?mod=Search&q={article_id}"

# Search Functions
def create_api_headers(auth_token):
    """Create standard headers for API requests"""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/vnd.dowjones.dna.content.v_1.0",
        "Accept-Language": "en",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "authorization": f"Bearer {auth_token}",
        "cache-control": "no-cache",
        "Origin": "https://dj.factiva.com",
        "Connection": "keep-alive",
        "Referer": "https://dj.factiva.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Priority": "u=0",
        "TE": "trailers"
    }

def extract_article_data(article):
    """
    Extract article data from the API response
    
    Parameters:
    -----------
    article : dict
        Article data from the API response
        
    Returns:
    --------
    dict
        Extracted article data
    """
    # Basic article information
    article_data = {
        'id': article.get('id'),
        'source_name': article.get('meta', {}).get('source', {}).get('name', 'Unknown Source'),
        'headline': article.get('attributes', {}).get('headline', {}).get('main', {}).get('text', '').strip(),
        'publication_date': article.get('attributes', {}).get('publication_date'),
        'load_date': article.get('attributes', {}).get('load_date'),
        'author': article.get('attributes', {}).get('byline', {}).get('text')
    }
    
    # Extract snippet
    snippets = article.get('attributes', {}).get('snippet', {}).get('content', [])
    if snippets:
        article_data['snippet'] = ' '.join([s.get('text', '') for s in snippets if s.get('text')])
    else:
        article_data['snippet'] = None
    
    # Extract language
    language = article.get('meta', {}).get('language', {}).get('code')
    if language:
        article_data['language'] = language
    
    # Extract more metadata if available
    metrics = article.get('meta', {}).get('metrics', {})
    if metrics:
        article_data['word_count'] = metrics.get('word_count')
    
    # Add links if available
    if 'links' in article and 'self' in article['links']:
        article_data['api_url'] = article['links']['self']
    
    return article_data

def check_parquet_support():
    """Check if pyarrow or fastparquet is installed for parquet support"""
    try:
        import pyarrow
        return True
    except ImportError:
        try:
            import fastparquet
            return True
        except ImportError:
            return False

def save_results(df, base_name, default_format='parquet'):
    """
    Save DataFrame results to file with appropriate format
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The data to save
    base_name : str
        Base name for the file (without extension)
    default_format : str, optional
        Default format (parquet or csv)
    """
    if df.empty:
        print("No data to save.")
        return
        
    # Check if parquet is supported
    parquet_supported = check_parquet_support()
    if not parquet_supported and default_format == 'parquet':
        print("WARNING: Parquet format not available. Please install pyarrow or fastparquet.")
        print("Falling back to CSV format.")
        default_format = 'csv'
    
    # Ask user for format preference
    format_options = "p=Parquet, c=CSV" if parquet_supported else "c=CSV"
    format_default = 'p' if default_format == 'parquet' and parquet_supported else 'c'
    format_choice = input(f"Export format ({format_options}) [{format_default}]: ").lower() or format_default
    
    timestamp = int(time.time())
    
    if format_choice == 'c' or not parquet_supported:
        # CSV format
        filename = f"{base_name}_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
    else:
        # Parquet format
        filename = f"{base_name}_{timestamp}.parquet"
        
        # Prepare data for parquet (handle None values and ensure consistent types)
        df_clean = df.copy()
        for col in df_clean.select_dtypes(include=['object']):
            df_clean[col] = df_clean[col].fillna('').astype('str')
        
        # Save to parquet
        df_clean.to_parquet(filename, index=False)
        print(f"Results saved to {filename}")

def search_free_text(query_text, n_days=7, max_articles=100):
    """
    Search for articles matching free text query from the last N days
    
    Parameters:
    -----------
    query_text : str
        Free text query to search for
    n_days : int, optional
        Number of days to look back (default: 7)
    max_articles : int, optional
        Maximum number of articles to retrieve (default: 100)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with matching articles
    """
    auth_token = get_valid_token()
    
    # URL and headers same as other functions
    url = "https://api.dowjones.com/content/search"
    headers = create_api_headers(auth_token)
    
    # Calculate date range
    today = datetime.now()
    past_date = today - timedelta(days=n_days)
    start_date = past_date.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    date_param = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    # Payload for free text search
    payload = {"data": {
        "attributes": {
            "descriptor": {
                "language": "en",
                "mode": "All"
            },
            "formatting": {
                "deduplication_level": "Similar",
                "markup_type": "None",
                "snippet_type": "Fixed",
                "sort_order": "-PublicationDateChronological",
                "is_content_boosted_down_enabled": True,
                "is_content_boosted_up_enabled": False,
                "is_cluster_boosting_enabled": True
            },
            "linguistics": {"is_lemmatization_on": True},
            "navigation": {
                "code_navigators": {
                    "custom_navigator": [
                        {
                            "max_buckets": 10,
                            "min_buckets": 0,
                            "navigator_type": ["Company", "Industry", "Person", "Region", "Language", "Subject", "Source"]
                        }
                    ],
                    "max_buckets": 0,
                    "min_buckets": 0,
                    "mode": "None"
                },
                "content_collection_count": ["Publications", "Websites", "Blogs", "Pictures", "Translated"],
                "is_return_collection_count": True,
                "is_return_djn_headline_coding": False,
                "is_return_headline_coding": True,
                "keyword_navigators": {
                    "is_return_keywords": False,
                    "max_keywords": 0
                },
                "time_navigators": {
                    "max_buckets": 0,
                    "min_buckets": 0,
                    "mode": "None"
                }
            },
            "page_limit": 20,
            "page_offset": 0,
            "query": {
                "content_collection": ["Publications", "Websites", "Blogs", "Pictures"],
                "search_string": [
                    {
                        "mode": "Unified",
                        "value": query_text  # Use the free text query
                    },
                    {
                        "mode": "Unified",
                        "scope": "Language",
                        "value": "en"
                    }
                ],
                "date": date_param,
                "is_enhance_query": True
            },
            "search_context": json.dumps({
                "server_name": "ngsearchawsp",
                "page_offsets": [0],
                "server_host": "search-newssearch-6545979d5b-tk2d5"
            })
        },
        "id": "Search",
        "type": "content"
    }}
    
    # Use the same pagination logic as other search functions
    all_articles = []
    total_retrieved = 0
    page_size = 20
    current_page = 0
    total_count = None
    
    try:
        print(f"Searching for '{query_text}' with date range: {start_date} to {end_date}")
        
        # Check if proxy is enabled in config
        proxy_config = CONFIG.get('proxy', {})
        use_proxy = proxy_config.get('use_proxy', False)
        proxies = None
        
        if use_proxy:
            proxy_url = proxy_config.get('proxy_url')
            if proxy_url:
                print(f"Using proxy: {proxy_url}")
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
        
        # Continue fetching until we reach the max_articles limit or run out of results
        while total_retrieved < max_articles:
            # Update the page offset for pagination
            payload["data"]["attributes"]["page_offset"] = current_page * page_size
            
            # Update search_context to include the current pagination state
            offsets = list(range(0, current_page * page_size + page_size, page_size))
            context_dict = {
                "server_name": "ngsearchawsp",
                "page_offsets": offsets,
                "server_host": "search-newssearch-6545979d5b-tk2d5"
            }
            payload["data"]["attributes"]["search_context"] = json.dumps(context_dict)
            
            # Make the request (with proxies if enabled)
            response = requests.request("POST", url, json=payload, headers=headers, proxies=proxies)
            
            # Check for authentication errors specifically
            if response.status_code == 401:
                print("Authentication Error: Your authentication token has expired or is invalid.")
                return pd.DataFrame()
                
            # Check for other errors
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                return pd.DataFrame()
            
            # Process the response
            data = json.loads(response.text)
            
            # Get metadata
            if total_count is None:
                total_count = data.get('meta', {}).get('total_count', 0)
            
            # Extract articles
            batch_articles = []
            for article in data.get('data', []):
                article_data = extract_article_data(article)
                batch_articles.append(article_data)
            
            # Add to our collection
            all_articles.extend(batch_articles)
            batch_count = len(batch_articles)
            total_retrieved += batch_count
            
            # If we got fewer articles than the page size, we've reached the end
            if batch_count < page_size or total_retrieved >= total_count:
                break
                
            # Prepare for the next page
            current_page += 1
            print(f"Retrieved {total_retrieved} articles so far, fetching more...")
        
        # Create DataFrame
        df = pd.DataFrame(all_articles) if all_articles else pd.DataFrame()
        
        # Add URL column
        if not df.empty and 'id' in df.columns:
            df['url'] = df['id'].apply(create_article_url)
        
        print(f"Retrieved {len(df)} articles out of {total_count} total results for '{query_text}'")
        
        return df
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def search_company_last_n_days(company_name, n_days, max_articles=100):
    """
    Search for articles about a specific company from the last N days
    using the exact request flow from the cURL logs
    
    Parameters:
    -----------
    company_name : str
        Name of the company to search for
    n_days : int
        Number of days to look back
    max_articles : int, optional
        Maximum number of articles to retrieve (default: 100)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with articles about the specified company
    """
    # Get the company code
    company_code = COMPANY_CODES.get(company_name)
    if not company_code:
        print(f"Error: No code found for company {company_name}")
        return pd.DataFrame()
    
    try:
        # Create a session with the required headers
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd"
        })
        
        # Step 1: Start with login to get initial cookies
        print("Starting authentication sequence...")
        auth0_url = "https://auth.accounts.dowjones.com/login-page"
        auth0_params = {
            "client_id": "zgQkNiR9DBqamZBqIi6D0NaIvzLKkh3q",
            "scope": "openid pib email",
            "response_type": "code",
            "redirect_uri": "https://global.factiva.com/factivalogin/callback.aspx",
            "connection": "DJPIB",
            "op": "localop",
            "ui_locales": "en-us-x-global-0-0",
            "protocol": "oauth2"
        }
        
        # Initial login page request
        login_response = session.get(auth0_url, params=auth0_params)
        print(f"Login page status: {login_response.status_code}")
        
        # Get CSRF token
        csrf_token = session.cookies.get('csrf')
        if not csrf_token:
            print("Failed to get CSRF token")
            return pd.DataFrame()
        
        print(f"Got CSRF token: {csrf_token[:10]}...")
        
        # Get credentials
        username, password = get_credentials()
        
        # Submit credentials
        auth0_submit_url = "https://auth.accounts.dowjones.com/usernamepassword/login"
        
        # Extract state parameter from the URL
        state_param = None
        if "state=" in login_response.url:
            state_param = login_response.url.split("state=")[1].split("&")[0]
        
        login_data = {
            "client_id": "zgQkNiR9DBqamZBqIi6D0NaIvzLKkh3q",
            "redirect_uri": "https://global.factiva.com/factivalogin/callback.aspx",
            "tenant": "dowjones",
            "response_type": "code",
            "scope": "openid pib email",
            "username": username,
            "password": password,
            "_csrf": csrf_token,
            "connection": "DJPIB",
            "state": state_param
        }
        
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://auth.accounts.dowjones.com",
            "Referer": login_response.url
        }
        
        print("Submitting credentials...")
        auth_response = session.post(
            auth0_submit_url,
            data=login_data,
            headers=login_headers,
            allow_redirects=False
        )
        
        # Process the form response
        if auth_response.status_code == 200:
            soup = BeautifulSoup(auth_response.text, 'html.parser')
            form = soup.find('form', {'name': 'hiddenform'})
            
            if form and form.get('action'):
                form_url = form.get('action')
                form_data = {}
                
                for input_tag in form.find_all('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Submit the form
                print(f"Submitting form to: {form_url}")
                form_response = session.post(
                    form_url,
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    allow_redirects=True
                )
                
                print(f"Form submission response status: {form_response.status_code}")
                print(f"Cookies after form submission: {list(session.cookies.keys())}")
                
                # Step 2: Now access the main factiva page
                factiva_url = "https://snapshot.factiva.com/Pages/Index"
                factiva_data = {
                    "sa_from": "GL",
                    "_XFORMSESSSTATE": "H4sIAAAAAAAEAKs2sKoOtVLSTynV98xLSa1Q0jGyqjaxUkrNU9IxtTLQsbRScvcBCSr5BSjpGFtFx%2BoYWBnU1tYCAPIGllo5AAAA",
                    "xsrftoken": session.cookies.get('xsrftoken', '')
                }
                
                print("Accessing main Factiva page...")
                main_response = session.post(
                    factiva_url,
                    data=factiva_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": "https://snapshot.factiva.com",
                        "Referer": "https://snapshot.factiva.com/du/Index?sa_from=GL"
                    }
                )
                
                print(f"Main page response status: {main_response.status_code}")
                
                # Step 3: Now make the search request, using the exact format from cURL logs
                search_url = "https://snapshot.factiva.com/Search/SSResults"
                
                # Format date parameter based on n_days
                date_param = "LastDay" if n_days == 1 else "Last3Months"  # Default to Last3Months for other values
                
                search_data = {
                    "_XFORMSESSSTATE": "H4sIAAAAAAAEAKs2sKoOtVLSD0hMTy3W98xLSa1Q0jGyqjaxUkrNU9IxtTLQsbRScvcBCSr5BSjpGFtFx%2BoYWBnU1tYCAOjw8yE8AAAA",
                    "_XFORMSTATE": "",
                    "xsrftoken": session.cookies.get('xsrftoken', ''),
                    "ins": "1",
                    "napc": "NS",
                    "searchModel": json.dumps({
                        "pid": "",
                        "pname": "",
                        "ptype": "",
                        "searchFilter": {
                            "ft": "",
                            "hch": "All",
                            "dt": date_param,
                            "ism": False,
                            "frtr": 0,
                            "nf": {
                                "company": {
                                    "include": [{
                                        "code": company_code,
                                        "desc": f"{company_name} Inc",
                                        "codeType": "Company",
                                        "source": "Autocomplete"
                                    }]
                                }
                            },
                            "sfc": {
                                "code": company_code,
                                "desc": f"{company_name} Inc",
                                "codeType": "Company",
                                "source": "Autocomplete"
                            },
                            "sl": {
                                "slid": "All",
                                "slds": "false",
                                "sljson": "[]",
                                "sln": "All Sources"
                            }
                        },
                        "ReturnUrl": ""
                    })
                }
                
                search_headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://snapshot.factiva.com",
                    "Referer": "https://snapshot.factiva.com/Pages/Index",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                print(f"Searching for {company_name} using {date_param} date range...")
                search_response = session.post(search_url, data=search_data, headers=search_headers)
                
                print(f"Search response status: {search_response.status_code}")
                
                # Now check if we got any results - let's save the HTML for debugging
                debug_file = f"{company_name.lower()}_search_debug.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(search_response.text)
                print(f"Saved search response HTML to {debug_file} for debugging")
                
                # Parse the results
                soup = BeautifulSoup(search_response.text, 'html.parser')
                
                # Check for error messages first
                error_messages = soup.select('.errorMessage, .alert-error, .message-error')
                if error_messages:
                    for error in error_messages:
                        print(f"Error from Factiva: {error.text.strip()}")
                
                # Find all article containers
                article_containers = soup.select('#searchResults .listContainer, .searchResults .listContainer')
                
                if not article_containers:
                    print("No article containers found in the response HTML.")
                    print("Trying alternative HTML structures...")
                    
                    # Try alternative selectors
                    article_containers = soup.select('.snippetContainer, .documentSnippet, .articleItem')
                    
                    if not article_containers:
                        print("Still no article containers found.")
                        
                        # Last resort: Just print how many elements with 'article' or 'news' in class/id
                        article_elements = soup.select('[class*=article], [class*=news], [id*=article], [id*=news]')
                        print(f"Found {len(article_elements)} potential article elements using wider search")
                        
                        # Check if there's any no-results message
                        no_results = soup.select('.noResults, .emptyResults, .no-results')
                        if no_results:
                            print(f"No results message found: {no_results[0].text.strip()}")
                        
                        # Let's try a different approach - make another request to get headlines
                        print("Trying to get headlines through the editor's choice API...")
                        editors_url = "https://snapshot.factiva.com/AJAX/GetEditorsChoiceHeadlines"
                        editors_data = {
                            "industryCodes": "iextrfu,ivicu,i764",
                            "languages": "en,ja,ko,zhcn,zhtw",
                            "_XFORMSESSSTATE": "H4sIAAAAAAAEAKs2sKoOtVLSD05NLErO0A8ODkotLs0pKVbSMbKqNrFSSs1T0jG1MtCxtFJy9wEJKvkFK%2BkYW0XH6hhYGdTW1gIA36wZL0EAAAA%3D",
                            "_XFORMSTATE": "",
                            "xsrftoken": session.cookies.get('xsrftoken', '')
                        }
                        
                        editors_headers = {
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "X-Requested-With": "XMLHttpRequest",
                            "Origin": "https://snapshot.factiva.com",
                            "Referer": "https://snapshot.factiva.com/Search/SSResults"
                        }
                        
                        editors_response = session.post(editors_url, data=editors_data, headers=editors_headers)
                        
                        if editors_response.status_code == 200:
                            try:
                                editors_data = editors_response.json()
                                print(f"Got {len(editors_data)} headlines from editor's choice")
                                
                                # Create a DataFrame with these headlines
                                headlines = []
                                for item in editors_data:
                                    headlines.append({
                                        'headline': item.get('Headline'),
                                        'url': item.get('Url'),
                                        'publication_date': item.get('Date'),
                                        'source_name': item.get('Source')
                                    })
                                
                                if headlines:
                                    return pd.DataFrame(headlines)
                            except Exception as e:
                                print(f"Error processing editor's choice data: {e}")
                        
                        return pd.DataFrame()
                
                # If we found article containers, extract the data
                articles = []
                for container in article_containers:
                    try:
                        # Extract headline
                        headline_elem = container.select_one('h3 a, .headline a, .title a')
                        headline = headline_elem.text.strip() if headline_elem else "No headline"
                        
                        # Extract URL
                        url = None
                        if headline_elem and headline_elem.has_attr('href'):
                            url = headline_elem['href']
                            if not url.startswith('http'):
                                url = 'https://snapshot.factiva.com' + url
                        
                        # Extract publication date
                        date_elem = container.select_one('.date, .timestamp, .pubDate')
                        publication_date = date_elem.text.strip() if date_elem else None
                        
                        # Extract source
                        source_elem = container.select_one('.source, .publication, .sourceName')
                        source_name = source_elem.text.strip() if source_elem else None
                        
                        # Extract snippet
                        snippet_elem = container.select_one('.snippet, .summary, .description')
                        snippet = snippet_elem.text.strip() if snippet_elem else None
                        
                        # Add to articles list
                        articles.append({
                            'headline': headline,
                            'url': url,
                            'publication_date': publication_date,
                            'source_name': source_name,
                            'snippet': snippet
                        })
                    except Exception as e:
                        print(f"Error extracting article data: {e}")
                
                # Return the results
                if articles:
                    print(f"Successfully extracted {len(articles)} articles about {company_name}")
                    return pd.DataFrame(articles)
                else:
                    print(f"No articles could be extracted for {company_name}")
                    return pd.DataFrame()
            else:
                print("No form found in authentication response")
        else:
            print(f"Authentication failed with status: {auth_response.status_code}")
        
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def search_company_direct_api(company_name, n_days=90, max_articles=100):
    """
    Search for articles about a specific company using direct API access
    with the exact payload structure from the working example.
    
    Parameters:
    -----------
    company_name : str
        Name of the company to search for
    n_days : int, optional
        Number of days to look back (default: 90 for Last3Months)
    max_articles : int, optional
        Maximum number of articles to retrieve (default: 100)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with articles about the specified company
    """
    # Get the company code
    company_code = COMPANY_CODES.get(company_name)
    if not company_code:
        print(f"Error: No code found for company {company_name}")
        return pd.DataFrame()
    
    # Use the working token from the example
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJEN0IwQTFERkJCNzlDRDFBQjM4NzNCMTcyODMyRjkxMENEQkRBREIiLCJ0eXAiOiJKV1QifQ.eyJwaWIiOnsiYWNjb3VudF9pZCI6IjlCTEEwMDQ2MDAiLCJhbGxvd19hdXRvX2xvZ2luIjoidHJ1ZSIsImFwYyI6IkZIIiwiY3RjIjoiRCIsIm1hc3Rlcl9hcHBfaWQiOiJaY01JZGlaajNmWDhtOU5JMWY4dGMxbDNDc0pFRGdjayIsInNlc3Npb25faWQiOiJwYnZpNFd3V19NRlJES09CWE1VMkRRWkJXSEU0VElNREdHSTRXQ01ERU1RWVRHWlJWTUpURE1NREZHTlNBIiwiZW1haWwiOiJKb2FubmEuWWF1QGJsYWNrcm9jay5jb20iLCJlaWQiOiJFNk9PMkhWQ1FIVlBFSExRMjdUNkJQTFNRQSJ9LCJpc3MiOiJodHRwczovL2FjY291bnRzLmRvd2pvbmVzLmNvbS9vYXV0aDIvdjIiLCJlbWFpbCI6IkpvYW5uYS5ZYXVAYmxhY2tyb2NrLmNvbSIsInN1YiI6ImIzMmMwMGIyLTI3Y2YtNGRkYi1hOGIyLTIxZDUzNDEwMGJjYyIsImF1ZCI6IlpjTUlkaVpqM2ZYOG05TkkxZjh0YzFsM0NzSkVEZ2NrIiwiYXpwIjoiWmNNSWRpWmozZlg4bTlOSTFmOHRjMWwzQ3NKRURnY2siLCJpYXQiOjE3NDQ1NTI4OTksImV4cCI6MTc0NDgxMjA5OX0.d4VJ7VKUmJ_MuNbbNFD9zdCf3zwl7mSTuyGoaXlziozA4sD9UrxRufNEEmAEquWpiuP6aWewLBcGx_BU9VZ-eGTzNlC3DaaAs7ESDdqoFQb1TNdLK0zZiJ5ID8Qxu525iA4rsDdbT6SQtI9PBrLpLBvE8tWl3Tk8BS4gwBuPaA4ka5uLiM95MFF7Uk6oTQ-j_nHCYxSPh4WlWYVLF6UpSQOhe_oM0xobx45nqy4AR-HHuKFnlM6wgLILzQEYFKsXpyMBCfsj_ViQKkFxjW9QRF37IFyru0TXayXgriRtasxg_CJk8oHf24fsLRCsfvzvON2odky_spW4K3PHYxRPMw"
    
    # Save this token for future use
    token_info = get_dow_jones_token_info(token)
    if token_info.get('status') == 'Valid':
        token_data = {
            'token': token,
            'expires_at': token_info.get('expires_at'),
            'email': token_info.get('email'),
            'issued_at': token_info.get('issued_at', datetime.now())
        }
        save_token(token_data)
    
    # URL for the API
    url = "https://api.dowjones.com/content/search"
    
    # Set up headers using the token
    headers = {
        "Accept": "application/vnd.dowjones.dna.content.v_1.0",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
        "authorization": f"Bearer {token}",
        "cache-control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://dj.factiva.com",
        "Priority": "u=0",
        "Referer": "https://dj.factiva.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
        "X-DJ-Page-Module-Action": "Company|NA|Sort"
    }
    
    # Determine the date range parameter based on n_days
    if n_days <= 1:
        date_param = {"days_range": "LastDay"}
    elif n_days <= 7:
        date_param = {"days_range": "LastWeek"}
    elif n_days <= 30:
        date_param = {"days_range": "LastMonth"}
    else:
        date_param = {"days_range": "Last3Months"}
    
    # Build the payload structure based on the working example
    payload = {"data": {
        "attributes": {
            "descriptor": {
                "language": "en",
                "mode": "All"
            },
            "formatting": {
                "deduplication_level": "Similar",
                "markup_type": "None",
                "snippet_type": "Fixed",
                "sort_order": "-PublicationDateChronological",
                "is_content_boosted_down_enabled": True,
                "is_content_boosted_up_enabled": False,
                "is_cluster_boosting_enabled": True
            },
            "linguistics": {"is_lemmatization_on": False},
            "navigation": {
                "code_navigators": {
                    "custom_navigator": [
                        {
                            "max_buckets": 10,
                            "min_buckets": 0,
                            "navigator_type": ["Company", "Industry", "Person", "Region", "Language", "Subject", "Source"]
                        }
                    ],
                    "max_buckets": 0,
                    "min_buckets": 0,
                    "mode": "None"
                },
                "content_collection_count": ["Publications", "Websites", "Blogs", "Pictures", "Translated"],
                "is_return_collection_count": True,
                "is_return_djn_headline_coding": False,
                "is_return_headline_coding": True,
                "keyword_navigators": {
                    "is_return_keywords": False,
                    "max_keywords": 0
                },
                "time_navigators": {
                    "max_buckets": 0,
                    "min_buckets": 0,
                    "mode": "None"
                }
            },
            "page_limit": 20,
            "page_offset": 0,
            "query": {
                "content_collection": ["Publications", "Websites", "Blogs", "Pictures"],
                "search_string": [
                    {
                        "mode": "Unified",
                        "value": f"fds:{company_code}"
                    },
                    {
                        "mode": "Unified",
                        "scope": "Language",
                        "value": "zhcn or en or zhtw or ja or ko"
                    }
                ],
                "date": date_param,
                "is_enhance_query": True,
                "boost_string": [
                    {
                        "mode": "Unified",
                        "scope": "Organization",
                        "value": company_code,
                        "boost": "Up",
                        "boost_value": 5
                    }
                ]
            },
            "search_context": "{\"server_name\":\"ngsearchawsp\",\"page_offsets\":[0],\"server_host\":\"search-newssearch-87d4995d5-cn6g4\"}"
        },
        "id": "Search",
        "type": "content"
    }}
    
    try:
        print(f"Searching for company {company_name} ({company_code}) using the direct API...")
        
        # Make the initial request
        response = requests.post(url, json=payload, headers=headers)
        
        # Check for authentication errors
        if response.status_code == 401:
            print("Authentication Error: Token has expired or is invalid.")
            print(f"Response: {response.text[:200]}...")
            return pd.DataFrame()
            
        # Check for other errors
        if response.status_code != 200:
            print(f"API error: Status code {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return pd.DataFrame()
        
        # Parse the response
        data = json.loads(response.text)
        
        # Get total count
        total_count = data.get('meta', {}).get('total_count', 0)
        print(f"Found {total_count} articles about {company_name}")
        
        # Extract articles from the first page
        articles = []
        for article in data.get('data', []):
            article_data = extract_article_data(article)
            articles.append(article_data)
        
        # Pagination: Continue fetching if there are more results and we want more
        page_size = 20  # API default
        current_offset = page_size
        
        while len(articles) < min(max_articles, total_count) and current_offset < total_count:
            # Update the pagination offset
            payload["data"]["attributes"]["page_offset"] = current_offset
            
            # Update the search context with new offsets
            context_dict = json.loads(payload["data"]["attributes"]["search_context"])
            context_dict["page_offsets"].append(current_offset)
            payload["data"]["attributes"]["search_context"] = json.dumps(context_dict)
            
            print(f"Fetching additional articles (offset: {current_offset})...")
            next_response = requests.post(url, json=payload, headers=headers)
            
            if next_response.status_code == 200:
                next_data = json.loads(next_response.text)
                next_articles = []
                
                for article in next_data.get('data', []):
                    article_data = extract_article_data(article)
                    next_articles.append(article_data)
                
                articles.extend(next_articles)
                current_offset += len(next_articles)
                
                # If we received fewer articles than expected, break
                if len(next_articles) < page_size:
                    break
            else:
                print(f"Error fetching additional articles: {next_response.status_code}")
                break
        
        # Create DataFrame and add URL column
        df = pd.DataFrame(articles) if articles else pd.DataFrame()
        
        if not df.empty and 'id' in df.columns:
            df['url'] = df['id'].apply(create_article_url)
        
        print(f"Retrieved {len(df)} articles about {company_name}")
        return df
        
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
        
# if __name__ == "__main__":
#     import time
    
#     def display_menu():
#         print("\n===== Dow Jones API Test Tool =====")
#         print("1. Check token information")
#         print("2. Test token validity")
#         print("3. Refresh token")
#         print("4. Search by free text")
#         print("5. Search by company name")
#         print("6. Exit")
#         choice = input("\nSelect an option (1-6): ")
#         return choice
    
#     def check_token_info():
#         print("\n----- Token Information -----")
#         token_info = get_dow_jones_token_info()
#         for key, value in token_info.items():
#             print(f"{key}: {value}")
    
#     def test_token():
#         print("\nTesting token validity...")
#         if check_token_validity():
#             print("✓ Token is valid! API connections working.")
#         else:
#             print("✗ Token is invalid or API connection failed.")
    
#     def refresh_token():
#         print("\nAttempting to refresh token...")
#         success = auto_refresh_token()
#         if success:
#             print("✓ Token refreshed successfully!")
#             check_token_info()
#         else:
#             print("✗ Failed to refresh token.")
    
#     def search_text():
#         query = input("\nEnter search query: ")
#         days = int(input("Number of days to look back: "))
#         max_results = int(input("Maximum number of results (10-500): "))
        
#         print(f"\nSearching for '{query}' from the last {days} days...")
#         results = search_free_text(query, n_days=days, max_articles=max_results)
        
#         if results.empty:
#             print("No results found.")
#         else:
#             print(f"\nFound {len(results)} articles:")
#             for i, (headline, date, source) in enumerate(
#                 zip(results['headline'].head(10), 
#                     results['publication_date'].head(10),
#                     results['source_name'].head(10)), 1):
#                 print(f"{i}. [{source}] {headline} ({date})")
            
#             if len(results) > 10:
#                 print(f"... and {len(results) - 10} more articles.")
            
#             save = input("\nSave results? (y/n): ")
#             if save.lower() == 'y':
#                 query_slug = query.replace(' ', '_')[:30].lower()
#                 save_results(results, f"dow_jones_{query_slug}", default_format='parquet')
    
#     def search_company():
#         print("\nAvailable companies:")
#         companies = list(COMPANY_CODES.keys())
#         for i, company in enumerate(companies, 1):
#             print(f"{i}. {company}")
        
#         company_idx = int(input("\nSelect company number: ")) - 1
#         if 0 <= company_idx < len(companies):
#             company_name = companies[company_idx]
#             days = int(input("Number of days to look back: "))
#             max_results = int(input("Maximum number of results (10-500): "))
            
#             print(f"\nSearching for {company_name} news from the last {days} days...")
#             # Use the direct API function
#             results = search_company_direct_api(company_name, days, max_articles=max_results)
            
#             if results.empty:
#                 print("No results found.")
#             else:
#                 print(f"\nFound {len(results)} articles about {company_name}:")
#                 for i, (headline, date, source) in enumerate(
#                     zip(results['headline'].head(10), 
#                         results['publication_date'].head(10),
#                         results['source_name'].head(10)), 1):
#                     print(f"{i}. [{source}] {headline} ({date})")
                
#                 if len(results) > 10:
#                     print(f"... and {len(results) - 10} more articles.")
                
#                 save = input("\nSave results? (y/n): ")
#                 if save.lower() == 'y':
#                     save_results(results, f"{company_name.lower()}_news", default_format='parquet')
#         else:
#             print("Invalid company selection.")
    
#     # Interactive menu for testing
#     print("Configuration loaded from config.json")
#     print("Dow Jones API Module - Local Testing Interface")
    
#     # Main menu loop
#     while True:
#         choice = display_menu()
        
#         if choice == '1':
#             check_token_info()
#         elif choice == '2':
#             test_token()
#         elif choice == '3':
#             refresh_token()
#         elif choice == '4':
#             search_text()
#         elif choice == '5':
#             search_company()
#         elif choice == '6':
#             print("\nExiting. Goodbye!")
#             break
#         else:
#             print("\nInvalid choice. Please try again.")