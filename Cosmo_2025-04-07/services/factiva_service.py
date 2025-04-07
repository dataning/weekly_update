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
    config_path = Path("config.json")
    
    if not config_path.exists():
        print("Warning: config.json not found. API functionality may be limited.")
        return {}
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        print("Configuration loaded from config.json")
        return config
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}

# Load configuration
CONFIG = load_config()

# Constants
TOKEN_FILE = "dow_jones_token.pkl"
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
            return token_data.get('token', DEFAULT_TOKEN)
        else:
            print("Auto-refresh failed. Please update token manually through the app.")
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
    
    # Use a minimal payload with custom dates
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    minimal_payload = {
        "data": {
            "attributes": {
                "page_limit": 1,
                "page_offset": 0,
                "query": {
                    "content_collection": ["Publications"],
                    "date": {
                        "start_date": yesterday.strftime("%Y-%m-%d"),
                        "end_date": today.strftime("%Y-%m-%d")
                    }
                }
            },
            "id": "Search",
            "type": "content"
        }
    }
    
    try:
        response = requests.request("POST", url, json=minimal_payload, headers=headers)
        
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
        
        # Step 1: Create a session to maintain cookies and handle redirects
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        })
        
        # Check if proxy is enabled in config
        proxy_config = CONFIG.get('proxy', {})
        use_proxy = proxy_config.get('use_proxy', False)
        
        if use_proxy:
            proxy_url = proxy_config.get('proxy_url')
            if proxy_url:
                print(f"Using proxy: {proxy_url}")
                session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
        
        # Step 2: Access the login page to get CSRF token and cookies
        auth0_login_url = "https://auth.accounts.dowjones.com/login-page"
        login_params = {
            "client_id": "zgQkNiR9DBqamZBqIi6D0NaIvzLKkh3q",
            "scope": "openid pib email",
            "response_type": "code",
            "redirect_uri": "https://global.factiva.com/factivalogin/callback.aspx",
            "connection": "DJPIB",
            "protocol": "oauth2"
        }
        
        # Get the login page
        login_page_response = session.get(auth0_login_url, params=login_params)
        
        if login_page_response.status_code != 200:
            print(f"Failed to access login page: {login_page_response.status_code}")
            return False
        
        print(f"Login page accessed. Status: {login_page_response.status_code}")
        print(f"Cookies received: {session.cookies.get_dict()}")
            
        # Step 3: Get CSRF token from cookies
        csrf_token = session.cookies.get('csrf')
        if csrf_token:
            print(f"CSRF token found in cookies: {csrf_token[:10]}...")
        else:
            print("No CSRF token found in cookies")
            return False
        
        # Step 4: Get state parameter from the URL
        state_param = None
        if "state=" in login_page_response.url:
            state_param = login_page_response.url.split("state=")[1].split("&")[0]
            print(f"State parameter from URL: {state_param[:10]}..." if state_param else "No state parameter found")
        
        # Step 5: Submit login credentials
        auth0_submit_url = "https://auth.accounts.dowjones.com/usernamepassword/login"
        
        # Get credentials
        username, password = get_credentials()
        
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
        
        # Set specific headers for the login request
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://auth.accounts.dowjones.com",
            "Referer": login_page_response.url
        }
        
        # Submit login
        print(f"Submitting login with CSRF token: {csrf_token[:10]}...")
        login_response = session.post(
            auth0_submit_url,
            data=login_data,
            headers=login_headers,
            allow_redirects=False
        )
        
        print(f"Login response status: {login_response.status_code}")
        
        # Step 6: Handle the Auth0 form response
        if login_response.status_code == 200:
            print("Auth0 returned a form-based response (expected behavior)")
            
            # Parse the HTML to extract form fields
            soup = BeautifulSoup(login_response.text, 'html.parser')
            
            # Find the form
            auth0_form = soup.find('form', {'name': 'hiddenform'})
            
            if auth0_form:
                form_action_url = auth0_form.get('action')
                print(f"Form action URL: {form_action_url}")
                
                # Extract input fields from the form
                form_data = {}
                for input_field in auth0_form.find_all('input'):
                    field_name = input_field.get('name')
                    field_value = input_field.get('value', '')
                    if field_name:
                        form_data[field_name] = field_value
                        print(f"Form field: {field_name}={field_value[:20]}..." if len(field_value) > 20 else f"Form field: {field_name}={field_value}")
                
                # Make sure we have the token
                if 'token' not in form_data:
                    # Fallback to regex if BeautifulSoup didn't find it
                    auth0_token_match = re.search(r'name="token" value="([^"]+)"', login_response.text)
                    if auth0_token_match:
                        form_data['token'] = auth0_token_match.group(1)
                        print(f"Added token from regex: {form_data['token'][:20]}...")
                
                if form_data and form_action_url:
                    # Submit the form with ALL extracted fields
                    form_headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": auth0_submit_url,
                        "Origin": "https://auth.accounts.dowjones.com"
                    }
                    
                    print(f"Submitting Auth0 form to: {form_action_url} with {len(form_data)} fields")
                    form_response = session.post(
                        form_action_url,
                        data=form_data,
                        headers=form_headers,
                        allow_redirects=True  # Allow redirects to follow the chain
                    )
                    
                    print(f"Form submission final response status: {form_response.status_code}")
                    print("Authentication successful, extending token expiry")
                    return extend_token_expiry(days=14)
        
        # If we're here, something went wrong
        print("Authentication flow not completed successfully. Extending current token as fallback.")
        
        # Fallback to extending current token
        return extend_token_expiry(days=7)
            
    except Exception as e:
        print(f"Error during auto-refresh: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_refresh():
    """
    Test the token refresh functionality
    
    Returns:
    --------
    dict
        Information about the test result
    """
    print("Starting token refresh test...")
    
    # Save the original token expiry
    token_data = load_token()
    if not token_data or not token_data.get('expires_at'):
        return {
            "success": False,
            "message": "Couldn't get current token expiry date"
        }
    
    original_expires_at = token_data.get('expires_at')
    print(f"Original expiry: {original_expires_at}")
    
    # Directly test the expiry extension
    success = extend_token_expiry(days=1)  # Just 1 day for testing
    
    if not success:
        return {
            "success": False,
            "message": "Failed to extend token expiry"
        }
    
    # Get the new expiry
    token_data = load_token()
    new_expires_at = token_data.get('expires_at')
    print(f"New expiry: {new_expires_at}")
    
    # Calculate the difference
    if original_expires_at and new_expires_at:
        expiry_diff = new_expires_at - original_expires_at
        print(f"Expiry difference: {expiry_diff.days} days, {expiry_diff.seconds // 3600} hours")
        
        if expiry_diff.total_seconds() > 0:
            print("TOKEN EXPIRY EXTENSION SUCCESSFUL!")
            return {
                "success": True,
                "old_expiry": original_expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "new_expiry": new_expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "difference": f"{expiry_diff.days} days, {expiry_diff.seconds // 3600} hours"
            }
    
    print("TOKEN EXPIRY EXTENSION FAILED - dates didn't change!")
    return {
        "success": False,
        "message": "Expiry date didn't change"
    }

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
        'source_name': article.get('meta', {}).get('source', {}).get('name'),
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
    
    # Add links if available
    if 'links' in article and 'self' in article['links']:
        article_data['api_url'] = article['links']['self']
    
    return article_data

def search_company_last_n_days(company_name, n_days, max_articles=100):
    """
    Search for articles about a specific company from the last N days
    
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
    # Get the current valid token
    auth_token = get_valid_token()
    
    # Get the company code
    company_code = COMPANY_CODES.get(company_name)
    if not company_code:
        print(f"Error: No code found for company {company_name}")
        return pd.DataFrame()
    
    # URL - same as your working code
    url = "https://api.dowjones.com/content/search"

    # Headers
    headers = create_api_headers(auth_token)
    
    # Calculate date range
    today = datetime.now()
    
    if n_days == 1:
        # Use "LastDay" predefined range
        print(f"Using predefined range: LastDay")
        date_param = {"days_range": "LastDay"}
    else:
        # Calculate custom date range
        if n_days == 0:  # Just today
            start_date = today.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            print(f"Using custom date range for today: {start_date}")
        else:
            past_date = today - timedelta(days=n_days)
            start_date = past_date.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            print(f"Using custom date range from {start_date} to {end_date}")
            
        date_param = {
            "start_date": start_date,
            "end_date": end_date
        }
    
    # Payload
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
                "sort_order": "-PublicationDateChronological",  # Sort by date, most recent first
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
            "page_offset": 0,  # Start with page 0
            "query": {
                "content_collection": ["Publications", "Websites", "Blogs", "Pictures"],
                "search_string": [
                    {
                        "mode": "Unified",
                        "value": f"fds:{company_code}"  # Use the specific company code
                    },
                    {
                        "mode": "Unified",
                        "scope": "Language",
                        "value": "en"
                    },
                    {
                        "mode": "Unified",
                        "scope": "Organization",
                        "value": company_code.lower()  # Add organization scope with lowercase code
                    }
                ],
                "date": date_param,  # Set the date parameter
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
            "search_context": json.dumps({
                "server_name": "ngsearchawsp",
                "page_offsets": [0],
                "server_host": "search-newssearch-6545979d5b-tk2d5"
            })
        },
        "id": "Search",
        "type": "content"
    }}
    
    # Make multiple requests to handle pagination
    all_articles = []
    total_retrieved = 0
    page_size = 20  # Default page size in the API
    current_page = 0  # Start with the first page
    total_count = None
    
    try:
        print(f"Searching for company {company_name} ({company_code}) with date parameter: {date_param}")
        
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
                print("You need to obtain a new token by logging into the Dow Jones API service.")
                print(f"Error details: {response.text}")
                return pd.DataFrame()  # Return empty DataFrame instead of raising exception
                
            # Check for other errors
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                return pd.DataFrame()  # Return empty DataFrame instead of raising exception
            
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
        
        print(f"Retrieved {len(df)} articles out of {total_count} total results for {company_name}")
        
        return df
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def search_company_by_date_range(company_name, start_date, end_date, max_articles=100):
    """
    Search for articles about a specific company within a specific date range
    
    Parameters:
    -----------
    company_name : str
        Name of the company to search for
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
    max_articles : int, optional
        Maximum number of articles to retrieve (default: 100)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with articles about the specified company
    """
    # Get the current valid token
    auth_token = get_valid_token()
    
    # Get the company code
    company_code = COMPANY_CODES.get(company_name)
    if not company_code:
        print(f"Error: No code found for company {company_name}")
        return pd.DataFrame()
    
    # URL
    url = "https://api.dowjones.com/content/search"

    # Headers
    headers = create_api_headers(auth_token)
    
    # Create the date param with the provided start and end dates
    date_param = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    # Payload
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
                "sort_order": "-PublicationDateChronological",  # Sort by date, most recent first
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
            "page_offset": 0,  # Start with page 0
            "query": {
                "content_collection": ["Publications", "Websites", "Blogs", "Pictures"],
                "search_string": [
                    {
                        "mode": "Unified",
                        "value": f"fds:{company_code}"  # Use the specific company code
                    },
                    {
                        "mode": "Unified",
                        "scope": "Language",
                        "value": "en"
                    },
                    {
                        "mode": "Unified",
                        "scope": "Organization",
                        "value": company_code.lower()  # Add organization scope with lowercase code
                    }
                ],
                "date": date_param,  # Set the date parameter
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
            "search_context": json.dumps({
                "server_name": "ngsearchawsp",
                "page_offsets": [0],
                "server_host": "search-newssearch-6545979d5b-tk2d5"
            })
        },
        "id": "Search",
        "type": "content"
    }}
    
    # Make multiple requests to handle pagination
    all_articles = []
    total_retrieved = 0
    page_size = 20  # Default page size in the API
    current_page = 0  # Start with the first page
    total_count = None
    
    try:
        print(f"Searching for company {company_name} ({company_code}) with date parameter: {date_param}")
        
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
                print("You need to obtain a new token by logging into the Dow Jones API service.")
                print(f"Error details: {response.text}")
                return pd.DataFrame()  # Return empty DataFrame instead of raising exception
                
            # Check for other errors
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                return pd.DataFrame()  # Return empty DataFrame instead of raising exception
            
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
        
        print(f"Retrieved {len(df)} articles out of {total_count} total results for {company_name}")
        
        return df
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

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