"""
Revamped Unified News Search - Streamlit Application
------------------------------------------
A streamlined Streamlit application for searching news articles
from both Dow Jones API and Opoint API with single search functionality.
Includes integration with News Tagging page.
"""

import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
import json
from pathlib import Path
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
import theme

# Flag to control Opoint API availability - set to False to disable
ENABLE_OPOINT = True

# Import the necessary modules
from services.factiva_service import (
    search_free_text,
    get_dow_jones_token_info,
    auto_refresh_token,
    update_token,
    get_valid_token
)

# Conditionally import Opoint-related modules
if ENABLE_OPOINT:
    from modules.news_search import search_news
else:
    # Define a placeholder function if Opoint is disabled
    def search_news(*args, **kwargs):
        return pd.DataFrame()

theme.set_page_config()
theme.apply_full_theme()

# Render header
render_header()

def load_access_code():
    """
    Load the factiva access code from config.json
    
    Returns:
    --------
    str
        The access code, or empty string if not found
    """
    config_path = Path("config.json")
    
    if not config_path.exists():
        print("Warning: config.json not found.")
        return ""
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Get access code from config
        access_code = config.get("dow_jones", {}).get("factiva_access_code", "")
        return access_code
    except Exception as e:
        print(f"Error loading config: {e}")
        return ""

def is_authorized_for_factiva(input_code):
    """
    Check if the provided code matches the factiva access code
    
    Parameters:
    -----------
    input_code : str
        User-provided access code
        
    Returns:
    --------
    bool
        True if authorized, False otherwise
    """
    if not input_code:
        return False
        
    # Load the correct access code from config
    correct_code = load_access_code()
    
    if not correct_code:  # If no code is configured, no access
        return False
        
    # Simple string comparison
    return input_code.strip() == correct_code.strip()

