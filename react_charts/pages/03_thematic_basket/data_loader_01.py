import os
import json
import logging
import pandas as pd
import yfinance as yf
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from dataclasses import dataclass, field
from typing import Dict, List
from tqdm.auto import tqdm

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
            # Handle index/benchmark tickers
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
            
            return {
                "Ticker": ticker,
                "Company": info.get("longName", ticker),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Market Cap (Billions)": market_cap_billions,
                "Issuer Type": "Issuer"
            }
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
        """Fetches company information for a list of tickers with a progress bar."""
        company_info_list = []
        for ticker in tqdm(ticker_list, desc="⏳ Company info", leave=False):
            company_info_list.append(self.fetch_company_info(ticker))
        return pd.DataFrame(company_info_list)

    def download_data(self, start_date: str = "2019-01-01") -> Dict[str, pd.DataFrame]:
        """Downloads historical data for each category and merges with company info, with progress bars."""
        data_dict = {}
        for category, ticker_list in tqdm(
            self.tickers.items(),
            desc="⬇️ Downloading baskets",
            total=len(self.tickers),
        ):
            logging.info(f"Downloading data for category '{category}' with tickers: {ticker_list}")
            data = yf.download(
                ticker_list,
                start=start_date,
                session=self.session,
                progress=False
            )
            if data.empty:
                logging.warning(f"No data fetched for category '{category}'.")
                continue
            
            # Flatten multi-index if present, keep Close prices
            if isinstance(data.columns, pd.MultiIndex):
                close_prices = data['Close']
                close_prices.columns = ticker_list
            else:
                close_prices = data

            # Reshape to long format
            df_long = close_prices.reset_index().melt(
                id_vars=['Date'],
                value_vars=ticker_list,
                var_name='Ticker',
                value_name='Price'
            )
            df_long['Category'] = category

            # Fetch & merge company info
            company_info_df = self.get_company_info_for_tickers(ticker_list)
            merged = pd.merge(df_long, company_info_df, on="Ticker", how="left")
            merged['Date'] = pd.to_datetime(merged['Date']).dt.strftime('%Y-%m-%d')

            data_dict[category] = merged

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
        logging.info(f"Assigned equal weight of {weight:.4f} for each ticker in '{category}'.")
        return data

    def save_weighted_baskets(self, weighted_baskets: Dict[str, pd.DataFrame], directory: str = "baskets"):
        """Saves the weighted baskets in Parquet format."""
        os.makedirs(directory, exist_ok=True)
        for category, df in weighted_baskets.items():
            path = os.path.join(directory, f"{category}_basket.parquet")
            df.to_parquet(path, engine='pyarrow')
            logging.info(f"Saved '{category}' basket to '{path}'")

    def load_weighted_baskets(self, directory: str = "baskets") -> Dict[str, pd.DataFrame]:
        """Loads weighted baskets from Parquet files."""
        baskets = {}
        for fn in os.listdir(directory):
            if fn.endswith(".parquet"):
                cat = fn.replace("_basket.parquet", "")
                path = os.path.join(directory, fn)
                baskets[cat] = pd.read_parquet(path, engine='pyarrow')
                logging.info(f"Loaded '{cat}' basket from '{path}'")
        return baskets


if __name__ == "__main__":
    # Instantiate and run
    loader = DataLoader()
    data_dict = loader.download_data("2019-01-01")

    weighted = {
        cat: loader.assign_equal_weights(df, cat)
        for cat, df in data_dict.items()
    }

    loader.save_weighted_baskets(weighted)
    loaded_baskets = loader.load_weighted_baskets()
    # Optionally inspect:
    for cat, df in loaded_baskets.items():
        print(f"{cat}: {len(df)} rows")

