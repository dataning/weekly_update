
The objective of the Markowitz portfolio optimisation problem is to minimize the **portfolio variance**, given a bunch of constraints.

Portfolio variance = _weights transposed_ * _covariance matrix_ * _weights_


### Prepare dataframe
```python
import yfinance as yf
test_pf = ['GE', 'JPM', 'MSFT', 'PG']
df_pf = yf.download(test_pf, period = "10y", interval = "1d"); df_pf

# Filtering the dataframe
start_date = '2015-01-02'
end_date = '2018-03-27'
subset_df = df_pf.loc[start_date:end_date]; subset_df
df = subset_df['Close']; df
```


A portfolio manager is often asked to manage a portfolio under certain risk and return constraints, so this is a very useful function for that.

- Use the function `efficient_return()` to get the minimized risk portfolio for a target return. Obtain an efficient return portfolio, with a target return of 0.2. Store the weights of that portfolio under weights, then print and inspect the weights.
	- Get the minimum risk portfolio for a target return
	`weights = ef.efficient_return(0.2)`
	`print (weights)`
- Use `portfolio_performance` to get the performance numbers for your selected portfolio.

## Maximum Sharpe vs. minimum volatility
- The Maximum Sharpe is a special case on the efficient frontier. Of all the risk-return optimized portfolios, it has the highest Sharpe ratio. 
- The minimum volatility is also a special case, as it is the one portfolio on the efficient frontier with the lowest level of risk.

## Maximum Sharpe portfolio

Most portfolio managers are interested in finding the Maximum Sharpe portfolio on the efficient frontier, when they do their portfolio optimization. Let's calculate it with PyportfolioOpt. 
- Import the efficient frontier function again, and feed it your expected returns and covariance matrix. 
- use max_sharpe() to obtain the maximum Sharpe ratio portfolio, and store those portfolio weights to raw_weights.
- because the raw weights are the direct output of the optimization problem and difficult to read, you collect the clean weights which look tidy and better understandable.
- returns the annualized return number and annualized volatility##

### Why are some of the weights in the Maximum Sharpe portfolio zero?
Some of the expected returns of the stocks are negative. That does not necessarily exclude them from the Maximum Sharpe portfolio, but in this case, those negative stocks just lower returns without lowering the risk of the portfolio. That's why they are not part of the optimal risk-return portfolio.

## Minimum Volatility Portfolio

The minimum volatility portfolio gives you the most optimal portfolio for the least amount of risk. It's in that sense a special case, as it serves as the "lowest risk benchmark" to all other portfolios on the efficient frontier. It does perform surprisingly well over time, and therefore some managers choose this portfolio as their preferred portfolio. Calculating it is very easy with PyPortfolioOpt. Get the efficient frontier using mu and Sigma. Then, this is where things change

As a portfolio manager you often want to understand how your chosen portfolio measures up to the minimum volatility portfolio.

```python
from pypfopt.efficient_frontier import EfficientFrontier

# Expected returns is mean return
mu = expected_returns.mean_historical_return(df); mu

# Annualize the covariance matrix of the returns by 252 trading days
Sigma = risk_models.sample_cov(df); Sigma # Same as above

# ------------------------- Maximum Sharpe portfolio ------------------------- #

# Obtain the efficient frontier
ef = EfficientFrontier(mu, Sigma); ef
raw_weights = ef.max_sharpe(); raw_weights
cleaned_weights = ef.clean_weights(); cleaned_weights

# Show portfolio performance: annualized return number, annualized volatility, the Sharpe Ratio
ef.portfolio_performance(verbose=True)
ret, vol, sr = ef.portfolio_performance(verbose=True)


# --------------------- What if the target reutrn is 0.2 --------------------- #

# Get the minimum risk portfolio for a target return 0.2
weights = ef.efficient_return(0.2)
print("PyPortfolioOpt Weights:", weights)

# Show portfolio performance: annualized return number, annualized volatility, the Sharpe Ratio
ef.portfolio_performance(verbose=True)
ret, vol, sr = ef.portfolio_performance(verbose=True)

# ----------------------- Minimum Volatility Portfolio ----------------------- #

# Obtain the efficient frontier
ef = EfficientFrontier(mu, Sigma); ef
raw_weights = ef.min_volatility(); raw_weights
cleaned_weights = ef.clean_weights(); cleaned_weights

# Show portfolio performance: annualized return number, annualized volatility, the Sharpe Ratio
ef.portfolio_performance(verbose=True)
ret, vol, sr = ef.portfolio_performance(verbose=True)
```

The min vol portfolio has a _lower_ performance but _lower_ risk, since all stocks have a positive weight in the min vol portfolio and some stocks have a negative expected return.
```python
cleaned_min_vol_weights = ef.clean_weights(); cleaned_weights
OrderedDict([('GE', 0.15742), ('JPM', 0.11922), ('MSFT', 0.0416), ('PG', 0.68176)])

cleaned_max_sharpe_weights = ef.clean_weights(); cleaned_weights
OrderedDict([('GE', 0.0), ('JPM', 0.42851), ('MSFT', 0.57149), ('PG', 0.0)])
```

