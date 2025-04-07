"""
Data processing utilities for the Gravity app
"""
import pandas as pd
import re
from datetime import datetime

def clean_text(text):
    """Clean and format text content"""
    if not isinstance(text, str):
        return ""
    # Replace multiple newlines and spaces with single ones
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def clean_dataframe(df):
    """Clean dataframe without adding columns"""
    if df is None:
        return None
        
    # Make a clean copy of the dataframe
    df_clean = df.copy()
    
    # Remove unnamed columns
    unnamed_cols = [col for col in df_clean.columns if 'Unnamed:' in col]
    if unnamed_cols:
        df_clean = df_clean.drop(columns=unnamed_cols)
        
    # Add selection column if it doesn't exist (required for functionality)
    if 'selected' not in df_clean.columns:
        df_clean['selected'] = False
        
    # Handle date formatting if needed
    if 'Date' in df_clean.columns and df_clean['Date'].dtype == 'object':
        try:
            df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        except:
            pass  # Keep original if conversion fails
            
    return df_clean

def create_column_mapping(df, prefix=""):
    """Create column mapping based on existing dataframe columns"""
    if df is None or df.empty:
        return {}
        
    columns = list(df.columns)
    
    # Default to theme/Company for main categories
    theme_col = next((col for col in ['Theme', 'theme', 'Company', 'company', 'search_term'] 
                      if col in columns), columns[0])
    
    # Default to subheader/News_Type for subcategories
    subheader_col = next((col for col in ['Subheader', 'subheader', 'News_Type', 'Category', 'category'] 
                         if col in columns), columns[0])
    
    # Create mapping without modifying the dataframe
    column_mapping = {
        'theme': theme_col,
        'subheader': subheader_col,
        'article_title': next((col for col in ['Article_Title', 'Title', 'header_text', 'Headline'] 
                              if col in columns), columns[0]),
        'source': next((col for col in ['Source', 'source', 'first_source_name', 'Publisher'] 
                       if col in columns), columns[0]),
        'date': next((col for col in ['Date', 'date', 'local_time_text', 'Publication_Date'] 
                     if col in columns), columns[0]),
        'content': next((col for col in ['Content', 'content', 'summary_text', 'body_text', 'Summary'] 
                        if col in columns), columns[0])
    }
    
    return column_mapping

def format_date(date_value):
    """Format date values consistently"""
    if pd.isna(date_value):
        return ''
        
    if isinstance(date_value, str):
        try:
            return pd.to_datetime(date_value).strftime('%d %B %Y')
        except Exception:
            return date_value
            
    try:
        return date_value.strftime('%d %B %Y')
    except Exception:
        return str(date_value)