
----

> The most common decomposition is between value added due to asset allocation and value added due to security selection.

> Consider a composite portfolio of stocks and bonds where the asset allocation weights differ from a composite benchmark and each asset class is actively managed by selecting individual securities.

> The first (parenthetical) term is the value added from the asset allocation decision. The second term is the value added from security selection within the stock and bond portfolios. The active weights in the first term refer to differences from the policy portfolio.


|        Fund        | Fund Return (%) | Benchmark Return (%) | Valued Added (%) |
|:------------------:|:---------------:|:--------------------:|:----------------:|
| Fidility Magellan  |      -5.6       |         -4.5         |       -1.1       |
| PIMCO Total Return |      -0.3       |         0.0          |       -0.3       |
|  Portfolio Return  |      -3.9       |         -2.7         |       -1.2       |
Specifically, the Fidelity Magellan mutual fund had a return of −5.6%, compared with a −4.5% return for its benchmark, the S&P 500 Index. In the same year, the PIMCO Total Return Fund had a return of −0.3%, compared with a 0.0% return for its benchmark, the Bloomberg Barclays US Aggregate Index. Consider an investor who invested in both actively managed funds, with 68% of the total portfolio in Fidelity and 32% in PIMCO. Assume that the investor’s policy portfolio (strategic asset allocation) specifies weights of 60% for equities and 40% for bonds.
- Security selection
	- As shown in the table, Fidelity Magellan added value of RA = RP − RB = −5.6% − (−4.5)% = −1.1%, and PIMCO Total Return added value of RA = RP − RB = −0.3% − (0.0%) = −0.3%. These value added numbers represent the skill in security selection within each individual fund.
	- Using the actual weights of 68% and 32% in the Fidelity and PIMCO funds, the combined value added from security selection was 0.68(−1.1%) + 0.32(−0.3%) = −0.8%.
- Asset allocation
	- The active asset allocation weights in 2018 were 68% − 60% = +8% for equities and ‒8% for bonds, so the value added by the active asset allocation decision was 0.08(−4.5%) − 0.08(0.0%) = −0.4%. The total value added by the investor’s active asset allocation decision and by the mutual funds through security selection was −0.8% − 0.4% = −1.2%. 
	- To confirm this total value added, note that the return on the investor’s portfolio was 0.68(−5.6%) + 0.32(−0.3%) = −3.9% and the return on the policy portfolio was 0.60(−4.5%) + 0.40(0.0%) = −2.7%, for a difference of −3.9% − (−2.7) = −1.2%.

Security selection is focused on the individual component; the return of individual component in managed portfolio - the individual component in the benchmark; get multiplication of the managed weight.  
- Fund 1: RA = RP − RB = −5.6% − (−4.5)% = −1.1%
- Fund 2: RA = RP − RB = −0.3% − (0.0%) = −0.3%
- Combined valued added: 0.68(−1.1%) + 0.32(−0.3%) = −0.8%

Asset allocation is focused on the overweight/underweight;
- Overweight: 68% − 60% = +8% for equities
- Underweight: 32% - 40% = -8% for bonds
- Combined valued added: 0.08(−4.5%) − 0.08(0.0%) = −0.4%

Security selection + Asset allocation = −0.8% - 0.4% = -1.2%

Evaluation: 
- Managed portfolio: 0.68(−5.6%) + 0.32(−0.3%) = −3.9% 
- Benchmark: 0.60(−4.5%) + 0.40(0.0%) = −2.7%

```python
data = {
		'Asset': ['Fidility Magellan', 'PIMCO Total Return'],
		'Active Weight': [0.68, 0.32],
		'Benchmark Weight': [0.6, 0.4],
		'Active Return': [-5.6, -0.3],
		'Benchmark Return': [-4.5, 0]}

df = pd.DataFrame(data); df

df['diff_weight'] = df['Active Weight'] - df['Benchmark Weight']; df
benchmark_return = df['Benchmark Return'].sum(); benchmark_return
active_return = (df['Active Return'] * df['Active Weight']).sum(); active_return

benchmark_return = (df['Benchmark Return'] * df['Benchmark Weight']).sum(); benchmark_return

value_added = active_return - benchmark_return; value_added
```


