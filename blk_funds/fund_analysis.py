import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn2
import re
from fuzzywuzzy import fuzz  # You might need to install this: pip install fuzzywuzzy[speedup]

# Load the parquet file - update the path to your file location
df = pd.read_parquet("blackrock_data/blackrock_all_regions_20250309.parquet")

# Print basic information about the dataset
print(f"Total records in the dataset: {len(df)}")
print("\nRegion distribution:")
region_counts = df['Region'].value_counts()
print(region_counts)

# Clean and standardize the data
# Some preprocessing to handle possible data issues
df['ISIN'] = df['ISIN'].astype(str).replace('nan', np.nan).replace('None', np.nan)
df['Name'] = df['Name'].astype(str).replace('nan', np.nan).replace('None', np.nan)

# Clean fund names for better matching
df['clean_name'] = df['Name'].str.replace(r'\(.*\)', '', regex=True).str.strip()
df['clean_name'] = df['clean_name'].str.replace('…', '', regex=False).str.strip()

# Extract fund family (BGF, BSF, iShares, etc.)
df['fund_family'] = df['clean_name'].str.extract(r'^(\w+)', expand=False)

# Filter for UK and US funds
uk_df = df[df['Region'] == 'UK']
us_df = df[df['Region'] == 'US']

print(f"\nUK funds: {len(uk_df)}")
print(f"US funds: {len(us_df)}")

# Analyze ISINs - the most reliable identifier for exact matches
uk_isins = set(uk_df['ISIN'].dropna())
us_isins = set(us_df['ISIN'].dropna())
common_isins = uk_isins.intersection(us_isins)

# Calculate overlap percentages
uk_overlap_pct = len(common_isins) / len(uk_isins) * 100 if len(uk_isins) > 0 else 0
us_overlap_pct = len(common_isins) / len(us_isins) * 100 if len(us_isins) > 0 else 0

print(f"\nExact ISIN matches: {len(common_isins)}")
print(f"Percentage of UK funds also in US: {uk_overlap_pct:.2f}%")
print(f"Percentage of US funds also in UK: {us_overlap_pct:.2f}%")

# Show some examples of matched funds
if len(common_isins) > 0:
    print("\nExamples of funds available in both regions:")
    matched_funds = df[df['ISIN'].isin(list(common_isins)[:5])]
    for isin in list(common_isins)[:5]:
        fund_info = df[df['ISIN'] == isin][['Region', 'Name', 'ISIN', 'Share Class Currency']].drop_duplicates()
        print(f"\nISIN: {isin}")
        for _, row in fund_info.iterrows():
            print(f"  {row['Region']}: {row['Name']} ({row['Share Class Currency']})")

# Analyze fund families by region
fund_family_counts = df.groupby(['Region', 'fund_family']).size().unstack(fill_value=0)
print("\nTop fund families by region:")
print(fund_family_counts.head())

# Look for funds without ISIN matches using fuzzy name matching
uk_exclusive = uk_df[~uk_df['ISIN'].isin(common_isins)]
us_exclusive = us_df[~us_df['ISIN'].isin(common_isins)]

print(f"\nUK-exclusive funds (not in US by ISIN): {len(uk_exclusive)}")
print(f"US-exclusive funds (not in UK by ISIN): {len(us_exclusive)}")

# Perform fuzzy matching on fund names
similarity_threshold = 85  # Adjust as needed
fuzzy_matches = []

# Limit to a sample for performance if there are many funds
uk_names = uk_exclusive['clean_name'].dropna().unique()[:100]  # Adjust sample size as needed
us_names = us_exclusive['clean_name'].dropna().unique()[:100]  # Adjust sample size as needed

for uk_name in uk_names:
    for us_name in us_names:
        similarity = fuzz.ratio(uk_name, us_name)
        if similarity > similarity_threshold:
            fuzzy_matches.append((uk_name, us_name, similarity))

print(f"\nAdditional fuzzy name matches (similarity > {similarity_threshold}%): {len(fuzzy_matches)}")
if fuzzy_matches:
    print("\nTop fuzzy matches examples:")
    for uk_name, us_name, score in sorted(fuzzy_matches, key=lambda x: x[2], reverse=True)[:5]:
        print(f"  {score}% match: \n    UK: {uk_name}\n    US: {us_name}")

# Analysis by fund type and currency
print("\nCurrency distribution in UK funds:")
print(uk_df['Share Class Currency'].value_counts().head())

print("\nCurrency distribution in US funds:")
print(us_df['Share Class Currency'].value_counts().head())

# Check distribution types (accumulating vs distributing)
if 'Distribution Type' in df.columns:
    print("\nDistribution types in UK:")
    print(uk_df['Distribution Type'].value_counts())
    
    print("\nDistribution types in US:")
    print(us_df['Distribution Type'].value_counts())

# Create visualizations

# 1. Venn diagram of ISIN overlap
plt.figure(figsize=(10, 6))
venn2([uk_isins, us_isins], ('UK Funds', 'US Funds'))
plt.title('Overlap of Fund ISINs between UK and US')
plt.savefig('uk_us_fund_overlap.png')

# 2. Bar chart of fund families by region
plt.figure(figsize=(12, 8))
top_families = fund_family_counts.sum(axis=0).nlargest(10).index
fund_family_chart = fund_family_counts.loc[:, top_families]
fund_family_chart.plot(kind='bar', stacked=True)
plt.title('Top Fund Families by Region')
plt.xlabel('Region')
plt.ylabel('Number of Funds')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('fund_families_by_region.png')

# 3. Heatmap of currency usage by region
currency_region = pd.crosstab(df['Region'], df['Share Class Currency'])
top_currencies = currency_region.sum(axis=0).nlargest(8).index
plt.figure(figsize=(12, 8))
sns.heatmap(currency_region[top_currencies], annot=True, fmt='d', cmap='Blues')
plt.title('Currency Usage by Region')
plt.tight_layout()
plt.savefig('currency_by_region.png')

# Summary statistics and conclusions
print("\n" + "="*50)
print("SUMMARY AND CONCLUSIONS")
print("="*50)

print(f"\n1. Total funds analyzed: {len(df)}")
print(f"   - UK funds: {len(uk_df)}")
print(f"   - US funds: {len(us_df)}")

print(f"\n2. Exact ISIN matches: {len(common_isins)}")
print(f"   - {uk_overlap_pct:.2f}% of UK funds are also offered in the US")
print(f"   - {us_overlap_pct:.2f}% of US funds are also offered in the UK")

print(f"\n3. Fuzzy name matches: {len(fuzzy_matches)}")
print(f"   - Additional potential matches beyond exact ISIN matches")

uk_only_families = set(uk_df['fund_family'].dropna()) - set(us_df['fund_family'].dropna())
us_only_families = set(us_df['fund_family'].dropna()) - set(uk_df['fund_family'].dropna())

print("\n4. Fund family analysis:")
print(f"   - Fund families unique to UK: {', '.join(list(uk_only_families)[:5])}...")
print(f"   - Fund families unique to US: {', '.join(list(us_only_families)[:5])}...")

# Final conclusion
is_subset = uk_overlap_pct > 90
print("\nCONCLUSION:")
if is_subset:
    print("UK funds appear to be largely a subset of US/Americas offshore funds.")
else:
    print("UK funds are NOT simply a subset of US/Americas offshore funds.")
    print("Each region has significant unique offerings tailored to local markets.")