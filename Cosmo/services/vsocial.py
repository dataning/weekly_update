import requests
import json
import pandas as pd
import base64
import time
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime

@dataclass
class SocialMediaPost:
    pid: str
    pid_link: str
    platform: str
    shares_count: int
    post_date: str
    poster_screen_name: str
    poster_name: str
    post_text: str
    percent_bots_retweets: Optional[float] = None
    human_reach: Optional[int] = None
    tweeter_is_bot: Optional[bool] = None
    retweeter_viral_states: Dict[str, float] = field(default_factory=dict)
    tweeter_is_verified: Optional[bool] = None
    percent_males: Optional[float] = None
    post_type: str = ""
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    sad_count: Optional[int] = None
    love_count: Optional[int] = None
    haha_count: Optional[int] = None
    wow_count: Optional[int] = None
    angry_count: Optional[int] = None
    article_url: Optional[str] = None
    page_users_count: Optional[int] = None
    poster_uid: str = ""
    profile_image_url: Optional[str] = None
    article_id: Optional[str] = None
    tweeter_state: Optional[str] = None
    tweeter_country: Optional[str] = None
    video_views_count: Optional[int] = None
    video_likes_count: Optional[int] = None
    video_comments_count: Optional[int] = None
    video_source: Optional[str] = None
    quotes_count: Optional[int] = None
    interactions_count: Optional[int] = None
    screenshot_link: Optional[str] = None
    post_language: Optional[str] = None
    post_translation: Optional[str] = None
    amplification_multiplier: Optional[float] = None
    post_image_url: Optional[str] = None
    url_description: Optional[str] = None
    url_preview_img_url: Optional[str] = None
    url_headline_text: Optional[str] = None
    poster_profile_create_date: Optional[str] = None
    poster_posts_count: Optional[int] = None
    poster_likes_count: Optional[int] = None
    poster_followees_count: Optional[int] = None
    poster_followers_count: Optional[int] = None
    poster_actions_per_day_count: Optional[int] = None
    poster_is_politician: Optional[bool] = None
    model_name: Optional[str] = None
    narrative_id: Optional[str] = None
    name: Optional[str] = None
    video_create_date: Optional[str] = None
    views_count: Optional[int] = None
    poster_username: Optional[str] = None
    poster_display_name: Optional[str] = None
    channel_username: Optional[str] = None
    channel_display_name: Optional[str] = None
    transcript: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    poster_additional_user_id: Optional[str] = None
    # Add the missing field that's causing the error
    african_retweets_count: Optional[int] = None
    # Add additional fields you might have seen in the JSON
    african_reach: Optional[int] = None
    retweeters_count_by_country: Optional[Dict] = field(default_factory=dict)
    is_blue_verified: Optional[bool] = None

# We're not using this dataclass anymore since the article posts API returns social media posts
# referencing articles rather than article metadata directly
@dataclass
class ArticleReference:
    """Metadata about articles extracted from posts that reference them"""
    article_id: str
    article_url: Optional[str] = None
    url_headline_text: Optional[str] = None
    url_description: Optional[str] = None
    url_preview_img_url: Optional[str] = None
    # Additional fields can be added as needed

# Function to load configuration from config.json
def load_config(config_file='config.json'):
    """Load configuration from config.json file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing {config_file}. Invalid JSON format.")
        return {}

# Function to save configuration to config.json
def save_config(config, config_file='config.json'):
    """Save configuration to config.json file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

# Function to login to Vinesight and get new cookies
def login_to_vinesight(username, password, use_proxy=False):
    """
    Login to Vinesight API and get new cookies
    
    Args:
        username: Vinesight account username
        password: Vinesight account password
        use_proxy: Whether to use corporate proxy
        
    Returns:
        dict: Login result containing success status, cookies and token
    """
    login_url = "https://dash-api.vinesight.com/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0"
    }
    
    # Setup proxies if enabled
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"Using proxy: {proxy_url} for login")
    
    try:
        response = requests.post(
            login_url, 
            json=payload, 
            headers=headers, 
            proxies=proxies
        )
        response.raise_for_status()
        
        # Extract cookies from response
        cookies = response.cookies.get_dict()
        
        # Extract JWT token from response if available
        response_data = response.json()
        if 'token' in response_data:
            # Some APIs return the token in the response body
            token = response_data['token']
        else:
            # Extract from cookies if not in response body
            token = cookies.get('session')
        
        return {
            'success': True,
            'cookies': cookies,
            'token': token
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }

