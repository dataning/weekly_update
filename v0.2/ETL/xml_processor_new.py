import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from lxml import etree
import pandas as pd
import time
from typing import List, Dict, Tuple, Set
import logging
from datetime import datetime
from io import StringIO, BytesIO
import os
from collections import defaultdict

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# Set proxy environment variables
# os.environ['HTTP_PROXY'] = 'http://webproxy.bfm.com:8080'
# os.environ['HTTPS_PROXY'] = 'http://webproxy.bfm.com:8080'

# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class NonProfitXMLStreamProcessor:
    """
    A processor for downloading and parsing XML files from ProPublica's Nonprofit Explorer.

    This class handles the retrieval and processing of Form 990 XML files for nonprofit
    organizations, converting them into a structured DataFrame format.

    :ivar ein: Employer Identification Number of the nonprofit
    :type ein: str
    :ivar base_url: Base URL for ProPublica's Nonprofit Explorer
    :type base_url: str
    :ivar org_url: Complete URL for the specific nonprofit organization
    :type org_url: str
    :ivar headers: HTTP headers for making requests
    :type headers: Dict[str, str]
    :ivar session: Requests session object for making HTTP requests
    :type session: requests.Session
    :ivar logger: Logger instance for the processor
    :type logger: logging.Logger
    """

    def __init__(self, ein: str):
        """
        Initialize the XML Stream Processor.

        :param ein: Employer Identification Number of the nonprofit organization
        :type ein: str
        :raises ValueError: If EIN format is invalid
        """
        self.ein = ein
        self.base_url = "https://projects.propublica.org"
        self.org_url = f"{self.base_url}/nonprofits/organizations/{ein}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.verify = False
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging configuration for the processor.

        :return: Configured logger instance
        :rtype: logging.Logger
        """
        logger = logging.getLogger(f"NonProfitXMLStreamProcessor_{self.ein}")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        if not logger.handlers:
            logger.addHandler(handler)
        return logger

    def get_xml_links(self) -> List[str]:
        """
        Retrieve XML download links from the organization's webpage.

        :return: List of URLs to XML files
        :rtype: List[str]
        :raises ConnectionError: If unable to connect to the website
        :raises HTTPError: If the webpage request fails
        """
        try:
            response = self.session.get(self.org_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            xml_links = soup.find_all('a', class_='btn', target='_blank', 
                                    href=lambda x: x and 'download-xml' in x)
            
            full_urls = [urljoin(self.base_url, link['href']) for link in xml_links]
            self.logger.info(f"Found {len(full_urls)} XML download links for EIN {self.ein}")
            return full_urls
            
        except Exception as e:
            self.logger.error(f"Error accessing webpage: {e}")
            return []

    def _clean_column_name(self, col: str) -> str:
        """
        Clean XML namespace from column names.

        :param col: Column name with potential namespace
        :type col: str
        :return: Cleaned column name
        :rtype: str
        """
        if '}' in col:
            col = col.split('}', 1)[1]
        return col

    def _extract_identifiers(self, root: etree._Element) -> Tuple[str, str]:
        """
        Extract nonprofit ID and year from XML content.

        :param root: Root element of the XML tree
        :type root: etree._Element
        :return: Tuple of (nonprofit_id, year)
        :rtype: Tuple[str, str]
        :raises XMLSyntaxError: If XML parsing fails
        """
        try:
            namespace = {'irs': 'http://www.irs.gov/efile'}
            ein_element = root.find('.//irs:Filer/irs:EIN', namespaces=namespace)
            return_ts_element = root.find('.//irs:ReturnHeader/irs:ReturnTs', namespaces=namespace)
            tax_year_element = root.find('.//irs:ReturnHeader/irs:TaxYear', namespaces=namespace)
            tax_period_end_element = root.find('.//irs:ReturnHeader/irs:TaxPeriodEndDt', namespaces=namespace)

            non_profit_id = ein_element.text.strip() if ein_element is not None else self.ein
            year = "Unknown"
            
            if tax_year_element is not None and tax_year_element.text:
                year = tax_year_element.text.strip()
            elif return_ts_element is not None and return_ts_element.text:
                try:
                    date_obj = datetime.strptime(return_ts_element.text.strip()[:10], "%Y-%m-%d")
                    year = str(date_obj.year)
                except:
                    pass
            elif tax_period_end_element is not None and tax_period_end_element.text:
                try:
                    date_obj = datetime.strptime(tax_period_end_element.text.strip(), "%Y-%m-%d")
                    year = str(date_obj.year)
                except:
                    pass

            return non_profit_id, year

        except Exception as e:
            self.logger.warning(f"Error extracting identifiers: {e}")
            return self.ein, "Unknown"

    def _parse_xml_content(self, xml_content: str) -> Tuple[List[Dict], Set[str]]:
        """
        Parse XML content into records list and unique fields set.
        Now includes group index tracking for repeated elements.
        """
        try:
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            xml_io = BytesIO(xml_content.encode('utf-8'))
            tree = etree.parse(xml_io, parser)
            root = tree.getroot()
            
            if root is None:
                self.logger.error("Failed to create XML root element")
                return [], set()

            non_profit_id, year = self._extract_identifiers(root)
            records = []
            unique_fields = set()
            group_counters = defaultdict(int)
            
            def traverse(element, path=""):
                try:
                    # Check if this is a group element
                    is_group = any(group_type in element.tag 
                                for group_type in ['Grp', 'Group', 'Table'])
                    
                    # Get the clean element tag
                    clean_tag = self._clean_column_name(element.tag)
                    
                    # For group elements, add an index
                    if is_group:
                        group_key = f"{path}/{clean_tag}"
                        group_counters[group_key] += 1
                        group_index = group_counters[group_key]
                        current_path = f"{year}/{path}/{clean_tag}[{group_index}]"
                    else:
                        current_path = f"{year}/{path}/{clean_tag}" if path else f"{year}/{clean_tag}"
                    
                    if element.text and element.text.strip():
                        field = {
                            "non_profit_id": non_profit_id,
                            "year": year,
                            "field_path": current_path,
                            "field_name": clean_tag,
                            "value": element.text.strip(),
                            "group_index": group_counters[f"{path}/{clean_tag}"] if is_group else None
                        }
                        records.append(field)
                        unique_fields.add(current_path)
                    
                    for key, value in element.attrib.items():
                        field_path = f"{current_path}/@{key}"
                        field = {
                            "non_profit_id": non_profit_id,
                            "year": year,
                            "field_path": field_path,
                            "field_name": key,
                            "value": value.strip(),
                            "group_index": group_counters[f"{path}/{clean_tag}"] if is_group else None
                        }
                        records.append(field)
                        unique_fields.add(field_path)
                    
                    for child in element:
                        traverse(child, current_path)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing element in traverse: {e}")
                    
            traverse(root)
            
            if records:
                self.logger.info(f"Successfully parsed XML with {len(records)} records for year {year}")
            
            return records, unique_fields
            
        except Exception as e:
            self.logger.error(f"Error in XML parsing: {e}")
            return [], set()

    def _download_and_parse_xml(self, url: str) -> pd.DataFrame:
        """
        Download and parse a single XML file, saving it locally.

        :param url: URL of the XML file to download
        :type url: str
        :return: DataFrame containing parsed XML data
        :rtype: pandas.DataFrame
        :raises ConnectionError: If download fails
        :raises IOError: If file saving fails
        :raises XMLSyntaxError: If XML parsing fails
        """
        try:
            response = self.session.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()

            content = response.content.decode('utf-8-sig')
            if not content.lstrip().startswith('<?xml'):
                content = f'<?xml version="1.0" encoding="UTF-8"?>\n{content}'

            current_directory = os.getcwd()
            xml_bank_dir = os.path.join(current_directory, "XML_bank")
            folder_name = os.path.join(xml_bank_dir, self.ein)
            os.makedirs(folder_name, exist_ok=True)
            file_name = os.path.join(folder_name, f"{self.ein}_{url.split('/')[-1]}.xml")
            
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(content)
            self.logger.info(f"Saved XML to {file_name}")

            records, _ = self._parse_xml_content(content)
            return pd.DataFrame(records) if records else pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error processing URL {url}: {e}")
            return pd.DataFrame()

    def process_all_xml(self, max_workers: int = 4, delay: float = 2.0) -> pd.DataFrame:
        """
        Process all available XML files for the nonprofit.

        :param max_workers: Maximum number of concurrent workers
        :type max_workers: int
        :param delay: Delay between requests in seconds
        :type delay: float
        :return: Combined DataFrame of all processed XML data
        :rtype: pandas.DataFrame
        :raises RuntimeError: If processing fails for all files
        """
        xml_urls = self.get_xml_links()
        if not xml_urls:
            self.logger.error("No XML files found to process.")
            return pd.DataFrame()

        dfs = []
        successful_files = 0
        
        for url in xml_urls:
            try:
                self.logger.info(f"Processing URL: {url}")
                df = self._download_and_parse_xml(url)
                if not df.empty:
                    dfs.append(df)
                    successful_files += 1
                time.sleep(delay)
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")

        if not dfs:
            self.logger.error("No data was successfully processed.")
            return pd.DataFrame()

        combined_df = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Successfully processed {successful_files} out of {len(xml_urls)} XML files")
        return combined_df

def process_ein(ein: str) -> pd.DataFrame:
    """
    Process XML files for a given nonprofit EIN and return the DataFrame.

    :param ein: Employer Identification Number of the nonprofit
    :type ein: str
    :return: DataFrame containing processed XML data
    :rtype: pandas.DataFrame
    :raises ValueError: If processing fails
    """
    try:
        processor = NonProfitXMLStreamProcessor(ein)
        df_long = processor.process_all_xml()
        
        if 'non_profit_id' in df_long.columns:
            df_long = df_long.rename(columns={'non_profit_id': 'EIN'})
            
        # Create base directory
        current_directory = os.getcwd()
        base_dir = os.path.join(current_directory, 'search_data')
        os.makedirs(base_dir, exist_ok=True)
        
        # Save to parquet
        file_path = os.path.join(base_dir, f"{ein}_long.parquet")
        df_long.to_parquet(file_path)
        
        return df_long

    except Exception as e:
        raise ValueError(f"Failed to process EIN {ein}: {e}")

def save_to_parquet(df: pd.DataFrame, ein: str, base_dir: str = 'search_data') -> str:
    """
    Save the long-format DataFrame to a parquet file.

    :param df: DataFrame containing nonprofit XML data
    :type df: pandas.DataFrame
    :param ein: Employer Identification Number of the nonprofit
    :type ein: str
    :param base_dir: Directory where the parquet file will be saved
    :type base_dir: str
    :return: Path to the saved parquet file
    :rtype: str
    """
    try:
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
            
        # Create directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Construct file path
        file_path = os.path.join(base_dir, f"{ein}_long.parquet")
        
        # Save DataFrame to parquet
        df.to_parquet(file_path)
        
        return file_path
        
    except Exception as e:
        raise IOError(f"Failed to save parquet file: {str(e)}")

def process_multiple_eins(ein_list: List[str], base_dir: str = 'search_data') -> Dict[str, pd.DataFrame]:
    """
    Process multiple EINs and return their respective DataFrames.
    
    :param ein_list: List of EINs to process
    :type ein_list: List[str]
    :param base_dir: Base directory for saving data
    :type base_dir: str
    :return: Dictionary mapping EINs to their respective DataFrames
    :rtype: Dict[str, pd.DataFrame]
    """
    results = {}
    errors = []
    
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Process each EIN
    for ein in ein_list:
        try:
            print(f"\nProcessing EIN: {ein}")
            df = process_ein(ein)
            
            if not df.empty:
                results[ein] = df
                
                # Save to parquet
                file_path = save_to_parquet(df, ein, base_dir)
                print(f"Saved data for EIN {ein} to {file_path}")
            else:
                print(f"No data found for EIN {ein}")
                errors.append((ein, "Empty DataFrame returned"))
                
        except Exception as e:
            print(f"Error processing EIN {ein}: {str(e)}")
            errors.append((ein, str(e)))
            continue
    
    # Save error log if there were any errors
    if errors:
        error_log_path = os.path.join(base_dir, 'processing_errors.txt')
        with open(error_log_path, 'w') as f:
            f.write("EIN Processing Errors:\n")
            for ein, error in errors:
                f.write(f"EIN {ein}: {error}\n")
        print(f"\nError log saved to: {error_log_path}")
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total EINs attempted: {len(ein_list)}")
    print(f"Successfully processed: {len(results)}")
    print(f"Failed: {len(errors)}")
    
    return results

def batch_process_eins(ein_file_path: str, batch_size: int = 5, delay_between_batches: float = 60.0) -> Dict[str, pd.DataFrame]:
    """
    Process EINs in batches from a file with delays between batches to avoid rate limiting.
    
    :param ein_file_path: Path to file containing EINs (one per line)
    :type ein_file_path: str
    :param batch_size: Number of EINs to process in each batch
    :type batch_size: int
    :param delay_between_batches: Delay in seconds between processing batches
    :type delay_between_batches: float
    :return: Dictionary mapping EINs to their respective DataFrames
    :rtype: Dict[str, pd.DataFrame]
    """
    # Read EINs from file
    with open(ein_file_path, 'r') as f:
        eins = [line.strip() for line in f if line.strip()]
    
    all_results = {}
    total_batches = (len(eins) + batch_size - 1) // batch_size
    
    print(f"Found {len(eins)} EINs to process in {total_batches} batches")
    
    # Process in batches
    for i in range(0, len(eins), batch_size):
        batch = eins[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\nProcessing batch {batch_num} of {total_batches}")
        print(f"EINs in this batch: {', '.join(batch)}")
        
        # Process the batch
        batch_results = process_multiple_eins(batch)
        all_results.update(batch_results)
        
        # Delay before next batch (except for the last batch)
        if i + batch_size < len(eins):
            print(f"\nWaiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)
    
    return all_results

if __name__ == "__main__":
    try:
        # Example 1: Process single EIN
        ein = "237172306"
        df_long = process_ein(ein)
        file_path = save_to_parquet(df_long, ein)
        print(f"Successfully saved data to {file_path}")
        
        # Example 2: Process multiple EINs
        # ein_list = ["237172306", "131644147", "131675294"]
        # results = process_multiple_eins(ein_list)
        
        # Example 3: Process from file in batches (commented out by default)
        # batch_results = batch_process_eins('ein_list.txt', batch_size=3, delay_between_batches=120.0)
        
    except Exception as e:
        print(f"Error: {str(e)}")


# 362722198 - Benedictine University
# 541603842 - George Mason University Foundation Inc
# 346576610 - Youngstown State University Foundation
# 951644037 - Pepperdine University
# 160743140 - Rochester Institute Of Technology
# 160865182 - University At Buffalo Foundation Inc
# 620465076 - Belmont University
# 042111203 - Clark University
# 362167048 - DePaul University
# 251035663 - Duquesne University
# 980681431 - Embry-Riddle Aeronautical University
# 581845423 - Georgia State University
# 111630906 - Hofstra University
# 060646701 - Quinnipiac University
# 383555142 - Wayne State University
# 486121167 - Wichita State University

# 344431169 - University Of Findlay
# 541071867 - Inova Health System Foundation
# 226029397 - Robert Wood Johnson Foundation
# 363635349 - Ronald & Maxine Linde Foundation
# 396786592 - Ray And Kay Eckstein Charitable Trust
# 621134070 - The Frist Foundation
# 741143071 - Paso Del Norte Health Foundation
# 460428166 - Waitt Foundation
# 542074788 - James S Mcdonnell Foundation
# 520895843 - Society For Neuroscience
# 311777710 - Foundation For Educational Funding
# 470606382 - Educationquest Foundation Inc
# 520794249 - Hoffberger Foundation Inc
# 846032307 - Morris Animal Foundation

# 880714148 - Maddie Mae Fund
# Morningstar Foundation
# George Family Foundation