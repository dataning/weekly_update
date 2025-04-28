import pandas as pd
import json
import random  # For demo data generation

# Step 1: Create sample dataframe
# In a real scenario, you would likely import from a CSV:
# df = pd.read_csv('sp500_companies.csv')

# Create basic industry categories (top level)
industries = [
    'Technology', 'Financial', 'Consumer Cyclical', 'Communication Services',
    'Healthcare', 'Consumer Defensive', 'Industrials', 'Real Estate',
    'Energy', 'Utilities', 'Basic Materials'
]

# Create a mapping from sectors to industries
sector_to_industry = {
    'IT Consulting & Other Services': 'Technology',
    'Application Software': 'Technology',
    'Semiconductors': 'Technology',
    'Life & Health Insurance': 'Financial',
    'Specialty Chemicals': 'Basic Materials',
    'Electric Utilities': 'Utilities',
    'Interactive Media & Services': 'Communication Services',
    'Broadline Retail': 'Consumer Cyclical',
    'Regional Banks': 'Financial',
    'Systems Software': 'Technology',
    'Pharmaceuticals': 'Healthcare',
    'Oil & Gas Exploration & Production': 'Energy',
    # Add more mappings as needed
}

# Create sample company data
companies = []
for sector, industry in sector_to_industry.items():
    # Create 3-5 companies per sector
    for i in range(random.randint(3, 5)):
        symbol = f"{sector[:3]}{i}".upper()
        name = f"{sector} Company {i}"
        market_cap = random.randint(100, 1000) * 1e8  # Random market cap in billions
        old_price = random.randint(50, 500)
        new_price = old_price * (1 + random.uniform(-0.15, 0.15))  # +/- 15% change
        performance = 100 * (new_price - old_price) / old_price
        
        companies.append({
            'Symbol': symbol,
            'Name': name,
            'Sector': sector,
            'Market Cap': market_cap,
            'Price': new_price,
            'OldPrice': old_price,
            'Performance': performance
        })

# Create DataFrame
df = pd.DataFrame(companies)

# Step 2: Format data for Highcharts treemap
# Start with top-level industries
data = []
for industry in industries:
    data.append({
        'id': industry,
        'name': industry,
        'custom': {'fullName': industry}
    })

# Add sectors (second level)
for sector in df['Sector'].unique():
    data.append({
        'id': sector,
        'name': sector,
        'parent': sector_to_industry[sector],
        'custom': {'fullName': sector}
    })

# Add companies (third level)
for _, row in df.iterrows():
    data.append({
        'name': row['Symbol'],
        'id': row['Symbol'],
        'value': row['Market Cap'],
        'parent': row['Sector'],
        'colorValue': row['Performance'],
        'custom': {
            'fullName': row['Name'],
            'performance': ('+' if row['Performance'] >= 0 else '') + f"{row['Performance']:.2f}%"
        }
    })

# Export to JSON
with open('sp500_treemap_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Created JSON data for {len(df)} companies across {len(df['Sector'].unique())} sectors.")
print("JSON data saved to sp500_treemap_data.json")

# For demonstration, print a sample of the data structure
print("\nSample of the data structure:")
print(json.dumps(data[:5], indent=2))