# Function to check if a JWT token is expired
def is_token_expired(token):
    """Check if JWT token is expired"""
    if not token:
        return True
    
    try:
        # JWT tokens have three parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            return True
        
        # Decode the payload (middle part)
        payload = parts[1]
        # Add padding if needed
        padding_needed = len(payload) % 4
        if padding_needed:
            payload += '=' * (4 - padding_needed)
        
        decoded = base64.b64decode(payload).decode('utf-8')
        data = json.loads(decoded)
        
        # Check if token has expiration time
        if 'exp' not in data and 'expire_timestamp' not in data:
            # If no expiration, assume it's expired
            return True
        
        # Compare expiration timestamp with current time
        exp_time = data.get('exp') or data.get('expire_timestamp')
        current_time = time.time()
        
        return current_time >= exp_time
    except Exception as e:
        print(f"Error checking token expiration: {e}")
        return True

# Function to refresh Vinesight token if expired
def refresh_vinesight_token(config, use_proxy=False):
    """
    Refresh Vinesight token if expired
    
    Args:
        config: Configuration dictionary
        use_proxy: Whether to use corporate proxy
        
    Returns:
        dict: Refresh result containing success status and message
    """
    if 'vinesight' not in config:
        config['vinesight'] = {
            "username": "alexander.williams@blackrock.com",
            "password": "BlackRock2024!",  # You should use a more secure way to store this
            "cookie_expiry_days": 7,
            "default_cookies": {}
        }
    
    vinesight_config = config['vinesight']
    
    # Check if we have credentials
    if 'username' not in vinesight_config or 'password' not in vinesight_config:
        return {
            'success': False,
            'error': 'Vinesight credentials not found'
        }
    
    # Get current token
    current_token = None
    if 'default_cookies' in vinesight_config and 'session' in vinesight_config['default_cookies']:
        current_token = vinesight_config['default_cookies']['session']
    
    # Check if token is expired
    if current_token and not is_token_expired(current_token):
        return {
            'success': True,
            'message': 'Token still valid'
        }
    
    # If expired, login to get new token
    login_result = login_to_vinesight(
        vinesight_config['username'],
        vinesight_config['password'],
        use_proxy=use_proxy
    )
    
    if not login_result['success']:
        return login_result
    
    # Update config with new cookies and timestamp
    vinesight_config['default_cookies'] = login_result['cookies']
    vinesight_config['last_refreshed'] = datetime.now().isoformat()
    
    # Save updated config
    save_config(config)
    
    return {
        'success': True,
        'message': 'Token refreshed successfully'
    }

# Function to get headers with current/refreshed cookies
def get_vinesight_headers(config=None, use_proxy=False):
    """
    Get headers for Vinesight API calls, refreshing token if needed
    
    Args:
        config: Configuration dictionary
        use_proxy: Whether to use corporate proxy
        
    Returns:
        dict: Headers for API requests
    """
    if config is None:
        config = load_config()
    
    # Refresh token if needed
    refresh_result = refresh_vinesight_token(config, use_proxy=use_proxy)
    if not refresh_result['success']:
        print(f"Warning: Failed to refresh token: {refresh_result.get('error', 'Unknown error')}")
    
    # Get cookies from config
    cookies = {}
    if 'vinesight' in config and 'default_cookies' in config['vinesight']:
        cookies = config['vinesight']['default_cookies']
    
    # Build cookie string
    cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
    
    # Create headers with cookies
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Origin": "https://dash.vinesight.com",
        "Connection": "keep-alive",
        "Referer": "https://dash.vinesight.com/",
        "Cookie": cookie_str,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers"
    }
    
    return headers

