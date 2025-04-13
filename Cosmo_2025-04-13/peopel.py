import requests
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def fetch_fund_manager_data(fund_id, manager_id, access_token):
    """
    Fetches fund manager data from Morningstar API
    
    Args:
        fund_id (str): The fund ID
        manager_id (str): The manager ID
        access_token (str): Access token for API authentication
        
    Returns:
        dict: JSON response data if successful, None otherwise
    """
    url = f"https://api-global.morningstar.com/sal-service/v1/fund/people/manager/{fund_id}/{manager_id}/data"
    
    querystring = {
        "languageId": "en",
        "locale": "en",
        "clientId": "finra",
        "benchmarkId": "mstarorcat",
        "component": "sal-components-mip-manager-pop-out",
        "version": "3.61.2",
        "access_token": access_token
    }
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Origin": "https://finra-markets.morningstar.com",
        "Referer": "https://finra-markets.morningstar.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def create_manager_dataframe(data):
    """
    Create a DataFrame with the fund manager's information
    
    Args:
        data (dict): The manager data JSON
        
    Returns:
        pd.DataFrame: DataFrame with manager information
    """
    # Extract manager basic info
    manager_info = {
        'Manager ID': data.get('fundManager', {}).get('personId'),
        'Manager Name': data.get('fundManager', {}).get('biography', {}).get('managerProvidedBiography', '').split('—')[0].strip(),
        'AUM ($)': data.get('fundAUM'),
        'AUM Currency': data.get('aumCurrencySymbol'),
        'Industry Experience (Years)': data.get('industryExperience'),
        'Years in Strategy': data.get('yearInStrategy'),
        'Tenure Performance': data.get('tenurePerformance') * 100,  # Convert to percentage
        'Index Performance': data.get('indexPerformance') * 100,  # Convert to percentage
        'Alpha': (data.get('tenurePerformance', 0) - data.get('indexPerformance', 0)) * 100,  # Performance difference
        'Gender': data.get('gender'),
        'Managed Fund Count': data.get('currentManagedFundCount')
    }
    
    # Extract biography
    bio_info = data.get('fundManager', {}).get('biography', {})
    if bio_info:
        manager_info['Biography'] = bio_info.get('managerProvidedBiography', '')
    
    # Create manager DataFrame
    return pd.DataFrame([manager_info])

def create_education_dataframe(data):
    """
    Create a DataFrame with the fund manager's education information
    
    Args:
        data (dict): The manager data JSON
        
    Returns:
        pd.DataFrame: DataFrame with education information
    """
    education_list = data.get('fundManager', {}).get('CollegeEducationDetailList', [])
    education_data = []
    
    for edu in education_list:
        education_data.append({
            'School': edu.get('school'),
            'Degree': edu.get('degree'),
            'Level': edu.get('level'),
            'Year': edu.get('year')
        })
        
    return pd.DataFrame(education_data)

def create_certification_dataframe(data):
    """
    Create a DataFrame with the fund manager's certification information
    
    Args:
        data (dict): The manager data JSON
        
    Returns:
        pd.DataFrame: DataFrame with certification information
    """
    cert_list = data.get('fundManager', {}).get('CertificationDetailList', [])
    cert_data = []
    
    for cert in cert_list:
        cert_data.append({
            'Certification': cert.get('certificationName'),
            'Year': cert.get('certificationYear')
        })
        
    return pd.DataFrame(cert_data)

def create_funds_dataframe(data):
    """
    Create a DataFrame with the fund manager's managed funds
    
    Args:
        data (dict): The manager data JSON
        
    Returns:
        pd.DataFrame: DataFrame with fund information
    """
    fund_list = data.get('currentManagedFundList', [])
    fund_data = []
    
    for fund in fund_list:
        # Convert start date from string to datetime
        start_date = None
        if fund.get('startDate'):
            try:
                start_date = datetime.fromisoformat(fund.get('startDate').replace('Z', '').replace('T00:00:00.000', ''))
            except (ValueError, TypeError):
                pass
                
        fund_data.append({
            'Fund ID': fund.get('fundId'),
            'Security ID': fund.get('secId'),
            'Name': fund.get('name'),
            'Symbol': fund.get('tradingSymbol', 'N/A'),
            'Country': fund.get('reportCountryId'),
            'Security Type': fund.get('securityType'),
            'Start Date': start_date,
            'Years Managing': (datetime.now() - start_date).days / 365.25 if start_date else None
        })
        
    funds_df = pd.DataFrame(fund_data)
    
    # Sort funds by start date (most recent first)
    if not funds_df.empty and 'Start Date' in funds_df.columns and funds_df['Start Date'].notna().any():
        funds_df = funds_df.sort_values(by='Start Date', ascending=False)
        
    return funds_df

def analyze_funds(funds_df):
    """
    Analyze fund data and provide summary statistics
    
    Args:
        funds_df (pd.DataFrame): DataFrame with fund information
        
    Returns:
        tuple: (country_counts_df, type_counts_df, year_counts)
    """
    # Count funds by country
    country_counts = funds_df['Country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Count']
    
    # Count funds by security type
    type_counts = funds_df['Security Type'].value_counts().reset_index()
    type_counts.columns = ['Security Type', 'Count']
    
    # Count funds by start year (if date available)
    year_counts = None
    if 'Start Date' in funds_df.columns and funds_df['Start Date'].notna().any():
        funds_df['Start Year'] = funds_df['Start Date'].dt.year
        year_counts = funds_df['Start Year'].value_counts().sort_index()
    
    return country_counts, type_counts, year_counts

