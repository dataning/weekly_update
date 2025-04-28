
- Focused on global tactical asset allocation mandates spanning geographies, asset classes, and alpha sources.
- The goal is to maximize the probability of exceeding client investment objectives

It's more blended investment approach: statistical modelling + intuition
> - Dynamic investment process
	- data intensive
		- Proprietary macroeconomic indicators, signals and tools to analyze market pricing; focused on continuously improving our access to innovative data sources and data processing techniques.
	- discretionary
	- systematic techniques

Portfolio building prospective
> - Marco-environment 
> 	- Growth
> 		- Cyclical turning points - a consistent forecaster of potential equity returns
> 		![[Screenshot 2022-12-25 at 11.57.42.png]]
> 		- Composition of growth - consumer vs. producer - implemented using industry equity baskets
> 		- Indicators: Use a broad set of leading and coincident economic indicators spanning the major global economies. These indicators seek to capture the underlying trend in economic output at both an aggregate and sectoral level. These tools provide the Team with timely measures of the level and acceleration of economic activity at both the global and country level.
> 		![[Screenshot 2022-12-25 at 12.12.11.png]]
> 			- Consumer Indicator
> 			- Manufacturing indicator
> 	- Inflation
> 		- Nominal bonds highly sensitive to shifts in inflation expectations
> 		- Exchange rate changes - important for small, open economies and emerging market bonds
> 		![[Screenshot 2022-12-25 at 12.01.07.png]]
> 		- Indicators: Use Alternative Inflation Indicators which strip out the effects of extreme or highly volatile price movements; perform a sectoral decomposition of the CPI basket and underweight volatile components and overweight stable components This helps to create more stable estimates of trend inflation
> 		![[Screenshot 2022-12-25 at 12.16.32.png]]
> 			- Sector-based movement and trends (z-score-based)
> 			- Annualised rolling CPI
> 	- Policy
> 		- Shifts in monetary policy expectations create relative value across yield curves
> 		- Fiscal policy and structural reform in EMs create regime changes in exchange rates
> 		![[Screenshot 2022-12-25 at 12.02.55.png]]
> 		- Indicators: Use Big Data-driven tool that analyzes unstructured central bank speeches to measure the policy stance of global central banks; combine the quantitative analysis of text data via Natural Language Processing with the fundamental central banking expertise to interpret those data. This tool is powerful for interpreting the direction of change and the level of policy stance at the country-level as well as comparing policy stance across global central banks.
> 		![[Screenshot 2022-12-25 at 13.24.35.png]]
> - Market pricing
> 	- Equity markets
> 	- Fixed income markets
> 	- Currency markets
> 	
> - discretionary
> - systematic approach 


Ultimately, it's really about misalignment - what's expected and what's behaved
> # Market pricing drive
> 	- Construct market-based pricing factors for the 3 factors
> 	- Monitor gap between Macro Indicators and Pricing Factors as a measure of mispricing and rank assets based on output

| Name            | Growth                                                          | Inflation                   | Policy                                              |
| --------------- | --------------------------------------------------------------- | --------------------------- | --------------------------------------------------- |
| Macro Indicator | Leading Economic indicator                                      | Survey inflation indicator  | text-based policy indicator                         |
| Pricing factor  | Fist Principal component of returns to growth-sensitive assets | 10-year inflation breakevens | Changes in the slop of the front-end of yeold curve | 
![[Screenshot 2022-12-25 at 16.43.25.png]]

Data source:
```cardlink
url: https://data.oecd.org/leadind/business-confidence-index-bci.htm
title: "Leading indicators - Business confidence index (BCI) - OECD Data"
description: "Find, compare and share OECD data by indicator."
host: data.oecd.org
favicon: /media/oecdorg/styleassets/images/favicon.ico
image: http://data.oecd.org/media/dataportal/custom/OECD_110x110.png
```

---

# Case study

This seems a good AutoML approach because it's essentially looking for pattern recognition or maybe some causal inference. The use of Hawkishness and 
> Workflow 
> - Distill economic data into macro insights
	- Growth: US labour market indicator continues to improve 
		- employment data z-sore
	- Inflation: Weak 2H16 gave way to pick up in core US inflation in early '17
		- Core CPI
		- Core PCE
	- Policy: Tightening not translating to financial conditions
		- Z-score
> - Identify common marco themes across insights
	- Ongoing improvements in growth and labour market, firming inflation, and loose financial conditions all support further Fed normalisation
> - Evaluation of pricing determines express
	- Markets are only pricing around 3 rate hikes over the next two years
	- Pricing is overly dovish
	- Higher interest rate are a headwind to both US equities and bonds
> - Result
	- Relative value underweight to US equities vs Japanese equities
	- Underweight US 5 year interest rate future vs cash
![[Screenshot 2022-12-25 at 16.56.32.png]]


----

Macro themes - determined by active risk

![[Screenshot 2022-12-25 at 18.42.36.png]]

![[Screenshot 2022-12-25 at 18.45.29.png]]![[Screenshot 2022-12-25 at 18.46.38.png]]