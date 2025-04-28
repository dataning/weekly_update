import os
import time
from typing import List

import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Constants
CACHE_PATH = "data/latest_sp500.parquet"
CACHE_EXPIRY_SEC = 24 * 3600  # 24 hours


def get_sp500_symbols() -> List[str]:
    """
    Retrieve the current list of S&P 500 symbols from Wikipedia.

    Returns:
        A list of ticker symbols with dots replaced by hyphens.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url, header=0)[0]
    return table['Symbol'].str.replace('.', '-', regex=False).tolist()


def fetch_latest_info(symbols: List[str]) -> List[dict]:
    """
    For each symbol, fetch the last two trading days of history
    to extract dates, latest price, and previous close.

    Returns:
        List of dicts with symbol, dates, prices, and raw info.
    """
    info_list = []
    for sym in tqdm(symbols, desc="Fetching prices", unit="symbol"):
        ticker = yf.Ticker(sym)
        # Get last 2 trading days to capture previous close and latest
        try:
            hist = ticker.history(period="2d", auto_adjust=False)
        except Exception:
            continue
        if hist.shape[0] < 2:
            continue
        # Extract data
        prev_date = hist.index[-2].date()
        prev_close = hist['Close'].iloc[-2]
        latest_date = hist.index[-1].date()
        latest_price = hist['Close'].iloc[-1]
        info_list.append({
            'Symbol': sym,
            'Date_prev': prev_date,
            'Previous_Close': float(prev_close),
            'Date_latest': latest_date,
            'Latest_Price': float(latest_price),
            'info': ticker.info,
        })
    return info_list


def build_df(prices: List[dict]) -> pd.DataFrame:
    """
    Construct a DataFrame with dates, latest price, previous close,
    market cap, and performance.
    """
    rows = []
    for entry in prices:
        sym = entry['Symbol']
        prev_date = entry['Date_prev']
        prev = entry['Previous_Close']
        latest_date = entry['Date_latest']
        latest = entry['Latest_Price']
        info = entry['info']

        name = info.get('longName') or info.get('shortName') or sym
        shares = info.get('sharesOutstanding', 0)
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        if not shares:
            continue

        market_cap = latest * shares
        performance = 100 * (latest - prev) / prev

        rows.append({
            'Symbol': sym,
            'Name': name,
            'Industry': industry,
            'Sector': sector,
            'Date_prev': prev_date,
            'Previous_Close': prev,
            'Date_latest': latest_date,
            'Latest_Price': latest,
            'Market Cap': market_cap,
            'Performance': performance,
        })
    df = pd.DataFrame(rows)
    columns = [
        'Symbol', 'Name', 'Industry', 'Sector',
        'Date_prev', 'Previous_Close',
        'Date_latest', 'Latest_Price',
        'Market Cap', 'Performance',
    ]
    return df[columns]


def get_latest_df(
    symbols: List[str],
    cache_path: str = CACHE_PATH,
    expiry_seconds: int = CACHE_EXPIRY_SEC
) -> pd.DataFrame:
    """
    Retrieve the latest S&P 500 metrics, caching the result for a day.
    """
    if os.path.exists(cache_path):
        age = time.time() - os.path.getmtime(cache_path)
        if age < expiry_seconds:
            return pd.read_parquet(cache_path)

    prices = fetch_latest_info(symbols)
    df = build_df(prices)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_parquet(cache_path)
    return df


def main() -> None:
    """
    Main entry point: fetch symbols, retrieve latest snapshot, and print DataFrame.
    """
    symbols = get_sp500_symbols()
    df = get_latest_df(symbols)
    print(df)


if __name__ == "__main__":
    main()
