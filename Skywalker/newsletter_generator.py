import pandas as pd
from datetime import datetime
import os
from jinja2 import Template

class NewsletterGenerator:
    def __init__(self, template_path='newsletter_template.html'):
        """
        Initialize the NewsletterGenerator with the path to the HTML template.
        
        Parameters:
        -----------
        template_path : str
            Path to the HTML template file
        """
        self.template_path = template_path
        # Read the template file
        with open(template_path, 'r', encoding='utf-8') as file:
            self.template_html = file.read()
    
    def generate_newsletter(self, df, output_path='generated_newsletter.html', preview_text='Your newsletter preview text here', 
                          column_mapping=None, colors=None, banner_path=None):
        """
        Generate a newsletter HTML from a pandas DataFrame.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing newsletter content with columns that can be mapped to:
            - section_name: The name of the section (e.g., "AirFirst")
            - news_type: "Company" or "Competitor & Customer"
            - article_title: Title of the article (None if no news)
            - source: Source name (None if no news)
            - date: Publication date (None if no news)
            - content: Article content (None if no news)
        
        output_path : str
            Path where the generated HTML will be saved
            
        preview_text : str
            Text to use as the email preview
            
        column_mapping : dict, optional
            Dictionary mapping the expected column names to the actual column names in the DataFrame.
            For example: {
                'section_name': 'Company',
                'news_type': 'News_Type',
                'article_title': 'Article_Title',
                'source': 'Source',
                'date': 'Date',
                'content': 'Content'
            }
            
        colors : dict, optional
            Dictionary containing color codes to customize the newsletter appearance.
            For example: {
                'primary': '#0168b1',  # Primary color (borders, headers)
                'secondary': '#333333',  # Secondary color (text)
                'background': '#e6e6e6',  # Page background color
                'header_bg': '#0168b1',  # Header background color
                'footer_bg': '#000000',  # Footer background color
                'highlight': '#0168b1'   # Text highlight/underline color
            }
            
        banner_path : str, optional
            Path to the HTML file containing the banner markup.
            If None, a default banner will be used.
        """
        # Apply column mapping if provided
        df_processed = df.copy()
        
        # Default column mapping if none provided
        if column_mapping is None:
            column_mapping = {
                'section_name': 'section_name',
                'news_type': 'news_type',
                'article_title': 'article_title',
                'source': 'source',
                'date': 'date',
                'content': 'content'
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
        
        # Load banner HTML from file if provided
        banner_html = ""
        if banner_path and os.path.exists(banner_path):
            with open(banner_path, 'r', encoding='utf-8') as file:
                banner_html = file.read()
                # Extract just the banner div from the HTML file if it contains full HTML document
                if "<body>" in banner_html and "</body>" in banner_html:
                    start_idx = banner_html.find("<body>") + len("<body>")
                    end_idx = banner_html.find("</body>")
                    banner_html = banner_html[start_idx:end_idx].strip()
        else:
            # Default banner if no file provided
            banner_html = """
            <div class="banner" style="width: 800px; height: 180px; background-color: #f2f2f2; display: flex; align-items: center; border-bottom: 2px solid #ccc;">
                <div class="title" style="font-family: Arial, sans-serif; font-size: 32px; color: #333; margin-left: 20px;">
                    Skywalker Newsletter
                </div>
            </div>
            """
            
        # Normalize column names
        col_map = {v: k for k, v in column_mapping.items() if v in df.columns}
        if col_map:
            df_processed = df_processed.rename(columns=col_map)
        
        # Process news_type values if they're in a different format
        if 'news_type' in df_processed.columns:
            df_processed['news_type'] = df_processed['news_type'].apply(
                lambda x: 'Company' if x in ['Company', 'Company News'] 
                else 'Competitor & Customer' if x in ['Competitor & Customer', 'Competitor & Customer News']
                else x
            )
        
        # Handle "No news updates this week" in article_title
        if 'article_title' in df_processed.columns:
            df_processed['article_title'] = df_processed['article_title'].apply(
                lambda x: None if x == 'No news updates this week' else x
            )
        
        # Convert date strings to datetime if needed
        if 'date' in df_processed.columns:
            def parse_date(date_val):
                if pd.isna(date_val):
                    return None
                if isinstance(date_val, str):
                    try:
                        return pd.to_datetime(date_val)
                    except:
                        return None
                return date_val
            
            df_processed['date'] = df_processed['date'].apply(parse_date)
        
        # Get unique sections
        sections = df_processed['section_name'].unique().tolist()
        
        # Process the data
        newsletter_data = {
            'preview_text': preview_text,
            'current_date': datetime.now().strftime('%d %B %Y'),
            'banner_html': banner_html,
            'sections': [],
            'colors': colors
        }
        
        # Process each section
        for section_name in sections:
            section_df = df_processed[df_processed['section_name'] == section_name]
            
            # Prepare section data
            section_data = {
                'name': section_name,
                'company_news': [],
                'competitor_news': []
            }
            
            # Process company news
            company_news = section_df[section_df['news_type'] == 'Company']
            if not company_news.empty and company_news['article_title'].notna().any():
                for _, row in company_news.iterrows():
                    if pd.notna(row.get('article_title')):
                        article = {
                            'title': row.get('article_title', ''),
                            'source': row.get('source', ''),
                            'date': row.get('date', '').strftime('%d %B %Y') if pd.notna(row.get('date')) else '',
                            'content': row.get('content', '')
                        }
                        section_data['company_news'].append(article)
            
            # Process competitor news
            competitor_news = section_df[section_df['news_type'] == 'Competitor & Customer']
            if not competitor_news.empty and competitor_news['article_title'].notna().any():
                for _, row in competitor_news.iterrows():
                    if pd.notna(row.get('article_title')):
                        article = {
                            'title': row.get('article_title', ''),
                            'source': row.get('source', ''),
                            'date': row.get('date', '').strftime('%d %B %Y') if pd.notna(row.get('date')) else '',
                            'content': row.get('content', '')
                        }
                        section_data['competitor_news'].append(article)
            
            newsletter_data['sections'].append(section_data)
        
        # Create a template
        template = Template(self.template_html)
        
        # Render the HTML with our data
        rendered_html = template.render(data=newsletter_data)
        
        # Save the generated HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        
        return rendered_html


# Example usage
if __name__ == "__main__":
    # Example with the dummy data format
    data = [
        # FakeCorp entries
        {
            "Company": "FakeCorp",
            "News_Type": "Company News",
            "Article_Title": "FakeCorp Launches Revolutionary Product",
            "Source": "Tech Insider",
            "Date": "01 March 2025",
            "Content": ("FakeCorp has unveiled a revolutionary product designed to disrupt the industry and "
                        "set new market standards in technology.")
        },
        {
            "Company": "FakeCorp",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "No news updates this week",
            "Source": None,
            "Date": None,
            "Content": None
        },
        # EcoTech entries
        {
            "Company": "EcoTech",
            "News_Type": "Company News",
            "Article_Title": "EcoTech Secures $2B in Funding",
            "Source": "Financial Times",
            "Date": "28 February 2025",
            "Content": ("EcoTech has secured $2 billion in funding to expand its renewable energy solutions and "
                        "enhance its global presence in sustainable technology.")
        },
        {
            "Company": "EcoTech",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "No news updates this week",
            "Source": None,
            "Date": None,
            "Content": None
        },
        # GreenWave entries
        {
            "Company": "GreenWave",
            "News_Type": "Company News",
            "Article_Title": "GreenWave Expands into European Markets",
            "Source": "Bloomberg",
            "Date": "27 February 2025",
            "Content": ("GreenWave has announced its expansion into several key European markets, aiming to boost "
                        "its sustainable technology portfolio.")
        },
        {
            "Company": "GreenWave",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "Major Partnership Announced with Global Firm",
            "Source": "Reuters",
            "Date": "27 February 2025",
            "Content": ("GreenWave has formed a major partnership with a global firm to accelerate the deployment "
                        "of sustainable technologies across multiple markets.")
        },
        # FutureTech entries
        {
            "Company": "FutureTech",
            "News_Type": "Company News",
            "Article_Title": "FutureTech Unveils AI-Powered Solutions",
            "Source": "Wired",
            "Date": "26 February 2025",
            "Content": ("FutureTech has introduced a new suite of AI-powered solutions designed to streamline operations "
                        "and improve customer experiences.")
        },
        {
            "Company": "FutureTech",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "Market Challenges Ahead, Analysts Warn",
            "Source": "Reuters",
            "Date": "26 February 2025",
            "Content": ("Analysts warn that rising market challenges and global competition could impact FutureTech's "
                        "growth prospects in the coming quarters.")
        },
        # Next set of companies with additional fake data
        {
            "Company": "Innova Solutions",
            "News_Type": "Company News",
            "Article_Title": "Innova Solutions Merges with TechDynamics",
            "Source": "Forbes",
            "Date": "02 March 2025",
            "Content": ("Innova Solutions has merged with TechDynamics in a move aimed at consolidating their positions "
                        "in the tech industry and fostering innovation.")
        },
        {
            "Company": "Innova Solutions",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "No news updates this week",
            "Source": None,
            "Date": None,
            "Content": None
        },
        {
            "Company": "Solaris Energy",
            "News_Type": "Company News",
            "Article_Title": "Solaris Energy Introduces New Solar Panels",
            "Source": "Energy Today",
            "Date": "01 March 2025",
            "Content": ("Solaris Energy has introduced a new range of solar panels that promise increased efficiency and "
                        "longer durability for residential and commercial installations.")
        },
        {
            "Company": "Solaris Energy",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "Industry Leaders Meet at Annual Summit",
            "Source": "CNBC",
            "Date": "28 February 2025",
            "Content": ("Industry leaders, including Solaris Energy executives, met at the annual summit to discuss new "
                        "trends and challenges in the renewable energy sector.")
        },
        {
            "Company": "CyberNetix",
            "News_Type": "Company News",
            "Article_Title": "CyberNetix Enhances Cybersecurity Platform",
            "Source": "ZDNet",
            "Date": "02 March 2025",
            "Content": ("CyberNetix has rolled out major enhancements to its cybersecurity platform, aimed at providing "
                        "better protection against emerging threats in the digital landscape.")
        },
        {
            "Company": "CyberNetix",
            "News_Type": "Competitor & Customer News",
            "Article_Title": "No news updates this week",
            "Source": None,
            "Date": None,
            "Content": None
        }
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Define column mapping
    column_mapping = {
        'section_name': 'Company',
        'news_type': 'News_Type',
        'article_title': 'Article_Title',
        'source': 'Source',
        'date': 'Date',
        'content': 'Content'
    }

    # Example 1: Default blue theme with blue banner
    generator = NewsletterGenerator('newsletter_template.html')
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path='blue_newsletter.html',
        preview_text='Blue Theme Newsletter - March 2025',
        column_mapping=column_mapping,
        banner_path='blue_banner.html'
    )
    print(f"Blue theme newsletter generated at: blue_newsletter.html")

    # Example 2: Green theme with green banner
    green_colors = {
        'primary': '#2C8B44',     # Green
        'secondary': '#333333',   # Dark gray
        'background': '#F0F7F0',  # Light green
        'header_bg': '#1A5D2B',   # Dark green
        'footer_bg': '#333333',   # Dark gray
        'highlight': '#2C8B44'    # Green
    }

    generator = NewsletterGenerator('newsletter_template.html')
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path='green_newsletter.html',
        preview_text='Green Theme Newsletter - March 2025',
        column_mapping=column_mapping,
        colors=green_colors,
        banner_path='green_banner.html'
    )
    print(f"Green theme newsletter generated at: green_newsletter.html")

    # Example 3: Purple theme with purple banner
    purple_colors = {
        'primary': '#673AB7',     # Purple
        'secondary': '#333333',   # Dark gray
        'background': '#F5F0FF',  # Light lavender
        'header_bg': '#4A148C',   # Dark purple
        'footer_bg': '#333333',   # Dark gray
        'highlight': '#9575CD'    # Light purple
    }

    generator = NewsletterGenerator('newsletter_template.html')
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path='purple_newsletter.html',
        preview_text='Purple Theme Newsletter - March 2025',
        column_mapping=column_mapping,
        colors=purple_colors,
        banner_path='purple_banner.html'
    )
    print(f"Purple theme newsletter generated at: purple_newsletter.html")

    # Example 4: Corporate theme with corporate banner
    corporate_colors = {
        'primary': '#D74B4B',      # Red
        'secondary': '#333333',    # Dark gray
        'background': '#F5F5F5',   # Light gray
        'header_bg': '#1D2951',    # Navy blue
        'footer_bg': '#1D2951',    # Navy blue
        'highlight': '#D74B4B'     # Red
    }

    generator = NewsletterGenerator('newsletter_template.html')
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path='corporate_newsletter.html',
        preview_text='Corporate Theme Newsletter - March 2025',
        column_mapping=column_mapping,
        colors=corporate_colors,
        banner_path='corporate_banner.html'
    )
    print(f"Corporate theme newsletter generated at: corporate_newsletter.html")