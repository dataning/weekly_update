import os
import json
import logging
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple, List

import pandas as pd
from pandas.tseries.offsets import MonthEnd
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Pre-defined offsets for period calculations
def _mtd_period(end: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    return end.to_period('M').start_time, end

_PERIOD_OFFSETS = {
    'MTD': _mtd_period,
    '1m': lambda end: (end - MonthEnd(1) + MonthEnd(0), end),
    '3m': lambda end: (end - pd.DateOffset(months=3), end),
    '6m': lambda end: (end - pd.DateOffset(months=6), end),
    'QTD': lambda end: (end.to_period('Q').start_time, end),
    'YTD': lambda end: (end.replace(month=1, day=1), end),
    '12m': lambda end: (end - pd.DateOffset(months=12), end),
}

@dataclass
class PortfolioPerformanceCalculator:
    weighted_baskets: Dict[str, pd.DataFrame] = field(default_factory=dict)
    basket_benchmark_mapping: Dict[str, str] = field(default_factory=dict)

    # Injectable loaders for testability
    data_loader: Optional[Callable[..., Dict[str, pd.DataFrame]]] = None
    mapping_loader: Optional[Callable[..., Dict[str, str]]] = None

    end_date: Optional[pd.Timestamp] = None

    # Results
    basket_performances: Dict[str, pd.Series] = field(default_factory=dict)
    benchmark_performances: Dict[str, pd.Series] = field(default_factory=dict)
    performance_summary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    relative_performance: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        # Lazy load baskets
        if self.data_loader and not self.weighted_baskets:
            self.weighted_baskets = self.data_loader()
        # Lazy load mapping
        if self.mapping_loader and not self.basket_benchmark_mapping:
            self.basket_benchmark_mapping = self.mapping_loader()

        # Determine end_date if not provided
        if self.end_date is None and self.weighted_baskets:
            any_df = next(iter(self.weighted_baskets.values()))
            self.end_date = pd.to_datetime(any_df['Date'].max())
        elif self.end_date is not None:
            self.end_date = pd.to_datetime(self.end_date)

    @staticmethod
    def load_json_mapping(path: str) -> Dict[str, str]:
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def load_weighted_baskets(format: str = 'json', directory: str = 'baskets') -> Dict[str, pd.DataFrame]:
        baskets: Dict[str, pd.DataFrame] = {}
        if format == 'json':
            path = os.path.join(directory, 'weighted_baskets.json')
            with open(path, 'r') as f:
                raw = json.load(f)
            for name, data in raw.items():
                baskets[name] = pd.DataFrame(data)
            logging.info(f"Loaded JSON baskets from {path}")
        elif format == 'parquet':
            for file in os.listdir(directory):
                if file.endswith('.parquet'):
                    name = file.replace('_basket.parquet', '')
                    full = os.path.join(directory, file)
                    baskets[name] = pd.read_parquet(full, engine='pyarrow')
                    logging.info(f"Loaded Parquet basket {name}")
        else:
            raise ValueError("format must be 'json' or 'parquet'")
        return baskets

    def _compute_returns(
        self,
        df: pd.DataFrame,
        weight_col: Optional[str] = None
    ) -> pd.Series:
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        if 'Ticker' in df.columns:
            df = df.groupby(['Date', 'Ticker']).last().reset_index()
            prices = df.pivot(index='Date', columns='Ticker', values='Price').ffill()
            returns = prices.pct_change(fill_method=None).fillna(0)
            if weight_col:
                weights = df.groupby('Ticker')[weight_col].first()
                return returns.multiply(weights, axis=1).sum(axis=1)
            else:
                return returns.iloc[:, 0]
        else:
            return df['Price'].ffill().pct_change(fill_method=None).fillna(0)

    def calculate_daily_returns(self) -> None:
        # Baskets
        for name, df in self.weighted_baskets.items():
            self.basket_performances[name] = self._compute_returns(df, weight_col='Weight')
        # Benchmarks
        unique_bench = set(self.basket_benchmark_mapping.values())
        for bench in unique_bench:
            if bench in self.weighted_baskets:
                self.benchmark_performances[bench] = self._compute_returns(
                    self.weighted_baskets[bench], weight_col=None
                )
        logging.info(f"Computed returns for {len(self.basket_performances)} baskets and {len(self.benchmark_performances)} benchmarks")

    def _get_date_range(self, period: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
        if period not in _PERIOD_OFFSETS:
            raise ValueError(f"Unsupported period: {period}")
        start, end = _PERIOD_OFFSETS[period](self.end_date)
        return pd.Timestamp(start), pd.Timestamp(end)

    @staticmethod
    def rebase_returns(returns: pd.DataFrame, base: float = 100) -> pd.DataFrame:
        return base * (1 + returns).cumprod()

    @staticmethod
    def calculate_cumulative(returns: pd.DataFrame) -> pd.DataFrame:
        return (1 + returns).cumprod()

    def get_aligned_performance_dfs(
        self,
        rebase: bool = False,
        base_value: float = 100,
        cumulative: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Return aligned basket and benchmark performance DataFrames.
        Aligns only on dates (rows), keeping basket vs. benchmark columns separate.
        Supports optional date filtering, rebase, or cumulative transformations.
        """
        # 1. Build raw DataFrames
        basket_df = pd.DataFrame(self.basket_performances)
        bench_df  = pd.DataFrame(self.benchmark_performances)

        # 2. Align only on the index (dates)
        full_idx   = basket_df.index.union(bench_df.index)
        basket_df  = basket_df.reindex(full_idx)
        bench_df   = bench_df.reindex(full_idx)

        # 3. Optional date filtering and reset first-day returns
        if start_date or end_date:
            start = pd.to_datetime(start_date) if start_date else basket_df.index.min()
            end   = pd.to_datetime(end_date)   if end_date   else basket_df.index.max()
            mask  = (basket_df.index >= start) & (basket_df.index <= end)
            basket_df = basket_df.loc[mask]
            bench_df  = bench_df.loc[mask]
            # ensure day-one returns are zero
            basket_df.iloc[0] = 0
            bench_df.iloc[0]  = 0

        # 4. Apply rebase or cumulative transform
        if rebase:
            basket_df = self.rebase_returns(basket_df, base_value)
            bench_df  = self.rebase_returns(bench_df, base_value)
        elif cumulative:
            basket_df = self.calculate_cumulative(basket_df)
            bench_df  = self.calculate_cumulative(bench_df)

        return basket_df, bench_df

    def calculate_performance_metrics(self) -> pd.DataFrame:
        summary = {}
        for name, series in self.basket_performances.items():
            metrics = {}
            for period in _PERIOD_OFFSETS:
                start, end = self._get_date_range(period)
                data = series.loc[start:end]
                metrics[period] = (data.add(1).prod() - 1) if not data.empty else 0.0
            summary[name] = metrics
        self.performance_summary = summary
        return pd.DataFrame(summary).T

    def calculate_relative_performance(self) -> pd.DataFrame:
        perf_df = pd.DataFrame(self.performance_summary).T
        data = []
        for basket, bench in self.basket_benchmark_mapping.items():
            if basket in perf_df.index and bench in perf_df.index:
                diff = perf_df.loc[basket] - perf_df.loc[bench]
                entry = {'Basket': basket, 'Benchmark': bench, **diff.to_dict()}
                data.append(entry)
        self.relative_performance = pd.DataFrame(data)
        return self.relative_performance

    def calculate_ticker_contributions(
        self,
        basket_name: str,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        if metrics is None:
            metrics = list(_PERIOD_OFFSETS.keys())
        df = self.weighted_baskets[basket_name].copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        grouped = df.groupby(['Date', 'Ticker']).last().reset_index()
        prices = grouped.pivot(index='Date', columns='Ticker', values='Price').ffill()
        daily = prices.pct_change().fillna(0)
        weights = grouped.groupby('Ticker')['Weight'].first()

        company_info = grouped.groupby('Ticker').agg({
            'Company': 'first', 'Sector': 'first', 'Industry': 'first',
            'Market Cap (Billions)': 'first', 'Issuer Type': 'first', 'Weight': 'first'
        }).fillna('N/A')

        contribs = {}
        for period in metrics:
            start, end = self._get_date_range(period)
            data = daily.loc[start:end]
            cum = (data + 1).prod() - 1
            abs_c = cum * weights
            total = abs_c.sum()
            rel_c = abs_c / total if abs(total) > 0 else abs_c * 0
            contribs[f"{period}_abs"] = abs_c
            contribs[f"{period}_rel"] = rel_c

        contrib_df = pd.DataFrame(contribs)
        result = company_info.join(contrib_df)
        return result


# from portfolio_calculator import PortfolioPerformanceCalculator

# Option A: Using built-in file loaders
calc = PortfolioPerformanceCalculator(
    data_loader=lambda: PortfolioPerformanceCalculator.load_weighted_baskets(
        format='parquet', directory='baskets'
    ),
    mapping_loader=lambda: PortfolioPerformanceCalculator.load_json_mapping(
        'basket_benchmark_mapping.json'
    )
)

# Option B: Directly passing pre-loaded dicts
# weighted_baskets = {'spx': df_spx, 'us_quality': df_usq, ...}
# mapping = {'us_quality': 'spx', ...}
# calc = PortfolioPerformanceCalculator(
#     weighted_baskets=weighted_baskets,
#     basket_benchmark_mapping=mapping
# )

# Compute returns
calc.calculate_daily_returns()

# Get aligned returns DataFrames
baskets_ret, benchmarks_ret = calc.get_aligned_performance_dfs(cumulative=True); baskets_ret, benchmarks_ret

# Performance summary
perf_df = calc.calculate_performance_metrics()
print(perf_df)

# Relative performance vs benchmarks
rel_df = calc.calculate_relative_performance()
print(rel_df)

# Ticker contributions for a basket
contrib_df = calc.calculate_ticker_contributions('us_defense')
print(contrib_df)