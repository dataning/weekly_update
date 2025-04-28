
----

# What is information ratio?

The information ratio (IR) is similar to the Sharpe ratio but uses a benchmark rather than the risk-free rate. The benchmark is usually chosen to represent the available investment universe such as the S&P 500 for a portfolio on large-cap US equities. In other words, IR is a measure of the risk-adjusted returns of a portfolio, where a higher ratio indicates that the portfolio has generated higher returns per unit of risk relative to the benchmark. 

----

# How do calculate information ratio

The IR measures the excess return of the portfolio, also called alpha, relative to the tracking error, which is the deviation of the portfolio returns from the benchmark returns

 $$ IR = \frac{Alpha}{Tracking\ Error}  $$

To calculate the information ratio in a Pandas dataframe, you will need to first calculate the excess returns of your portfolio over a benchmark, and then divide that by the portfolio's standard deviation of returns. 

```python
import pandas as pd

# Load the data for the portfolio and benchmark returns
returns = pd.read_csv('portfolio_returns.csv')
benchmark_returns = pd.read_csv('benchmark_returns.csv')

# Calculate the excess returns by subtracting the benchmark returns from the portfolio returns
excess_returns = returns - benchmark_returns

# Calculate the standard deviation of the excess returns
std_dev = excess_returns.std()

# Calculate the information ratio by dividing the mean of the excess returns by the standard deviation
information_ratio = excess_returns.mean() / std_dev

print(information_ratio)
```