def perform_factiva_search(search_terms, days_back, max_articles):
    """
    Perform a search using the Factiva (Dow Jones) API
    
    Parameters:
    -----------
    search_terms : list
        List of search terms to query
    days_back : int
        Number of days to look back
    max_articles : int
        Maximum number of articles per search term
        
    Returns:
    --------
    pandas.DataFrame
        Combined DataFrame with all search results
    """
    # Check user authorization
    if not is_authorized_for_factiva(st.session_state.get('access_code', '')):
        st.error("You are not authorized to use the Factiva API.")
        return pd.DataFrame()
        
    all_results = []
    
    for term in search_terms:
        st.info(f"Searching Factiva for: {term}")
        term_df = search_free_text(term, n_days=days_back, max_articles=max_articles)
        
        if not term_df.empty:
            # Add search term and source columns
            term_df['search_term'] = term
            term_df['source_api'] = 'Factiva'
            # Combine with main results
            all_results.append(term_df)
        
        # Small delay to avoid overloading the API
        time.sleep(0.5)
    
    # Combine all results into a single DataFrame
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Add timestamp of when the search was performed
        combined_df['search_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate a unique ID for each article
        combined_df['article_id'] = [f"factiva_{i}" for i in range(len(combined_df))]
        
        # Add selection column
        combined_df['selected'] = False
        
        st.success(f"Found {len(combined_df)} articles from Factiva")
        return combined_df
    else:
        st.warning("No articles found from Factiva")
        return pd.DataFrame()

def perform_opoint_search(search_terms, days_back, max_articles, use_proxy=False):
    """
    Perform a search using the Opoint API
    
    Parameters:
    -----------
    search_terms : list
        List of search terms to query
    days_back : int
        Number of days to look back
    max_articles : int
        Maximum number of articles per search term
    use_proxy : bool, default False
        Whether to use a proxy
        
    Returns:
    --------
    pandas.DataFrame
        Combined DataFrame with all search results
    """
    # Skip if Opoint is disabled
    if not ENABLE_OPOINT:
        st.warning("Opoint API is disabled.")
        return pd.DataFrame()
        
    # Convert days to hours for Opoint
    hours_back = days_back * 24
    
    st.info(f"Searching Opoint for: {', '.join(search_terms)}")
    
    try:
        # Call the Opoint search function
        df = search_news(
            companies=search_terms,
            hours_back=hours_back,
            initial_limit=max_articles,
            use_proxy=use_proxy
        )
        
        if not df.empty:
            # Add source column
            df['source_api'] = 'Opoint'
            
            # Generate a unique ID for each article
            df['article_id'] = [f"opoint_{i}" for i in range(len(df))]
            
            # Add selection column
            df['selected'] = False
            
            # Add timestamp of when the search was performed
            df['search_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.success(f"Found {len(df)} articles from Opoint")
            return df
        else:
            st.warning("No articles found from Opoint")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error in Opoint search: {str(e)}")
        return pd.DataFrame()

def perform_joint_search(search_terms, days_back, max_articles, use_proxy=False):
    """
    Perform a joint search across both Factiva and Opoint APIs with improved date alignment
    
    Parameters:
    -----------
    search_terms : list
        List of search terms to query
    days_back : int
        Number of days to look back
    max_articles : int
        Maximum number of articles per search term
    use_proxy : bool, default False
        Whether to use a proxy
        
    Returns:
    --------
    pandas.DataFrame
        Combined DataFrame with results from both APIs
    """
    # Check user authorization for Factiva
    is_factiva_authorized = is_authorized_for_factiva(st.session_state.get('access_code', ''))
    
    # Search Factiva API
    factiva_df = pd.DataFrame()
    opoint_df = pd.DataFrame()
    
    # Search Factiva if token is valid and user is authorized
    if is_factiva_authorized:
        try:
            token_info = get_dow_jones_token_info()
            if token_info.get('status') == 'Valid':
                factiva_df = perform_factiva_search(search_terms, days_back, max_articles)
            else:
                st.warning("Factiva token is invalid or expired. Skipping Factiva search.")
        except Exception as e:
            st.error(f"Error in Factiva search: {str(e)}")
    else:
        st.info("You are not authorized to use Factiva. Using Opoint API only.")
    
    # Search Opoint API only if enabled
    if ENABLE_OPOINT:
        try:
            opoint_df = perform_opoint_search(search_terms, days_back, max_articles, use_proxy)
        except Exception as e:
            st.error(f"Error in Opoint search: {str(e)}")
    
    # If Opoint is disabled and user is not authorized for Factiva, return empty DataFrame
    if not ENABLE_OPOINT and not is_factiva_authorized:
        st.error("You are not authorized to use Factiva and Opoint is disabled. No search possible.")
        return pd.DataFrame()
        
    # If only Factiva search was performed, return those results
    if opoint_df.empty and not factiva_df.empty:
        return factiva_df
        
    # If only Opoint search was performed, return those results
    if factiva_df.empty and not opoint_df.empty:
        return opoint_df
    
    # Combine results for joint search
    combined_df = pd.concat([factiva_df, opoint_df], ignore_index=True)
    
    if combined_df.empty:
        return pd.DataFrame()
    
    # Perform standardization and deduplication for joint search
    try:
        # Create standardized date column
        # For Factiva (which has YYYY-MM-DD format)
        if 'publication_date' in combined_df.columns:
            factiva_mask = combined_df['source_api'] == 'Factiva'
            if factiva_mask.any():
                try:
                    if pd.api.types.is_datetime64_any_dtype(combined_df['publication_date']):
                        combined_df.loc[factiva_mask, 'unified_date'] = combined_df.loc[factiva_mask, 'publication_date']
                    else:
                        # Parse and convert to datetime first
                        dates = pd.to_datetime(combined_df.loc[factiva_mask, 'publication_date'], errors='coerce')
                        # Convert to string in standard format
                        combined_df.loc[factiva_mask, 'unified_date'] = dates.dt.strftime('%Y-%m-%d')
                except Exception as e:
                    st.warning(f"Error processing Factiva dates: {e}")
        
        # For Opoint (which has ISO format 20250323T11:57:12+0100)
        if 'local_time_text' in combined_df.columns:
            opoint_mask = combined_df['source_api'] == 'Opoint'
            if opoint_mask.any():
                try:
                    # Parse the ISO format to datetime
                    dates = pd.to_datetime(combined_df.loc[opoint_mask, 'local_time_text'], errors='coerce')
                    # Convert to string in standard format
                    combined_df.loc[opoint_mask, 'unified_date'] = dates.dt.strftime('%Y-%m-%d')
                except Exception as e:
                    st.warning(f"Error processing Opoint dates: {e}")
        
        # Create standardized title column
        if 'headline' in combined_df.columns and 'header_text' in combined_df.columns:
            # Use headline from Factiva and header_text from Opoint
            combined_df['unified_title'] = combined_df.apply(
                lambda row: row['headline'] if row['source_api'] == 'Factiva' 
                            else row['header_text'], axis=1
            )
        elif 'headline' in combined_df.columns:
            combined_df['unified_title'] = combined_df['headline']
        elif 'header_text' in combined_df.columns:
            combined_df['unified_title'] = combined_df['header_text']
        
        # FIX: Create title column from unified_title
        if 'unified_title' in combined_df.columns and 'title' not in combined_df.columns:
            combined_df['title'] = combined_df['unified_title']
        
        # Create standardized source column
        if 'source_name' in combined_df.columns and 'first_source_name' in combined_df.columns:
            combined_df['source'] = combined_df.apply(
                lambda row: row['source_name'] if row['source_api'] == 'Factiva' 
                           else row['first_source_name'], axis=1
            )
        
        # Create standardized summary column
        if 'snippet' in combined_df.columns and 'summary_text' in combined_df.columns:
            combined_df['summary'] = combined_df.apply(
                lambda row: row['snippet'] if row['source_api'] == 'Factiva' 
                           else row['summary_text'], axis=1
            )
        
        # Create standardized URL column
        if 'url' not in combined_df.columns:
            if 'factiva_url' in combined_df.columns and 'url_text' in combined_df.columns:
                combined_df['url'] = combined_df.apply(
                    lambda row: row['factiva_url'] if row['source_api'] == 'Factiva' 
                               else row['url_text'], axis=1
                )
        
        # Perform deduplication
        if 'unified_title' in combined_df.columns:
            # Group by title to identify duplicates
            title_groups = combined_df.groupby('unified_title')
            
            merged_rows = []
            
            for title, group in title_groups:
                if len(group) > 1 and len(set(group['source_api'])) > 1:
                    # We have articles from different sources that might be duplicates
                    
                    # Create a merged record taking the best from both sources
                    merged_row = {}
                    
                    # Start with the Factiva data if available
                    factiva_rows = group[group['source_api'] == 'Factiva']
                    opoint_rows = group[group['source_api'] == 'Opoint']
                    
                    if not factiva_rows.empty:
                        factiva_data = factiva_rows.iloc[0].to_dict()
                        merged_row.update(factiva_data)
                    
                    if not opoint_rows.empty:
                        opoint_data = opoint_rows.iloc[0].to_dict()
                        
                        # Update with Opoint-specific fields
                        for field, value in opoint_data.items():
                            if field not in merged_row or pd.isna(merged_row[field]):
                                merged_row[field] = value
                    
                    # Mark as merged source
                    merged_row['source_api'] = 'Merged'
                    merged_row['selected'] = False
                    
                    merged_rows.append(merged_row)
                else:
                    # Just add all rows from this group
                    for _, row in group.iterrows():
                        merged_rows.append(row.to_dict())
            
            # Create new dataframe with deduplication results
            if merged_rows:
                combined_df = pd.DataFrame(merged_rows)
                st.success(f"Combined and deduplicated results: {len(combined_df)} articles")
        
        # Make sure we have a standard date column
        if 'date' not in combined_df.columns and 'unified_date' in combined_df.columns:
            combined_df['date'] = combined_df['unified_date']
        
        # Final standardization of columns for display
        standard_columns = ['selected', 'title', 'source', 'date', 'summary', 'search_term', 'source_api', 'url', 'article_id']
        final_columns = [col for col in standard_columns if col in combined_df.columns]
        
        # Return only standardized columns
        try:
            return combined_df[final_columns]
        except:
            # If column selection fails, return original combined dataframe
            return combined_df
            
    except Exception as e:
        st.warning(f"Error during deduplication: {str(e)}")
        st.info("Using combined results without deduplication")
        return combined_df
        
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
    # Make a copy to avoid modifying the original
    standardized_df = df.copy()
    
    # Create a mapping of standard columns to source-specific columns
    column_mapping = {
        # Title
        'title': ['headline', 'header_text', 'unified_title', 'header', 'title_text', 'title'],
        # Source
        'source': ['source_name', 'first_source_name'],
        # Date
        'date': ['publication_date', 'local_time_text', 'unified_date'],
        # Summary
        'summary': ['snippet', 'summary_text'],
        # URL
        'url': ['factiva_url', 'url_text']
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
    
    # Special handling for date format standardization
    if 'date' in standardized_df.columns:
        try:
            # If it's already a datetime, format it to YYYY-MM-DD
            if pd.api.types.is_datetime64_any_dtype(standardized_df['date']):
                standardized_df['date'] = standardized_df['date'].dt.strftime('%Y-%m-%d')
            else:
                # Try to convert to datetime first, then format
                temp_dates = pd.to_datetime(standardized_df['date'], errors='coerce')
                standardized_df['date'] = temp_dates.dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error standardizing date format: {e}")
    
    # Special handling for dates from different API sources
    if 'source_api' in standardized_df.columns:
        # Process Opoint dates 
        opoint_mask = standardized_df['source_api'] == 'Opoint'
        
        if opoint_mask.any() and 'local_time_text' in standardized_df.columns:
            try:
                # Parse the Opoint date format (20250323T11:57:12+0100)
                opoint_dates = pd.to_datetime(
                    standardized_df.loc[opoint_mask, 'local_time_text'], 
                    errors='coerce'
                )
                
                # Format to Factiva style (2025-03-23)
                standardized_df.loc[opoint_mask, 'date'] = opoint_dates.dt.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Error formatting Opoint dates: {e}")
    
    # Select columns for display
    display_cols = ['selected']
    
    # Add the standard columns if they exist
    standard_cols = ['title', 'source', 'date', 'summary', 'search_term', 'source_api', 'url']
    for col in standard_cols:
        if col in standardized_df.columns:
            display_cols.append(col)
    
    # Add article ID if it exists
    if 'article_id' in standardized_df.columns:
        display_cols.append('article_id')
    
    # Return only the columns we want to display
    try:
        display_df = standardized_df[
            [col for col in display_cols if col in standardized_df.columns]
        ]
        return display_df
    except:
        # If there's any issue with column selection, return the full standardized DF
        return standardized_df

def display_unified_results(df):
    """
    Display unified search results with improved selection capability,
    enhanced filtering options, and integration with the News Tagging page
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing search results
    """
    # Summary statistics
    st.markdown(f"<h3>{len(df)} articles found</h3>", unsafe_allow_html=True)
    
    # Create a copy of the dataframe to avoid modifying the original directly
    working_df = df.copy()
    
    # Start with a standardized view of the data
    display_df = standardize_columns(working_df)
    
    # Ensure we have unique article IDs for reliable selection tracking
    if 'article_id' not in display_df.columns:
        display_df['article_id'] = [f"article_{i}" for i in range(len(display_df))]
        # Store these IDs back in the original dataframe
        if len(working_df) == len(display_df):
            working_df['article_id'] = display_df['article_id'].values
    
    # Initialize the filtered dataframe to start with all data
    filtered_df = display_df.copy()
    original_count = len(filtered_df)
    
    # Add waterfall filtering options
    st.markdown("### Waterfall Filtering")
    st.info("Apply filters sequentially: first exclude sources, then filter by keywords, finally select preferred sources.")
    
    # Initialize session state for tracking filters
    if 'excluded_sources' not in st.session_state:
        st.session_state.excluded_sources = []
    if 'title_keywords' not in st.session_state:
        st.session_state.title_keywords = []
    if 'preferred_sources' not in st.session_state:
        st.session_state.preferred_sources = []
    
    # Create expandable sections for each filtering step
    with st.expander("Step 1: Exclude News Sources", expanded=True):
        st.markdown("Select sources you want to **remove** from results:")
        
        # Extract unique sources if the source column exists
        if 'source' in filtered_df.columns and len(filtered_df) > 0:
            # Get all unique sources
            all_sources = sorted(filtered_df['source'].unique().tolist())
            
            if len(all_sources) > 0:
                # Create a multiselect filter for sources to exclude
                excluded_sources = st.multiselect(
                    "Select sources to exclude:",
                    options=all_sources,
                    default=st.session_state.excluded_sources,
                    help="Select one or more sources to remove from results",
                    key="excluded_sources_filter"
                )
                
                # Store in session state
                st.session_state.excluded_sources = excluded_sources
                
                # Apply the exclusion filter
                if excluded_sources:
                    source_mask = ~filtered_df['source'].isin(excluded_sources)
                    if source_mask.any():
                        filtered_df = filtered_df.loc[source_mask]
                        excluded_count = original_count - len(filtered_df)
                        st.success(f"Excluded {excluded_count} articles from selected sources. {len(filtered_df)} articles remaining.")
                    else:
                        st.warning("All articles would be excluded by this filter!")
                        # Reset to original to prevent empty results
                        filtered_df = display_df.copy()
                
        # Show count after first filter
        step1_count = len(filtered_df)
        st.write(f"Articles remaining after Step 1: {step1_count}")
    
    # Step 2: Filter by keywords in title
    with st.expander("Step 2: Filter by Keywords in Title", expanded=True):
        st.markdown("Enter keywords that should be present in article titles (comma-separated):")
        
        # Text input for keywords
        keyword_input = st.text_input(
            "Keywords to include in title:",
            value=", ".join(st.session_state.title_keywords),
            placeholder="BlackRock, etc.",
            help="Articles will be shown only if title contains ANY of these keywords",
            key="title_keywords_filter"
        )
        
        # Process the keyword input
        if keyword_input:
            # Split by comma and clean up
            keywords = [k.strip() for k in keyword_input.split(',') if k.strip()]
            
            # Store in session state
            st.session_state.title_keywords = keywords
            
            if keywords and 'title' in filtered_df.columns:
                title_mask = pd.Series(False, index=filtered_df.index)
                
                # Check for each keyword (OR logic between keywords)
                for keyword in keywords:
                    keyword_match = filtered_df['title'].astype(str).str.contains(keyword, case=False, na=False)
                    title_mask = title_mask | keyword_match
                
                # Apply the keyword filter
                if title_mask.any():
                    filtered_df = filtered_df.loc[title_mask]
                    keyword_filtered_count = step1_count - len(filtered_df)
                    st.success(f"Filtered to {len(filtered_df)} articles containing at least one keyword.")
                else:
                    st.warning(f"No articles found containing any of these keywords: {', '.join(keywords)}")
        
        # Show count after second filter
        step2_count = len(filtered_df)
        st.write(f"Articles remaining after Step 2: {step2_count}")
    
    # Step 3: Filter by preferred sources
    with st.expander("Step 3: Select Preferred Sources", expanded=True):
        st.markdown("Select sources you want to **keep** (leave empty to keep all remaining sources):")
        
        # Get remaining sources after previous filters
        remaining_sources = sorted(filtered_df['source'].unique().tolist())
        
        if remaining_sources:
            # Create a multiselect filter for preferred sources
            preferred_sources = st.multiselect(
                "Select preferred sources:",
                options=remaining_sources,
                default=st.session_state.preferred_sources,
                help="Select one or more sources to keep (empty = keep all)",
                key="preferred_sources_filter"
            )
            
            # Store in session state
            st.session_state.preferred_sources = preferred_sources
            
            # Apply the preferred sources filter
            if preferred_sources:
                source_mask = filtered_df['source'].isin(preferred_sources)
                if source_mask.any():
                    filtered_df = filtered_df.loc[source_mask]
                    preferred_filtered_count = step2_count - len(filtered_df)
                    st.success(f"Kept {len(filtered_df)} articles from preferred sources.")
                else:
                    st.warning("No articles found from preferred sources!")
        
        # Show count after third filter
        step3_count = len(filtered_df)
        st.write(f"Articles remaining after Step 3: {step3_count}")
    
    # Add a "Reset All Filters" button
    if st.button("Reset All Filters", key="reset_all_filters"):
        # Clear all filters
        st.session_state.excluded_sources = []
        st.session_state.title_keywords = []
        st.session_state.preferred_sources = []
        # Reset to original data
        filtered_df = display_df.copy()
        st.success("All filters have been reset.")
        st.experimental_rerun()
    
    # Show final filtered results count
    st.markdown(f"### Filtered Results: {len(filtered_df)} articles")
    
    # Check for existing selections and initialize if needed
    if 'selected_article_ids' not in st.session_state:
        st.session_state.selected_article_ids = set()
    
    # Sync any existing selections from dataframe to session state
    if 'article_id' in working_df.columns:
        selected_in_df = working_df.loc[working_df['selected'] == True, 'article_id'].tolist()
        for article_id in selected_in_df:
            st.session_state.selected_article_ids.add(article_id)
    
    # Update the filtered dataframe's 'selected' column based on session state
    if 'article_id' in filtered_df.columns:
        filtered_df['selected'] = filtered_df['article_id'].apply(
            lambda x: x in st.session_state.selected_article_ids
        )
    
    # Display the data using data_editor - hide article_id from view
    if not filtered_df.empty:
        # Setup column configuration for data_editor
        column_config = {
            "selected": st.column_config.CheckboxColumn("Select"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "source": st.column_config.TextColumn("Source"),
            "date": st.column_config.TextColumn("Date"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
            "search_term": st.column_config.TextColumn("Search Term"),
            "source_api": st.column_config.TextColumn("Source API"),
            "article_id": st.column_config.TextColumn("ID", disabled=True)
        }
        
        # Configure URL columns if they exist
        for url_col in ['url', 'factiva_url']:
            if url_col in filtered_df.columns:
                column_config[url_col] = st.column_config.LinkColumn("URL")
        
        # Initialize selection state for callback
        if 'selection_change_id' not in st.session_state:
            st.session_state.selection_change_id = None
        if 'selection_change_state' not in st.session_state:
            st.session_state.selection_change_state = False
            
        # Create a callback for selection changes
        def on_selection_change(article_id, state):
            # Update session state selection set
            if state:
                st.session_state.selected_article_ids.add(article_id)
            else:
                if article_id in st.session_state.selected_article_ids:
                    st.session_state.selected_article_ids.remove(article_id)
            
            # Force update of working dataframe
            working_df['selected'] = working_df['article_id'].apply(
                lambda x: x in st.session_state.selected_article_ids
            )
            
            # Update session state
            st.session_state.search_results = working_df
            
        # Create a container for the table with fixed height
        table_container = st.container()
        with table_container:
            # Calculate selected count for key generation
            selected_count = len(st.session_state.selected_article_ids)
            
            # Use st.data_editor with a custom key to force refresh and make selection more responsive
            edited_df = st.data_editor(
                filtered_df,
                column_config=column_config,
                use_container_width=True,
                num_rows="fixed",
                height=600,
                disabled=[col for col in filtered_df.columns if col != "selected"],
                hide_index=True,
                key=f"news_data_editor_{selected_count}",
                column_order=["selected"] + [col for col in filtered_df.columns if col != "selected" and col != "article_id"] + ["article_id"]
            )
            
            # Process selection changes immediately
            for idx, row in edited_df.iterrows():
                article_id = row['article_id']
                is_selected = row['selected']
                
                # Check if selection state changed
                previous_state = article_id in st.session_state.selected_article_ids
                if is_selected != previous_state:
                    on_selection_change(article_id, is_selected)
        
        # Count selected items
        selected_count = len(st.session_state.selected_article_ids)
        st.write(f"Total selected: {selected_count} articles")
        
        # Create action buttons for selections
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if selected_count > 0:
                if st.button("Create Filtered Dataset", 
                            type="primary",
                            key="create_filtered_btn"):
                    # Store the filtered dataset
                    filtered_data = working_df[working_df['article_id'].isin(st.session_state.selected_article_ids)].copy()
                    
                    # Standardize the data before storing
                    standardized_data = standardize_columns(filtered_data)
                    
                    # Ensure all required columns are present
                    required_columns = ['article_id', 'title', 'date', 'source', 'summary', 'search_term', 'source_api', 'url']
                    for col in required_columns:
                        if col not in standardized_data.columns:
                            standardized_data[col] = ""
                    
                    # Store both versions - original for the filtered dataset view and standardized for tagging
                    st.session_state.filtered_dataset = standardized_data
                    
                    # IMPORTANT: Also store for News Tagging page
                    st.session_state.selected_news_df = standardized_data
                    
                    st.session_state.show_filtered = True  # Set a flag to show the dataset
        
        with col2:
            if selected_count > 0:
                if st.button("Clear Selection", key="clear_selection_btn"):
                    # Clear selection
                    st.session_state.selected_article_ids = set()
                    working_df['selected'] = False
                    st.session_state.search_results = working_df
                    st.rerun()
        
        with col3:
            # Download button for all results
            csv = working_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download All Results as CSV",
                csv,
                f"news_search_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="download_all_csv"
            )
            
        with col4:
            # Add button to go to News Tagging page - only active when selections exist
            if selected_count > 0:
                if st.button("Tag Selected Articles", 
                           key="go_to_tagging_btn",
                           type="primary",
                           use_container_width=True):
                    # Store selected articles in session state for the News Tagging page
                    filtered_data = working_df[working_df['article_id'].isin(st.session_state.selected_article_ids)].copy()
                    
                    # Ensure all required columns are present and standardized
                    required_columns = ['article_id', 'title', 'date', 'source', 'summary', 'search_term', 'source_api', 'url']
                    
                    # Standardize columns before storing
                    standardized_data = standardize_columns(filtered_data)
                    
                    # Check for missing required columns and add placeholders if needed
                    for col in required_columns:
                        if col not in standardized_data.columns:
                            standardized_data[col] = ""
                    
                    # Store the standardized data
                    st.session_state.selected_news_df = standardized_data
                    
                    # Navigate to the News Tagging page
                    st.switch_page("pages/02_news_tagging.py")
    
        # Display the filtered dataset if available
        if st.session_state.get('show_filtered', False):
            # Get the stored filtered dataset
            filtered_data = st.session_state.filtered_dataset
            
            # Show the filtered dataset with single column layout and buttons below
            st.markdown("---")  # Add divider for separation
            st.subheader("Filtered Dataset")
            st.success(f"Created filtered dataset with {len(filtered_data)} articles")
            
            # Display dataframe
            st.dataframe(filtered_data, use_container_width=True, hide_index=True)
            
            # Create buttons row
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                # Add download option
                csv = filtered_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download Filtered Dataset as CSV",
                    csv,
                    f"filtered_news_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key="download_filtered_csv",
                    use_container_width=True
                )
            
            with btn_col2:
                # Add button to clear the filtered view
                if st.button("Hide Filtered Dataset", key="hide_filtered_btn", use_container_width=True):
                    st.session_state.show_filtered = False
                    st.rerun()
            
            # Add guidance text
            st.write("### Next Steps")
            st.write("You can now tag these articles or continue searching.")
            
            # Add button to go to tagging with these filtered articles - full width
            if st.button("Tag Filtered Articles", 
                       key="tag_filtered_btn",
                       type="primary",
                       use_container_width=True):
                # Get the filtered data and ensure it's properly standardized
                filtered_data = st.session_state.filtered_dataset.copy()
                
                # Ensure all required columns are present and standardized
                required_columns = ['article_id', 'title', 'date', 'source', 'summary', 'search_term', 'source_api', 'url']
                
                # Standardize columns before storing
                standardized_data = standardize_columns(filtered_data)
                
                # Check for missing required columns and add placeholders if needed
                for col in required_columns:
                    if col not in standardized_data.columns:
                        standardized_data[col] = ""
                
                # Store the standardized data
                st.session_state.selected_news_df = standardized_data
                
                # Navigate to the News Tagging page
                st.switch_page("pages/02_news_tagging.py")
    else:
        st.info("No articles found matching your filter criteria. Try adjusting your filters.")
                
def display_token_management():
    """Handle token management UI and functionality for Dow Jones API"""
    with st.expander("🔑 Dow Jones API Token Management", expanded=False):
        # Get token info
        token_info = get_dow_jones_token_info()
        
        # Show current token status
        if 'error' in token_info:
            st.error(f"Token error: {token_info['error']}")
            token_valid = False
        else:
            status = token_info.get('status', 'Unknown')
            if status == 'Valid':
                st.success(f"Token valid! {token_info.get('time_status', '')}")
                token_valid = True
            else:
                st.warning(f"Token status: {status} - {token_info.get('time_status', '')}")
                token_valid = False
        
        # Token management options
        col1, col2 = st.columns(2)
        
        with col1:
            # Auto-refresh button if token is expired
            if not token_valid:
                if st.button("🔄 Auto-Refresh Token", key="auto_refresh_token_btn"):
                    with st.spinner("Attempting to refresh token automatically..."):
                        if auto_refresh_token():
                            st.success("Token refreshed successfully!")
                            time.sleep(2)  # Give user time to see success message
                            st.rerun()  # Refresh the app to use the new token
                        else:
                            st.error("Automatic token refresh failed. Please update manually.")
        
        with col2:
            # Manual update section
            new_token = st.text_input("New API Token", 
                              type="password", 
                              help="Paste your new Dow Jones API token here",
                              key="new_token_input")
            
            if st.button("Update Token", key="update_token_btn"):
                if new_token:
                    with st.spinner("Validating new token..."):
                        if update_token(new_token):
                            st.success("Token updated successfully!")
                            time.sleep(2)  # Give user time to see success message
                            st.rerun()  # Refresh the app to use the new token
                        else:
                            st.error("Failed to update token. Please check if it's valid.")
                else:
                    st.error("Please enter a token")
        
        return token_valid

def main():
    """Main application function with fully combined card layout UI"""
    # App header
    st.markdown("<h2 style='color: #000000; margin-bottom: 1rem;'>📰 News Search</h2>", unsafe_allow_html=True)
    # st.markdown("<div style='background-color: #E3F2FD; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
    #             "Search for news across multiple sources, then tag and organize for your newsletter."
    #             "</div>", unsafe_allow_html=True)
    
    # Initialize session state variables
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    
    if "show_filtered" not in st.session_state:
        st.session_state.show_filtered = False
    
    # Token management section stays in the sidebar
    with st.sidebar:
        st.header("Access & Token Management")
        
        # Get or initialize the access code in session state
        if 'access_code' not in st.session_state:
            st.session_state.access_code = ""
        
        # Access code input field (kept in sidebar for security/confidentiality)
        access_code = st.text_input(
            "Enter Factiva access code",
            type="password",
            value=st.session_state.access_code,
            placeholder="Enter special access code",
            help="Enter the special code to access Factiva search features",
            key="access_code_input"
        )
        
        # Update access code in session state when changed
        if access_code != st.session_state.access_code:
            st.session_state.access_code = access_code
            # Force a rerun to update available search options
            st.rerun()
        
        # Determine if user is authorized for Factiva
        is_factiva_auth = is_authorized_for_factiva(access_code)
        
        # Show authorization status
        if access_code:
            if is_factiva_auth:
                st.success("✅ Access granted to all search features.")
            else:
                st.warning("⚠️ Invalid code. You only have access to Opoint search.")
        
        # Token management for Factiva if needed and authorized
        if is_factiva_auth:
            token_valid = display_token_management()
    
    # Determine available search options based on authorization
    search_options = []
    
    # Always add Opoint if enabled
    if ENABLE_OPOINT:
        search_options.append("Opoint")
        
    # Add Factiva and Joint Search if authorized
    if is_factiva_auth:
        search_options = ["Joint Search", "Factiva (Dow Jones)"] + search_options
        default_index = 0  # Default to Joint Search
    else:
        default_index = 0  # Default to Opoint (which would be index 0 in this case)
        
    # Show message if no search options are available
    if not search_options:
        st.error("No search options available. Please contact administrator.")
        return
        
    # Create two columns inside the card
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Search engine selection
        search_engine = st.radio(
            "Search Engine:",
            search_options,
            index=default_index,
            key="search_engine_radio",
            horizontal=True
        )
        
        # Search query input
        search_query = st.text_area(
            "Search Terms (one per line or comma-separated):",
            placeholder="BlackRock",
            help="Enter one keyword or phrase per line, or separate with commas",
            height=70,
            key="unified_search_query"
        )

        # Search button inside the card
        search_button = st.button(
            "🔍 Search News", 
            type="primary", 
            use_container_width=True,
            key="unified_search_btn"
        )

    with col2:
        # Time range
        days_back = st.slider(
            "Days to look back:",
            min_value=1,
            max_value=30,
            value=1,  # Default to 1 day
            step=1,
            key="unified_days_back_slider"
        )
        
        # Max articles
        max_articles = st.number_input(
            "Maximum articles per search term:",
            min_value=10,
            max_value=1000,
            value=500,
            step=10,
            key="unified_max_articles_input"
        )
        
        # Network options
        use_proxy = st.checkbox("Use BLK N@twork", value=True, key="unified_use_proxy_checkbox")
    

    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Horizontal rule to separate search from results
    st.markdown("---")
    
    # Process search when button is clicked
    if search_button:
        if not search_query:
            st.error("Please enter search terms")
        else:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Starting search...")
            progress_bar.progress(10)
            
            # Parse search terms (split by comma or newline)
            search_terms = [term.strip() for term in re.split(r'[,\n]', search_query) if term.strip()]
            
            try:
                # Determine which search to perform
                if search_engine == "Factiva (Dow Jones)" and is_authorized_for_factiva(st.session_state.access_code):
                    status_text.text("Searching Factiva...")
                    progress_bar.progress(30)
                    
                    # Call Factiva search function
                    results_df = perform_factiva_search(search_terms, days_back, max_articles)
                    
                elif search_engine == "Opoint" and ENABLE_OPOINT:
                    status_text.text("Searching Opoint...")
                    progress_bar.progress(30)
                    
                    # Call Opoint search function
                    results_df = perform_opoint_search(search_terms, days_back, max_articles, use_proxy)
                    
                elif search_engine == "Joint Search" and is_authorized_for_factiva(st.session_state.access_code):
                    status_text.text("Performing joint search...")
                    progress_bar.progress(20)
                    
                    # Call joint search function
                    results_df = perform_joint_search(search_terms, days_back, max_articles, use_proxy)
                
                else:
                    st.error("You are not authorized to use this search engine.")
                    results_df = pd.DataFrame()
                
                status_text.text("Processing results...")
                progress_bar.progress(90)
                
                # Store results in session state
                st.session_state.search_results = results_df
                
                # Reset filtered dataset flag when new search is performed
                st.session_state.show_filtered = False
                
                # Complete progress
                progress_bar.progress(100)
                status_text.text("Search complete!")
                
                # Force a refresh to show the results
                time.sleep(1)  # Brief pause to show completion
                st.rerun()
                
            except Exception as e:
                st.error(f"Error during search: {str(e)}")
                progress_bar.empty()
                status_text.empty()
    
    # Display results if available
    if st.session_state.search_results is not None:
        if not st.session_state.search_results.empty:
            display_unified_results(st.session_state.search_results)
        else:
            st.info("No articles found matching your search criteria.")
    else:
        # Show empty state with guidance
        # st.info("Enter your search terms above and click 'Search News' to begin.")
        
        # Multi-step workflow explanation
        # st.markdown("### News Search to Newsletter Workflow")
        step1, step2, step3 = st.columns(3)
        
        with step1:
            st.markdown("### 1. Search & Select")
            st.markdown("- Enter search terms")
            st.markdown("- Browse search results")
            st.markdown("- Check boxes to select articles")
            st.markdown("- Click 'Tag Selected Articles'")
            
        with step2:
            st.markdown("### 2. Tag & Organize")
            st.markdown("- Add themes to articles")
            st.markdown("- Add regional subheaders")
            st.markdown("- Organize content by topic")
            st.markdown("- Finalize your selection")
            
        with step3:
            st.markdown("### 3. Generate Newsletter")
            st.markdown("- Select newsletter template")
            st.markdown("- Add introduction text")
            st.markdown("- Preview your newsletter")
            st.markdown("- Export or send to colleagues")

if __name__ == "__main__":
    main()

# Render sidebar component
render_sidebar()

# Render footer component
render_footer()