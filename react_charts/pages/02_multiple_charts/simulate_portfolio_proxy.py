import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Step 1: Simulate daily return data for 3 ETFs and a hedge fund
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', end='2023-06-30', freq='B')  # Two quarters
n = len(dates)

# Create a DataFrame for returns
returns = pd.DataFrame(index=dates)
returns['SPY'] = np.random.normal(0.0004, 0.01, n)   # Simulated US Equity ETF returns
returns['HYG'] = np.random.normal(0.0003, 0.008, n)  # Simulated High Yield Credit ETF returns
returns['BNDX'] = np.random.normal(0.0002, 0.006, n) # Simulated Global Bonds ETF returns

returns

# Simulate the hedge fund return as a weighted combination of ETFs + some alpha noise
initial_weights = {'SPY': 0.5, 'HYG': 0.25, 'BNDX': 0.15}
returns['MultiCap_Fund'] = (
    initial_weights['SPY'] * returns['SPY'] +
    initial_weights['HYG'] * returns['HYG'] +
    initial_weights['BNDX'] * returns['BNDX'] +
    np.random.normal(0, 0.001, n)  # Add alpha noise
)

# Step 2: Define quarterly manager-reported weights
quarterly_reports = [
    {'date': '2023-04-01', 'weights': {'SPY': 0.4, 'HYG': 0.35, 'BNDX': 0.15}},  # Q1
    {'date': '2023-07-01', 'weights': {'SPY': 0.35, 'HYG': 0.4, 'BNDX': 0.15}},  # Q2
]
quarterly_reports

# Step 3: Walk through calibration for each quarter
calibration_steps = []

tickers = ['SPY', 'HYG', 'BNDX']


for report in quarterly_reports:
    report_date = pd.to_datetime(report['date'])
    
    # Step 3a: Select the lookback window (last 60 business days)
    lookback_returns = returns.loc[:report_date].tail(60)
    
    # Step 3b: Run linear regression to estimate factor exposures (proxies)
    X = lookback_returns[tickers]
    y = lookback_returns['MultiCap_Fund']
    model = LinearRegression().fit(X, y)
    estimated_weights = dict(zip(tickers, model.coef_))
    
    # Step 3c: Blend with manager-reported weights (50/50)
    reported_weights = report['weights']
    blended_weights = {
        t: 0.5 * estimated_weights.get(t, 0) + 0.5 * reported_weights.get(t, 0)
        for t in tickers
    }
    
    # Step 3d: Record the calibration step
    calibration_steps.append({
        'Date': report_date,
        'Estimated Weights': estimated_weights,
        'Reported Weights': reported_weights,
        'Blended Weights': blended_weights
    })

calibration_steps

# Step 4: Format into a readable DataFrame
records = []
for step in calibration_steps:
    for t in tickers:
        records.append({
            'Date': step['Date'],
            'ETF': t,
            'Estimated': step['Estimated Weights'][t],
            'Reported': step['Reported Weights'][t],
            'Blended': step['Blended Weights'][t]
        })

calibration_df = pd.DataFrame(records)

calibration_df
