"""
Newsletter generation module for the Gravity app with dedicated Summary section,
enhanced to allow dynamic color changes for banner, dividers, and subheader highlights.
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
from utils.html_processing import apply_image_content

def apply_custom_colors(html_content, color_dict):
    """
    Replaces CSS color placeholders in the HTML content with user-chosen colors.
    We look for lines commented like: 
        background-color: #ffce00; /* banner-bg */

    Example color_dict:
        {
            'banner_bg': '#FFD700',
            'divider_color_1': '#123456',
            'divider_color_2': '#ABCDEF',
            'subheader_bg': '#666666'
        }

    Make sure your template's <style> block has lines like:
        background-color: #ffce00; /* banner-bg */
        background-color: #000000; /* divider-color-1 */
        background-color: #ffce00; /* divider-color-2 */
        background-color: #ffce00; /* subheader-bg */
    """
    import re

    updated_html = html_content

    # Build a list of (regex pattern, replacement) pairs:
    replacements = [
        # banner background
        (
            r'(background-color:\s*#[0-9A-Fa-f]{3,6};\s*/\*\s*banner-bg\s*\*/)',
            f'background-color: {color_dict["banner_bg"]}; /* banner-bg */'
        ),
        # divider color 1
        (
            r'(background-color:\s*#[0-9A-Fa-f]{3,6};\s*/\*\s*divider-color-1\s*\*/)',
            f'background-color: {color_dict["divider_color_1"]}; /* divider-color-1 */'
        ),
        # divider color 2
        (
            r'(background-color:\s*#[0-9A-Fa-f]{3,6};\s*/\*\s*divider-color-2\s*\*/)',
            f'background-color: {color_dict["divider_color_2"]}; /* divider-color-2 */'
        ),
        # subheader background
        (
            r'(background-color:\s*#[0-9A-Fa-f]{3,6};\s*/\*\s*subheader-bg\s*\*/)',
            f'background-color: {color_dict["subheader_bg"]}; /* subheader-bg */'
        ),
    ]

    for (pattern, replacement) in replacements:
        updated_html = re.sub(pattern, replacement, updated_html)

    return updated_html


class NewsletterGenerator:
    """
    Core newsletter generation functionality with an enhanced template
    that allows dynamic color changes for banner, dividers, and subheaders.
    """
    def __init__(self, template_path=None, template_content=None, template_type='default'):
        """
        Initialize with either a template path or direct template content
        
        Args:
            template_path: Path to HTML template file
            template_content: HTML template content as string
            template_type: Type of template to use ('default', 'blackrock', 'skywalker', etc.)
        """
        self.template_type = template_type
        
        # Determine the template path if not explicitly provided
        if template_path is None and template_type != 'default':
            if template_type == 'blackrock':
                template_path = 'templates/blackrock_template.html'
            elif template_type == 'skywalker':
                template_path = 'templates/skywalker_template.html'
            else:
                template_path = 'templates/newsletter_template.html'
                
        # Load template from file if it exists, or fallback
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                self.template_html = file.read()
        elif template_content:
            self.template_html = template_content
        else:
            template_path = 'templates/newsletter_template.html'
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as file:
                    self.template_html = file.read()
            else:
                raise ValueError("No template found. Provide template_path or template_content.")
        
        # Prepare the Jinja template
        self.template = Template(self.template_html)

    def _format_date(self, date_value):
        """Format date values consistently."""
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
        """Extract article data from a DataFrame row with proper validation."""
        return {
            'title': row.get('article_title', ''),
            'source': row.get('source', ''),
            'date': self._format_date(row.get('date')),
            'content': row.get('content', ''),
            'subheader': row.get('subheader', 'General'),
            'subsection': row.get('subsection', 'General')  # for legacy or fallback
        }

    def _process_sections(self, df_processed):
        """Process news sections using theme and subheader organization."""
        custom_sections = []
        
        if 'theme' in df_processed.columns:
            unique_themes = df_processed['theme'].unique()
        else:
            unique_themes = ['General Theme']
            
        for theme in unique_themes:
            theme_df = df_processed[df_processed['theme'] == theme]
            if theme_df.empty:
                continue
            
            custom_section = {
                'name': theme,
                'articles': [],
                'subsections': {},
                'company_news': [],
                'competitor_news': []
            }
            
            if 'subheader' in theme_df.columns:
                unique_subheaders = theme_df['subheader'].dropna().unique()
            else:
                unique_subheaders = ['General']
            
            for subheader in unique_subheaders:
                if pd.isna(subheader):
                    continue
                subheader_df = theme_df[theme_df['subheader'] == subheader]
                
                for _, row in subheader_df.iterrows():
                    if pd.notna(row.get('article_title')) and row.get('article_title') != 'No news updates this week':
                        article = self._process_article(row)
                        custom_section['articles'].append(article)
                        
                        if subheader not in custom_section['subsections']:
                            custom_section['subsections'][subheader] = []
                        custom_section['subsections'][subheader].append(article)

                        subheader_lower = str(subheader).lower()
                        if ('company' in subheader_lower or 'product' in subheader_lower or 
                            'industry' in subheader_lower or 'market' in subheader_lower):
                            custom_section['company_news'].append(article)
                        else:
                            custom_section['competitor_news'].append(article)
            
            if custom_section['articles']:
                custom_sections.append(custom_section)
        
        return custom_sections

    def _validate_dataframe(self, df, column_mapping):
        """Validate and preprocess DataFrame columns."""
        df_processed = df.copy()
        if column_mapping:
            col_map = {v: k for k, v in column_mapping.items() if v in df.columns}
            if col_map:
                df_processed = df_processed.rename(columns=col_map)
        
        # Map Company->theme, News_Type->subheader if they exist
        if 'Company' in df_processed.columns and 'theme' not in df_processed.columns:
            df_processed['theme'] = df_processed['Company']
        if 'News_Type' in df_processed.columns and 'subheader' not in df_processed.columns:
            df_processed['subheader'] = df_processed['News_Type']
        
        # Ensure columns exist
        required_cols = {
            'theme': 'General Theme',
            'subheader': 'General',
            'subsection': 'General',
            'article_title': '',
            'content': ''
        }
        for col, default_val in required_cols.items():
            if col not in df_processed.columns:
                df_processed[col] = default_val
        
        # Parse date column if present
        if 'date' in df_processed.columns:
            df_processed['date'] = df_processed['date'].apply(
                lambda x: pd.to_datetime(x, errors='coerce') if not pd.isna(x) else None
            )
        else:
            df_processed['date'] = datetime.now()
        
        return df_processed

    def generate_newsletter(
        self, 
        df,
        output_path=None,
        preview_text='Your newsletter preview text here', 
        column_mapping=None,
        colors=None,   # <--- we pass in user colors here
        banner_input=None,
        summary_html="",
        image_html="",
        content_width=800,
        mobile_friendly=True,
        save_to_disk=True,
        additional_data=None,
        template_type=None,
        skip_banner_injection=False  # NEW PARAMETER
    ):
        """
        Generate a newsletter from a DataFrame, with optional custom banner
        and dynamic color replacements.

        colors: a dict that can also include keys like 'banner_bg', 'divider_color_1', 'divider_color_2', 'subheader_bg'
                e.g. {
                   'banner_bg': '#FFD700',
                   'divider_color_1': '#000000',
                   'divider_color_2': '#ffce00',
                   'subheader_bg': '#ffce00',
                   ... // other color definitions
                }
        skip_banner_injection: if True, don't replace the banner in the template
        """
        # 1) Possibly switch template types
        if template_type and template_type != self.template_type:
            self.__init__(template_type=template_type)
        
        # 2) Default column mapping if none provided
        if column_mapping is None:
            column_mapping = {
                'theme': 'theme',
                'subheader': 'subheader',
                'article_title': 'Article_Title',
                'source': 'Source',
                'date': 'Date',
                'content': 'Content'
            }
        
        # 3) Default color dict
        if colors is None:
            colors = {
                'primary': '#0168b1',
                'secondary': '#333333',
                'background': '#e6e6e6',
                'header_bg': '#0168b1',
                'footer_bg': '#000000',
                'highlight': '#ffce00',
                # Add your custom placeholders so we don't break
                'banner_bg': '#ffce00',
                'divider_color_1': '#000000',
                'divider_color_2': '#ffce00',
                'subheader_bg': '#ffce00',
            }
        
        # 4) Handle built-in vs. custom banner
        custom_banner_html = None
        custom_banner_styles = None
        
        # Only process banner if skip_banner_injection is False
        if not skip_banner_injection:
            if banner_input and ('<table' in str(banner_input) or '<div' in str(banner_input)):
                # If banner_input is already raw HTML from get_modified_banner_html
                print("[DEBUG] `banner_input` is raw HTML; skipping extract.")
                custom_banner_html = str(banner_input)
            else:
                # Possibly a file or path
                if banner_input:
                    print("[DEBUG] Attempting to parse banner_input as a custom file.")
                    custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_input, content_width)
        else:
            print("[DEBUG] skip_banner_injection=True; Keeping original template banner.")
        
        # 5) Prepare output path if saving
        if save_to_disk and not output_path:
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            suffix = f"_{self.template_type}" if self.template_type != 'default' else ""
            output_path = os.path.join(
                temp_dir, 
                f"newsletter{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        
        # 6) Validate/preprocess DataFrame
        df_processed = self._validate_dataframe(df, column_mapping)
        custom_sections = self._process_sections(df_processed)
        
        primary_sections = []
        for section in custom_sections:
            primary_sections.append({
                'name': section['name'],
                'company_news': section['company_news'],
                'competitor_news': section['competitor_news']
            })
        
        # 7) Add summary content
        summary_content = ""
        if summary_html:
            summary_content = summary_html  # already HTML

        # 8) Build data context for the template
        newsletter_data = {
            'preview_text': preview_text,
            'current_date': datetime.now().strftime('%d %B %Y'),
            'sections': primary_sections,         # old format
            'custom_sections': custom_sections,   # new format
            'colors': colors,
            'content_width': content_width,
            'template_type': self.template_type,
            'summary_content': summary_content,
            'image_html': image_html,
            'tagline_title': 'The BLK Daily News',
            'tagline_description': (
                'is a firmwide newsletter delivering headlines about BlackRock, '
                'our business, and our industry — curated daily by Global Corp Comms.'
            ),
            'footer_text': 'Limited. Not for external distribution.',
            'subscription_url': '#',
            'news_site_url': '#',
            'news_site_text': 'blackrock.lonebuffalo.com',
        }
        
        if additional_data:
            newsletter_data.update(additional_data)
        
        # Template-specific additions
        if self.template_type == 'blackrock':
            newsletter_data['newsletter_title'] = 'BlackRock Daily News'
        elif self.template_type == 'skywalker':
            newsletter_data['newsletter_title'] = 'Skywalker Newsletter'
            newsletter_data['tagline_title'] = 'The Skywalker News'
            newsletter_data['tagline_description'] = (
                'delivers the latest updates from across the galaxy, curated weekly by the Jedi Council.'
            )
            newsletter_data['footer_text'] = 'For Jedi eyes only. Do not distribute to the dark side.'
        
        # 9) Render base template
        rendered_html = self.template.render(data=newsletter_data)
        
        # 10) Inject the banner (if we have one) - ONLY if skip_banner_injection is False
        if custom_banner_html and not skip_banner_injection:
            rendered_html = inject_banner_into_newsletter(
                rendered_html, 
                custom_banner_html, 
                custom_banner_styles,
                content_width
            )
        else:
            if skip_banner_injection:
                print("[DEBUG] Skipping banner injection to preserve original template.")
            else:
                print("[DEBUG] No custom banner HTML provided. Using default banner in template, if any.")
        
        # 11) Update dimensions
        rendered_html = update_html_dimensions(rendered_html, content_width)
        
        # 12) Dynamic color placeholders
        #     If you have user-specified 'banner_bg', 'divider_color_1', etc., apply them now:
        rendered_html = apply_custom_colors(rendered_html, colors)

        # 13) Mobile-friendly check
        if not mobile_friendly:
            # Force a minimal media query so it won't be truly mobile
            rendered_html = rendered_html.replace('@media only screen and (max-width:480px)', '@media only screen and (max-width:1px)')
        
        # 14) Optionally save to disk
        if save_to_disk and output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(rendered_html)
        
        # Return final HTML + path
        return rendered_html, output_path