# Function to fetch data from API
def fetch_data_from_api(config=None, use_proxy=False):
    """
    Fetch data from Vinesight API using credentials from config
    
    Args:
        config: Configuration dictionary
        use_proxy: Whether to use corporate proxy
        
    Returns:
        list: Raw API response data
    """
    if config is None:
        config = load_config()
    
    url = "https://dash-api.vinesight.com/home/get_post_center_posts"
    querystring = {
        "offset": "0",
        "past_hours": "24",
        "start_date": "",
        "end_date": "",
        "topic_id": "4819780",
        "text_type": "",
        "images_type": "",
        "videos_type": "",
        "quote_tweets_type": "",
        "sort": "virality",
        "state_from": "",
        "state_about": "",
        "country_from": "",
        "country_about": "",
        "location_operator": "and",
        "language": "",
        "position": "critical",
        "company": "",
        "narrative_model": "",
        "search_text": "",
        "platform": ["FACEBOOK", "REDDIT", "INSTAGRAM", "TWITTER", "TELEGRAM", "TIKTOK", "FCHAN", "TRUTHSOCIAL", "GAB", "GETTR", "VK"],
        "url_type": ""
    }
    payload = ""
    headers = get_vinesight_headers(config, use_proxy=use_proxy)
    
    # Setup proxies if enabled
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"Using proxy: {proxy_url} for API request")
    
    try:
        response = requests.request(
            "GET", 
            url, 
            data=payload, 
            headers=headers, 
            params=querystring,
            proxies=proxies
        )
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Update cookies if they've changed
        if response.cookies:
            if 'vinesight' not in config:
                config['vinesight'] = {}
            if 'default_cookies' not in config['vinesight']:
                config['vinesight']['default_cookies'] = {}
            
            # Update with new cookies
            for key, value in response.cookies.items():
                config['vinesight']['default_cookies'][key] = value
            
            # Save updated config
            save_config(config)
        
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        # Fallback to sample data from file if API fails
        return load_data_from_file()

# New function to fetch article posts from API
def fetch_article_posts(config=None, use_proxy=False):
    """
    Fetch article posts from Vinesight API using credentials from config
    
    Args:
        config: Configuration dictionary
        use_proxy: Whether to use corporate proxy
        
    Returns:
        list: Article posts data
    """
    if config is None:
        config = load_config()
    
    url = "https://dash-api.vinesight.com/home/get_article_posts"
    querystring = {
        "state_from": "",
        "state_about": "",
        "country_from": "",
        "country_about": "",
        "location_operator": "and",
        "language": "",
        "position": "critical",
        "company": "",
        "narrative_model": "",
        "search_text": "",
        "past_hours": "24",
        "start_date": "",
        "end_date": "",
        "topic_id": "4819780",
        "show_msm": "false",
        "sort": "date_desc",
        "article_id": [
            "1903896119329046898",
            "1903888307664179320",
            "1903888035693130097",
            "1903886968657694804",
            "1903884246655107419",
            "1903884167537938473",
            "1903882683677331558",
            "1903874050092585351",
            "1903861422930436603",
            "1903853246726492631"
        ]
    }
    payload = ""
    headers = get_vinesight_headers(config, use_proxy=use_proxy) if config else {
        "cookie": "session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFsZXhhbmRlci53aWxsaWFtc0BibGFja3JvY2suY29tIiwiZXhwaXJlX3RpbWVzdGFtcCI6MTc0NTM2MTc0Ny45MTcyNjJ9.agvdceIMdsJahYjRvcwgSfEXS5bsxI48WbUDDuoVaHo",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en;q=0.5",
        "Connection": "keep-alive",
        "Cookie": "AMP_a5afb18362=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIyMTdiMjAyNC0wOGQxLTQyNDktYTdmYS1hODMyZmJjOWU2M2IlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJ1c2VyX2lkXzMwNCUyMiUyQyUyMnNlc3Npb25JZCUyMiUzQTE3NDI4MDAyMDUwNjAlMkMlMjJvcHRPdXQlMjIlM0FmYWxzZSUyQyUyMmxhc3RFdmVudFRpbWUlMjIlM0ExNzQyODAwNTU4MDc1JTJDJTIybGFzdEV2ZW50SWQlMjIlM0EyOCUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMCU3RA==; AMP_MKTG_a5afb18362=JTdCJTdE; session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFsZXhhbmRlci53aWxsaWFtc0BibGFja3JvY2suY29tIiwiZXhwaXJlX3RpbWVzdGFtcCI6MTc0NTM5MjQwMC4zMTgwMDR9.vIbdEkAmELIh9rYxbSUcqgRHL1Q2HHcEXcG4HjFfT08",
        "Origin": "https://dash.vinesight.com",
        "Referer": "https://dash.vinesight.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0"
    }
    
    # Setup proxies if enabled
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"Using proxy: {proxy_url} for article API request")
    
    try:
        response = requests.request(
            "GET", 
            url, 
            data=payload, 
            headers=headers, 
            params=querystring,
            proxies=proxies
        )
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = json.loads(response.text)
        
        # Debug the response structure
        print(f"Response type: {type(data)}")
        
        # Explicitly check for different response formats and extract posts array
        if isinstance(data, dict) and 'posts' in data:
            print(f"Found 'posts' key in response, with {len(data['posts'])} posts")
            return data['posts']
        elif isinstance(data, list):
            print(f"Response is a list with {len(data)} items")
            return data
        else:
            print(f"Unexpected response format: {type(data)}")
            # Return empty list for empty or unexpected response format
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Article API request error: {e}")
        return []  # Return empty list if API call fails
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.text[:200]}...")  # Show first 200 chars of response
        return []
        
