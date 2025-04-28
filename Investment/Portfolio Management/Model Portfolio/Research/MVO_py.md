
```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

# Load data for a set of stocks
data = pd.read_csv("stock_data.csv")

# Calculate the returns for each stock
returns = data.pct_change()

# Calculate the mean and covariance of the returns
mean_returns = returns.mean()
cov_matrix = returns.cov()

# Define the number of stocks in the portfolio
num_stocks = len(mean_returns)

# Set the portfolio risk tolerance
risk_tolerance = 0.2

# Define the optimization function
def portfolio_variance(x):
  return np.dot(x.T, np.dot(cov_matrix, x))

# Define the optimization constraints
constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
               {'type': 'ineq', 'fun': lambda x: risk_tolerance - portfolio_variance(x)}]

# Define the optimization bounds
bounds = [(0, 1) for i in range(num_stocks)]

# Set the initial guess for the portfolio weights
x0 = np.ones(num_stocks) / num_stocks

# Run the optimization
result = minimize(fun=portfolio_variance,
                  x0=x0,
                  constraints=constraints,
                  bounds=bounds,
                  method='SLSQP')

# Extract the optimized portfolio weights
optimal_weights = result.x

# Calculate the expected return and risk of the optimal portfolio
portfolio_return = np.sum(mean_returns * optimal_weights)
portfolio_risk = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))

print("Optimal portfolio weights:", optimal_weights)
print("Expected return:", portfolio_return)
print("Risk:", portfolio_risk)

```