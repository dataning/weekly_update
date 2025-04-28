# Portfolio return 

Portfolios typically hold more than one security; this could be for a number of reasons, including:
	- risk diversification;
	- having multiple investment strategies in play;
	- matching a set of known liabilities;
	- matching the cashflows of a benchmark.


Each security $i$ in a portfolio has a market value $MVi$ , a weight $wi$ and a return $ri$ . The weight is the security’s proportion of the overall portfolio value:
 $$ wi = \frac{MVi}{\sum MVi}$$
## Weight at portfolio level
This implies that the sum of the security weights over the portfolio is always 1. Note that weights can be negative. This most commonly occurs when a port- folio holds derivatives such as currency forwards, futures or swaps, which may have negative market values. In this case, the sum of the weights of the other securities in the portfolio will be greater than one. 

$$ \sum_i wi = 1$$

## Return at portfolio level
The portfolio’s overall return R is the sum-produact of its security weights and returns:
 $$ R = \sum_i w_ir_i$$

## Performance contribution at portfolio level
In other words, the return of a portfolio over a given interval is the sum of its performance contributions over that interval.
 $$ R = \sum_i c_i$$


## Composition of portfolio changes
- security transactions (buying or selling stocks);
- cash flows (dividends and coupons);
- revaluation (stock splits);
- internal changes within a security (sinking bond paydowns);
- changes from one security type to another (bonds maturing, bonds being called, convertible bonds turning into equity).


### Accurate intraday contributions
A continuous view of the holdings and valuation of the managed portfolio is seldom available. Instead, the analyst must work with snapshots of the portfolio, usually at the start or end of the day, and include the effects of trades and other cash flows between these points.

#### Why time frequency is key 
At some point a trader will buy into a stock after the market opens and sell it out before the market closes. The stock will generate a contribution to the portfolio’s overall performance, but its weight at the beginning and the end of the calculation interval will be zero. In this case, a conventional use of weights and returns will report the security’s return contribution as zero when it is not.
> Does this mean that in carbon emission we could get away with quarterly weight? 

#### Highly leveraged securities
The other reason to work with performance contributions is that they often convey a clearer picture of the source of portfolio returns. A highly leveraged swap may have a very large return but a small exposure.
In this case it may not be clear whether the swap is making any impact on the portfolio’s overall return. The swap’s performance contribution provides a much more transparent way to assess its impact on the portfolio’s return.

A disadvantage of using return contributions is that weight must now be calculated as following. The sum of the wi terms may differ slightly from 1 on days where there is significant intraday trading, but this is always preferable to reporting the wrong overall return.
 $$ w_i = \frac{c_i}{r_i} $$
