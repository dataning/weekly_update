import requests
import json
import pandas as pd
import base64
import time
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

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

@dataclass
class ArticleReference:
    """Metadata about articles extracted from posts that reference them"""
    article_id: str
    article_url: Optional[str] = None
    url_headline_text: Optional[str] = None
    url_description: Optional[str] = None
    url_preview_img_url: Optional[str] = None
    # Additional fields can be added as needed


# ---------------------------------------------------------------------------
#                     CONFIGURATION LOAD/SAVE FUNCTIONS
# ---------------------------------------------------------------------------

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

def save_config(config, config_file='config.json'):
    """Save configuration to config.json file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False


# ---------------------------------------------------------------------------
#                              AUTH/TOKEN LOGIC
# ---------------------------------------------------------------------------

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
    payload = {"username": username, "password": password}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0"
    }
    
    # Setup proxies if enabled
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {'http': proxy_url, 'https': proxy_url}
        print(f"Using proxy: {proxy_url} for login")
    
    try:
        response = requests.post(login_url, json=payload, headers=headers, proxies=proxies)
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
        return {'success': False, 'error': 'Vinesight credentials not found'}
    
    # Get current token from 'session' cookie
    current_token = None
    if 'default_cookies' in vinesight_config and 'session' in vinesight_config['default_cookies']:
        current_token = vinesight_config['default_cookies']['session']
    
    # Check if token is expired
    if current_token and not is_token_expired(current_token):
        return {'success': True, 'message': 'Token still valid'}
    
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
    
    return {'success': True, 'message': 'Token refreshed successfully'}

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


# ---------------------------------------------------------------------------
#                            MAIN DATA FETCH LOGIC
# ---------------------------------------------------------------------------

def load_data_from_file(file_path='paste.txt'):
    """
    Fallback function to load data from a local file
    if the API fetch fails.
    """
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

def fetch_data_from_api(config=None, use_proxy=False, max_pages=10, limit_per_page=100):
    """
    Fetch data from Vinesight API using credentials from config with pagination
    
    Args:
        config: Configuration dictionary
        use_proxy: Whether to use corporate proxy
        max_pages: Maximum number of pages to fetch (to avoid infinite loops)
        limit_per_page: Number of results per page
        
    Returns:
        list: Raw API response data
    """
    if config is None:
        config = load_config()
    
    base_url = "https://dash-api.vinesight.com/home/get_post_center_posts"
    
    all_results = []
    current_page = 0
    
    while current_page < max_pages:
        offset = current_page * limit_per_page
        querystring = {
            "offset": str(offset),
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
            "platform": [
                "FACEBOOK","REDDIT","INSTAGRAM","TWITTER","TELEGRAM","TIKTOK",
                "FCHAN","TRUTHSOCIAL","GAB","GETTR","VK"
            ],
            "url_type": "",
            "limit": str(limit_per_page)
        }
        payload = ""
        headers = get_vinesight_headers(config, use_proxy=use_proxy)
        
        # Setup proxies if enabled
        proxies = None
        if use_proxy:
            proxy_url = "http://webproxy.blackrock.com:8080"
            proxies = {'http': proxy_url, 'https': proxy_url}
            print(f"Using proxy: {proxy_url} for API request (page {current_page+1})")
        
        try:
            print(f"Fetching page {current_page+1} (offset {offset})...")
            response = requests.request(
                "GET", 
                base_url, 
                data=payload, 
                headers=headers, 
                params=querystring,
                proxies=proxies
            )
            response.raise_for_status()  # Raise exception for HTTP errors
            
            page_data = json.loads(response.text)
            
            # If no data or fewer than limit, assume last page
            if not page_data or (isinstance(page_data, list) and len(page_data) < limit_per_page):
                print(f"Reached end of data at page {current_page+1}")
                all_results.extend(page_data)
                break
                
            all_results.extend(page_data)
            print(f"Retrieved {len(page_data)} posts from page {current_page+1}")
            
            # Update cookies if they've changed
            if response.cookies:
                if 'vinesight' not in config:
                    config['vinesight'] = {}
                if 'default_cookies' not in config['vinesight']:
                    config['vinesight']['default_cookies'] = {}
                
                # Update with new cookies
                for key, value in response.cookies.items():
                    config['vinesight']['default_cookies'][key] = value
                save_config(config)
            
            current_page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"API request error on page {current_page+1}: {e}")
            # Return partial data or fallback
            if all_results:
                break
            else:
                return load_data_from_file()
    
    print(f"Total posts retrieved: {len(all_results)}")
    return all_results

def fetch_article_posts_batch(config, article_ids, use_proxy=False):
    """
    Fetch article posts for a specific batch of article IDs
    """
    if not article_ids:
        return []
        
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
        "article_id": article_ids  # Use the provided article IDs
    }
    payload = ""
    headers = get_vinesight_headers(config, use_proxy=use_proxy)
    
    # Setup proxies if enabled
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {'http': proxy_url, 'https': proxy_url}
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
        response.raise_for_status()
        
        data = json.loads(response.text)
        
        # Extract posts array depending on response format
        if isinstance(data, dict) and 'posts' in data:
            return data['posts']
        elif isinstance(data, list):
            return data
        else:
            print(f"Unexpected response format: {type(data)}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Article API request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.text[:200]}...")
        return []

def fetch_all_article_posts(config=None, use_proxy=False, max_batches=10):
    """
    Two-step process:
    1. Fetch main posts to discover article_ids
    2. Fetch article posts in batches
    """
    if config is None:
        config = load_config()
    
    print("Step 1: Fetching posts with article references...")
    all_posts = fetch_data_from_api(config, use_proxy=use_proxy, max_pages=20)
    
    article_ids = set()
    for post in all_posts:
        if 'article_id' in post and post['article_id']:
            article_ids.add(post['article_id'])
    
    print(f"Found {len(article_ids)} unique article IDs in posts")
    article_ids = list(article_ids)
    
    print("Step 2: Fetching article posts for these IDs...")
    all_article_posts = []
    batch_size = 10
    num_batches = min(max_batches, (len(article_ids) + batch_size - 1) // batch_size)
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(article_ids))
        batch_ids = article_ids[start_idx:end_idx]
        
        print(f"Fetching batch {batch_num+1}/{num_batches} with {len(batch_ids)} article IDs...")
        batch_posts = fetch_article_posts_batch(config, batch_ids, use_proxy)
        
        if batch_posts:
            all_article_posts.extend(batch_posts)
            print(f"Retrieved {len(batch_posts)} posts for this batch")
        else:
            print(f"No posts retrieved for batch {batch_num+1}")
    
    print(f"Total article posts retrieved: {len(all_article_posts)}")
    return all_article_posts


# ---------------------------------------------------------------------------
#                             PROCESSING FUNCTIONS
# ---------------------------------------------------------------------------

def fetch_article_posts(config=None, use_proxy=False):
    """
    Original fallback to fetch article posts with hardcoded IDs
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
        "Cookie": "AMP_a5afb18362=...; session=eyJhbGc...",
        "Origin": "https://dash.vinesight.com",
        "Referer": "https://dash.vinesight.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0"
    }
    
    proxies = None
    if use_proxy:
        proxy_url = "http://webproxy.blackrock.com:8080"
        proxies = {'http': proxy_url, 'https': proxy_url}
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
        response.raise_for_status()
        
        data = json.loads(response.text)
        print(f"Response type: {type(data)}")
        
        if isinstance(data, dict) and 'posts' in data:
            print(f"Found 'posts' key in response, with {len(data['posts'])} posts")
            return data['posts']
        elif isinstance(data, list):
            print(f"Response is a list with {len(data)} items")
            return data
        else:
            print(f"Unexpected response format: {type(data)}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Article API request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {response.text[:200]}...")
        return []