# Function to load data from file (fallback)
def load_data_from_file(file_path='paste.txt'):
    try:
        with open(file_path, 'r') as file:
            data = file.read()
        
        # The data in the file might not be complete JSON, so we'll add necessary brackets
        if not data.strip().startswith('['):
            data = '[' + data
        if not data.strip().endswith(']'):
            data = data + ']'
        
        return json.loads(data)
    except Exception as e:
        print(f"Error loading data from file: {e}")
        return []

# Function to convert JSON data to SocialMediaPost instances
def convert_to_dataclass(data):
    posts = []
    for item in data:
        try:
            post = SocialMediaPost(**item)
            posts.append(post)
        except Exception as e:
            print(f"Error converting item to dataclass: {e}")
    return posts

# Since the article posts API returns social media posts, we'll use the same
# SocialMediaPost dataclass for consistency and extract article metadata separately
def process_article_posts(data):
    """
    Process article posts data to extract both posts and article metadata
    
    Args:
        data: The raw data from fetch_article_posts API
        
    Returns:
        tuple: (list of SocialMediaPost objects, dict of ArticleReference objects)
    """
    posts = []
    article_metadata = {}
    
    # Debug the response
    print(f"Processing {len(data) if isinstance(data, list) else 'non-list'} article data items")
    
    # If data is not a list, handle it
    if not isinstance(data, list):
        if isinstance(data, dict) and 'posts' in data:
            data = data['posts']
            print(f"Extracted 'posts' array with {len(data)} items")
        else:
            print(f"Unable to process data of type {type(data)}")
            return [], {}
    
    # Process each item
    for item in data:
        try:
            # If the item is a string, try to parse it as JSON
            if isinstance(item, str):
                try:
                    import json
                    item = json.loads(item)
                except json.JSONDecodeError:
                    print(f"Could not parse item as JSON")
                    continue
            
            # Get all valid fields for SocialMediaPost
            import inspect
            valid_fields = set(inspect.signature(SocialMediaPost.__init__).parameters.keys()) - {'self'}
            
            # Filter the item to include only valid fields
            filtered_item = {k: v for k, v in item.items() if k in valid_fields}
            
            # Create a social media post object with only the valid fields
            post = SocialMediaPost(**filtered_item)
            posts.append(post)
            
            # Extract and store article metadata if we have both article_id and article_url
            if post.article_id and post.article_url:
                article_metadata[post.article_id] = ArticleReference(
                    article_id=post.article_id,
                    article_url=post.article_url,
                    url_headline_text=post.url_headline_text,
                    url_description=post.url_description,
                    url_preview_img_url=post.url_preview_img_url
                )
        except Exception as e:
            print(f"Error processing article post item: {e}")
            if isinstance(item, dict):
                print(f"Problem item keys: {sorted(item.keys())}")
    
    print(f"Successfully processed {len(posts)} posts and extracted {len(article_metadata)} article metadata items")
    return posts, article_metadata

