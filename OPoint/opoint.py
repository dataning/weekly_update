import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import nest_asyncio

# Apply the nested asyncio fix for Jupyter
nest_asyncio.apply()

async def get_company_news_complete(company, from_timestamp, session, headers, base_url, proxy=None, initial_limit=500):
    """
    Get all news for a specific company since the from_timestamp
    Makes multiple requests if necessary to ensure ALL articles are retrieved
    
    Parameters:
    -----------
    company : str
        Company name to search for
    from_timestamp : int
        Unix timestamp to search from
    session : aiohttp.ClientSession
        Active client session for making requests
    headers : dict
        API request headers
    base_url : str
        API base URL
    proxy : str, optional
        Proxy server to use
    initial_limit : int, default 500
        Initial number of articles to request
        
    Returns:
    --------
    list
        List of processed article dictionaries
    """
    # First attempt - try with initial limit
    payload = {
        "searchterm": company,
        "params": {
            "requestedarticles": initial_limit,
            "from": from_timestamp,
            "main": {
                "header": 1,
                "summary": 1,
                "text": 1
            },
            "sortby": "date desc"
        }
    }
    
    print(f"\nSearching for {company} news...")
    
    try:
        async with session.post(
            base_url,
            json=payload,
            headers=headers,
            timeout=60,  # Long timeout
            proxy=proxy
        ) as response:
            response.raise_for_status()
            search_results = await response.json()
            
            # Get total number of results available
            total_found = search_results.get('searchresult', {}).get('hits', 0)
            documents = search_results.get('searchresult', {}).get('document', [])
            
            print(f"{company}: Total articles found: {total_found}")
            print(f"{company}: Articles retrieved in first batch: {len(documents)}")
            
            # If we got fewer results than total, we need more requests
            if len(documents) < total_found and documents:
                # We'll need to make more requests to get everything
                all_documents = documents.copy()
                
                try:
                    # Find the timestamp of the oldest article in the current batch
                    oldest_timestamp = None
                    for doc in documents:
                        if 'timestampinsec' in doc:
                            ts = int(doc['timestampinsec'])
                            if oldest_timestamp is None or ts < oldest_timestamp:
                                oldest_timestamp = ts
                    
                    if oldest_timestamp is not None and oldest_timestamp > from_timestamp:
                        print(f"{company}: Oldest article timestamp in first batch: {datetime.fromtimestamp(oldest_timestamp)}")
                        print(f"{company}: Getting remaining articles with a second request...")
                        
                        # Create a new payload for the older articles
                        second_payload = {
                            "searchterm": company,
                            "params": {
                                "requestedarticles": total_found - len(documents),  # Adjust limit for the rest
                                "from": from_timestamp,  # Original start time
                                "to": oldest_timestamp,  # Up to the oldest article we already have
                                "main": {
                                    "header": 1,
                                    "summary": 1,
                                    "text": 1
                                },
                                "sortby": "date desc"
                            }
                        }
                        
                        async with session.post(
                            base_url,
                            json=second_payload,
                            headers=headers,
                            timeout=60,  # Long timeout
                            proxy=proxy
                        ) as second_response:
                            second_response.raise_for_status()
                            second_results = await second_response.json()
                            second_documents = second_results.get('searchresult', {}).get('document', [])
                            
                            print(f"{company}: Articles retrieved in second batch: {len(second_documents)}")
                            
                            # Add these to our collection
                            all_documents.extend(second_documents)
                
                except (ValueError, TypeError, KeyError) as e:
                    print(f"{company}: Error processing timestamps: {e}")
                    # Continue with what we have
            else:
                # We got everything in one go
                all_documents = documents
            
            # Process all documents
            results_list = []
            for doc in all_documents:
                # Flatten metadata using json_normalize
                flat_metadata = pd.json_normalize(doc, sep='_')
                if not flat_metadata.empty:
                    flat_metadata_dict = flat_metadata.to_dict(orient='records')[0]
                    flat_metadata_dict['search_term'] = company  # Add search term
                    
                    # Add a datetime column for easier filtering if timestamp exists
                    if 'timestampinsec' in flat_metadata_dict:
                        try:
                            timestamp = int(flat_metadata_dict['timestampinsec'])
                            flat_metadata_dict['datetime'] = datetime.fromtimestamp(timestamp)
                        except (ValueError, TypeError):
                            flat_metadata_dict['datetime'] = None
                            
                    results_list.append(flat_metadata_dict)
            
            print(f"{company}: Retrieved {len(results_list)} total articles")
            return results_list
            
    except Exception as e:
        print(f"{company}: Error during search: {str(e)}")
        return []


