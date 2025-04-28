import os
import json
import logging
import pandas as pd
import yfinance as yf
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from dataclasses import dataclass, field
from typing import Dict, List

# os.environ["http_proxy"] = "http://webproxy.blackrock.com:8080"
# os.environ["https_proxy"] = "http://webproxy.blackrock.com:8080"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

@dataclass
class DataLoader:
    tickers_file: str = 'pages/03_thematic_basket/basket_issuers.json'
    session: requests.Session = field(default_factory=requests.Session, init=False)
    tickers: Dict[str, List[str]] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        # Disable SSL verification warnings and session verification
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.session.verify = False
        # Load tickers from JSON during initialization
        self.load_tickers_from_json()

    def load_tickers_from_json(self):
        """Load tickers from a JSON file into a dictionary."""
        try:
            with open(self.tickers_file, 'r') as file:
                self.tickers = json.load(file)
            logging.info(f"Loaded tickers from JSON file. Available categories: {list(self.tickers.keys())}")
        except Exception as e:
            logging.error(f"Error loading tickers from JSON file: {e}")
            raise

    def fetch_company_info(self, ticker: str) -> dict:
        """Fetches sector, industry, and other information for a given ticker."""
        try:
            # Check if ticker is an index/benchmark (starts with ^)
            if ticker.startswith('^'):
                return {
                    "Ticker": ticker,
                    "Company": ticker.replace('^', '').upper(),
                    "Sector": "Index",
                    "Industry": "Benchmark",
                    "Market Cap (Billions)": None,
                    "Issuer Type": "Benchmark"
                }

            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            market_cap = info.get("marketCap", None)
            market_cap_billions = market_cap / 1_000_000_000 if market_cap else None
            
            company_info = {
                "Ticker": ticker,
                "Company": info.get("longName", ticker),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Market Cap (Billions)": market_cap_billions,
                "Issuer Type": "Issuer"
            }
            logging.info(f"Fetched company info for {ticker}: {company_info}")
            return company_info
        except Exception as e:
            logging.error(f"Error fetching company info for {ticker}: {e}")
            return {
                "Ticker": ticker,
                "Company": ticker,
                "Sector": None,
                "Industry": None,
                "Market Cap (Billions)": None,
                "Issuer Type": "Issuer"
            }

    def get_company_info_for_tickers(self, ticker_list: List[str]) -> pd.DataFrame:
        """Fetches company information for a list of tickers and returns it as a DataFrame."""
        company_info_list = [self.fetch_company_info(ticker) for ticker in ticker_list]
        return pd.DataFrame(company_info_list)

    def download_data(self, start_date: str = "2019-01-01") -> Dict[str, pd.DataFrame]:
        """Downloads historical data for each category of tickers and merges with company info."""
        data_dict = {}
        
        for category, ticker_list in self.tickers.items():
            logging.info(f"Downloading data for category '{category}' with tickers: {ticker_list}")
            data = yf.download(ticker_list, start=start_date, session=self.session, progress=False)
            if data.empty:
                logging.warning(f"No data fetched for category '{category}'.")
                continue
            
            # Handle the multi-index columns from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                # Flatten the multi-index and keep only the 'Close' prices
                close_prices = data['Close']
                close_prices.columns = ticker_list
            else:
                close_prices = data
            
            # Reshape the data to long format
            df_long = close_prices.reset_index().melt(
                id_vars=['Date'],
                value_vars=ticker_list,
                var_name='Ticker',
                value_name='Price'
            )
            
            # Add category column
            df_long['Category'] = category
            
            # Get company info and merge
            company_info_df = self.get_company_info_for_tickers(ticker_list)
            merged_data = pd.merge(df_long, company_info_df, on="Ticker", how="left")
            
            # Format the Date column
            merged_data['Date'] = pd.to_datetime(merged_data['Date']).dt.strftime('%Y-%m-%d')
            
            data_dict[category] = merged_data
        
        logging.info("Data download and merging with company info complete.")
        return data_dict

    def assign_equal_weights(self, data: pd.DataFrame, category: str) -> pd.DataFrame:
        """Assigns equal weights to each ticker in a given category's data."""
        if data.empty:
            logging.warning(f"No data available to assign weights for category '{category}'.")
            return data

        num_tickers = len(self.tickers[category])
        weight = 1 / num_tickers if num_tickers > 1 else 1
        data['Weight'] = weight
        logging.info(f"Assigned equal weight of {weight} for each ticker in category '{category}'.")
        return data

    def save_weighted_baskets(self, weighted_baskets: Dict[str, pd.DataFrame], directory: str = "baskets") -> None:
        """Saves the weighted baskets in Parquet format."""
        os.makedirs(directory, exist_ok=True)
        
        for category, data in weighted_baskets.items():
            file_path = os.path.join(directory, f"{category}_basket.parquet")
            data.to_parquet(file_path, engine='pyarrow')
            logging.info(f"Saved {category} basket to '{file_path}' in Parquet format")

    def load_weighted_baskets(self, directory: str = "baskets") -> Dict[str, pd.DataFrame]:
        """Load weighted baskets exclusively from Parquet files in the specified directory."""
        weighted_baskets = {}
        
        for filename in os.listdir(directory):
            if filename.endswith(".parquet"):
                category = filename.replace("_basket.parquet", "")
                file_path = os.path.join(directory, filename)
                data = pd.read_parquet(file_path, engine='pyarrow')
                weighted_baskets[category] = data
                logging.info(f"Loaded {category} basket from '{file_path}' in Parquet format")

        return weighted_baskets


# Create instance
data_loader = DataLoader()

# Download data with company information
data_dict = data_loader.download_data("2019-01-01")

# Assign weights
weighted_baskets = {}
for category, data in data_dict.items():
    weighted_data = data_loader.assign_equal_weights(data, category)
    weighted_baskets[category] = weighted_data

weighted_baskets


# Save the baskets
data_loader.save_weighted_baskets(weighted_baskets)

# Load them back if needed
loaded_baskets = data_loader.load_weighted_baskets()
loaded_baskets