# Improved article processing function
def improved_process_article_posts(data):
    """
    Process article posts data to extract both posts and article metadata
    
    Args:
        data: The raw data from fetch_article_posts API
        
    Returns:
        tuple: (list of SocialMediaPost objects, dict of ArticleReference objects)
    """
    posts = []
    article_metadata = {}
    
    # Debug the response
    print(f"Processing {len(data) if isinstance(data, list) else 'non-list'} article data items")
    
    # If data is not a list, handle it
    if not isinstance(data, list):
        if isinstance(data, dict) and 'posts' in data:
            data = data['posts']
            print(f"Extracted 'posts' array with {len(data)} items")
        else:
            print(f"Unable to process data of type {type(data)}")
            return [], {}
    
    # Process each item
    for item in data:
        try:
            # If the item is a string, try to parse it as JSON
            if isinstance(item, str):
                try:
                    import json
                    item = json.loads(item)
                except json.JSONDecodeError:
                    print(f"Could not parse item as JSON")
                    continue
            
            # Get all valid fields for SocialMediaPost
            import inspect
            valid_fields = set(inspect.signature(SocialMediaPost.__init__).parameters.keys()) - {'self'}
            
            # Filter the item to include only valid fields
            filtered_item = {k: v for k, v in item.items() if k in valid_fields}
            
            # Create a social media post object with only the valid fields
            post = SocialMediaPost(**filtered_item)
            posts.append(post)
            
            # Extract and store article metadata if we have both article_id and article_url
            if post.article_id and post.article_url:
                article_metadata[post.article_id] = ArticleReference(
                    article_id=post.article_id,
                    article_url=post.article_url,
                    url_headline_text=post.url_headline_text,
                    url_description=post.url_description,
                    url_preview_img_url=post.url_preview_img_url
                )
        except Exception as e:
            print(f"Error processing article post item: {e}")
            if isinstance(item, dict):
                print(f"Problem item keys: {sorted(item.keys())}")
    
    print(f"Successfully processed {len(posts)} posts and extracted {len(article_metadata)} article metadata items")
    return posts, article_metadata
    
# Function to convert dataclass instances to a pandas DataFrame
def create_dataframe(posts):
    return pd.DataFrame([vars(post) for post in posts])

# Function to analyze the data
def analyze_data(df):
    if df.empty:
        return "No data to analyze"
    
    # Basic statistics
    total_posts = len(df)
    platforms = df['platform'].value_counts().to_dict()
    avg_shares = df['shares_count'].mean()
    avg_likes = df['likes_count'].mean()
    avg_interactions = df['interactions_count'].mean()
    
    # Add a column for BlackRock mentions
    df['mentions_blackrock'] = df['post_text'].str.lower().str.contains('blackrock')
    blackrock_mentions = df[df['mentions_blackrock']]
    
    # Top posts by interactions
    top_posts = df.sort_values('interactions_count', ascending=False).head(5)
    
    # Bot analysis
    avg_bot_percentage = df['percent_bots_retweets'].mean()
    
    # Result summary
    results = {
        'total_posts': total_posts,
        'platforms': platforms,
        'avg_shares': avg_shares,
        'avg_likes': avg_likes,
        'avg_interactions': avg_interactions,
        'blackrock_mentions': len(blackrock_mentions),
        'top_posts': top_posts[['poster_name', 'post_text', 'interactions_count']].to_dict('records'),
        'avg_bot_percentage': avg_bot_percentage
    }
    
    return results