def convert_to_dataclass(data):
    """Convert raw JSON data to a list of SocialMediaPost dataclass instances."""
    posts = []
    for item in data:
        try:
            post = SocialMediaPost(**item)
            posts.append(post)
        except Exception as e:
            print(f"Error converting item to dataclass: {e}")
    return posts

def create_dataframe(posts):
    """Convert a list of SocialMediaPost objects into a pandas DataFrame."""
    return pd.DataFrame([vars(post) for post in posts])

def analyze_data(df):
    """Basic analysis of social media posts."""
    if df.empty:
        return "No data to analyze"
    
    total_posts = len(df)
    platforms = df['platform'].value_counts().to_dict() if 'platform' in df.columns else {}
    avg_shares = df['shares_count'].mean() if 'shares_count' in df.columns else 0
    avg_likes = df['likes_count'].mean() if 'likes_count' in df.columns else 0
    avg_interactions = df['interactions_count'].mean() if 'interactions_count' in df.columns else 0
    
    # Add a column for 'mentions_blackrock'
    df['mentions_blackrock'] = df['post_text'].str.lower().str.contains('blackrock') if 'post_text' in df.columns else False
    blackrock_mentions = df['mentions_blackrock'].sum() if 'mentions_blackrock' in df.columns else 0
    
    top_posts = []
    if 'interactions_count' in df.columns:
        top_posts = df.sort_values('interactions_count', ascending=False).head(5)
        top_posts = top_posts[['poster_name', 'post_text', 'interactions_count']].to_dict('records')
    
    avg_bot_percentage = df['percent_bots_retweets'].mean() if 'percent_bots_retweets' in df.columns else 0
    
    return {
        'total_posts': total_posts,
        'platforms': platforms,
        'avg_shares': avg_shares,
        'avg_likes': avg_likes,
        'avg_interactions': avg_interactions,
        'blackrock_mentions': blackrock_mentions,
        'top_posts': top_posts,
        'avg_bot_percentage': avg_bot_percentage
    }

