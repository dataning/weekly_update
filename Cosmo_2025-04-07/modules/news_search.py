"""
News search core functionality for the Gravity app
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from services.opoint_service import get_all_companies_news_sync

def search_news(companies, hours_back, initial_limit=500, use_proxy=False):
    """
    Search for news about the given companies
    
    Parameters:
    -----------
    companies : list
        List of company names to search for
    hours_back : int
        Number of hours to look back
    initial_limit : int, default 500
        Initial number of articles to request per company
    use_proxy : bool, default False
        Whether to use a proxy
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the found news articles
    """
    with st.status("Searching for news...", expanded=True) as status:
        st.write(f"Looking for news about {', '.join(companies)}")
        st.write(f"Searching the past {hours_back} hours")
        
        try:
            # Call the function from the service module
            df = get_all_companies_news_sync(
                companies=companies,
                hours_back=hours_back,
                initial_limit=initial_limit,
                use_proxy=use_proxy
            )
            
            if df is not None and not df.empty:
                status.update(label=f"✅ Found {len(df)} articles", state="complete")
                return df
            else:
                status.update(label="❌ No articles found", state="error")
                return pd.DataFrame()
        
        except Exception as e:
            st.error(f"Error during search: {str(e)}")
            status.update(label="❌ Search failed", state="error")
            return pd.DataFrame()

def standardize_opoint_dates(df):
    """
    Standardize Opoint date formats to match Factiva format (2025-03-23)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Opoint data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standardized date formats
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Handle local_time_text column if it exists (20250323T11:57:12+0100)
    if 'local_time_text' in result_df.columns:
        try:
            # Parse the ISO format dates from Opoint
            result_df['unified_date'] = pd.to_datetime(result_df['local_time_text'], errors='coerce')
            
            # Format to match Factiva's format (2025-03-23)
            result_df['unified_date'] = result_df['unified_date'].dt.strftime('%Y-%m-%d')
        except Exception as e:
            st.warning(f"Error standardizing Opoint dates: {e}")
            
    # Handle datetime column if it exists (this is the parsed timestamp)
    elif 'datetime' in result_df.columns:
        try:
            result_df['unified_date'] = result_df['datetime'].dt.strftime('%Y-%m-%d')
        except Exception as e:
            st.warning(f"Error standardizing Opoint datetime: {e}")
    
    return result_df

