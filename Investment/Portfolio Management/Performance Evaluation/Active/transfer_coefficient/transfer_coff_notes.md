
----

> It's a curious fact that Renaissance Technologies (RenTec), the top-performing quant fund founded by Jim Simons, which we mentioned in Chapter 1, Machine Learning for Trading – From Idea to Execution, has produced similar returns as Warren Buffet, despite extremely different approaches. Warren Buffet's investment firm Berkshire Hathaway holds some 100-150 stocks for fairly long periods, whereas RenTec may execute 100,000 trades per day. How can we compare these distinct strategies?
> 
> A high IR reflects an attractive out-performance of the benchmark relative to the additional risk taken. The Fundamental Law of Active Management explains how such a result can be achieved: it approximates the IR as the product of the information coefficient (IC) and the breadth of the strategy.
> 
  As discussed in the previous chapter, the IC measures the rank correlation between return forecasts, like those implied by an alpha factor, and the actual forward returns. Hence, it is a measure of the forecasting skill of the manager. The breadth of the strategy is measured by the independent number of bets (that is, trades) an investor makes in a given time period, and thus represents the ability to apply the forecasting skills.

> The Fundamental Law states that the IR, also known as the appraisal risk (Treynor and Black), is the product of both values. In other words, it summarizes the importance to play both often (high breadth) and to play well (high IC):

IR ∼ IC ∗ √brea

> This framework has been extended to include the transfer coefficient (TC) to reflect portfolio constraints as an additional factor (for example, on short-selling) that may limit the information ratio below a level otherwise achievable given IC or strategy breadth. The TC proxies the efficiency with which the manager translates insights into portfolio bets: if there are no constraints, the TC would simply equal one; but if the manager does not short stocks even though forecasts suggests they should, the TC will be less than one and reduce the IC (Clarke et al., 2002).

----

> The transfer coefficient is an increasing function of IC. One way to look at this is that the larger the IC, the less the transaction costs matter and the closer the portfolio gets to the ideal transfer coefficient of 1.

> The 130/30 strategy affords the manager the opportunity to avoid much of the loss of portfolio construction efficiency. One way to measure this efficiency is by using the transfer coefficient, which is the correlation between active weights, and forecast residual returns in portfolio construction. The closer the transfer coefficient comes to 1.0, the more efficient is the portfolio construction.

----

The information coefficient (IC) and the transfer coefficient (TC) are both measures of the strength of the relationship between a predictor variable (also known as an independent variable) and a target variable (also known as a dependent variable) in a statistical model.

The IC is a measure of the predictiveness of a predictor variable, while the TC is a measure of the ability of a predictor variable to transfer its predictive power to other datasets or contexts.

In general, the IC is a measure of the strength of the linear relationship between a predictor variable and the target variable, while the TC is a measure of the strength of the non-linear relationship between the two variables.

The IC is typically calculated as the correlation between the predictor variable and the target variable, while the TC is typically calculated using information theory or machine learning techniques.

Both the IC and the TC are used in statistical modeling and machine learning to evaluate the importance of predictor variables and to select the most relevant variables for a model. However, the IC is more commonly used in financial modeling and the TC is more commonly used in machine learning.