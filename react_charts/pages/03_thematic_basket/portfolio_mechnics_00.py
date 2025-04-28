import os
import json
import logging
import pandas as pd
from pandas.tseries.offsets import MonthEnd, QuarterEnd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class PortfolioPerformanceCalculator:
    weighted_baskets: Dict[str, pd.DataFrame] = field(default_factory=dict)
    basket_benchmark_mapping: Dict[str, str] = field(default_factory=dict)
    end_date: Optional[datetime] = None

    # Store calculated results
    basket_performances: Dict[str, pd.Series] = field(default_factory=dict)
    benchmark_performances: Dict[str, pd.Series] = field(default_factory=dict)
    performance_summary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    relative_performance: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        if not self.basket_benchmark_mapping:
            self.basket_benchmark_mapping = self.load_benchmark_mapping("basket_benchmark_mapping.json")

        # Ensure end_date is a datetime object
        if self.end_date is None and self.weighted_baskets:
            first_basket = next(iter(self.weighted_baskets.values()))
            self.end_date = pd.to_datetime(first_basket['Date'].max())
        elif self.end_date is not None:
            self.end_date = pd.to_datetime(self.end_date)

    @staticmethod
    def load_benchmark_mapping(file_path: str) -> Dict[str, str]:
        """Load basket benchmark mapping from a JSON file."""
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def load_weighted_baskets(format: str = "json", directory: str = "baskets") -> Dict[str, pd.DataFrame]:
        """Load weighted baskets from local files in JSON or Parquet format."""
        weighted_baskets = {}

        if format == "json":
            file_path = os.path.join(directory, 'weighted_baskets.json')
            with open(file_path, "r") as f:
                weighted_baskets_json = json.load(f)
                weighted_baskets = {name: pd.DataFrame(data) for name, data in weighted_baskets_json.items()}
            logging.info(f"Weighted baskets loaded from '{file_path}' in JSON format")

        elif format == "parquet":
            for filename in os.listdir(directory):
                if filename.endswith(".parquet"):
                    category = filename.replace("_basket.parquet", "")
                    file_path = os.path.join(directory, filename)
                    weighted_baskets[category] = pd.read_parquet(file_path, engine='pyarrow')
                    logging.info(f"Loaded {category} basket from '{file_path}' in Parquet format")

        else:
            raise ValueError("Invalid format specified. Choose 'json' or 'parquet'.")

        return weighted_baskets

    def calculate_daily_returns(self) -> None:
        """Calculate daily returns for each basket and unique benchmark."""
        # Calculate daily returns for baskets
        for name, basket_data in self.weighted_baskets.items():
            # Convert Date to datetime and set as index
            basket_data = basket_data.copy()
            basket_data['Date'] = pd.to_datetime(basket_data['Date'])
            basket_data.set_index('Date', inplace=True)
            
            # Group by Date and Ticker to handle multiple entries per day
            grouped = basket_data.groupby(['Date', 'Ticker']).last().reset_index()
            
            # Pivot the data to get prices in columns
            prices = grouped.pivot(index='Date', columns='Ticker', values='Price')
            
            # Calculate daily returns
            daily_returns = prices.ffill().pct_change(fill_method=None).fillna(0)
            
            # Get weights for each ticker
            weights = grouped.groupby('Ticker')['Weight'].first()
            
            # Calculate weighted returns
            weighted_returns = daily_returns.multiply(weights, axis=1)
            self.basket_performances[name] = weighted_returns.sum(axis=1)

        # Identify unique benchmark tickers and calculate daily returns for them
        unique_benchmarks = set(self.basket_benchmark_mapping.values())
        for benchmark_ticker in unique_benchmarks:
            if benchmark_ticker in self.weighted_baskets:
                benchmark_data = self.weighted_baskets[benchmark_ticker].copy()
                benchmark_data['Date'] = pd.to_datetime(benchmark_data['Date'])
                benchmark_data.set_index('Date', inplace=True)
                
                # Calculate returns directly for benchmarks (usually single ticker)
                daily_returns = (
                    benchmark_data['Price']
                    .ffill()
                    .pct_change(fill_method=None)
                    .fillna(0)
                )
                self.benchmark_performances[benchmark_ticker] = daily_returns

        logging.info(f"Calculated daily returns for {len(self.basket_performances)} baskets and {len(self.benchmark_performances)} benchmarks")

    @staticmethod
    def rebase_returns(returns_df: pd.DataFrame, base_value: float = 100) -> pd.DataFrame:
        """
        Rebase a DataFrame of returns to a specified base value.
        
        Parameters:
        -----------
        returns_df : pd.DataFrame
            DataFrame containing returns (not cumulative returns)
        base_value : float, default 100
            Starting value for the rebased series
            
        Returns:
        --------
        pd.DataFrame
            Rebased performance series starting at base_value
        """
        return base_value * (1 + returns_df).cumprod()

    def get_aligned_performance_dfs(self, 
                                  rebase: bool = False, 
                                  base_value: float = 100,
                                  cumulative: bool = False,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Return aligned basket and benchmark performances as DataFrames with optional date filtering.
        """
        basket_df = pd.DataFrame(self.basket_performances)
        benchmark_df = pd.DataFrame(self.benchmark_performances)
        
        # Convert string dates to datetime if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)
        
        # Align indices
        combined_index = basket_df.index.union(benchmark_df.index)
        basket_df = basket_df.reindex(combined_index)
        benchmark_df = benchmark_df.reindex(combined_index)
        
        # Apply date filtering
        if start_date or end_date:
            date_mask = pd.Series(True, index=combined_index)
            if start_date:
                date_mask &= combined_index >= start_date
            if end_date:
                date_mask &= combined_index <= end_date
            
            basket_df = basket_df[date_mask]
            benchmark_df = benchmark_df[date_mask]
            
            # Recalculate returns for the first day of filtered period
            if start_date and not basket_df.empty:
                basket_df.iloc[0] = 0
                benchmark_df.iloc[0] = 0
        
        # Apply transformations after date filtering
        if rebase:
            basket_df = self.rebase_returns(basket_df, base_value)
            benchmark_df = self.rebase_returns(benchmark_df, base_value)
        elif cumulative:
            basket_df = self.calculate_cumulative_return(basket_df)
            benchmark_df = self.calculate_cumulative_return(benchmark_df)
        
        return basket_df, benchmark_df

    def _get_date_range(self, performance: pd.Series, period: str) -> tuple:
            """Get start and end dates for a period."""
            end_date = self.end_date
            
            if period == 'MTD':
                start_date = end_date.to_period('M').start_time
            elif period == '1m':
                start_date = end_date - pd.DateOffset(months=1)
            elif period == 'QTD':
                start_date = end_date.to_period('Q').start_time
            elif period == '3m':
                start_date = end_date - pd.DateOffset(months=3)
            elif period == '6m':
                start_date = end_date - pd.DateOffset(months=6)
            elif period == 'YTD':
                start_date = end_date.replace(month=1, day=1)
            elif period == '12m':
                start_date = end_date - pd.DateOffset(months=12)
            else:
                raise ValueError(f"Unsupported period: {period}")

            # Convert to timezone-naive timestamps if the input index is timezone-naive
            start_date = pd.Timestamp(start_date)
            end_date = pd.Timestamp(end_date)

            # Only handle timezone conversion if the performance index has a timezone
            if hasattr(performance.index, 'tz') and performance.index.tz is not None:
                if start_date.tz is None:
                    start_date = start_date.tz_localize(performance.index.tz)
                if end_date.tz is None:
                    end_date = end_date.tz_localize(performance.index.tz)
            else:
                # Ensure timezone-naive dates for timezone-naive index
                if start_date.tz is not None:
                    start_date = start_date.tz_localize(None)
                if end_date.tz is not None:
                    end_date = end_date.tz_localize(None)

            return start_date, end_date

    def _calculate_period_return(self, performance: pd.Series, period: str) -> float:
        """Calculate return for a specific period."""
        start_date, end_date = self._get_date_range(performance, period)
        return performance.loc[start_date:end_date].add(1).prod() - 1

    @staticmethod
    def calculate_cumulative_return(returns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cumulative returns from a DataFrame of returns.
        
        Parameters:
        -----------
        returns_df : pd.DataFrame
            DataFrame containing returns (not cumulative returns)
            
        Returns:
        --------
        pd.DataFrame
            Cumulative returns starting at 1.0
        """
        return (1 + returns_df).cumprod()

    def calculate_performance_metrics(self) -> pd.DataFrame:
        """Calculate performance metrics for all periods."""
        for basket, performance in self.basket_performances.items():
            self.performance_summary[basket] = {
                'MTD': self._calculate_period_return(performance, 'MTD'),
                '1m': self._calculate_period_return(performance, '1m'),
                'QTD': self._calculate_period_return(performance, 'QTD'),
                '3m': self._calculate_period_return(performance, '3m'),
                '6m': self._calculate_period_return(performance, '6m'),
                'YTD': self._calculate_period_return(performance, 'YTD'),
                '12m': self._calculate_period_return(performance, '12m'),
            }
        
        return pd.DataFrame(self.performance_summary).T

    def calculate_relative_performance(self) -> pd.DataFrame:
        """Calculate relative performance against benchmarks with separate columns for basket and benchmark names."""
        performance_df = pd.DataFrame(self.performance_summary).T
        relative_performance_data = []

        for basket, benchmark in self.basket_benchmark_mapping.items():
            if basket in performance_df.index and benchmark in performance_df.index:
                relative_performance = performance_df.loc[basket] - performance_df.loc[benchmark]
                relative_performance_data.append({
                    "Basket": basket,
                    "Benchmark": benchmark,
                    **relative_performance.round(2).to_dict()  # Two decimal rounding
                })

        self.relative_performance = pd.DataFrame(relative_performance_data)
        return self.relative_performance

    def calculate_ticker_contributions(
            self,
            basket_name: str,
            metrics: Optional[List[str]] = None
        ) -> pd.DataFrame:
            """Calculate individual ticker contributions for a specific basket with company information."""
            if metrics is None:
                metrics = ['MTD', '1m', 'QTD', '3m', '6m', 'YTD', '12m']
                
            basket_data = self.weighted_baskets[basket_name]
            
            # Ensure Date is datetime and set as index
            basket_data = basket_data.copy()
            basket_data['Date'] = pd.to_datetime(basket_data['Date'])
            basket_data.set_index('Date', inplace=True)
            
            # Group by Date and Ticker to handle multiple entries per day
            grouped = basket_data.groupby(['Date', 'Ticker']).last().reset_index()
            
            # Pivot the data to get prices in columns
            prices = grouped.pivot(index='Date', columns='Ticker', values='Price')
            
            # Calculate daily returns
            daily_returns = prices.ffill().pct_change().fillna(0)
            
            # Get weights for each ticker
            weights = grouped.groupby('Ticker')['Weight'].first()

            # Get company information for each ticker
            company_info = grouped.groupby('Ticker').agg({
                'Company': 'first',
                'Sector': 'first',
                'Industry': 'first',
                'Market Cap (Billions)': 'first',
                'Issuer Type': 'first',
                'Weight': 'first'
            }).fillna('N/A')

            contributions = {}
            for metric in metrics:
                # Define the period for cumulative return calculation
                start_date, end_date = self._get_date_range(daily_returns.index.to_series(), metric)
                
                # Calculate cumulative returns for each ticker over the period
                period_returns = daily_returns.loc[start_date:end_date]
                cumulative_returns = (period_returns + 1).prod() - 1
                
                # Calculate weighted contribution for each ticker
                contributions[f'{metric}_abs'] = (cumulative_returns * weights).fillna(0)
                
                # Calculate the total performance for the period
                total_performance = contributions[f'{metric}_abs'].sum()
                
                # Compute relative contributions
                if abs(total_performance) > 1e-10:  # Avoid division by zero
                    contributions[f'{metric}_rel'] = contributions[f'{metric}_abs'] / total_performance
                else:
                    contributions[f'{metric}_rel'] = pd.Series(0, index=contributions[f'{metric}_abs'].index)

            # Convert contributions to DataFrame
            contributions_df = pd.DataFrame(contributions)
            
            # Merge with company information
            result_df = pd.merge(
                company_info,
                contributions_df,
                left_index=True,
                right_index=True,
                how='left'
            )
            
            # Sort by absolute contribution to YTD (or first available period if YTD not present)
            sort_column = next((col for col in contributions_df.columns if 'YTD_abs' in col), 
                            next((col for col in contributions_df.columns if '_abs' in col), None))
            if sort_column:
                result_df = result_df.sort_values(by=sort_column, ascending=False)

            # Reorder columns to put company info first
            company_cols = ['Company', 'Sector', 'Industry', 'Market Cap (Billions)', 'Issuer Type',  'Weight']
            metric_cols = [col for col in result_df.columns if col not in company_cols]
            result_df = result_df[company_cols + metric_cols]

            return result_df

# Example usage:
loaded_baskets_parquet = PortfolioPerformanceCalculator.load_weighted_baskets(format="parquet"); loaded_baskets_parquet

# Create calculator instance
calculator = PortfolioPerformanceCalculator(weighted_baskets=loaded_baskets_parquet)
# Calculate returns
calculator.calculate_daily_returns()

# Get raw returns
basket_returns_df, benchmark_returns_df = calculator.get_aligned_performance_dfs()
benchmark_returns_df

# Get cumulative returns
basket_cum_df, benchmark_cum_df = calculator.get_aligned_performance_dfs(cumulative=True)
basket_cum_df
benchmark_cum_df

# Get rebased returns with date filtering
basket_rebased_df, benchmark_rebased_df = calculator.get_aligned_performance_dfs(
    rebase=True,
    base_value=100,
    start_date="2025-01-01",
    end_date="2025-04-18"
)


performance_summary = calculator.calculate_performance_metrics(); performance_summary
performance_summary

relative_performance = calculator.calculate_relative_performance(); relative_performance

# print(relative_performance)

ticker_contributions = calculator.calculate_ticker_contributions('us_defense'); ticker_contributions


# # Load baskets from files
# # loaded_baskets_json = PortfolioPerformanceCalculator.load_weighted_baskets(format="json")
loaded_baskets_parquet = PortfolioPerformanceCalculator.load_weighted_baskets(format="parquet"); loaded_baskets_parquet

# # Initialize the calculator with loaded data
# calculator = PortfolioPerformanceCalculator(weighted_baskets=loaded_baskets_parquet)

# # Perform calculations
# calculator.calculate_daily_returns()
# performance_summary = calculator.calculate_performance_metrics()
# performance_summary
# relative_performance = calculator.calculate_relative_performance()
# relative_performance

# print("Performance Summary:\n", performance_summary)
# print("\nRelative Performance:\n", relative_performance)
# print("\nTicker Contributions:\n", ticker_contributions)