# Function to analyze article posts data
def analyze_article_posts(df, article_metadata_dict):
    if df.empty:
        return "No article posts data to analyze"
    
    # Basic statistics
    total_posts = len(df)
    platforms = df['platform'].value_counts().to_dict()
    
    # Articles being referenced
    article_references = df['article_id'].value_counts().to_dict()
    total_articles = len(article_references)
    
    # Add a column for BlackRock mentions
    df['mentions_blackrock'] = df['post_text'].str.lower().str.contains('blackrock')
    
    # Group posts by article_id
    articles_data = []
    for article_id, count in article_references.items():
        article_posts = df[df['article_id'] == article_id]
        article_data = {
            'article_id': article_id,
            'posts_count': count,
            'headline': None,
            'platforms': article_posts['platform'].value_counts().to_dict(),
            'avg_interactions': article_posts['interactions_count'].mean(),
            'total_interactions': article_posts['interactions_count'].sum(),
            'blackrock_mentions': article_posts['mentions_blackrock'].sum()
        }
        
        # Add headline from metadata if available
        if article_id in article_metadata_dict:
            article_data['headline'] = article_metadata_dict[article_id].url_headline_text
            article_data['url'] = article_metadata_dict[article_id].article_url
        
        articles_data.append(article_data)
    
    # Sort articles by total number of posts
    sorted_articles = sorted(articles_data, key=lambda x: x['posts_count'], reverse=True)
    top_articles = sorted_articles[:5]
    
    # Posts and interaction statistics by platform
    interactions_by_platform = df.groupby('platform')['interactions_count'].agg(['sum', 'mean']).to_dict()
    
    # Result summary
    results = {
        'total_posts': total_posts,
        'total_articles': total_articles,
        'platforms': platforms,
        'top_articles': top_articles,
        'interactions_by_platform': interactions_by_platform,
        'blackrock_mentions': df['mentions_blackrock'].sum()
    }
    
    return results

