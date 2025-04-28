import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import os
from pathlib import Path

def get_content_from_jina(deepcast_url):
    """
    Get content from r.jina.ai for a DeepCast URL and parse it into structured DataFrames
    """
    jina_url = f"https://r.jina.ai/{deepcast_url}"
    
    try:
        response = requests.get(jina_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        sections = parse_sections(soup.get_text())
        dfs = create_dataframes(sections)
        combined_df = combine_podcast_dataframes(dfs)
        dfs['combined'] = combined_df
        
        # Extract episode name from URL for filename
        path_parts = urlparse(deepcast_url).path.split('/')
        episode_name = path_parts[-1] if path_parts[-1] else path_parts[-2]
        
        # Let the main script handle file saving
        return dfs
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def parse_sections(text):
    """Parse text content into structured sections"""
    sections = {
        'summary': [],
        'takeaways': [],
        'quotes': [],
        'episode_info': {
            'content': []
        }
    }
    
    current_section = None
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        # Check for section headers
        if 'DeepSummary' in line:
            current_section = 'summary'
        elif 'Key Episode Takeaways' in line:
            current_section = 'takeaways'
        elif 'Top Episodes Quotes' in line:
            current_section = 'quotes'
        elif '#### Episode Information' in line:
            current_section = 'episode_info'
            i += 1  # Skip the header line
            # Collect all content until "#### Stay Connected"
            while i < len(lines) and '#### Stay Connected' not in lines[i]:
                if lines[i].strip():  # Only add non-empty lines
                    sections['episode_info']['content'].append(lines[i].strip())
                i += 1
            current_section = None  # Reset section after collecting episode info
        
        # Process content based on current section
        if current_section == 'summary':
            if line and not line.startswith('####'):
                sections['summary'].append(line)
        elif current_section == 'takeaways':
            if re.match(r'^\d+\.', line):
                sections['takeaways'].append(line)
        elif current_section == 'quotes':
            if re.match(r'^\d+\.', line):
                sections['quotes'].append(line)
        
        i += 1
    
    return sections

def create_dataframes(sections):
    """Convert parsed sections into DataFrames"""
    dfs = {}
    
    # Summary DataFrame
    dfs['summary'] = pd.DataFrame({'content': sections['summary']})
    
    # Takeaways DataFrame
    dfs['takeaways'] = pd.DataFrame({'content': sections['takeaways']})
    
    # Quotes DataFrame
    dfs['quotes'] = pd.DataFrame({'content': sections['quotes']})

    # Episode Info DataFrame
    dfs['episode_info'] = pd.DataFrame({'content': sections['episode_info']['content']})
    
    return dfs

def combine_podcast_dataframes(dfs):
    """
    Combines multiple podcast-related DataFrames into a single DataFrame with section and content columns.
    """
    combined_data = []
    
    # Process Summary
    for _, row in dfs['summary'].iterrows():
        combined_data.append({
            'section': 'Summary',
            'content': row['content']
        })
    
    # Process Takeaways
    for _, row in dfs['takeaways'].iterrows():
        combined_data.append({
            'section': 'Key Takeaways',
            'content': row['content']
        })
    
    # Process Quotes
    for _, row in dfs['quotes'].iterrows():
        combined_data.append({
            'section': 'Quotes',
            'content': row['content']
        })
    
    # Process Episode Info
    for _, row in dfs['episode_info'].iterrows():
        combined_data.append({
            'section': 'Episode Info',
            'content': row['content']
        })
    
    # Create combined DataFrame
    combined_df = pd.DataFrame(combined_data)
    
    return combined_df

# # Example usage
# deepcast_url = "https://deepcast.fm/episode/secret-agent-send-your-children-to-a-village-how-to-detect-a-lie-instantly-the-eye-contact-trick-i-learnt-from-12-years-as-a-secret-service-agent-evy-poumpouras"

# dfs = get_content_from_jina(deepcast_url)

# if dfs:
#     print("\nCombined DataFrame:")
#     print(dfs['combined'])