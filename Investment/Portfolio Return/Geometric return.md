
The terms “arithmetic” and “geometric” are common in the field of performance measurement; arithmetic reflects additive relationships and geometric reflects multi- plicative or compounding relationships.

| Period            | Value (£m) | Market Return (%) |
|-------------------|------------|-------------------|
| Start value (VS)  | 100        |                   |
| End of period 1   | 112        | 12.00             |
| End of period 2   | 95         | -15.18            |
| End of period 3   | 99         | 4.21              |
| End of period 4   | 107        | 8.08              |
| End value (VE)    | 115        | 7.48              |


To calculate the entire period return, you can use the following formula:

Entire Period Return = (End Value / Start Value - 1) * 100

Using the provided values:

Start Value (VS): 100 End Value (VE): 115

Entire Period Return = (115 / 100 - 1) * 100 = 0.15 * 100 = 15%

The entire period return is 15%.

----

## Chain-linking return

Chain-linking returns over several periods is a method to calculate the cumulative return over a series of periods. It helps to understand the overall performance of an investment across multiple time frames. To calculate chain-linked returns, you can follow these steps:

### CRAMP
1.  **C**onvert: Convert each period's return to a decimal by dividing the percentage return by 100.
2.  **R**aise: Add 1 to each decimal return.
3.  **A**ccumulate: Multiply the decimal returns (1 + return) together.
4.  **M**inus: Subtract 1 from the result.
5.  **P**ercent: Multiply the result by 100 to get the chain-linked return in percentage.

Using the provided data:
```
Period 1: 12.00%
Period 2: -15.18%
Period 3: 4.21%
Period 4: 8.08%
```

### work-out
```
# Add 1 to each decimal return:
Period 1: 1.1200
Period 2: 0.8482
Period 3: 1.0421
Period 4: 1.0808

1.1200 * 0.8482 * 1.0421 * 1.0808 = 1.1496
1.1496 - 1 = 0.1496
0.1496 * 100 = 14.96%

```


```python
import pandas as pd
from rich import pretty
from rich.progress import Progress
pretty.install()

# Create a DataFrame with the provided data
data = {
'Period': ['Start value (VS)', 'End of period 1', 'End of period 2', 'End of period 3', 'End of period 4', 'End value (VE)'],
'Value (£m)': [100, 112, 95, 99, 107, 115],
'Market Return (%)': [None, 12.00, -15.18, 4.21, 8.08, 7.48]
}

df = pd.DataFrame(data); df

# Calculate the returns based on the values in the 'Value (£m)' column
df['Calculated Return'] = df['Value (£m)'].pct_change(); df

# Chain-link the returns
chain_linked_return = (df['Calculated Return'] + 1).prod() - 1; chain_linked_return

# Convert the result to a percentage
chain_linked_return_percentage = chain_linked_return * 100; chain_linked_return_percentage
print(f"Chain-linked return: {chain_linked_return_percentage:.2f}%")
```


----

## Annualised return 


Assume the rate of return is +20% in the first period and −20% in the second period Assuming a start value of £100. The value at the end of the first period is £120. The value at the end of the second period is £96. What is the annualised return?

To calculate the annualized return, we'll use the geometric mean formula.

1.  Calculate the return for each period: 
	a. Period 1 return: +20% 
	b. Period 2 return: -20%
2.  Convert the returns to growth factors (1 + return): 
	a. Period 1 growth factor: 1 + 0.20 = 1.20 
	b. Period 2 growth factor: 1 - 0.20 = 0.80
3.  Multiply the growth factors together: 
	- 1.20 * 0.80 = 0.96
1.  Raise the result to the power of (1 / number of periods) - 1: 
	- (0.96)^(1/2) = 0.9798
2.  Subtract 1 from the result and multiply by 100 to get the percentage: 
	- (0.9798 - 1) * 100 = -2.02%
    
The annualized return for this two-period investment is -2.02%.