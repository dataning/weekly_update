import pandas as pd
from datetime import datetime
import os
import re
from jinja2 import Template

class NewsletterGenerator:
    def __init__(self, template_path=None, template_content=None):
        """
        Initialize the NewsletterGenerator with either a template path or direct template content.
        """
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                self.template_html = file.read()
        elif template_content:
            self.template_html = template_content
        else:
            raise ValueError("Either template_path or template_content must be provided")
        
        # Prepare the Jinja template once for reuse
        self.template = Template(self.template_html)
    
    def _format_date(self, date_value):
        """Format date values consistently across different input types"""
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
        """
        Process news sections directly using theme and subheader columns
        """
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
    
    def generate_newsletter_in_memory(self, df, preview_text='Your newsletter preview text here', 
                                     column_mapping=None, colors=None, banner_html=None):
        """
        Generate a newsletter HTML from a pandas DataFrame without writing to disk.
        """
        # Default column mapping if none provided
        if column_mapping is None:
            column_mapping = {
                'theme': 'theme',         # Direct use of theme column
                'subheader': 'subheader', # Direct use of subheader column
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
        
        # Use default banner if none provided
        if not banner_html:
            banner_html = """
            <div class="banner" style="width: 800px; height: 180px; background-color: #f2f2f2; display: flex; align-items: center; border-bottom: 2px solid #ccc;">
                <div class="title" style="font-family: Arial, sans-serif; font-size: 32px; color: #333; margin-left: 20px;">
                    Newsletter
                </div>
            </div>
            """
        
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
            'banner_html': banner_html,
            'sections': primary_sections,  # For backward compatibility
            'custom_sections': custom_sections,  # New theme/subheader based sections
            'colors': colors
        }
        
        # Render the HTML with our data
        rendered_html = self.template.render(data=newsletter_data)
        
        # Post-process the HTML to clean up any potential issues
        rendered_html = self._post_process_html(rendered_html)
        
        return rendered_html
    
    def _post_process_html(self, html):
        """Clean up the generated HTML for better email compatibility"""
        # Remove empty sections 
        html = re.sub(r'<div class="section">\s*<h2>[^<]+</h2>\s*<p>No articles to display.</p>\s*</div>', '', html)
        
        # Remove consecutive blank lines
        html = re.sub(r'\n{3,}', '\n\n', html)
        
        return html
    
    def generate_newsletter(self, df, output_path='generated_newsletter.html', preview_text='Your newsletter preview text here', 
                           column_mapping=None, colors=None, banner_path=None):
        """
        Generate a newsletter HTML from a pandas DataFrame and save to disk.
        """
        # Process banner HTML from file if provided
        banner_html = ""
        if banner_path and os.path.exists(banner_path):
            with open(banner_path, 'r', encoding='utf-8') as file:
                banner_html = file.read()
                # Extract just the banner div from the HTML file if it contains full HTML document
                if "<body>" in banner_html and "</body>" in banner_html:
                    start_idx = banner_html.find("<body>") + len("<body>")
                    end_idx = banner_html.find("</body>")
                    banner_html = banner_html[start_idx:end_idx].strip()
        
        # Generate the newsletter in memory
        rendered_html = self.generate_newsletter_in_memory(
            df, 
            preview_text=preview_text,
            column_mapping=column_mapping,
            colors=colors,
            banner_html=banner_html
        )
        
        # Save the generated HTML if output_path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
        
        return rendered_html