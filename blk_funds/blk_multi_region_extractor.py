import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import json
import time
from io import StringIO
from urllib.parse import urljoin
from datetime import datetime

# Make sure pyarrow is installed for parquet support
try:
    import pyarrow
except ImportError:
    print("Warning: pyarrow is not installed. Installing it now for parquet support...")
    import subprocess
    subprocess.check_call(["pip", "install", "pyarrow"])

def extract_blackrock_data(base_url, region, output_folder="blackrock_data", add_metadata=True):
    """
    Extracts BlackRock product data from a specific regional page and saves it to an Excel file.
    
    Args:
        base_url (str): The URL for BlackRock product list.
        region (str): Region identifier (e.g., 'uk', 'us', 'de').
        output_folder (str): Folder to save the output Excel files.
        add_metadata (bool): Whether to add metadata columns like Region and Source URL.
    
    Returns:
        str: Path to saved file if successful, None otherwise.
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created directory: {output_folder}")
    
    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = os.path.join(output_folder, f"blackrock_products_{region}_{timestamp}.xlsx")
    
    # Set up headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Create a session to maintain cookies
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print(f"Requesting {base_url} for region {region}")
        response = session.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Try to use pandas to directly read HTML tables
        print("Attempting to use pandas to read HTML tables directly...")
        try:
            # Use StringIO to avoid FutureWarning
            from io import StringIO
            html_io = StringIO(response.text)
            dfs = pd.read_html(html_io)
            if dfs and len(dfs) > 0:
                # Find the largest table (likely the main product table)
                largest_df = max(dfs, key=len)
                if len(largest_df) > 0:
                    print(f"Successfully extracted {len(largest_df)} rows using pandas")
                    
                    # Add metadata columns for identification and traceability
                    if add_metadata:
                        largest_df['Region'] = region.upper()  # Use uppercase for consistency
                        largest_df['Source_URL'] = base_url
                        largest_df['Extract_Date'] = datetime.now().strftime("%Y-%m-%d")
                    
                    largest_df.to_excel(output_file, index=False)
                    print(f"Data saved to {output_file}")
                    return output_file
        except Exception as e:
            print(f"Error using pandas to read HTML tables: {str(e)}")
        
        # Method 2: Extract table data directly with BeautifulSoup
        print("Attempting to extract table data directly...")
        tables = soup.find_all('table')
        
        if tables:
            print(f"Found {len(tables)} tables in the page")
            
            # Find the main product table (typically the largest one)
            main_table = max(tables, key=lambda t: len(t.find_all('tr')))
            
            # Extract headers
            headers = []
            header_row = main_table.find('thead').find('tr') if main_table.find('thead') else main_table.find_all('tr')[0]
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract rows
            rows = []
            tbody = main_table.find('tbody') if main_table.find('tbody') else main_table
            for tr in tbody.find_all('tr'):
                if tr == header_row:  # Skip header row if we're iterating through it again
                    continue
                row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if row and any(cell for cell in row):  # Skip empty rows
                    rows.append(row)
            
            if headers and rows:
                # Create DataFrame
                df = pd.DataFrame(rows, columns=headers if len(headers) == len(rows[0]) else None)
                
                # Add metadata columns for identification and traceability
                if add_metadata:
                    df['Region'] = region.upper()  # Use uppercase for consistency
                    df['Source_URL'] = base_url
                    df['Extract_Date'] = datetime.now().strftime("%Y-%m-%d")
                
                print(f"Successfully extracted {len(rows)} rows of data")
                
                # Save to Excel
                df.to_excel(output_file, index=False)
                print(f"Data saved to {output_file}")
                return output_file
            else:
                print("Could not extract proper table structure")
        
        # Method 3: Look for JSON data embedded in the page
        print("Searching for embedded JSON data...")
        
        # Find script tags that might contain product data
        for script in soup.find_all('script'):
            script_text = script.string
            if not script_text:
                continue
                
            # Look for patterns like "window.products = [...]" or "var products = [...]"
            json_patterns = [
                r'(?:window\.|var\s+)(\w+)\s*=\s*(\[.+?\]);',  # Array pattern
                r'(?:window\.|var\s+)(\w+)\s*=\s*({.+?});'      # Object pattern
            ]
            
            for pattern in json_patterns:
                product_data_matches = re.finditer(pattern, script_text, re.DOTALL)
                
                for product_data_match in product_data_matches:
                    try:
                        var_name = product_data_match.group(1)
                        json_str = product_data_match.group(2)
                        
                        # Only process variables that sound like they contain product data
                        if not any(term in var_name.lower() for term in 
                                ['product', 'fund', 'etf', 'data', 'item', 'result']):
                            continue
                        
                        # Clean up the JSON string
                        json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Convert property names to quoted strings
                        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                        
                        # Parse the JSON data
                        data = json.loads(json_str)
                        
                        # Handle both array and object patterns
                        products = []
                        if isinstance(data, list):
                            products = data
                        elif isinstance(data, dict):
                            # Try to find arrays within the object
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                    products = value
                                    break
                        
                        if products and len(products) > 0:
                            print(f"Found {len(products)} products in embedded JSON")
                            
                            # Convert to DataFrame and save
                            df = pd.DataFrame(products)
                            
                            # Add metadata columns for identification and traceability
                            if add_metadata:
                                df['Region'] = region.upper()  # Use uppercase for consistency
                                df['Source_URL'] = base_url
                                df['Extract_Date'] = datetime.now().strftime("%Y-%m-%d")
                            
                            df.to_excel(output_file, index=False)
                            print(f"Data saved to {output_file}")
                            return output_file
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Error parsing JSON: {str(e)}")
        
        # Method 4: Try to access API endpoints directly
        print("Attempting to access known API patterns...")
        
        # Common API patterns for BlackRock
        api_patterns = [
            "/api/product-list",
            "/api/products/export",
            "/api/product/list",
            "/api-gateway/products",
            f"/api/products/{region}/all",
            f"/{region}/api/products",
            "/api-gateway/data/product-list"
        ]
        
        for pattern in api_patterns:
            api_url = urljoin(base_url, pattern)
            try:
                print(f"Trying API endpoint: {api_url}")
                api_response = session.get(api_url)
                
                if api_response.status_code == 200:
                    try:
                        # Try to parse as JSON
                        data = api_response.json()
                        
                        # Check if this is product data
                        if isinstance(data, list) and len(data) > 0:
                            print(f"Found {len(data)} products from API")
                            df = pd.DataFrame(data)
                            # Add metadata columns for identification and traceability
                            if add_metadata:
                                df['Region'] = region.upper()  # Use uppercase for consistency
                                df['Source_URL'] = base_url
                                df['Extract_Date'] = datetime.now().strftime("%Y-%m-%d")
                            df.to_excel(output_file, index=False)
                            print(f"Data saved to {output_file}")
                            return output_file
                        elif isinstance(data, dict):
                            # Look for product data in common dictionary keys
                            for key in ['products', 'items', 'results', 'data', 'funds', 'etfs']:
                                if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                                    products = data[key]
                                    print(f"Found {len(products)} products from API under key '{key}'")
                                    df = pd.DataFrame(products)
                                    # Add metadata columns for identification and traceability
                                    if add_metadata:
                                        df['Region'] = region.upper()  # Use uppercase for consistency
                                        df['Source_URL'] = base_url
                                        df['Extract_Date'] = datetime.now().strftime("%Y-%m-%d")
                                    df.to_excel(output_file, index=False)
                                    print(f"Data saved to {output_file}")
                                    return output_file
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Error parsing API response: {str(e)}")
            except Exception as e:
                print(f"Error accessing API: {str(e)}")
        
        print(f"All extraction methods failed for region {region}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request error for region {region}: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for region {region}: {str(e)}")
        return None


def extract_all_regions(output_folder="blackrock_data", add_metadata=True):
    """
    Extract BlackRock product data from multiple regions.
    
    Args:
        output_folder (str): Folder to save all extracted data.
        add_metadata (bool): Whether to add metadata columns like Region, Source URL, and Extract Date.
    """
    # Define regions and their URLs (updated based on successful runs)
    regions = {
        "ae": "https://www.blackrock.com/ae/intermediaries/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "americans_offshore": "https://www.blackrock.com/americas-offshore/en/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalNetAssetsFund&sortDirection=desc&dataView=perfNav",
        "at": "https://www.blackrock.com/at/privatanleger/produkte/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfNav",
        "au": "https://www.blackrock.com/au/products/investment-funds#/?productView=all&pageNumber=1&sortColumn=navAmount&sortDirection=desc&dataView=perfNav",
        "be": "https://www.blackrock.com/be/individual/nl/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "br": "https://www.blackrock.com/br/products/product-list#/?productView=all&style=44341&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfNav",
        "ca": "https://www.blackrock.com/ca/investors/en/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalNetAssets&sortDirection=desc&dataView=perfNav",
        "co": "https://www.blackrock.com/co/productos/lista-de-producto#/?productView=all&style=44342%7C44341&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfNav",
        "dk": "https://www.blackrock.com/dk/individual/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "es": "https://www.blackrock.com/es/profesionales/productos/lista-de-producto#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "fr": "https://www.blackrock.com/fr/particuliers/products/investment-funds#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfNav",
        "hk": "https://www.blackrock.com/hk/en/products/products-list#/?productView=all&pageNumber=1&sortColumn=localExchangeTicker&sortDirection=asc&dataView=perfNav",
        "il": "https://www.blackrock.com/il/individual/en/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "it": "https://www.blackrock.com/it/investitori-privati/products/product-list#/?productView=all&style=44342%7C44341&fac=43535%7C43580%7C43581%7C43584%7C43585%7C43615&pageNumber=1&sortColumn=navAmount&sortDirection=desc&dataView=perfNav",
        "jp": "https://www.blackrock.com/jp/individual-en/en/products/products-list#type=all&style=All&view=perfNav&pageSize=100&pageNumber=1&sortColumn=fundSeriesName&sortDirection=desc",
        "lu": "https://www.blackrock.com/lu/individual/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "nl": "https://www.blackrock.com/nl/particuliere-beleggers/produkten/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "se": "https://www.blackrock.com/se/individual/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "sg": "https://www.blackrock.com/sg/en/products/products-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfCum",
        "uk": "https://www.blackrock.com/uk/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
        "us": "https://www.blackrock.com/us/individual/products/investment-funds#/?productView=all&pageNumber=1&sortColumn=totalNetAssets&sortDirection=desc&dataView=perfNav",
        "za": "https://www.blackrock.com/za/individual/products/product-list#/?productView=all&pageNumber=1&sortColumn=totalFundSizeInMillions&sortDirection=desc&dataView=perfDiscrete",
    }
    
    results = {}
    all_data_dfs = []
    
    # Process each region
    for region, url in regions.items():
        print(f"\n{'='*50}")
        print(f"Processing region: {region}")
        print(f"{'='*50}")
        
        result_file = extract_blackrock_data(url, region, output_folder, add_metadata)
        results[region] = result_file
        
        # If extraction was successful, try to read the file for potential merging
        if result_file and os.path.exists(result_file):
            try:
                region_df = pd.read_excel(result_file)
                all_data_dfs.append(region_df)
                print(f"Added data from {region} for potential combined file")
            except Exception as e:
                print(f"Error reading {result_file} for combined file: {str(e)}")
    
    # Create a combined file with all regions if we have data
    if all_data_dfs:
        try:
            # Concatenate all dataframes
            combined_df = pd.concat(all_data_dfs, ignore_index=True)
            
            # Handle data type issues before saving to parquet
            # Convert problematic columns to string to avoid type conversion errors
            for col in combined_df.columns:
                if combined_df[col].dtype == 'object':
                    # Check if this column might be causing issues
                    if any(isinstance(x, float) for x in combined_df[col].dropna()):
                        print(f"Converting mixed-type column '{col}' to string for compatibility")
                        combined_df[col] = combined_df[col].astype(str)
            
            # Save as Excel first (more forgiving with data types)
            excel_file = os.path.join(output_folder, f"blackrock_all_regions_{datetime.now().strftime('%Y%m%d')}.xlsx")
            combined_df.to_excel(excel_file, index=False)
            print(f"\nCreated Excel file: {excel_file}")
            
            # Now try to save as parquet
            try:
                parquet_file = os.path.join(output_folder, f"blackrock_all_regions_{datetime.now().strftime('%Y%m%d')}.parquet")
                combined_df.to_parquet(parquet_file, index=False)
                print(f"Created combined parquet file: {parquet_file}")
            except Exception as parquet_err:
                print(f"Error creating parquet file: {str(parquet_err)}")
                print("Excel file was still created successfully.")
        except Exception as e:
            print(f"\nError creating combined file: {str(e)}")
    
    # Print summary
    print("\n\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    
    for region, file_path in results.items():
        status = "SUCCESS" if file_path else "FAILED"
        file_info = file_path if file_path else "No data extracted"
        print(f"{region.upper()}: {status} - {file_info}")
    
    print("\nComplete!")


def add_custom_region(region_id, url, output_folder="blackrock_data", add_metadata=True):
    """
    Extract BlackRock product data from a custom region URL.
    
    Args:
        region_id (str): Custom identifier for the region (e.g., 'asia', 'latam').
        url (str): The URL for BlackRock product list for this region.
        output_folder (str): Folder to save the extracted data.
        add_metadata (bool): Whether to add metadata columns like Region, Source URL, and Extract Date.
    """
    print(f"\n{'='*50}")
    print(f"Processing custom region: {region_id}")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    result_file = extract_blackrock_data(url, region_id, output_folder, add_metadata)
    
    if result_file:
        print(f"\nSuccessfully extracted data for {region_id}")
        print(f"Data saved to: {result_file}")
    else:
        print(f"\nFailed to extract data for {region_id}")


if __name__ == "__main__":
    # Default output folder
    output_folder = "blackrock_data"
    
    # Extract data from all predefined regions
    # Extract all regions with metadata columns
    extract_all_regions(output_folder, add_metadata=True)
    
    # Example: Add a custom region if needed
    # add_custom_region("custom", "https://www.blackrock.com/custom/url", output_folder, add_metadata=True)