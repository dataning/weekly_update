import requests
import pandas as pd
import tempfile
import os
from lxml import etree
import io
import json
import datetime

def read_portfolio_ids(file_path):
    """
    Read portfolio IDs from a file.
    
    Parameters:
    file_path (str): Path to the file containing portfolio IDs
    
    Returns:
    str: Portfolio IDs as a string (e.g., "123456-789012-345678")
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Portfolio IDs file not found: {file_path}")
            return None
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        # Check if the content is a simple string of IDs
        if '-' in content and content.replace('-', '').isdigit():
            return content
        
        # Try to parse as JSON if it appears to be JSON formatted
        if content.startswith('{') or content.startswith('['):
            try:
                data = json.loads(content)
                # If it's a list, join with dashes
                if isinstance(data, list):
                    return '-'.join([str(item) for item in data])
                # If it's a dict with a specific key
                elif isinstance(data, dict) and 'portfolio_ids' in data:
                    ids = data['portfolio_ids']
                    if isinstance(ids, list):
                        return '-'.join([str(item) for item in ids])
                    else:
                        return str(ids)
            except json.JSONDecodeError:
                pass
        
        # If we can't parse it as JSON, assume it's a simple string
        # Strip any whitespace, newlines, quotes, etc.
        clean_content = content.replace('\n', '').replace('\r', '').replace(' ', '').replace('"', '').replace("'", '')
        
        # Check if it's a valid format
        if '-' in clean_content:
            return clean_content
        
        print(f"Could not parse portfolio IDs from file: {file_path}")
        return None
    
    except Exception as e:
        print(f"Error reading portfolio IDs file: {e}")
        return None

def parse_excel_xml_content(content):
    """
    Parse Excel XML content directly from bytes.
    
    Parameters:
    content (bytes): The XML content as bytes
    
    Returns:
    pandas.DataFrame or dict: DataFrame containing the data or dict of DataFrames for multiple sheets
    """
    try:
        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        
        # Parse XML with proper namespace handling
        parser = etree.XMLParser(recover=True)  # Recover mode for malformed XML
        tree = etree.parse(io.BytesIO(content), parser)
        root = tree.getroot()
        
        # Print the XML structure for debugging
        print(f"Root tag: {root.tag}")
        
        # Extract the namespace
        ns = root.nsmap
        print(f"Namespace map: {ns}")
        
        # Try different namespace approaches
        ns_uri = None
        if ns:
            ns_uri = ns.get(None) or ns.get('ss') or next(iter(ns.values()), None)
        
        print(f"Using namespace URI: {ns_uri}")
        
        # Register the namespace properly for XPath
        ns_dict = {"ss": ns_uri} if ns_uri else {}
        
        # Find all worksheets using various methods
        worksheets = []
        
        # Method 1: Using namespace
        if ns_uri:
            try:
                worksheets = root.xpath('//ss:Worksheet', namespaces=ns_dict)
                print(f"Found {len(worksheets)} worksheets using namespace")
            except Exception as e:
                print(f"Error finding worksheets with namespace: {e}")
        
        # Method 2: Using local-name
        if not worksheets:
            try:
                worksheets = root.xpath("//*[local-name()='Worksheet']")
                print(f"Found {len(worksheets)} worksheets using local-name")
            except Exception as e:
                print(f"Error finding worksheets with local-name: {e}")
        
        # Method 3: Direct findall
        if not worksheets:
            try:
                worksheets = root.findall('.//{*}Worksheet')
                print(f"Found {len(worksheets)} worksheets using findall")
            except Exception as e:
                print(f"Error finding worksheets with findall: {e}")
        
        # If still no worksheets, try to find Table elements directly
        if not worksheets:
            try:
                tables = root.xpath("//*[local-name()='Table']")
                print(f"Found {len(tables)} tables directly")
                if tables:
                    # Create a dummy worksheet structure
                    from lxml.etree import Element
                    worksheets = [Element('Worksheet')]
                    for i, table in enumerate(tables):
                        # Add the table as a child of the worksheet
                        worksheet = Element('Worksheet')
                        worksheet.set('Name', f'Sheet{i+1}')
                        worksheet.append(table)
                        worksheets[i] = worksheet
            except Exception as e:
                print(f"Error finding tables directly: {e}")
        
        if not worksheets:
            # Print the first 1000 characters of the XML content for debugging
            print("No worksheets found. XML content preview:")
            print(content[:1000])
            return None
        
        result_dfs = {}
        
        # Process each worksheet
        for worksheet in worksheets:
            # Get worksheet name
            worksheet_name = None
            
            # Try different ways to get the worksheet name
            if ns_uri:
                worksheet_name = worksheet.get(f'{{{ns_uri}}}Name')
            
            if worksheet_name is None:
                worksheet_name = worksheet.get('Name')
            
            if worksheet_name is None:
                # Get ID or any other attribute that might identify the worksheet
                for attr_name in worksheet.attrib:
                    if 'name' in attr_name.lower() or 'id' in attr_name.lower():
                        worksheet_name = worksheet.get(attr_name)
                        break
            
            # Use a default name if still None
            if worksheet_name is None:
                worksheet_name = f'Sheet{len(result_dfs) + 1}'
                
            print(f"\nProcessing worksheet: {worksheet_name}")
            
            # Find the table element using different methods
            table = None
            
            # Method 1: Using namespace
            if ns_uri:
                table = worksheet.find(f'.//{{{ns_uri}}}Table')
            
            # Method 2: Using local-name
            if table is None:
                try:
                    tables = worksheet.xpath(".//*[local-name()='Table']")
                    if tables:
                        table = tables[0]
                except Exception as e:
                    print(f"Error finding table with xpath: {e}")
            
            # Method 3: Direct find
            if table is None:
                table = worksheet.find('.//{*}Table')
            
            # If the worksheet itself is a table (from the dummy structure)
            if table is None and 'Table' in worksheet.tag:
                table = worksheet
                
            if table is None:
                print(f"No table found in worksheet {worksheet_name}")
                continue
            
            # Find all rows using different methods
            rows = []
            
            # Method A: Using namespace
            if ns_uri:
                rows = table.findall(f'.//{{{ns_uri}}}Row')
            
            # Method B: Using local-name
            if not rows:
                try:
                    rows = table.xpath(".//*[local-name()='Row']")
                except Exception as e:
                    print(f"Error finding rows with xpath: {e}")
            
            # Method C: Direct findall
            if not rows:
                rows = table.findall('.//{*}Row')
                
            print(f"Found {len(rows)} rows in worksheet {worksheet_name}")
            
            if not rows:
                print(f"No rows found in worksheet {worksheet_name}")
                continue
            
            # Extract data from rows
            data = []
            for row in rows:
                row_data = []
                
                # Find all cells using different methods
                cells = []
                
                # Method 1: Using namespace
                if ns_uri:
                    cells = row.findall(f'.//{{{ns_uri}}}Cell')
                
                # Method 2: Using local-name
                if not cells:
                    try:
                        cells = row.xpath(".//*[local-name()='Cell']")
                    except Exception as e:
                        print(f"Error finding cells with xpath: {e}")
                
                # Method 3: Direct findall
                if not cells:
                    cells = row.findall('.//{*}Cell')
                
                for cell in cells:
                    # Get cell value using different methods
                    value = None
                    
                    # Method 1: Try to get value from Data element
                    data_elem = None
                    
                    if ns_uri:
                        data_elem = cell.find(f'.//{{{ns_uri}}}Data')
                    
                    if data_elem is None:
                        try:
                            data_elems = cell.xpath(".//*[local-name()='Data']")
                            if data_elems:
                                data_elem = data_elems[0]
                        except Exception:
                            pass
                    
                    if data_elem is None:
                        data_elem = cell.find('.//{*}Data')
                    
                    if data_elem is not None and data_elem.text:
                        value = data_elem.text.strip()
                    
                    # Method 2: Try to get value directly from cell text
                    if value is None and cell.text:
                        value = cell.text.strip()
                    
                    # Check for merged cells (indicated by Index attribute)
                    cell_index = None
                    
                    if ns_uri:
                        cell_index = cell.get(f'{{{ns_uri}}}Index')
                    
                    if cell_index is None:
                        cell_index = cell.get('Index')
                    
                    if cell_index is None:
                        # Try to get any attribute that might indicate index
                        for attr_name in cell.attrib:
                            if 'index' in attr_name.lower():
                                cell_index = cell.get(attr_name)
                                break
                    
                    if cell_index:
                        try:
                            # If there's an Index attribute, it means some cells were skipped
                            # Add None values for the skipped cells
                            index = int(cell_index)
                            while len(row_data) < index - 1:  # -1 because Index is 1-based
                                row_data.append(None)
                        except ValueError:
                            pass
                    
                    row_data.append(value)
                
                if row_data:  # Only add non-empty rows
                    data.append(row_data)
            
            if not data:
                print(f"No data extracted from worksheet {worksheet_name}")
                continue
            
            # Determine max columns
            max_cols = max(len(row) for row in data)
            
            # Make sure all rows have the same length
            for i in range(len(data)):
                if len(data[i]) < max_cols:
                    data[i].extend([None] * (max_cols - len(data[i])))
            
            # First row as headers
            headers = data[0] if data else []
            content_data = data[1:] if len(data) > 1 else []
            
            # Generate column names if header row has empty values
            for i in range(len(headers)):
                if headers[i] is None or headers[i] == '':
                    headers[i] = f'Column{i+1}'
            
            # Create DataFrame
            df = pd.DataFrame(content_data, columns=headers)
            result_dfs[worksheet_name] = df
            
            print(f"Created DataFrame for worksheet '{worksheet_name}' with {len(df)} rows and {len(headers)} columns")
        
        if not result_dfs:
            print("No data frames created from any worksheet")
            return None
        
        # If there's only one worksheet, return just the DataFrame
        if len(result_dfs) == 1:
            return next(iter(result_dfs.values()))
        else:
            return result_dfs
        
    except Exception as e:
        print(f"Error parsing XML: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_excel_to_dataframe(file_path):
    """
    Parse an Excel file to a pandas DataFrame.
    This function tries different parsing methods based on the file format.
    
    Parameters:
    file_path (str): Path to the Excel file
    
    Returns:
    pandas.DataFrame or dict: DataFrame containing the data or dict of DataFrames for multiple sheets
    """
    try:
        # First try with pandas read_excel (works for most Excel files)
        return pd.read_excel(file_path, sheet_name=None)
    
    except Exception as e1:
        print(f"Standard Excel parsing failed: {e1}")
        
        try:
            # Try using pd.read_excel with specific engine
            return pd.read_excel(file_path, engine='openpyxl', sheet_name=None)
        
        except Exception as e2:
            print(f"Openpyxl parsing failed: {e2}")
            
            try:
                # Try using pd.read_excel with xlrd engine
                return pd.read_excel(file_path, engine='xlrd', sheet_name=None)
            
            except Exception as e3:
                print(f"xlrd parsing failed: {e3}")
                
                # As a last resort, try the custom XML-based parser
                print("Trying custom XML parser...")
                
                # Read the file content
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Try to parse the XML content
                return parse_excel_xml_content(content)

def save_to_parquet(df_data, output_dir=None, prefix=None):
    """
    Save DataFrame(s) to parquet file(s).
    
    Parameters:
    df_data (DataFrame or dict): DataFrame or dictionary of DataFrames to save
    output_dir (str, optional): Directory to save the parquet file(s). If None, uses the current directory.
    prefix (str, optional): Prefix for the parquet file names
    
    Returns:
    list: Paths to the saved parquet files
    """
    # Use current directory if no output directory is specified
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate prefix with timestamp if none provided
    if prefix is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"blackrock_data_{timestamp}"
    
    saved_files = []
    
    try:
        # If a single DataFrame is provided
        if isinstance(df_data, pd.DataFrame):
            file_path = os.path.join(output_dir, f"{prefix}.parquet")
            df_data.to_parquet(file_path)
            saved_files.append(file_path)
            print(f"Saved DataFrame to {file_path}")
        
        # If a dictionary of DataFrames is provided
        elif isinstance(df_data, dict):
            for sheet_name, df in df_data.items():
                # Clean up sheet name for use in filename
                clean_name = ''.join(c if c.isalnum() else '_' for c in sheet_name)
                file_path = os.path.join(output_dir, f"{prefix}_{clean_name}.parquet")
                df.to_parquet(file_path)
                saved_files.append(file_path)
                print(f"Saved sheet '{sheet_name}' to {file_path}")
        
        else:
            print(f"Unexpected data type: {type(df_data)}. Cannot save to parquet.")
        
        return saved_files
    
    except Exception as e:
        print(f"Error saving to parquet: {e}")
        import traceback
        traceback.print_exc()
        return saved_files

# Region-specific download functions

def download_blackrock_americas_excel(output_file=None, portfolio_ids=None, portfolio_ids_file=None):
    """
    Downloads an Excel file from BlackRock Americas product screener and saves it to the specified path.
    """
    url = "https://www.blackrock.com/americas-offshore/en/product-list/product-screener-v3.1.jsn"
    
    querystring = {
        "type": "excel",
        "siteEntryPassthrough": "true",
        "dcrPath": "/templatedata/config/product-screener-v3/data/en/Americas-offshore/product-screener-excel-config",
        "disclosureContentDcrPath": "/templatedata/content/article/data/en/one/DEFAULT/product-screener-all-disclaimer"
    }
    
    # Separate payload into base parameters and portfolio IDs
    payload_base = "productView=all&portfolios="
    
    # Try to get portfolio IDs from file if provided
    if portfolio_ids_file and portfolio_ids is None:
        file_ids = read_portfolio_ids(portfolio_ids_file)
        if file_ids:
            portfolio_ids = file_ids
    
    # Use default portfolio IDs if none provided
    if portfolio_ids is None:
        portfolio_ids = "228238-228239-228240-228242-228243-228268"
        print(f"Using default portfolio IDs: {portfolio_ids}")
    else:
        print(f"Using portfolio IDs: {portfolio_ids}")
    
    # Combined payload
    payload = payload_base + portfolio_ids
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://www.blackrock.com/americas-offshore/en/products/product-list",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.blackrock.com",
        "Connection": "keep-alive"
    }
    
    # If no output file is specified, create a temporary file
    if output_file is None:
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, "blackrock_americas_products.xls")
    
    try:
        # Make the request
        response = requests.request(
            "POST", 
            url, 
            data=payload, 
            headers=headers, 
            params=querystring, 
            stream=True
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Write the response content to file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded Excel file to {output_file}")
        return output_file
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

def download_blackrock_uk_excel(output_file=None, portfolio_ids=None, portfolio_ids_file=None):
    """
    Downloads an Excel file from BlackRock UK product screener and saves it to the specified path.
    """
    url = "https://www.blackrock.com/uk/product-screener/product-screener-v3.1.jsn"
    
    querystring = {
        "type": "excel",
        "siteEntryPassthrough": "true",
        "dcrPath": "/templatedata/config/product-screener-v3/data/en/uk/product-screener/product-screener-excel-config",
        "userType": "individual",
        "disclosureContentDcrPath": "/templatedata/content/article/data/en/uk-one/DEFAULT/product-screener-disclaimer-none"
    }
    
    # Separate payload into base parameters and portfolio IDs
    payload_base = "productView=all&portfolios="
    
    # Try to get portfolio IDs from file if provided
    if portfolio_ids_file and portfolio_ids is None:
        file_ids = read_portfolio_ids(portfolio_ids_file)
        if file_ids:
            portfolio_ids = file_ids
    
    # Use default portfolio IDs if none provided
    if portfolio_ids is None:
        portfolio_ids = "228238-228242-228268-228273"
        print(f"Using default portfolio IDs: {portfolio_ids}")
    else:
        print(f"Using portfolio IDs: {portfolio_ids}")
    
    # Combined payload
    payload = payload_base + portfolio_ids
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://www.blackrock.com/uk/products/product-list",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.blackrock.com",
        "Connection": "keep-alive"
    }
    
    # If no output file is specified, create a temporary file
    if output_file is None:
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, "blackrock_uk_products.xls")
    
    try:
        # Make the request
        response = requests.request(
            "POST", 
            url, 
            data=payload, 
            headers=headers, 
            params=querystring, 
            stream=True
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Write the response content to file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded Excel file to {output_file}")
        return output_file
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

# You can add more region-specific download functions here as needed
# For example:
# def download_blackrock_europe_excel(...):
#     ...

# Unified function to handle multiple regions
def download_blackrock_excel(region="americas", output_file=None, portfolio_ids=None, portfolio_ids_file=None):
    """
    Downloads a BlackRock Excel file from the specified region's product screener.
    
    Parameters:
    region (str): Region to download from ('americas' or 'uk')
    output_file (str, optional): Path to save the downloaded Excel file
    portfolio_ids (str, optional): Portfolio IDs as a string (e.g., "123456-789012")
    portfolio_ids_file (str, optional): Path to a file containing portfolio IDs
    
    Returns:
    str: Path to the downloaded file
    """
    if region.lower() == "uk":
        return download_blackrock_uk_excel(output_file, portfolio_ids, portfolio_ids_file)
    # Add more conditions for other regions as needed
    # elif region.lower() == "europe":
    #    return download_blackrock_europe_excel(output_file, portfolio_ids, portfolio_ids_file)
    else:  # Default to Americas
        return download_blackrock_americas_excel(output_file, portfolio_ids, portfolio_ids_file)

def main(region="americas", portfolio_ids=None, portfolio_ids_file=None, output_dir=None, parquet_prefix=None, save_parquet=True):
    """
    Main function to download and parse BlackRock Excel files from different regions.
    
    Parameters:
    region (str): Region to download from ('americas' or 'uk')
    portfolio_ids (str, optional): Portfolio IDs to download
    portfolio_ids_file (str, optional): Path to a file containing portfolio IDs
    output_dir (str, optional): Directory to save the parquet file(s)
    parquet_prefix (str, optional): Prefix for the parquet file names
    save_parquet (bool, optional): Whether to save the data as parquet files
    
    Returns:
    pandas.DataFrame or dict: DataFrame(s) containing the parsed data
    list: Paths to the saved parquet files (if save_parquet is True)
    """
    # Download the Excel file
    excel_file = download_blackrock_excel(
        region=region, 
        portfolio_ids=portfolio_ids, 
        portfolio_ids_file=portfolio_ids_file
    )
    
    saved_files = []
    if excel_file:
        # Parse the Excel file
        dfs = parse_excel_to_dataframe(excel_file)
        
        if dfs is not None:
            if isinstance(dfs, dict):
                # Multiple sheets
                print("\nSuccessfully parsed multiple sheets:")
                for sheet_name, df in dfs.items():
                    print(f"\nSheet: {sheet_name}")
                    print(f"Shape: {df.shape}")
                    print("First 5 rows:")
                    print(df.head())
            else:
                # Single sheet
                print("\nSuccessfully parsed Excel file:")
                print(f"Shape: {dfs.shape}")
                print("First 5 rows:")
                print(dfs.head())
            
            # Save to parquet if requested
            if save_parquet:
                if parquet_prefix is None:
                    parquet_prefix = f"blackrock_{region.lower()}"
                saved_files = save_to_parquet(dfs, output_dir=output_dir, prefix=parquet_prefix)
                return dfs, saved_files
            
            return dfs
        else:
            print("Failed to parse Excel file.")
            return None if not save_parquet else (None, [])
    else:
        print("Failed to download Excel file.")
        return None if not save_parquet else (None, [])

if __name__ == "__main__":
    import argparse
    
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Download and parse BlackRock Excel files')
    parser.add_argument('--region', type=str, default='americas', help='Region to download from (americas or uk)')
    parser.add_argument('--portfolio-ids', type=str, help='Portfolio IDs as a string (e.g., "123456-789012")')
    parser.add_argument('--portfolio-file', type=str, help='Path to a file containing portfolio IDs')
    parser.add_argument('--output-dir', type=str, help='Directory to save the parquet file(s)')
    parser.add_argument('--prefix', type=str, help='Prefix for the parquet file names')
    parser.add_argument('--no-save', action='store_true', help='Do not save data as parquet files')
    
    args = parser.parse_args()
    
    # Call main function with command-line arguments
    result = main(
        region=args.region,
        portfolio_ids=args.portfolio_ids,
        portfolio_ids_file=args.portfolio_file,
        output_dir=args.output_dir,
        parquet_prefix=args.prefix,
        save_parquet=not args.no_save
    )
    
    if result is None or (isinstance(result, tuple) and result[0] is None):
        print("Failed to process BlackRock data.")
    else:
        print("Successfully processed BlackRock data.")