
> To evaluate and compare different strategies or to improve an existing strategy, we need metrics that reflect their performance with respect to our objectives. In investment and trading, the most common objectives are the return and the risk of the investment portfolio.
> 
> Typically, these metrics are compared to a benchmark that represents alternative investment opportunities, such as a summary of the investment universe like the S&P 500 for US equities or the risk-free interest rate for fixed income assets.
> 
> There are several metrics to evaluate these objectives. In this section, we will review the most common measures for comparing portfolio results. These measures will be useful when we look at different approaches to optimize portfolio performance, simulate the interaction of a strategy with the market using Zipline, and compute relevant performance metrics using the pyfolio library in later sections

---

# Capturing risk-return trade-offs in a single number
> The return and risk objectives imply a trade-off: taking more risk may yield higher returns in some circumstances, but also implies greater downside. To compare how different strategies navigate this trade-off, ratios that compute a measure of return per unit of risk are very popular.
> - Sharpe ratio (SR)
> - Information ratio (IR)