def standardize_factiva_dates(df):
    """
    Standardize Factiva date formats
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Factiva data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standardized date formats
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Handle publication_date column if it exists
    if 'publication_date' in result_df.columns:
        try:
            # Check if already in datetime format
            if pd.api.types.is_datetime64_any_dtype(result_df['publication_date']):
                result_df['unified_date'] = result_df['publication_date'].dt.strftime('%Y-%m-%d')
            else:
                # Parse and format the date
                result_df['unified_date'] = pd.to_datetime(result_df['publication_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        except Exception as e:
            st.warning(f"Error standardizing Factiva dates: {e}")
    
    return result_df

def standardize_columns(df):
    """
    Standardize column names across different data sources
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to standardize
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standardized columns
    """
    standardized_df = df.copy()
    
    # Create a mapping of standard columns to source-specific columns
    column_mapping = {
        # Title
        'title': ['headline', 'header_text', 'unified_title', 'header', 'title_text', 'Title'],
        # Source
        'source': ['source_name', 'first_source_name'],
        # Date
        'date': ['publication_date', 'local_time_text', 'unified_date'],
        # Summary
        'summary': ['snippet', 'summary_text']
    }
    
    # Add standard columns based on existing data
    for std_col, source_cols in column_mapping.items():
        # Check if standard column already exists
        if std_col not in standardized_df.columns:
            # Try each source column
            for src_col in source_cols:
                if src_col in df.columns:
                    standardized_df[std_col] = df[src_col]
                    break
    
    # Ensure dates are formatted consistently
    if 'date' in standardized_df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(standardized_df['date']):
                standardized_df['date'] = standardized_df['date'].dt.strftime('%Y-%m-%d')
        except:
            pass
    
    # Add URL standardization
    if 'url' not in standardized_df.columns:
        # Try to use factiva_url or url_text
        if 'factiva_url' in standardized_df.columns:
            standardized_df['url'] = standardized_df['factiva_url']
        elif 'url_text' in standardized_df.columns:
            standardized_df['url'] = standardized_df['url_text']
    
    return standardized_df

def perform_joint_search(factiva_df, opoint_df):
    """
    Combine results from Factiva and Opoint with proper column alignment
    
    Parameters:
    -----------
    factiva_df : pandas.DataFrame
        DataFrame with Factiva search results
    opoint_df : pandas.DataFrame
        DataFrame with Opoint search results
        
    Returns:
    --------
    pandas.DataFrame
        Combined DataFrame with standardized columns
    """
    # First standardize dates for each source
    if not factiva_df.empty:
        factiva_df = standardize_factiva_dates(factiva_df)
    
    if not opoint_df.empty:
        opoint_df = standardize_opoint_dates(opoint_df)
    
    # Combine results
    combined_df = pd.concat([factiva_df, opoint_df], ignore_index=True)
    
    if combined_df.empty:
        return pd.DataFrame()
    
    # Standardize all columns
    standardized_df = standardize_columns(combined_df)
    
    # Perform deduplication based on title
    if 'title' in standardized_df.columns:
        # Convert titles to lowercase for comparison
        standardized_df['title_lower'] = standardized_df['title'].str.lower()
        
        # Drop duplicates based on lowercase title, keeping first occurrence
        # (First occurrences will be from Factiva due to concat order)
        standardized_df = standardized_df.drop_duplicates(subset='title_lower', keep='first')
        
        # Remove the temporary column
        standardized_df = standardized_df.drop('title_lower', axis=1)
    
    return standardized_df

def filter_news_data(df, filter_params):
    """
    Apply filters to the news data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to filter
    filter_params : dict
        Dictionary of filter parameters
        
    Returns:
    --------
    pandas.DataFrame
        Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # Apply company filter
    company_filter = filter_params.get('company_filter')
    if company_filter and 'search_term' in df.columns:
        filtered_df = filtered_df[filtered_df['search_term'].isin(company_filter)]
    
    # Apply source filter
    source_filter = filter_params.get('source_filter')
    if source_filter and 'first_source_name' in df.columns:
        # Convert source names to strings for proper comparison
        filtered_df['source_str'] = filtered_df['first_source_name'].astype(str)
        filtered_df = filtered_df[filtered_df['source_str'].isin(source_filter)]
        filtered_df = filtered_df.drop('source_str', axis=1)
    
    # Apply country filter
    country_filter = filter_params.get('country_filter')
    if country_filter and 'countryname' in df.columns:
        filtered_df['countryname_str'] = filtered_df['countryname'].astype(str)
        filtered_df = filtered_df[filtered_df['countryname_str'].isin(country_filter)]
        filtered_df = filtered_df.drop('countryname_str', axis=1)
    
    # Apply site rank filter
    rank_min, rank_max = filter_params.get('rank_min'), filter_params.get('rank_max')
    if rank_min is not None and rank_max is not None and 'site_rank_rank_country' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['site_rank_rank_country'] >= rank_min) & 
            (filtered_df['site_rank_rank_country'] <= rank_max)
        ]
    
    # Apply date filter
    days_back = filter_params.get('days_back')
    if days_back and 'local_time_datetime' in filtered_df.columns:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            filtered_df['date_str'] = filtered_df['local_time_datetime'].dt.strftime('%Y-%m-%d')
            filtered_df = filtered_df[
                (filtered_df['date_str'] >= start_date_str) & 
                (filtered_df['date_str'] <= end_date_str)
            ]
            filtered_df = filtered_df.drop('date_str', axis=1)
        except Exception as e:
            st.warning(f"Could not filter by date: {str(e)}")
    
    # Apply search term in title/summary filter
    search_terms_filter = filter_params.get('search_terms_filter')
    if search_terms_filter and 'search_term' in df.columns and company_filter:
        text_match = pd.Series(False, index=filtered_df.index)
        
        for term in company_filter:
            term_match = pd.Series(False, index=filtered_df.index)
            
            if 'header_text' in filtered_df.columns:
                header_match = filtered_df['header_text'].str.contains(term, case=False, na=False)
                term_match = term_match | header_match
            
            if 'summary_text' in filtered_df.columns:
                summary_match = filtered_df['summary_text'].str.contains(term, case=False, na=False)
                term_match = term_match | summary_match
            
            text_match = text_match | term_match
        
        filtered_df = filtered_df[text_match]
    
    return filtered_df

def create_company_distribution_chart(df):
    """
    Create a bar chart for news distribution by company
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing news data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure for the chart
    """
    if 'search_term' in df.columns:
        company_counts = df['search_term'].value_counts().reset_index()
        company_counts.columns = ['Company', 'Count']
        
        fig = px.bar(
            company_counts, 
            x='Company', 
            y='Count',
            color='Company',
            labels={'Count': 'Number of Articles', 'Company': 'Company Name'},
            title=f"News Distribution ({len(df)} articles)"
        )
        return fig
    return None