# Main function to fetch data, create DataFrame and analyze
def main(fetch_articles=False, config_file='config.json', use_proxy=False):
    """
    Main function to fetch and process social media and article data
    
    Args:
        fetch_articles: Whether to also fetch article data
        config_file: Path to the configuration file
        use_proxy: Whether to use corporate proxy for API requests
        
    Returns:
        DataFrame or tuple of DataFrames and metadata
    """
    try:
        # Log proxy usage
        if use_proxy:
            print("Main function using proxy: http://webproxy.blackrock.com:8080")
            
        # Load configuration
        print("Loading configuration...")
        config = load_config(config_file)
        
        # Initialize config.json if it doesn't exist
        if not os.path.exists(config_file) or not config:
            print("Initializing new configuration file...")
            config = {
                "vinesight": {
                    "username": "alexander.williams@blackrock.com",
                    "password": "BlackRock2024!",  # Note: Storing passwords in plain text is not secure
                    "cookie_expiry_days": 7,
                    "default_cookies": {
                        "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFsZXhhbmRlci53aWxsaWFtc0BibGFja3JvY2suY29tIiwiZXhwaXJlX3RpbWVzdGFtcCI6MTc0NTM5MjQwMC4zMTgwMDR9.vIbdEkAmELIh9rYxbSUcqgRHL1Q2HHcEXcG4HjFfT08",
                        "AMP_a5afb18362": "JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIyMTdiMjAyNC0wOGQxLTQyNDktYTdmYS1hODMyZmJjOWU2M2IlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJ1c2VyX2lkXzMwNCUyMiUyQyUyMnNlc3Npb25JZCUyMiUzQTE3NDI4MDAyMDUwNjAlMkMlMjJvcHRPdXQlMjIlM0FmYWxzZSUyQyUyMmxhc3RFdmVudFRpbWUlMjIlM0ExNzQyODAwNTU4MDc1JTJDJTIybGFzdEV2ZW50SWQlMjIlM0EyOCUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMCU3RA==",
                        "AMP_MKTG_a5afb18362": "JTdCJTdE"
                    },
                    "last_refreshed": datetime.now().isoformat()
                }
            }
            save_config(config, config_file)
        
        # Fetch social media posts data from API
        print("Fetching social media posts data from API...")
        raw_data = fetch_data_from_api(config, use_proxy=use_proxy)
        
        # Create dataclass instances
        print("Converting data to dataclass instances...")
        posts = convert_to_dataclass(raw_data)
        
        # Create the DataFrame
        print("Creating pandas DataFrame...")
        df = create_dataframe(posts)
        
        # Analyze the data
        print("Analyzing data...")
        analysis_results = analyze_data(df)
        
        # Print analysis results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Total posts: {analysis_results['total_posts']}")
        print(f"Platforms: {analysis_results['platforms']}")
        print(f"Average shares: {analysis_results['avg_shares']:.1f}")
        print(f"Average likes: {analysis_results['avg_likes']:.1f}")
        print(f"Average interactions: {analysis_results['avg_interactions']:.1f}")
        print(f"Posts mentioning BlackRock: {analysis_results['blackrock_mentions']}")
        print(f"Average bot percentage in retweets: {analysis_results['avg_bot_percentage']:.1f}%")
        
        print("\nTop posts by interactions:")
        for i, post in enumerate(analysis_results['top_posts'], 1):
            post_text = post['post_text']
            if len(post_text) > 100:
                post_text = post_text[:97] + "..."
            print(f"{i}. {post['poster_name']}: {post_text} ({post['interactions_count']} interactions)")
        
        # Optionally fetch and analyze article posts data
        if fetch_articles:
            print("\nFetching article posts data from API...")
            article_posts_data = fetch_article_posts(config, use_proxy=use_proxy)
            
            print("Processing article posts data...")
            article_posts, article_metadata = process_article_posts(article_posts_data)
            
            print("Creating article posts DataFrame...")
            article_posts_df = create_dataframe(article_posts)
            
            print("Analyzing article posts data...")
            article_analysis = analyze_article_posts(article_posts_df, article_metadata)
            
            print("\n=== ARTICLE POSTS ANALYSIS RESULTS ===")
            print(f"Total posts about articles: {article_analysis['total_posts']}")
            print(f"Unique articles referenced: {article_analysis['total_articles']}")
            print(f"Platform distribution: {article_analysis['platforms']}")
            print(f"Posts mentioning BlackRock: {article_analysis['blackrock_mentions']}")
            
            print("\nTop articles by number of posts:")
            for i, article in enumerate(article_analysis['top_articles'], 1):
                headline = article.get('headline', 'Untitled')
                if headline and len(headline) > 100:
                    headline = headline[:97] + "..."
                print(f"{i}. {headline} ({article['posts_count']} posts, {article['total_interactions']} total interactions)")
            
            # Return both DataFrames and the article metadata
            return df, article_posts_df, article_metadata
            
        # Return the DataFrame for further use
        return df
    
    except Exception as e:
        print(f"Error in main function: {e}")
        if fetch_articles:
            return pd.DataFrame(), pd.DataFrame(), {}
        return pd.DataFrame()

# Function to create or update the Vinesight section in config.json
def setup_vinesight_config(config_file='config.json', use_proxy=False):
    """
    Initialize or update Vinesight config in the config.json file
    
    Args:
        config_file: Path to the configuration file
        use_proxy: Whether to use corporate proxy for API requests
        
    Returns:
        dict: Updated configuration
    """
    config = load_config(config_file)
    
    # Check if config exists and has vinesight section
    if 'vinesight' not in config:
        print("Setting up Vinesight configuration...")
        
        # Get from user input or use defaults
        username = input("Enter Vinesight username (default: alexander.williams@blackrock.com): ") or "alexander.williams@blackrock.com"
        password = input("Enter Vinesight password (default: BlackRock2024!): ") or "BlackRock2024!"
        
        # Create vinesight config section
        config['vinesight'] = {
            "username": username,
            "password": password,
            "cookie_expiry_days": 7,
            "default_cookies": {
                "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFsZXhhbmRlci53aWxsaWFtc0BibGFja3JvY2suY29tIiwiZXhwaXJlX3RpbWVzdGFtcCI6MTc0NTM5MjQwMC4zMTgwMDR9.vIbdEkAmELIh9rYxbSUcqgRHL1Q2HHcEXcG4HjFfT08"
            },
            "last_refreshed": datetime.now().isoformat()
        }
        
        # Save the config
        save_config(config, config_file)
        print("Vinesight configuration has been set up.")
        
        # Try to refresh token immediately
        print("Attempting to refresh token...")
        refresh_result = refresh_vinesight_token(config, use_proxy=use_proxy)
        if refresh_result['success']:
            print("Token refreshed successfully.")
        else:
            print(f"Token refresh failed: {refresh_result.get('error', 'Unknown error')}")
    
    return config