![[Screenshot 2023-04-13 at 18.44.42.png]]

----

## Expected risk and return based on historic data

Efficient frontier optimization requires knowledge of the expected risk Sigma and expected returns mu. In practice, these are rather difficult to know with any certainty. The best we can do is to come up with estimates, for example by extrapolating historical data. But that is where we go wrong. If history would repeat itself perfectly, we would all be able to predict financial markets and stock movements. The truth is, the mean historic returns, or the historic portfolio variance are not perfect inputs and do not reflect future expected risk and return perfectly. Hence the resulting weights of our optimization problem, would have worked well in the past, but we have no guarantee that it will work well in the future.

## Exponentially weighted returns

So what can we do about this? Well, the problem is not with the optimization approach; that procedure is sound, and provides strong mathematical guarantees, given that the inputs are correct. We therefore need to think about better measures for expected risk and return. A possible improvement is to use exponentially weighted risk and return. It assigns more importance to the most recent data, and thus aims to improve the estimates. Here you see how an exponential mean, or moving average, is build up. The last observation at t-1 gets assigned the heaviest weight in the mean

## Exponentially weighted covariance

The exponentially weighted covariance is also just another option in the risk_models function. For Sigma, you therefore follow the same steps. Take the `exponential_cov` from the risk models function, define the span and keep the frequency to 252 trading days. I take a different span for the variance calculation here, as it does not need to be the same span as for the exponential returns calculation.

## Using downside risk in the optimization

Another way to adjust our portfolio optimization problem, is to use downside risk only. Remember what we did for the Sortino ratio? For that ratio you calculated the variance of the negative returns only, as a way to measure downside risk. In PyPortfolioOpt you can do the same, but here it is called semicovariance. So instead of using the standard volatility, you can use the semicovariance matrix for the portfolio optimization problem

Making the adjustment to use the semicovariance for risk, is again very straight forward. Simply take the semicovariance option from risk models, at the point where you define Sigma. In this case, you need to define a benchmark, if the return falls below this benchmark it's considered a negative return and used in the variance calculation.

```python
from pypfopt import expected_returns
from pypfopt import risk_models

# Exponentially weighted moving average
mu_ema = expected_returns.ema_historical_return(df, span=252, frequency=252)

# Exponentially weighted covariance
Sigma_ew = risk_models.exp_cov(df, span=180, frequency=252)

Sigma_semi = risk_models.semicovariance(df, benchmark=0, frequency=252)
```

you're going to perform portfolio optimization with a slightly different way of estimating risk and returns; you're going to give more weight to recent data in the optimization.



----

Each of the methods mentioned has its own advantages and drawbacks, and the choice of the best method depends on the specific context and requirements of your analysis.

1.  Exponentially Weighted Moving Average (EWMA):
	- ```cagr_ewma = ((1 + returns.ewm(span=span).mean().iloc[-1]) ** frequency - 1)```
	- Advantages: More responsive to recent data points, as it assigns exponentially decreasing weights to past observations. It is often better suited for financial time series analysis, as it can better capture recent trends and changes.
	- Drawbacks: May be more sensitive to noise, as it emphasizes recent data points.
2.  Weighted Moving Average (WMA):
	- ```cagr_wma = ((1 + returns.rolling(window=span).apply(lambda x: np.average(x, weights=np.linspace(1, span, span)))[-1]) ** frequency - 1)```
	- Advantages: Offers more control over the weights assigned to observations, which can be tailored to better suit the specific characteristics of the time series.
	- Drawbacks: Requires more computation than SMA and may be less intuitive than EWMA.
3.  Simple Moving Average (SMA):
	- ```cagr_sma = ((1 + returns.rolling(window=span).mean().iloc[-1]) ** frequency - 1)```
	- Advantages: Easy to understand and compute, as it assigns equal weights to all observations in the moving window.
	- Drawbacks: Less responsive to recent data points, as it does not differentiate between the importance of past observations.

In summary, if you need a more responsive moving average that emphasizes recent data points, the EWMA method is likely a better choice. If you need more control over the weighting scheme and are willing to put in extra computation effort, the WMA method may be suitable. If simplicity and ease of computation are your priorities, the SMA method is a good option.

Ultimately, the choice of the best method depends on the nature of the data you are working with and the specific goals of your analysis. It is often helpful to experiment with different methods and compare their performance to make an informed decision.




--- 


```cardlink
url: https://www.kenwuyang.com/en/post/portfolio-optimization-with-python/
title: "Portfolio Optimization with Python and R | Yang (Ken) Wu"
description: "Portfolio optimization with Python and visualization with R"
host: www.kenwuyang.com
favicon: /media/icon_hu0e8b0ab40745ceb4f4042bc1d9ce4c3c_13641_32x32_fill_lanczos_center_2.png
image: https://www.kenwuyang.com/en/post/portfolio-optimization-with-python/featured.jpg
```
[Portfolio Optimization with Python and R | Yang (Ken) Wu](https://www.kenwuyang.com/en/post/portfolio-optimization-with-python/)

https://www.rinfinance.com/archive/2019/[https://www.rinfinance.com/archive/2019/](https://www.rinfinance.com/archive/2019/)