async def get_all_companies_news(companies, hours_back=24, initial_limit=500, use_proxy=False):
    """
    Get ALL news for multiple companies from the past specified hours
    
    Parameters:
    -----------
    companies : list
        List of company names to search for
    hours_back : int, default 24
        Number of hours to look back
    initial_limit : int, default 500
        Initial number of articles to request per company
    use_proxy : bool, default False
        Whether to use a proxy
        
    Returns:
    --------
    pandas.DataFrame
        Complete DataFrame containing all news articles from the specified companies and time period
    """
    # Define constants
    token = "9ef7b1d41d41e23ec75bc4ae447567936f08cc6d"
    base_url = "https://api.opoint.com/search/"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Calculate the Unix timestamp for N hours ago
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    from_timestamp = int(start_time.timestamp())
    
    print(f"Searching for news from the past {hours_back} hours...")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Companies: {', '.join(companies)}")
    
    # Proxy setup
    proxy = None
    if use_proxy:
        proxy = "http://webproxy.blackrock.com:8080"
    
    all_results = []
    
    # Create a single session for all requests
    async with aiohttp.ClientSession() as session:
        # Create tasks for all companies
        tasks = [
            get_company_news_complete(
                company=company,
                from_timestamp=from_timestamp,
                session=session,
                headers=headers,
                base_url=base_url,
                proxy=proxy,
                initial_limit=initial_limit
            )
            for company in companies
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Combine all results
        for company_results in results:
            all_results.extend(company_results)
    
    # Create final DataFrame
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Remove duplicates
        if 'header' in df.columns and 'id_site' in df.columns:
            original_count = len(df)
            df = df.drop_duplicates(subset=['header', 'id_site'])
            duplicates_removed = original_count - len(df)
            if duplicates_removed > 0:
                print(f"\nRemoved {duplicates_removed} duplicate articles")
        
        print(f"\nFinal count: Retrieved {len(df)} unique articles from the past {hours_back} hours")
        
        # Print company-specific stats
        if 'search_term' in df.columns:
            company_counts = df['search_term'].value_counts()
            print("\nArticles per company:")
            for company, count in company_counts.items():
                print(f"  - {company}: {count} articles")
        
        # Add date range info
        if 'datetime' in df.columns:
            df_with_dates = df[df['datetime'].notna()]
            if not df_with_dates.empty:
                min_date = df_with_dates['datetime'].min()
                max_date = df_with_dates['datetime'].max()
                print(f"\nDate range: {min_date.strftime('%Y-%m-%d %H:%M')} to {max_date.strftime('%Y-%m-%d %H:%M')}")
        
        return df
    else:
        print("No results found")
        return pd.DataFrame()


def get_all_companies_news_sync(companies, hours_back=24, initial_limit=500, use_proxy=False):
    """Synchronous wrapper for the async function"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(get_all_companies_news(companies, hours_back, initial_limit, use_proxy))


# Example usage
if __name__ == "__main__":
    # List of companies to search for
    companies = ["BlackRock", "Tesla", "Microsoft", "Apple"]
    
    # Get ALL news for these companies from the last 24 hours
    df = get_all_companies_news_sync(companies, hours_back=24, initial_limit=500)
    
    # Display the first few rows
    if df is not None and not df.empty:
        print("\nSample of articles:")
        sample_cols = ['search_term', 'header', 'datetime', 'id_site']
        sample_cols = [col for col in sample_cols if col in df.columns]
        print(df[sample_cols].head())
    
    # Save to CSV if needed
    # df.to_csv('all_companies_news.csv', index=False)

# Import the function
# from multi_company_all_news import get_all_companies_news_sync

# Basic usage - get all news for multiple companies
# companies = ["BlackRock", "Tesla", "Microsoft", "Apple"]
# df = get_all_companies_news_sync(companies, hours_back=24); df
# df.columns
# # Get news from the past 48 hours
# df = get_all_companies_news_sync(companies, hours_back=48)

# # Get news for different companies
# financial_companies = ["BlackRock", "Goldman Sachs", "JPMorgan", "Morgan Stanley", "Citigroup"]
# df = get_all_companies_news_sync(financial_companies)

# # Save results to CSV
# df.to_csv('all_company_news.csv', index=False)

# # Filter results if needed
# blackrock_news = df[df['search_term'] == 'BlackRock']