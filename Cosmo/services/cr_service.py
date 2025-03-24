"""
CriticalMention API Client Service
---------------------------------
Enhanced client for retrieving and processing data from the CriticalMention API,
including full field extraction with all URL and media fields.
"""

import requests
import pandas as pd
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


@dataclass
class MediaMention:
    """Comprehensive dataclass representing a media mention from the CriticalMention API"""
    # Required fields
    uuid: str
    title: str
    channel_name: str
    text: str
    
    # Optional fields with proper typing
    # Basic identifiers
    id: Optional[Union[int, str]] = None
    
    # Content metadata
    program_type: Optional[str] = None
    affiliate: Optional[str] = None
    author: Optional[str] = None
    callsign: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    
    # Market information
    market_name: Optional[str] = None
    market_country: Optional[str] = None
    market_state: Optional[str] = None
    market_id: Optional[Union[int, str]] = None
    market_rank: Optional[Union[int, str]] = None
    
    # Timing information
    time: Optional[str] = None
    timestamp: Optional[str] = None
    local_time: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[int] = None
    broadcast_tz: Optional[str] = None
    timezone: Optional[str] = None
    
    # Analytics
    sentiment: Optional[float] = None
    audience: Optional[int] = None
    publicity: Optional[Union[int, float]] = None
    local_publicity: Optional[Union[int, float]] = None
    local_audience: Optional[Union[int, float]] = None
    
    # Media URLs
    thumbnail: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    media_url: Optional[str] = None
    media_url_no_highlight: Optional[str] = None
    relative_media_url: Optional[str] = None
    legacy_media: Optional[str] = None
    media: Optional[str] = None
    content_url: Optional[str] = None
    outlet_logo_url: Optional[str] = None
    
    # IDs and references
    channel_id: Optional[Union[int, str]] = None
    program_id: Optional[str] = None
    data_source_id: Optional[Union[int, str]] = None
    alert_id: Optional[Union[int, str]] = None
    alert_name: Optional[str] = None
    cm_outlet_id: Optional[str] = None
    media_outlet_id: Optional[str] = None
    media_outlet_id_channel: Optional[Union[int, str]] = None
    media_outlet_id_program: Optional[Union[int, str]] = None
    
    # Additional fields
    source_type: Optional[str] = None
    post_type: Optional[str] = None
    cc_text: Optional[str] = None
    cc_text_hi: Optional[str] = None
    cc_text_hi_words: Optional[str] = None
    alias: Optional[str] = None
    mime_type: Optional[str] = None
    protocol: Optional[str] = None
    currency_code: Optional[str] = None
    text_only: Optional[bool] = None
    copyright: Optional[str] = None
    topics: Optional[Any] = None
    author_id: Optional[str] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'MediaMention':
        """
        Create a MediaMention instance from API data, dynamically capturing all fields.
        
        Args:
            data: Dictionary containing API response for a single mention
            
        Returns:
            MediaMention instance with all available fields populated
        """
        # Extract the four required fields with fallbacks to prevent errors
        required_fields = {
            'uuid': data.get('uuid', ''),
            'title': data.get('title', ''),
            'channel_name': data.get('channelName', data.get('channel_name', '')),
            'text': data.get('text', '')
        }
        
        # Create instance with required fields
        instance = cls(**required_fields)
        
        # Special handling for fields with naming differences
        if 'channelName' in data and 'channel_name' not in data:
            data['channel_name'] = data['channelName']
        
        # Dynamically set all other fields from the data dictionary
        for key, value in data.items():
            if key not in required_fields and hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance


