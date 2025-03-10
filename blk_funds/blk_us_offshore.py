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

def download_blackrock_excel(output_file=None, portfolio_ids=None, portfolio_ids_file=None):
    """
    Downloads an Excel file from BlackRock product screener and saves it to the specified path.
    
    Parameters:
    output_file (str, optional): Path to save the downloaded Excel file. If None, a temporary file will be created.
    portfolio_ids (str, optional): Portfolio IDs as a string (e.g., "123456-789012-345678").
    portfolio_ids_file (str, optional): Path to a file containing portfolio IDs.
    
    Returns:
    str: Path to the downloaded file
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
        output_file = os.path.join(temp_dir, "blackrock_products.xls")
    
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
                return parse_office_xml_spreadsheet(file_path)

def parse_office_xml_spreadsheet(file_path):
    """
    Parse a Microsoft Office XML Spreadsheet file (.xls with XML content)
    and convert it to a pandas DataFrame.
    
    Parameters:
    file_path (str): Path to the XML Excel file
    
    Returns:
    pandas.DataFrame or dict: DataFrame containing the data or dict of DataFrames for multiple sheets
    """
    try:
        # Read the file handling BOM correctly
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        
        # Parse XML with proper namespace handling
        parser = etree.XMLParser(recover=True)  # Recover mode for malformed XML
        tree = etree.parse(io.BytesIO(content), parser)
        root = tree.getroot()
        
        # Extract the namespace
        ns = root.nsmap
        ns_uri = ns.get(None) or ns.get('ss')
        
        print(f"Root tag: {root.tag}")
        print(f"Namespace: {ns_uri}")
        
        # Register the namespace properly for XPath
        ns_dict = {"ss": ns_uri} if ns_uri else {}
        
        # Find all worksheets
        if ns_uri:
            worksheets = root.xpath('//ss:Worksheet', namespaces=ns_dict)
        else:
            worksheets = root.findall('.//*[local-name()="Worksheet"]')
            
        print(f"Found {len(worksheets)} worksheets")
        
        if not worksheets:
            # Try without namespace
            try:
                worksheets = root.findall('.//{*}Worksheet')
                print(f"Found {len(worksheets)} worksheets without namespace")
            except Exception as e:
                print(f"Error finding worksheets: {e}")
        
        if not worksheets:
            print("No worksheets found in the XML structure.")
            return None
        
        result_dfs = {}
        
        # Process each worksheet
        for worksheet in worksheets:
            # Get worksheet name
            if ns_uri:
                worksheet_name = worksheet.get(f'{{{ns_uri}}}Name', 'Sheet')
            else:
                worksheet_name = worksheet.get('Name', 'Sheet')
                
            print(f"\nProcessing worksheet: {worksheet_name}")
            
            # Find the table element
            if ns_uri:
                table = worksheet.find(f'.//{{{ns_uri}}}Table')
            else:
                table = worksheet.find('.//*[local-name()="Table"]')
                
            if table is None:
                print(f"No table found in worksheet {worksheet_name}")
                continue
            
            # Find all rows
            if ns_uri:
                rows = table.findall(f'.//{{{ns_uri}}}Row')
            else:
                rows = table.findall('.//*[local-name()="Row"]')
                
            print(f"Found {len(rows)} rows in worksheet {worksheet_name}")
            
            if not rows:
                print(f"No rows found in worksheet {worksheet_name}")
                continue
            
            # Extract data from rows
            data = []
            for row in rows:
                row_data = []
                
                # Find all cells in the row
                if ns_uri:
                    cells = row.findall(f'.//{{{ns_uri}}}Cell')
                else:
                    cells = row.findall('.//*[local-name()="Cell"]')
                
                for cell in cells:
                    # Get cell value - it's in a Data element inside the Cell
                    if ns_uri:
                        data_elem = cell.find(f'.//{{{ns_uri}}}Data')
                        cell_index = cell.get(f'{{{ns_uri}}}Index')
                    else:
                        data_elem = cell.find('.//*[local-name()="Data"]')
                        cell_index = cell.get('Index')
                    
                    # Extract value
                    value = None
                    if data_elem is not None and data_elem.text:
                        value = data_elem.text.strip()
                    
                    # Check for merged cells (indicated by Index attribute)
                    if cell_index:
                        # If there's an Index attribute, it means some cells were skipped
                        # Add None values for the skipped cells
                        index = int(cell_index)
                        while len(row_data) < index - 1:  # -1 because Index is 1-based
                            row_data.append(None)
                    
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

def main(portfolio_ids=None, portfolio_ids_file=None, output_dir=None, parquet_prefix=None, save_parquet=True):
    """
    Main function to download and parse the BlackRock Excel file, and optionally save as parquet.
    
    Parameters:
    portfolio_ids (str, optional): Portfolio IDs to download (e.g., "228238-228239-228240")
    portfolio_ids_file (str, optional): Path to a file containing portfolio IDs
    output_dir (str, optional): Directory to save the parquet file(s)
    parquet_prefix (str, optional): Prefix for the parquet file names
    save_parquet (bool, optional): Whether to save the data as parquet files (default: True)
    
    Returns:
    pandas.DataFrame or dict: DataFrame(s) containing the parsed data
    list: Paths to the saved parquet files (if save_parquet is True)
    """
    # Download the Excel file
    excel_file = download_blackrock_excel(portfolio_ids=portfolio_ids, portfolio_ids_file=portfolio_ids_file)
    
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
                saved_files = save_to_parquet(dfs, output_dir=output_dir, prefix=parquet_prefix)
                return dfs, saved_files
            
            return dfs
        else:
            print("Failed to parse Excel file.")
            return None
    else:
        print("Failed to download Excel file.")
        return None

if __name__ == "__main__":
    main()
