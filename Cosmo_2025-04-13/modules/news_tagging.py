"""
News tagging functionality for the Gravity app
"""
import pandas as pd

def apply_theme_to_selected(df, theme_list):
    """
    Apply themes to selected articles
    
    Args:
        df: DataFrame containing articles
        theme_list: List of themes to apply
        
    Returns:
        tuple: (Modified dataframe, count of affected rows)
    """
    mask = df['selected'] == True
    if mask.any():
        # For selected rows, append new themes (avoid duplicates)
        for idx in df[mask].index:
            current_themes = set([] if pd.isna(df.at[idx, 'Theme']) or df.at[idx, 'Theme'] == "" else 
                                [t.strip() for t in df.at[idx, 'Theme'].split(",")])
            new_themes = current_themes.union(set(theme_list))
            df.at[idx, 'Theme'] = ", ".join(new_themes)
        return df, mask.sum()
    else:
        return df, 0

def apply_subheader_to_selected(df, subheader_list):
    """
    Apply subheaders to selected articles
    
    Args:
        df: DataFrame containing articles
        subheader_list: List of subheaders to apply
        
    Returns:
        tuple: (Modified dataframe, count of affected rows)
    """
    mask = df['selected'] == True
    if mask.any():
        # For selected rows, append new subheaders (avoid duplicates)
        for idx in df[mask].index:
            current_subheaders = set([] if pd.isna(df.at[idx, 'Subheader']) or df.at[idx, 'Subheader'] == "" else 
                                   [s.strip() for s in df.at[idx, 'Subheader'].split(",")])
            new_subheaders = current_subheaders.union(set(subheader_list))
            df.at[idx, 'Subheader'] = ", ".join(new_subheaders)
        return df, mask.sum()
    else:
        return df, 0

def clear_all_checks(df):
    """
    Clear all checked selections
    
    Args:
        df: DataFrame with selected column
        
    Returns:
        DataFrame with cleared selections
    """
    df_copy = df.copy()
    df_copy['selected'] = False
    return df_copy

def reset_all_tags(df):
    """
    Reset Theme and Subheader fields
    
    Args:
        df: DataFrame with Theme and Subheader columns
        
    Returns:
        DataFrame with reset tags
    """
    df_copy = df.copy()
    df_copy['Theme'] = ""
    df_copy['Subheader'] = ""
    return df_copy