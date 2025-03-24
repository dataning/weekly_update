"""
Newsletter generation module for the Gravity app
"""
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from jinja2 import Template
from services.banner_service import (
    get_modified_banner_html,
    extract_banner_from_html,
    inject_banner_into_newsletter,
    update_html_dimensions
)
from utils.html_processing import apply_summary_at_position, apply_image_content

class NewsletterGenerator:
    """
    Core newsletter generation functionality
    """
    def __init__(self, template_path=None, template_content=None):
        """
        Initialize with either a template path or direct template content
        
        Args:
            template_path: Path to HTML template file
            template_content: HTML template content as string
        """
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                self.template_html = file.read()
        elif template_content:
            self.template_html = template_content
        else:
            template_path = 'templates/newsletter_template.html'
            # Try to load the default template
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as file:
                    self.template_html = file.read()
            else:
                raise ValueError("No template found. Please provide template_path or template_content")
        
        # Prepare the Jinja template once for reuse
        self.template = Template(self.template_html)
    
    def _format_date(self, date_value):
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
    
    def _process_article(self, row):
        """Extract article data from a DataFrame row with proper validation"""
        return {
            'title': row.get('article_title', ''),
            'source': row.get('source', ''),
            'date': self._format_date(row.get('date')),
            'content': row.get('content', ''),
            'subheader': row.get('subheader', 'General'),  # Use subheader directly
            'subsection': row.get('subsection', 'General')  # Keep for backwards compatibility
        }
    
    def _process_sections(self, df_processed):
        """Process news sections using theme and subheader organization"""
        custom_sections = []
        
        # Get unique themes
        if 'theme' in df_processed.columns:
            unique_themes = df_processed['theme'].unique()
        else:
            unique_themes = ['General Theme']
            
        # Process each theme
        for theme in unique_themes:
            # Filter for this theme
            theme_df = df_processed[df_processed['theme'] == theme]
            
            # Skip if no articles for this theme
            if theme_df.empty:
                continue
            
            # Initialize the section structure
            custom_section = {
                'name': theme,
                'articles': [],
                'subsections': {},
                # For backward compatibility
                'company_news': [],
                'competitor_news': []
            }
            
            # Get unique subheaders for this theme
            if 'subheader' in theme_df.columns:
                unique_subheaders = theme_df['subheader'].dropna().unique()
            else:
                unique_subheaders = ['General']
            
            # Process each subheader
            for subheader in unique_subheaders:
                if pd.isna(subheader):
                    continue
                    
                # Filter for this subheader
                subheader_df = theme_df[theme_df['subheader'] == subheader]
                
                # Process articles for this subheader
                for _, row in subheader_df.iterrows():
                    if pd.notna(row.get('article_title')) and row.get('article_title') != 'No news updates this week':
                        article = self._process_article(row)
                        
                        # Add to general articles list
                        custom_section['articles'].append(article)
                        
                        # Organize by subheader
                        if subheader not in custom_section['subsections']:
                            custom_section['subsections'][subheader] = []
                        
                        custom_section['subsections'][subheader].append(article)
                        
                        # For backward compatibility: map to either company_news or competitor_news
                        # Based on common subheader patterns
                        subheader_lower = str(subheader).lower()
                        if ('company' in subheader_lower or 'product' in subheader_lower or 
                            'industry' in subheader_lower or 'market' in subheader_lower):
                            custom_section['company_news'].append(article)
                        else:
                            # All other types go to competitor news
                            custom_section['competitor_news'].append(article)
            
            # Only add sections that have articles
            if custom_section['articles']:
                custom_sections.append(custom_section)
            
        return custom_sections
    
    def _validate_dataframe(self, df, column_mapping):
        """Validate and preprocess DataFrame columns"""
        df_processed = df.copy()
        
        # Apply column mapping if provided
        if column_mapping:
            col_map = {v: k for k, v in column_mapping.items() if v in df.columns}
            if col_map:
                df_processed = df_processed.rename(columns=col_map)
        
        # Map Company to theme and News_Type to subheader if they exist
        if 'Company' in df_processed.columns and 'theme' not in df_processed.columns:
            df_processed['theme'] = df_processed['Company']
            
        if 'News_Type' in df_processed.columns and 'subheader' not in df_processed.columns:
            df_processed['subheader'] = df_processed['News_Type']
        
        # Ensure required columns exist with defaults
        required_columns = {
            'theme': 'General Theme',
            'subheader': 'General',
            'subsection': 'General',  # Legacy - kept for backward compatibility
            'article_title': '',
            'content': ''
        }
        
        for col, default in required_columns.items():
            if col not in df_processed.columns:
                df_processed[col] = default
        
        # Process date column
        if 'date' in df_processed.columns:
            df_processed['date'] = df_processed['date'].apply(
                lambda x: pd.to_datetime(x, errors='coerce') if not pd.isna(x) else None
            )
        else:
            df_processed['date'] = datetime.now()
            
        return df_processed
    
    def generate_newsletter(
        self, df, output_path=None, preview_text='Your newsletter preview text here', 
        column_mapping=None, colors=None, banner_input=None, summary_html="", 
        image_html="", content_width=800, mobile_friendly=True, save_to_disk=True
    ):
        """
        Generate a newsletter from a DataFrame
        
        Args:
            df: DataFrame with news articles
            output_path: Where to save the HTML (None for in-memory only)
            preview_text: Text shown in email clients as preview
            column_mapping: Map of DataFrame columns to newsletter fields
            colors: Dictionary of colors for styling
            banner_input: Banner HTML content or file
            summary_html: HTML content for summary section
            image_html: HTML content for image section
            content_width: Width of newsletter in pixels
            mobile_friendly: Whether to include mobile responsive styles
            save_to_disk: Whether to save the generated HTML to disk (default: True)
            
        Returns:
            tuple: (newsletter_html, output_path)
        """
        # Default column mapping if none provided
        if column_mapping is None:
            column_mapping = {
                'theme': 'theme',
                'subheader': 'subheader',
                'article_title': 'Article_Title',
                'source': 'Source',
                'date': 'Date',
                'content': 'Content'
            }
        
        # Default colors if not provided
        if colors is None:
            colors = {
                'primary': '#0168b1',     # Blue (default)
                'secondary': '#333333',   # Dark gray
                'background': '#e6e6e6',  # Light gray
                'header_bg': '#0168b1',   # Blue (default)
                'footer_bg': '#000000',   # Black
                'highlight': '#0168b1'    # Blue (default)
            }
        
        # Process banner HTML
        custom_banner_html = None
        custom_banner_styles = None
        
        if banner_input:
            # Extract and resize the banner to match content width
            custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_input, content_width)
            
        # Create a temp output path if save_to_disk is True and no path is provided
        if save_to_disk and output_path is None:
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        # Validate and process the DataFrame
        df_processed = self._validate_dataframe(df, column_mapping)
        
        # Process the custom sections with theme/subheader organization
        custom_sections = self._process_sections(df_processed)
        
        # For backwards compatibility - transform custom sections to legacy format
        primary_sections = []
        for section in custom_sections:
            primary_sections.append({
                'name': section['name'],
                'company_news': section['company_news'],
                'competitor_news': section['competitor_news']
            })
        
        # Assemble all data for the template
        newsletter_data = {
            'preview_text': preview_text,
            'current_date': datetime.now().strftime('%d %B %Y'),
            'sections': primary_sections,  # For backward compatibility
            'custom_sections': custom_sections,  # New theme/subheader based sections
            'colors': colors
        }
        
        # Render the HTML with our data
        rendered_html = self.template.render(data=newsletter_data)
        
        # Inject custom banner
        rendered_html = inject_banner_into_newsletter(
            rendered_html, 
            custom_banner_html, 
            custom_banner_styles,
            content_width
        )
        
        # Add summary if provided
        if summary_html:
            rendered_html = apply_summary_at_position(rendered_html, summary_html, "after_banner")
        
        # Add image if provided
        if image_html:
            rendered_html = apply_image_content(rendered_html, image_html)
        
        # Update dimensions
        rendered_html = update_html_dimensions(rendered_html, content_width)
        
        # Handle mobile responsiveness
        if not mobile_friendly:
            rendered_html = rendered_html.replace('@media only screen and (max-width:480px)', '@media only screen and (max-width:1px)')
        
        # Write the final HTML to file only if save_to_disk is True
        if save_to_disk and output_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(rendered_html)
            
        return rendered_html, output_path