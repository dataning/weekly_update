# Value At Risk (VAR) Models

[Link](https://www.youtube.com/watch?v=92WaNz9mPeY)

##   What Are We Trying to Calculate?
- We want to estimate the worst 1% of the possible outcomes.
- We want to know how much this market could possibly move against us, so we know how much capital we need to support the position .

##  Why We Use Returns
-  Consider the returns of the IPC over the same period, where returns are defined as the percentage change in the index
![[Pictures/Screenshot 2021-07-27 at 14.14.01.png]]

##  Estimating Volatility
-   Once we have a time series of returns, we can gauge their relative dispersion with a measure called variance. 
	-  Variance is calculated by subtracting the average return from each individual return, squaring that figure, summing the squares across all observations, and dividing the sum by the number of observations.
	-  The square root of the variance, called the **standard deviation** or the **volatility**, can be used to estimate risk.
	-  In a normal distribution, 2.33 * the standard deviation represents the largest possible movement 99% of the time (1.64 * the standard deviation for 95%).

##  Using Volatility to Estimate Value at Risk
-   The variance of the daily IPC returns between 1/95 and 12/96 was 0.000324
-   The standard deviation was 0.018012 or 1.8012%
-   2.33 * 1.8012% = 0.041968 or 4.1968%
-   We can conclude that we could expect to lose no more than 4.1968% of the value of our position, 99% of the time.
-   This means that an investment in the IPC of MXP 100 investment would suffer daily losses over MXP 4.2 only about 1% of the time.
-   In fact, the IPC lost more than 4.2% 8 times since 1/1/95, or about 1.5% of the time.
-   While this figure is approximately accurate, it illustrates a problem VaR has in certain markets, that it occasionally underestimates the number of large market moves.
-   This problem, while frequent at the security or desk level, usually disappears at the portfolio level.

## One Asset VaR
1.  Collect price data
2.  Create return series
3.  Estimate variance of return series
4.  Take square root of variance to get volatility (standard deviation )
5.  Multiply volatility by 2.33 by position size to get estimate of 99% worst case loss.
6. 