def process_article_posts(data):
    """
    Process article posts data to extract both posts and article metadata
    """
    posts = []
    article_metadata = {}
    
    print(f"Processing {len(data) if isinstance(data, list) else 'non-list'} article data items")
    if not isinstance(data, list):
        if isinstance(data, dict) and 'posts' in data:
            data = data['posts']
            print(f"Extracted 'posts' array with {len(data)} items")
        else:
            print(f"Unable to process data of type {type(data)}")
            return [], {}
    
    for item in data:
        try:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    print(f"Could not parse item as JSON")
                    continue
            
            import inspect
            valid_fields = set(inspect.signature(SocialMediaPost.__init__).parameters.keys()) - {'self'}
            filtered_item = {k: v for k, v in item.items() if k in valid_fields}
            
            post = SocialMediaPost(**filtered_item)
            posts.append(post)
            
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

def analyze_article_posts(df, article_metadata_dict):
    """
    Analyze article posts data with proper handling for empty DataFrames
    """
    if df.empty:
        print("Warning: No article posts data available to analyze")
        return {
            'total_posts': 0,
            'total_articles': 0,
            'platforms': {},
            'top_articles': [],
            'interactions_by_platform': {},
            'blackrock_mentions': 0
        }
    
    total_posts = len(df)
    platforms = df['platform'].value_counts().to_dict() if 'platform' in df.columns else {}
    article_references = df['article_id'].value_counts().to_dict() if 'article_id' in df.columns else {}
    total_articles = len(article_references)
    
    df['mentions_blackrock'] = df['post_text'].str.lower().str.contains('blackrock') if 'post_text' in df.columns else False
    
    articles_data = []
    for article_id, count in article_references.items():
        article_posts = df[df['article_id'] == article_id]
        article_data = {
            'article_id': article_id,
            'posts_count': count,
            'headline': None,
            'platforms': article_posts['platform'].value_counts().to_dict() if 'platform' in article_posts.columns else {},
            'avg_interactions': article_posts['interactions_count'].mean() if 'interactions_count' in article_posts.columns else 0,
            'total_interactions': article_posts['interactions_count'].sum() if 'interactions_count' in article_posts.columns else 0,
            'blackrock_mentions': article_posts['mentions_blackrock'].sum()
        }
        if article_id in article_metadata_dict:
            article_data['headline'] = article_metadata_dict[article_id].url_headline_text
            article_data['url'] = article_metadata_dict[article_id].article_url
        
        articles_data.append(article_data)
    
    sorted_articles = sorted(articles_data, key=lambda x: x['posts_count'], reverse=True)
    top_articles = sorted_articles[:5] if sorted_articles else []
    
    interactions_by_platform = {}
    if 'platform' in df.columns and 'interactions_count' in df.columns and not df.empty:
        # Group and compute sum, mean
        group_result = df.groupby('platform')['interactions_count'].agg(['sum', 'mean'])
        interactions_by_platform = group_result.to_dict()
    
    return {
        'total_posts': total_posts,
        'total_articles': total_articles,
        'platforms': platforms,
        'top_articles': top_articles,
        'interactions_by_platform': interactions_by_platform,
        'blackrock_mentions': df['mentions_blackrock'].sum()
    }


# ---------------------------------------------------------------------------
#                              MAIN SCRIPT LOGIC
# ---------------------------------------------------------------------------