# Execute the main function when the script is run directly (not when imported)
if __name__ == "__main__":
    # Setup Vinesight configuration if needed
    config_file = 'config.json'
    
    # Get proxy option from environment or command line args
    use_proxy = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'proxy':
        use_proxy = True
        print("Proxy mode enabled from command line argument")
    elif os.environ.get('USE_PROXY', '').lower() in ('true', '1', 'yes'):
        use_proxy = True
        print("Proxy mode enabled from environment variable")
    
    if not os.path.exists(config_file):
        setup_vinesight_config(config_file, use_proxy=use_proxy)
    
    # Set fetch_articles=True to also fetch and analyze article data
    result = main(fetch_articles=True, config_file=config_file, use_proxy=use_proxy)
    
    if isinstance(result, tuple) and len(result) == 3:
        df, article_posts_df, article_metadata = result
    else:
        df = result
        article_posts_df = pd.DataFrame()
        article_metadata = {}
    
    # Additional analysis examples for social media posts
    if not df.empty:
        print("\n=== ADDITIONAL ANALYSIS ===")
        
        # Platform distribution
        print("\nPlatform distribution:")
        print(df['platform'].value_counts())
        
        # User verification status
        print("\nVerified vs unverified accounts:")
        print(df['tweeter_is_verified'].value_counts())
        
        # Gender distribution (if available)
        if not df['percent_males'].isna().all():
            print("\nGender distribution in audience:")
            male_percent = df['percent_males'].mean()
            print(f"Male: {male_percent:.1f}%, Female: {(100-male_percent):.1f}%")
        
        # Language distribution
        print("\nLanguage distribution:")
        print(df['post_language'].value_counts())
        
        # Amplification analysis
        print("\nAverage amplification multiplier: {:.2f}".format(df['amplification_multiplier'].mean()))
    
    # Additional analysis for article posts data
    if not article_posts_df.empty:
        print("\n=== ADDITIONAL ARTICLE POSTS ANALYSIS ===")
        
        # Platform distribution for article posts
        print("\nPlatform distribution for article posts:")
        print(article_posts_df['platform'].value_counts())
        
        # Article posting dates
        article_posts_df['post_date_parsed'] = pd.to_datetime(article_posts_df['post_date'])
        print("\nArticle post date range:")
        print(f"Earliest: {article_posts_df['post_date_parsed'].min()}")
        print(f"Latest: {article_posts_df['post_date_parsed'].max()}")
        
        # Articles with most engagement
        print("\nArticles with most engagement:")
        article_engagement = article_posts_df.groupby('article_id')['interactions_count'].sum().sort_values(ascending=False)
        for article_id, interactions in article_engagement.head(3).items():
            headline = "Unknown"
            if article_id in article_metadata:
                headline = article_metadata[article_id].url_headline_text or "Unknown"
            if headline and len(headline) > 80:
                headline = headline[:77] + "..."
            print(f"- {headline} ({interactions} total interactions)")
        
        # Distribution of post types by article
        if len(article_metadata) > 0:
            print("\nPlatform distribution by top article:")
            top_article_id = article_engagement.index[0]
            top_article_posts = article_posts_df[article_posts_df['article_id'] == top_article_id]
            print(f"Article: {article_metadata.get(top_article_id, ArticleReference(top_article_id)).url_headline_text or 'Unknown'}")
            print(top_article_posts['platform'].value_counts())