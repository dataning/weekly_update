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