class CriticalMentionClient:
    """Enhanced client for retrieving and processing data from CriticalMention API"""
    
    def __init__(self, auth_cookie: str, use_proxy: bool = False):
        self.auth_cookie = auth_cookie
        self.base_url = "https://app.criticalmention.com/allmedia/dashboard/content"
        self.mentions = []
        self.df = None
        self.url_fields = []
        self.use_proxy = use_proxy
        self.proxy_url = "http://webproxy.blackrock.com:8080"
    
    def fetch_mentions(self, start_date: str, end_date: str, limit: int = 500, use_proxy: bool = None) -> List[MediaMention]:
        """
        Fetch mentions from the CriticalMention API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of mentions to fetch
            use_proxy: Whether to use a proxy (overrides instance setting if provided)
            
        Returns:
            List of MediaMention objects
        """
        # Use the provided proxy setting if given, otherwise use the instance setting
        use_proxy_for_request = use_proxy if use_proxy is not None else self.use_proxy
        
        # Parse base URL to extract any query parameters
        base_url = self.base_url
        keyword_param = ""
        
        # Check if there's a keyword parameter in the base_url
        if "?keyword=" in base_url:
            parts = base_url.split("?keyword=")
            base_url = parts[0]
            keyword_param = parts[1]
        
        querystring = {
            "limit": str(limit),
            "start": start_date,
            "end": end_date,
            "ascdesc": "desc",
            "page": "1",
            "timezone": "America/New_York",
            "data_source_ids": "1,5,7",  # TV, Radio, Online News
            "sort_order": "timestamp",
            "updatedMapping": "true"
        }
        
        # Add keyword from base_url if it exists
        if keyword_param:
            querystring["keyword"] = keyword_param
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://app.criticalmention.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Cookie": self.auth_cookie,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers"
        }
        
        # Setup proxies if enabled
        proxies = None
        if use_proxy_for_request:
            proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            print(f"Using proxy: {self.proxy_url}")
        
        try:
            # Pass proxies to requests.get if they're configured
            response = requests.get(
                base_url, 
                headers=headers, 
                params=querystring,
                proxies=proxies
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' in data and 'clips' in data['results']:
                self.mentions = [MediaMention.from_api_data(clip) for clip in data['results']['clips']]
                return self.mentions
            else:
                print("No clips found in API response")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return []
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert mentions to a pandas DataFrame with all fields.
        
        Returns:
            DataFrame containing all mention data
        """
        if not self.mentions:
            print("No mentions to convert to DataFrame")
            return pd.DataFrame()
        
        # Convert mentions to list of dictionaries
        mentions_data = []
        for mention in self.mentions:
            # Convert to dictionary
            mention_dict = vars(mention)
            
            # Special handling for contacts field (if it's a list of dicts)
            if 'contacts' in mention_dict and isinstance(mention_dict['contacts'], list):
                contacts = mention_dict['contacts']
                if contacts:
                    # Create a string summary of contacts
                    contact_summary = []
                    for contact in contacts:
                        if isinstance(contact, dict):
                            name_parts = []
                            if 'first_name' in contact and contact['first_name']:
                                name_parts.append(contact['first_name'])
                            if 'last_name' in contact and contact['last_name']:
                                name_parts.append(contact['last_name'])
                            
                            if name_parts:
                                contact_name = " ".join(name_parts)
                                if 'roles' in contact and contact['roles']:
                                    roles = ", ".join(contact['roles'])
                                    contact_summary.append(f"{contact_name} ({roles})")
                                else:
                                    contact_summary.append(contact_name)
                    
                    if contact_summary:
                        mention_dict['contacts_summary'] = "; ".join(contact_summary)
            
            mentions_data.append(mention_dict)
        
        # Create DataFrame
        self.df = pd.DataFrame(mentions_data)
        
        # Identify URL-related fields for convenience
        self.url_fields = [col for col in self.df.columns if 
                         ('url' in col.lower() or 
                          'media' in col.lower() or 
                          'thumbnail' in col.lower() or 
                          'legacy_media' in col.lower()) and 
                         not col.endswith('_id')]
        
        return self.df
    
    def process_json_data(self, json_data: Union[str, Dict], use_proxy: bool = None) -> pd.DataFrame:
        """
        Process raw JSON data from CriticalMention API directly into a DataFrame.
        
        Args:
            json_data: JSON data either as a string or parsed dictionary
            use_proxy: Whether to use a proxy (for future API calls)
            
        Returns:
            DataFrame containing all mention data
        """
        # Update proxy setting if provided
        if use_proxy is not None:
            self.use_proxy = use_proxy
            
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                return pd.DataFrame()
        else:
            data = json_data
            
        if 'results' in data and 'clips' in data['results']:
            self.mentions = [MediaMention.from_api_data(clip) for clip in data['results']['clips']]
            return self.to_dataframe()
        else:
            print("No clips found in JSON data")
            return pd.DataFrame()
    
    def analyze_sentiment(self) -> Dict[str, Any]:
        """
        Analyze sentiment distribution across mentions.
        
        Returns:
            Dictionary with sentiment analysis metrics
        """
        if self.df is None:
            self.to_dataframe()
        
        if self.df.empty or 'sentiment' not in self.df.columns:
            return {}
        
        return {
            'average_sentiment': self.df['sentiment'].mean(),
            'positive_mentions': len(self.df[self.df['sentiment'] > 0]),
            'negative_mentions': len(self.df[self.df['sentiment'] < 0]),
            'neutral_mentions': len(self.df[self.df['sentiment'] == 0])
        }
    
    def channel_distribution(self) -> pd.Series:
        """
        Get distribution of mentions by channel.
        
        Returns:
            Series with channel counts
        """
        if self.df is None:
            self.to_dataframe()
        
        if self.df.empty or 'channel_name' not in self.df.columns:
            return pd.Series()
        
        return self.df['channel_name'].value_counts()
    
    def get_url_fields(self) -> pd.DataFrame:
        """
        Get a DataFrame with only identification and URL-related fields.
        
        Returns:
            DataFrame with ID and URL fields
        """
        if self.df is None:
            self.to_dataframe()
        
        if self.df.empty:
            return pd.DataFrame()
        
        # Include identifier columns plus URL fields
        id_columns = ['uuid', 'title', 'channel_name', 'time', 'timestamp']
        id_columns = [col for col in id_columns if col in self.df.columns]
        
        selected_columns = id_columns + self.url_fields
        
        return self.df[selected_columns]
    
    def save_to_csv(self, filename: str, include_only_urls: bool = False) -> None:
        """
        Save mentions to a CSV file.
        
        Args:
            filename: Output CSV filename
            include_only_urls: If True, saves only ID and URL fields
        """
        if self.df is None:
            self.to_dataframe()
        
        if self.df.empty:
            print("No data to save")
            return
        
        # Choose which DataFrame to save
        if include_only_urls:
            url_df = self.get_url_fields()
            url_df.to_csv(filename, index=False)
            print(f"URL data saved to {filename} ({len(url_df.columns)} columns)")
        else:
            self.df.to_csv(filename, index=False)
            print(f"Data saved to {filename} ({len(self.df.columns)} columns)")