def main(fetch_articles=False, config_file='config.json', use_proxy=False, max_pages=10):
    """
    Main function to fetch and process social media and article data
    
    Args:
        fetch_articles: Whether to also fetch article data
        config_file: Path to the configuration file
        use_proxy: Whether to use corporate proxy for API requests
        max_pages: Maximum number of pages to fetch per API call
        
    Returns:
        DataFrame or tuple of DataFrames and metadata
    """
    try:
        if use_proxy:
            print("Main function using proxy: http://webproxy.blackrock.com:8080")
        
        print("Loading configuration...")
        config = load_config(config_file)
        
        # If config doesn't exist or is empty, create a default
        if not os.path.exists(config_file) or not config:
            print("Initializing new configuration file...")
            config = {
                "vinesight": {
                    "username": "alexander.williams@blackrock.com",
                    "password": "BlackRock2024!",
                    "cookie_expiry_days": 7,
                    "default_cookies": {
                        "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    "last_refreshed": datetime.now().isoformat()
                }
            }
            save_config(config, config_file)
        
        print("Fetching social media posts data from API...")
        raw_data = fetch_data_from_api(config, use_proxy=use_proxy, max_pages=max_pages)
        
        print("Converting data to dataclass instances...")
        posts = convert_to_dataclass(raw_data)
        
        print("Creating pandas DataFrame...")
        df = create_dataframe(posts)
        
        print("Analyzing data...")
        analysis_results = analyze_data(df)
        
        print("\n=== ANALYSIS RESULTS ===")
        if isinstance(analysis_results, dict):
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
        else:
            print(analysis_results)  # In case it's just a string "No data to analyze"
        
        # Optionally fetch article data
        if fetch_articles:
            print("\nFetching article posts data from API...")
            article_posts_df = pd.DataFrame()
            article_metadata = {}
            
            try:
                article_posts_data = fetch_all_article_posts(config, use_proxy=use_proxy)
                if not article_posts_data:
                    # Fallback to direct fetch with default IDs
                    print("No article posts found via two-step approach, trying fallback with default IDs...")
                    article_posts_data = fetch_article_posts(config, use_proxy=use_proxy)
                
                print(f"Processing article posts data ({len(article_posts_data)} items)...")
                if article_posts_data:
                    article_posts, article_metadata = process_article_posts(article_posts_data)
                    article_posts_df = create_dataframe(article_posts)
                else:
                    print("No article posts data available after all attempts.")
            except Exception as e:
                print(f"Error fetching or processing article posts: {e}")
                article_posts_df = pd.DataFrame()
                article_metadata = {}
            
            if article_posts_df.empty:
                print("Warning: Article posts DataFrame is empty.")
            else:
                print(f"Article posts DataFrame created with {len(article_posts_df)} rows.")
            
            print("Analyzing article posts data...")
            article_analysis = analyze_article_posts(article_posts_df, article_metadata)
            
            print("\n=== ARTICLE POSTS ANALYSIS RESULTS ===")
            print(f"Total posts about articles: {article_analysis['total_posts']}")
            print(f"Unique articles referenced: {article_analysis['total_articles']}")
            if article_analysis['platforms']:
                print(f"Platform distribution: {article_analysis['platforms']}")
            else:
                print("Platform distribution: No data available")
            print(f"Posts mentioning BlackRock: {article_analysis['blackrock_mentions']}")
            
            if article_analysis['top_articles']:
                print("\nTop articles by number of posts:")
                for i, article in enumerate(article_analysis['top_articles'], 1):
                    headline = article.get('headline', 'Untitled')
                    if headline and len(headline) > 100:
                        headline = headline[:97] + "..."
                    print(f"{i}. {headline} ({article['posts_count']} posts, {article['total_interactions']} total interactions)")
            else:
                print("\nNo top articles available")
            
            # Return both DataFrames and the article metadata
            return df, article_posts_df, article_metadata
        
        return df
    
    except Exception as e:
        import traceback
        print(f"Error in main function: {e}")
        print(traceback.format_exc())
        if fetch_articles:
            return pd.DataFrame(), pd.DataFrame(), {}
        return pd.DataFrame()

def setup_vinesight_config(config_file='config.json', use_proxy=False):
    """
    Initialize or update Vinesight config in the config.json file
    """
    config = load_config(config_file)
    
    if 'vinesight' not in config:
        print("Setting up Vinesight configuration...")
        username = input("Enter Vinesight username (default: alexander.williams@blackrock.com): ") or "alexander.williams@blackrock.com"
        password = input("Enter Vinesight password (default: BlackRock2024!): ") or "BlackRock2024!"
        
        config['vinesight'] = {
            "username": username,
            "password": password,
            "cookie_expiry_days": 7,
            "default_cookies": {
                "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            },
            "last_refreshed": datetime.now().isoformat()
        }
        save_config(config, config_file)
        
        print("Vinesight configuration has been set up.")
        print("Attempting to refresh token...")
        refresh_result = refresh_vinesight_token(config, use_proxy=use_proxy)
        if refresh_result['success']:
            print("Token refreshed successfully.")
        else:
            print(f"Token refresh failed: {refresh_result.get('error', 'Unknown error')}")
    
    return config


# ---------------------------------------------------------------------------
#                          ENTRY POINT / EXECUTION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config_file = 'config.json'
    
    # Determine proxy usage
    use_proxy = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'proxy':
        use_proxy = True
        print("Proxy mode enabled from command line argument")
    elif os.environ.get('USE_PROXY', '').lower() in ('true', '1', 'yes'):
        use_proxy = True
        print("Proxy mode enabled from environment variable")
    
    if not os.path.exists(config_file):
        setup_vinesight_config(config_file, use_proxy=use_proxy)
    
    # Fetch both social posts and article posts
    result = main(fetch_articles=True, config_file=config_file, use_proxy=use_proxy, max_pages=20)
    
    # Unpack the result
    if isinstance(result, tuple) and len(result) == 3:
        df, article_posts_df, article_metadata = result
    else:
        df = result
        article_posts_df = pd.DataFrame()
        article_metadata = {}
    
    # Additional analysis examples for social media posts
    if not df.empty:
        print("\n=== ADDITIONAL ANALYSIS ===")
        
        print("\nPlatform distribution:")
        if 'platform' in df.columns:
            print(df['platform'].value_counts())
        
        print("\nVerified vs unverified accounts:")
        if 'tweeter_is_verified' in df.columns:
            print(df['tweeter_is_verified'].value_counts(dropna=False))
        
        if 'percent_males' in df.columns and not df['percent_males'].isna().all():
            print("\nGender distribution in audience (avg across posts):")
            male_percent = df['percent_males'].mean()
            print(f"Male: {male_percent:.1f}%, Female: {(100-male_percent):.1f}%")
        
        if 'post_language' in df.columns:
            print("\nLanguage distribution:")
            print(df['post_language'].value_counts())
        
        if 'amplification_multiplier' in df.columns:
            avg_amp = df['amplification_multiplier'].mean()
            print(f"\nAverage amplification multiplier: {avg_amp:.2f}")
    
    # Additional analysis for article posts data
    if not article_posts_df.empty:
        print("\n=== ADDITIONAL ARTICLE POSTS ANALYSIS ===")
        
        if 'platform' in article_posts_df.columns:
            print("\nPlatform distribution for article posts:")
            print(article_posts_df['platform'].value_counts())
        
        if 'post_date' in article_posts_df.columns:
            print("\nArticle post date range:")
            article_posts_df['post_date_parsed'] = pd.to_datetime(article_posts_df['post_date'], errors='coerce')
            print(f"Earliest: {article_posts_df['post_date_parsed'].min()}")
            print(f"Latest:   {article_posts_df['post_date_parsed'].max()}")
        
        if 'interactions_count' in article_posts_df.columns and 'article_id' in article_posts_df.columns:
            print("\nArticles with most engagement:")
            article_engagement = (
                article_posts_df.groupby('article_id')['interactions_count']
                .sum()
                .sort_values(ascending=False)
            )
            for article_id, interactions in article_engagement.head(3).items():
                headline = "Unknown"
                if article_id in article_metadata:
                    headline = article_metadata[article_id].url_headline_text or "Unknown"
                if headline and len(headline) > 80:
                    headline = headline[:77] + "..."
                print(f"- {headline} ({interactions} total interactions)")
            
            # Distribution of post platforms for top article
            top_article_id = article_engagement.index[0]
            top_article_posts = article_posts_df[article_posts_df['article_id'] == top_article_id]
            print(f"\nPlatform distribution for top-article ({top_article_id}):")
            if 'platform' in top_article_posts.columns:
                print(top_article_posts['platform'].value_counts())
    
    # -----------------------------------------------------------------------
    #    >>>>>  HERE ARE THE LAST FEW LINES MERGED INTO THE MAIN CODE  <<<<<
    # -----------------------------------------------------------------------
    
    # Convert 'retweeters_count_by_country' to string if it exists
    if not df.empty and 'retweeters_count_by_country' in df.columns:
        df['retweeters_count_by_country'] = df['retweeters_count_by_country'].astype(str)
    
    # Generate a timestamp string (e.g., 2025-04-06_14)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H')
    
    # Construct the output filename with timestamp
    output_filename = f"Social_daily_{timestamp}.parquet"
    
    # Save the dataframe as a Parquet file
    if not df.empty:
        df.to_parquet(output_filename)
        print(f"\nDataFrame saved to '{output_filename}' with {len(df)} rows.")
    else:
        print("\nNo data in df to save. Skipping Parquet write.")