def print_manager_summary(manager_df, country_counts, type_counts):
    """
    Print a comprehensive summary of the fund manager
    
    Args:
        manager_df (pd.DataFrame): DataFrame with manager information
        country_counts (pd.DataFrame): DataFrame with country counts
        type_counts (pd.DataFrame): DataFrame with security type counts
    """
    print("\n==== MANAGER PROFILE SUMMARY ====")
    print(f"Manager: {manager_df['Manager Name'].iloc[0]}")
    print(f"AUM: {manager_df['AUM Currency'].iloc[0]}{manager_df['AUM ($)'].iloc[0]:,.0f}")
    print(f"Industry Experience: {manager_df['Industry Experience (Years)'].iloc[0]:.1f} years")
    print(f"Years in Strategy: {manager_df['Years in Strategy'].iloc[0]:.1f} years")
    print(f"Tenure Performance: {manager_df['Tenure Performance'].iloc[0]:.2f}%")
    print(f"Index Performance: {manager_df['Index Performance'].iloc[0]:.2f}%")
    print(f"Alpha: {manager_df['Alpha'].iloc[0]:.2f}%")
    print(f"Total Managed Funds: {manager_df['Managed Fund Count'].iloc[0]}")
    
    # Top countries
    top_countries = country_counts.head(3)['Country'].tolist()
    print(f"Top Countries: {', '.join(top_countries)}")
    
    # Security types
    security_types = type_counts['Security Type'].tolist()
    print(f"Security Types: {', '.join(security_types)}")

def get_fund_manager_data(fund_id, manager_id, access_token=None, json_file=None):
    """
    Get fund manager data either from API or from a JSON file
    
    Args:
        fund_id (str): The fund ID
        manager_id (str): The manager ID
        access_token (str, optional): Access token for API authentication
        json_file (str, optional): Path to a JSON file with the data
        
    Returns:
        tuple: DataFrames containing manager info, funds, education, certifications
    """
    # Get data from API or file
    if json_file:
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return None, None, None, None
    elif access_token:
        data = fetch_fund_manager_data(fund_id, manager_id, access_token)
        if not data:
            return None, None, None, None
    else:
        print("Either access_token or json_file must be provided")
        return None, None, None, None
    
    # Process the data into DataFrames
    manager_df = create_manager_dataframe(data)
    education_df = create_education_dataframe(data)
    certifications_df = create_certification_dataframe(data)
    funds_df = create_funds_dataframe(data)
    
    return manager_df, funds_df, education_df, certifications_df

def main():
    """Main function to run the analysis"""
    # API parameters
    FUND_ID = "F0000045XT"
    MANAGER_ID = "147740"
    ACCESS_TOKEN = "TKOFrzpGUYRPG8agp8N8BpIe8cIt"
    
    # Get data (either from API or local file)
    try:
        # Option 1: Use API
        manager_df, funds_df, education_df, certifications_df = get_fund_manager_data(
            FUND_ID, MANAGER_ID, access_token=ACCESS_TOKEN
        )
        
        # Option 2: Use local file
        # manager_df, funds_df, education_df, certifications_df = get_fund_manager_data(
        #     FUND_ID, MANAGER_ID, json_file='paste.txt'
        # )
        
        if manager_df is None:
            print("Failed to get data. Exiting.")
            return
        
        # Display manager information
        print("\n==== FUND MANAGER INFORMATION ====")
        print(manager_df[['Manager Name', 'AUM ($)', 'Industry Experience (Years)', 
                          'Tenure Performance', 'Index Performance', 'Alpha']].to_string(index=False))
        
        # Display education information
        if not education_df.empty:
            print("\n==== EDUCATION ====")
            print(education_df.to_string(index=False))
        
        # Display certification information
        if not certifications_df.empty:
            print("\n==== CERTIFICATIONS ====")
            print(certifications_df.to_string(index=False))
        
        # Display managed funds summary
        if not funds_df.empty:
            print(f"\n==== MANAGING {len(funds_df)} FUNDS ====")
            print(f"Most recent 5 funds:")
            print(funds_df[['Name', 'Symbol', 'Country', 'Start Date']].head().to_string(index=False))
            
            # Analyze fund data
            country_counts, type_counts, year_counts = analyze_funds(funds_df)
            
            print("\n==== FUNDS BY COUNTRY ====")
            print(country_counts.to_string(index=False))
            
            print("\n==== FUNDS BY SECURITY TYPE ====")
            print(type_counts.to_string(index=False))
            
            if year_counts is not None:
                print("\n==== FUND LAUNCH TIMELINE ====")
                print(year_counts)
            
            # Print comprehensive summary
            print_manager_summary(manager_df, country_counts, type_counts)
        
        # Return all DataFrames for further analysis if needed
        return {
            'manager': manager_df,
            'funds': funds_df,
            'education': education_df,
            'certifications': certifications_df
        }
            
    except Exception as e:
        print(f"Error in main function: {e}")
        return None

if __name__ == "__main__":
    main()