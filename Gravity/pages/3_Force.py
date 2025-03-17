import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import re
import os
import base64
import io
from PIL import Image
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import uuid
import streamlit.components.v1 as components

# Set page configuration as the very first Streamlit command
st.set_page_config(
    page_title="News Explorer & Newsletter Generator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enhance the appearance
st.markdown("""
<style>
    /* Gravity Branding Header Styles */
    .Gravity-header {
        display: flex;
        align-items: center;
        padding: 30px;
        background: #000000;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
        width: 100%;
        height: 160px;
    }
    
    .stars {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 40px 70px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 50px 160px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 90px 40px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 130px 80px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
            radial-gradient(2px 2px at 160px 120px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0));
    }
    
    .Gravity-icon {
        position: relative;
        width: 60px;
        height: 60px;
        margin-right: 20px;
    }
    
    .icon-circle {
        position: absolute;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%);
        box-shadow: 0 0 20px rgba(255, 235, 59, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .icon-silhouette {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 30px;
        height: 40px;
    }
    
    .Gravity-title {
        font-family: 'Segoe UI', Arial, sans-serif;
        position: relative;
        z-index: 2;
    }
    
    .brand-name {
        color: #ffffff !important;
        font-size: 48px;
        font-weight: 700;
        letter-spacing: 3px;
        margin: 0;
        text-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
    }
            
    .Gravity-brand {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    .tagline {
        color: #ffffff;
        font-size: 18px;
        font-weight: 400;
        margin: 5px 0 0 0;
        letter-spacing: 1px;
    }
    
    /* Light beam effect */
    .light-beam {
        position: absolute;
        width: 150px;
        height: 100%;
        background: linear-gradient(90deg, 
                                  rgba(255, 255, 255, 0) 0%, 
                                  rgba(255, 255, 255, 0.1) 50%, 
                                  rgba(255, 255, 255, 0) 100%);
        transform: skewX(-20deg);
        animation: beam 8s infinite;
        opacity: 0.7;
    }
    
    @keyframes beam {
        0% { left: -150px; }
        30% { left: 100%; }
        100% { left: 100%; }
    }
    
    /* Spaceman styling */
    .spaceman {
        position: absolute;
        height: 80px;
        z-index: 2;
        opacity: 0.9;
        /* Combine multiple animations with slower timing */
        animation: 
            drift-x 40s linear infinite alternate, 
            drift-y 35s ease-in-out infinite alternate,
            spin 60s linear infinite;
        /* Start the spaceman in the middle-right area */
        top: 40px;
        right: 100px;
    }
    
    /* Horizontal drifting across the banner */
    @keyframes drift-x {
        0% { right: 30%; }
        20% { right: 80%; }
        40% { right: 20%; }
        60% { right: 65%; }
        80% { right: 40%; }
        100% { right: 70%; }
    }
    
    /* Vertical drifting */
    @keyframes drift-y {
        0% { top: 20px; }
        15% { top: 70px; }
        30% { top: 40px; }
        45% { top: 90px; }
        60% { top: 30px; }
        75% { top: 60px; }
        100% { top: 50px; }
    }
    
    /* Full rotation, including upside down */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        20% { transform: rotate(180deg); }
        40% { transform: rotate(90deg); }
        60% { transform: rotate(360deg); }
        80% { transform: rotate(270deg); }
        100% { transform: rotate(720deg); }
    }

    /* Original styles */
    .main-header {
        font-size: 42px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: 400;
        color: #64748B;
        margin-top: 0px;
    }
    .feature-card {
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 20px;
        background-color: white;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }
    .feature-icon {
        font-size: 36px;
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 22px;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 10px;
    }
    .feature-description {
        font-size: 16px;
        color: #4B5563;
        margin-bottom: 15px;
    }
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
    .page-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .stats-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stats-number {
        font-size: 28px;
        font-weight: 700;
        color: #1E3A8A;
    }
    .stats-label {
        font-size: 16px;
        color: #64748B;
    }
    .testimonial {
        font-style: italic;
        color: #4B5563;
        padding: 15px;
        border-left: 4px solid #1E3A8A;
        background-color: #F8FAFC;
        margin: 20px 0;
    }

    .nav-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.5rem 1rem;
        background-color: #f0f2f6;
        color: #262730;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 1rem;
        border: none;
        cursor: pointer;
    }
    .nav-button:hover {
        background-color: #e0e2e6;
    }
    
    /* Add CSS to make preview more responsive */
    .preview-container iframe {
        width: 100%;
        border: none;
        transition: all 0.3s ease;
    }
    
    /* Fix for components with on_change */
    div[data-testid="stForm"] {
        background-color: transparent;
        border: none;
        padding: 0;
    }
    
    /* Style for summary section */
    .summary-section {
        background-color: #f8f9fa;
        border-left: 3px solid #0168b1;
        padding: 10px 15px;
        margin: 10px 0;
    }
    
    /* Style for image preview */
    .image-preview {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Style for email form */
    .email-form {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
    }
    
    /* Make tab content fill available space */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    
    /* Style for the tab indicator */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0168b1 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="Gravity-header">
  <div class="stars"></div>
  <div class="light-beam"></div>
  
  <!-- Floating spaceman icon -->
  <div class="spaceman">
    <svg width="100" height="120" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
      <!-- Helmet -->
      <circle cx="50" cy="20" r="15" fill="white" opacity="0.9"/>
      <!-- Visor -->
      <circle cx="50" cy="20" r="10" fill="#0088ff" opacity="0.7"/>
      <!-- Body -->
      <rect x="35" y="30" width="30" height="45" rx="8" fill="white" opacity="0.8"/>
      <!-- Arms -->
      <rect x="20" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
      <rect x="60" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
      <!-- Legs -->
      <rect x="38" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
      <rect x="52" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
    </svg>
  </div>
  
  <div class="Gravity-icon">
    <div class="icon-circle">
      <svg class="icon-silhouette" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L9 9H3L8 14L6 21L12 17L18 21L16 14L21 9H15L12 2Z" fill="white"/>
      </svg>
    </div>
  </div>
  
  <div class="Gravity-title">
    <h1 class="brand-name">Gravity</h1>
    <p class="tagline">To the Stars We Reach, With the News We Lead</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state for navigation and data persistence
if "tagged_news_df" not in st.session_state:
    st.session_state.tagged_news_df = None
if "filtered_news_df" not in st.session_state:
    st.session_state.filtered_news_df = None
if "selected_news_df" not in st.session_state:
    st.session_state.selected_news_df = None
if "news_df" not in st.session_state:
    st.session_state.news_df = None
if "last_config" not in st.session_state:
    st.session_state.last_config = {
        'color_theme': None,
        'banner_selection': None,
        'content_width': None,
        'mobile_friendly': None,
        'preview_text': None,
        'summary_html': None,
        'image_html': None,
        'banner_text': {}
    }
if "needs_update" not in st.session_state:
    st.session_state.needs_update = True
if "newsletter_error" not in st.session_state:
    st.session_state.newsletter_error = False
if "banner_text" not in st.session_state:
    st.session_state.banner_text = {
        'corporate_top': 'BlackRock',
        'corporate_middle': 'NEWSLETTER',
        'gips_brand': 'BlackRock',
        'gips_subtitle': 'GIPS Infrastructure',
        'gips_headline': 'Weekly Newsletter',
        'modern_brand': 'BlackRock News',
        'modern_date': datetime.now().strftime('%B %d, %Y'),
        'modern_tagline': 'Your weekly update on market insights',
        'gradient_title': 'Market Insights',
        'gradient_subtitle': 'Weekly Newsletter',
        'gradient_edition': f'Edition #{datetime.now().strftime("%W")} | {datetime.now().strftime("%B %Y")}'
    }
if "preview_updating" not in st.session_state:
    st.session_state.preview_updating = False
if "summary_html" not in st.session_state:
    st.session_state.summary_html = ""
if "image_html" not in st.session_state:
    st.session_state.image_html = ""
if "email_history" not in st.session_state:
    st.session_state.email_history = []
    
# Create necessary directories
TEMP_DIR = "temp"
BANNERS_DIR = "banners"

for directory in [TEMP_DIR, BANNERS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Import the Opoint news function
# This is a placeholder that would be replaced with actual implementation
try:
    from opoint_module import get_all_companies_news_sync
except ImportError:
    # If the import fails, we'll define a function to show a warning
    def get_all_companies_news_sync(*args, **kwargs):
        st.error("❌ Failed to import get_all_companies_news_sync. Make sure the opoint module is accessible.")
        return pd.DataFrame()

# Import banner utilities - Placeholder for actual implementation
try:
    from banner_templates import (
        ensure_banner_files,
        get_modified_banner_html,
        extract_banner_from_html,
        inject_banner_into_newsletter,
        update_html_dimensions,
        COLOR_BANNER_TEMPLATES,
        BANNER_FILENAMES,
        DEFAULT_BANNER_TEXTS
    )
except ImportError:
    # Placeholder definitions if the banner_templates module isn't available
    def ensure_banner_files(dir_path):
        pass
    
    def get_modified_banner_html(banner_type, text_values):
        return f"<div style='background-color:#0168b1; color:white; padding:20px; text-align:center;'><h1>{text_values.get('corporate_middle', 'NEWSLETTER')}</h1></div>"
    
    def extract_banner_from_html(html_content, width=800):
        return f"<div style='background-color:#0168b1; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>", None
    
    def inject_banner_into_newsletter(newsletter_html, banner_html, banner_styles, width=800):
        return newsletter_html
    
    def update_html_dimensions(html_content, width=800):
        return html_content
    
    COLOR_BANNER_TEMPLATES = {
        "blue": "<div style='background-color:#0168b1; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "green": "<div style='background-color:#2C8B44; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "red": "<div style='background-color:#D32F2F; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "purple": "<div style='background-color:#673AB7; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "corporate": "<div style='background-color:#1D2951; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "teal": "<div style='background-color:#00897B; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "amber": "<div style='background-color:#FFB300; color:black; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "indigo": "<div style='background-color:#3949AB; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "cyan": "<div style='background-color:#00ACC1; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>",
        "brown": "<div style='background-color:#795548; color:white; padding:20px; text-align:center;'><h1>NEWSLETTER</h1></div>"
    }
    
    BANNER_FILENAMES = {
        "BlackRock Corporate (Default)": "corpcomm_banner.html",
        "GIPS Infrastructure": "gips_banner.html",
        "Modern Design": "modern_banner.html",
        "Gradient Style": "gradient_banner.html"
    }
    
    DEFAULT_BANNER_TEXTS = {
        'corporate_top': 'BlackRock',
        'corporate_middle': 'NEWSLETTER',
        'gips_brand': 'BlackRock',
        'gips_subtitle': 'GIPS Infrastructure',
        'gips_headline': 'Weekly Newsletter',
        'modern_brand': 'BlackRock News',
        'modern_date': datetime.now().strftime('%B %d, %Y'),
        'modern_tagline': 'Your weekly update on market insights',
        'gradient_title': 'Market Insights',
        'gradient_subtitle': 'Weekly Newsletter',
        'gradient_edition': f'Edition #{datetime.now().strftime("%W")} | {datetime.now().strftime("%B %Y")}'
    }

# Try importing the newsletter generator module
try:
    from newsletter_generator import NewsletterGenerator
except ImportError:
    # Create a minimal implementation if the module isn't available
    class NewsletterGenerator:
        def __init__(self, template_path):
            self.template_path = template_path
            
        def generate_newsletter(self, df, output_path, preview_text, column_mapping, colors, banner_path):
            # Simple placeholder implementation
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Newsletter</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                </style>
            </head>
            <body>
                <div style="background-color:{colors['primary']}; color:white; padding:20px; text-align:center;">
                    <h1>Newsletter</h1>
                </div>
                <div style="padding:20px;">
                    <h2>Articles</h2>
                    <ul>
            """
            
            for _, row in df.iterrows():
                title = row.get('Article_Title', 'Untitled')
                source = row.get('Source', 'Unknown Source')
                html += f"<li><strong>{title}</strong> - {source}</li>\n"
                
            html += """
                    </ul>
                </div>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
                
            return html

# Email Sender class for sending HTML emails
class EmailSender:
    """
    Class for sending HTML-templated emails via BlackRock's internal mail server.
    """
    
    def __init__(self, internal_mail_server='mailhub.blackrock.com'):
        """
        Initialize email sender with BlackRock's internal mail server
        """
        self.mail_server = internal_mail_server
        
    def _html_to_text(self, html):
        """
        Simple converter from HTML to plain text.
        """
        # Remove HTML tags
        text = re.sub(r'<.*?>', ' ', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Replace common HTML entities
        replacements = {
            '&nbsp;': ' ', 
            '&lt;': '<', 
            '&gt;': '>', 
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'",
            '&ndash;': '-',
            '&mdash;': '--'
        }
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
            
        return text.strip()
    
    def send_html_email(self, from_email, to_emails, subject, html_content, cc_emails=None, bcc_emails=None):
        """
        Send an HTML email via BlackRock's internal mail server
        
        Args:
            from_email (str): Sender's email address
            to_emails (str or list): Recipient email(s) - can be a string or list
            subject (str): Email subject
            html_content (str): HTML content as a string
            cc_emails (str or list): CC recipients - can be a string or list
            bcc_emails (str or list): BCC recipients - can be a string or list
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Convert email parameters to lists if they're strings
        if isinstance(to_emails, str):
            to_emails = [email.strip() for email in to_emails.split(',') if email.strip()]
            
        if cc_emails and isinstance(cc_emails, str):
            cc_emails = [email.strip() for email in cc_emails.split(',') if email.strip()]
            
        if bcc_emails and isinstance(bcc_emails, str):
            bcc_emails = [email.strip() for email in bcc_emails.split(',') if email.strip()]
            
        # Create message container
        msg_root = MIMEMultipart('related')
        msg_root['Subject'] = subject
        msg_root['From'] = from_email
        msg_root['To'] = ", ".join(to_emails)
        
        # Add CC if provided
        if cc_emails:
            msg_root['Cc'] = ", ".join(cc_emails)
            # Add CC emails to recipient list for sending
            to_emails.extend(cc_emails)
            
        # Add BCC if provided (only to recipient list, not headers)
        if bcc_emails:
            to_emails.extend(bcc_emails)
            
        msg_root.preamble = 'This is a multi-part message in MIME format.'
        
        # Create alternative part for HTML/plain text
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        
        try:
            # Create plain text version
            text_content = self._html_to_text(html_content)
            
            # Attach text part
            msg_text_plain = MIMEText(text_content, 'plain')
            msg_alternative.attach(msg_text_plain)
            
            # Attach HTML part
            msg_text_html = MIMEText(html_content, 'html')
            msg_alternative.attach(msg_text_html)
            
        except Exception as e:
            logging.error(f"Error processing HTML content: {e}")
            return False, f"Error processing HTML content: {e}"
        
        # Send the email
        try:
            with smtplib.SMTP(self.mail_server) as server:
                server.send_message(msg_root)
                recipients_count = len(to_emails)
                logging.info(f"Email sent successfully to {recipients_count} recipient(s)")
                return True, f"Email sent successfully to {recipients_count} recipient(s)"
                
        except Exception as e:
            error_msg = f"Failed to send email. Error: {e}"
            logging.error(error_msg)
            return False, error_msg

# Utility Functions
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

def trigger_update():
    """Trigger update for newsletter preview"""
    st.session_state.needs_update = True
    st.session_state.newsletter_error = False
    
    # Regenerate newsletter if we have enough data
    if ('column_mapping' in st.session_state and 
        'selected_news_df' in st.session_state and 
        st.session_state.selected_news_df is not None):
        
        regenerate_newsletter(
            st.session_state.selected_news_df,
            st.session_state.column_mapping,
            st.session_state.colors,
            st.session_state.preview_text,
            st.session_state.content_width,
            st.session_state.mobile_friendly,
            st.session_state.banner_selection,
            st.session_state.banner_html_file,
            st.session_state.default_banner,
            force=True
        )

# Find this function in your code (around line 450)
def create_column_mapping_interface(df, key_prefix=""):
    """Create column mapping interface that works with existing columns"""
    columns = list(df.columns)
    
    # Default to theme/Company for main categories
    theme_col_default = None
    if 'Theme' in columns:
        theme_col_default = columns.index('Theme')
    elif 'theme' in columns:
        theme_col_default = columns.index('theme')
    elif 'Company' in columns:
        theme_col_default = columns.index('Company')
    else:
        theme_col_default = 0
        
    # Default to subheader/News_Type for subcategories
    subheader_col_default = None
    if 'Subheader' in columns:
        subheader_col_default = columns.index('Subheader')
    elif 'subheader' in columns:
        subheader_col_default = columns.index('subheader')
    elif 'News_Type' in columns:
        subheader_col_default = columns.index('News_Type')
    else:
        subheader_col_default = 0
    
    # Create unique keys using the key_prefix parameter
    theme_key = f"{key_prefix}theme_col_selectbox"
    subheader_key = f"{key_prefix}subheader_col_selectbox"
    
    # Allow user to select which columns to use, with appropriate defaults
    theme_col = st.selectbox(
        "Theme Column", 
        options=columns, 
        index=theme_col_default,
        on_change=trigger_update,
        key=theme_key  # Use the unique key
    )
    
    subheader_col = st.selectbox(
        "Subheader Column", 
        options=columns, 
        index=subheader_col_default,
        on_change=trigger_update,
        key=subheader_key  # Use the unique key
    )
    
    # Create mapping without modifying the dataframe
    column_mapping = {
        'theme': theme_col,
        'subheader': subheader_col,
        'article_title': 'Article_Title' if 'Article_Title' in columns else ('header_text' if 'header_text' in columns else columns[0]),
        'source': 'Source' if 'Source' in columns else ('first_source_name' if 'first_source_name' in columns else columns[0]),
        'date': 'Date' if 'Date' in columns else ('local_time_text' if 'local_time_text' in columns else columns[0]),
        'content': 'Content' if 'Content' in columns else ('summary_text' if 'summary_text' in columns else columns[0])
    }
    
    return column_mapping

def apply_summary_at_position(html_content, summary_html, position="after_banner"):
    """
    Apply the summary at a specific position in the newsletter.
    Works entirely in memory - no file operations.
    """
    if not summary_html or not html_content:
        return html_content
    
    # First priority: Always look for the Please submit any feedback section
    feedback_container_patterns = [
        r'(<div[^>]*>\s*Please submit any feedback:.*?<\/div>)',  # Standard pattern
        r'(<div[^>]*>\s*Please submit any feedback\s*:.*?<\/div>)',  # With spacing
        r'(<div[^>]*>\s*Additional\s+Information:.*?<\/div>)',  # With word spacing
        r'(<div[^>]*class=["\']footer-info["\'][^>]*>.*?Please submit any feedback.*?<\/div>)',  # With class
        r'(<tr[^>]*>\s*<td[^>]*>\s*Please submit any feedback:.*?<\/td>\s*<\/tr>)',  # Table-based footer
    ]
    
    # Try each pattern to find the Please submit any feedback section
    for pattern in feedback_container_patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            container = match.group(1)
            text_start = re.search(r'(Please submit any feedback)', container, re.IGNORECASE)
            if text_start:
                text_pos = text_start.start(1)
                new_container = container[:text_pos] + f"{summary_html} " + container[text_pos:]
                return html_content.replace(container, new_container)
            else:
                summary_div = f'{summary_html} '
                new_container = container.replace('>', '>' + summary_div, 1)
                return html_content.replace(container, new_container)
    
    # Simpler patterns if no match
    simpler_patterns = [
        r'(Please submit any feedback)',  # Just the text
        r'(Additional\s+Information:)',   # Just the section heading
    ]
    
    for pattern in simpler_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            text = match.group(1)
            summary_with_spacing = f'{summary_html} {text}'
            return html_content.replace(text, summary_with_spacing)
    
    # Position-based logic if no patterns match
    if position == "top" or position == "Top of newsletter":
        body_match = re.search(r'<body.*?>', html_content)
        if body_match:
            body_tag = body_match.group(0)
            return html_content.replace(
                body_tag,
                f"{body_tag}\n<div class='newsletter-summary'>{summary_html}</div>"
            )
    
    elif position == "after_banner" or position == "After banner":
        banner_patterns = [
            r'<!-- Custom Banner -->.*?</table>',  # After custom banner
            r'<img[^>]*Header\.jpg[^>]*>',         # After header image
            r'<div class="banner">.*?</div>'        # After banner div
        ]
        
        for pattern in banner_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                insertion_point = match.group(0)
                return html_content.replace(
                    insertion_point,
                    f"{insertion_point}\n<div class='newsletter-summary'>{summary_html}</div>"
                )
    
    elif position == "before_articles" or position == "Before articles":
        article_patterns = [
            r'<div class="articles-section">',     # Articles section
            r'<table[^>]*class="article-table"',   # Article table
            r'<h2[^>]*>Latest News</h2>'           # News heading
        ]
        
        for pattern in article_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                insertion_point = match.group(0)
                return html_content.replace(
                    insertion_point,
                    f"<div class='newsletter-summary'>{summary_html}</div>\n{insertion_point}"
                )
    
    # Fallback - add after BANNER_INSERTION_POINT marker
    banner_marker = "<!-- BANNER_INSERTION_POINT -->"
    if banner_marker in html_content:
        parts = html_content.split(banner_marker, 1)
        if len(parts) == 2:
            table_end_idx = parts[1].find("</table>")
            if table_end_idx > -1:
                insertion_point = table_end_idx + 8  # Length of "</table>"
                modified_html = parts[0] + banner_marker + parts[1][:insertion_point] + f"\n\n<!-- SUMMARY START -->\n{summary_html}\n<!-- SUMMARY END -->\n\n" + parts[1][insertion_point:]
                return modified_html
    
    # Ultimate fallback: append to beginning of HTML
    return f"<!-- SUMMARY START -->\n{summary_html}\n<!-- SUMMARY END -->\n\n{html_content}"

def apply_image_content(html_content, image_html):
    """
    Apply the image and caption content below the summary section.
    """
    if not image_html or not html_content:
        return html_content
    
    # First approach: Look for the Weekly Summary heading and its container div
    weekly_summary_pattern = r'<h3[^>]*>Weekly Summary</h3>.*?</div>'
    match = re.search(weekly_summary_pattern, html_content, re.DOTALL)
    if match:
        # Insert the image right after the summary div
        summary_section = match.group(0)
        return html_content.replace(
            summary_section,
            f"{summary_section}\n{image_html}"
        )
    
    # Second approach: Try using BeautifulSoup for more reliable HTML parsing
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        summary_heading = soup.find('h3', string='Weekly Summary')
        if summary_heading:
            # Find the parent div containing the summary
            summary_div = summary_heading.find_parent('div')
            if summary_div:
                # Create a new tag from the image HTML
                img_soup = BeautifulSoup(image_html, 'html.parser')
                # Insert the image content after the summary div
                summary_div.insert_after(img_soup)
                return str(soup)
    except Exception as e:
        # Continue with fallback approaches if BeautifulSoup fails
        pass
    
    # Look for newsletter-summary class
    summary_class = 'newsletter-summary'
    if summary_class in html_content:
        pattern = f'<div class=[\'"]?{summary_class}[\'"]?.*?</div>'
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            insertion_point = match.group(0)
            return html_content.replace(
                insertion_point,
                f"{insertion_point}\n{image_html}"
            )
    
    # Try feedback section
    feedback_patterns = [
        r'(<div[^>]*>\s*Please submit any feedback:.*?<\/div>)',
        r'(<div[^>]*>\s*Please submit any feedback\s*:.*?<\/div>)'
    ]
    
    for pattern in feedback_patterns:
        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            container = match.group(1)
            return html_content.replace(
                container,
                f"{image_html}\n{container}"
            )
    
    # Try after banner
    banner_patterns = [
        r'<!-- Custom Banner -->.*?</table>',
        r'<img[^>]*Header\.jpg[^>]*>',
        r'<div class="banner">.*?</div>'
    ]
    
    for pattern in banner_patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            insertion_point = match.group(0)
            return html_content.replace(
                insertion_point,
                f"{insertion_point}\n{image_html}"
            )
    
    # Fallback: add at beginning of body
    body_match = re.search(r'<body.*?>', html_content)
    if body_match:
        body_tag = body_match.group(0)
        return html_content.replace(
            body_tag,
            f"{body_tag}\n{image_html}"
        )
    
    return html_content

def generate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_input=None, banner_type="blue", summary_html="", image_html=""):
    """Generate a newsletter with all content including summary and images."""
    generator = NewsletterGenerator('newsletter_template.html')
    output_path = os.path.join(TEMP_DIR, f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # Process banner HTML
    custom_banner_html = None
    custom_banner_styles = None
    
    if banner_input:
        # Extract and resize the banner to match content width
        custom_banner_html, custom_banner_styles = extract_banner_from_html(banner_input, content_width)
        
    if not custom_banner_html:
        custom_banner_html = COLOR_BANNER_TEMPLATES.get(banner_type, COLOR_BANNER_TEMPLATES["blue"])
        custom_banner_html = re.sub(r'width: 800px', f'width: {content_width}px', custom_banner_html)
    
    # Create temporary banner file
    banner_file_path = os.path.join(TEMP_DIR, f"temp_banner_{banner_type}.html")
    with open(banner_file_path, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
 <style>
/* Banner styles */
 </style>
</head>
<body>
<!-- This is a placeholder banner that will be replaced -->
</body>
</html>""")
    
    # Generate the newsletter
    newsletter_html = generator.generate_newsletter(
        df, 
        output_path=output_path,
        preview_text=preview_text,
        column_mapping=column_mapping,
        colors=colors,
        banner_path=banner_file_path
    )
    
    # Read the generated newsletter
    with open(output_path, 'r', encoding='utf-8') as file:
        newsletter_html = file.read()
    
    # Inject custom banner
    newsletter_html = inject_banner_into_newsletter(
        newsletter_html, 
        custom_banner_html, 
        custom_banner_styles,
        content_width
    )
    
    # Add summary if provided
    if summary_html:
        newsletter_html = apply_summary_at_position(newsletter_html, summary_html, "after_banner")
    
    # Add image if provided
    if image_html:
        newsletter_html = apply_image_content(newsletter_html, image_html)
    
    # Update dimensions
    newsletter_html = update_html_dimensions(newsletter_html, content_width)
    
    # Handle mobile responsiveness
    if not mobile_friendly:
        newsletter_html = newsletter_html.replace('@media only screen and (max-width:480px)', '@media only screen and (max-width:1px)')
    
    # Write the final HTML to file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(newsletter_html)
    
    # Clean up temporary banner file
    try:
        os.remove(banner_file_path)
    except:
        pass
        
    return newsletter_html, output_path

def regenerate_newsletter(df, column_mapping, colors, preview_text, content_width, mobile_friendly, banner_selection, banner_html_file, default_banner, force=False):
    """
    Regenerate the newsletter based on current configuration
    
    Parameters:
    - force: If True, will regenerate even if needs_update is False
    
    Returns:
    - success: Boolean indicating if generation was successful
    """
    if not (st.session_state.needs_update or force) or st.session_state.preview_updating:
        return True

    # Set flag to prevent concurrent updates
    st.session_state.preview_updating = True
    
    try:
        summary_html = st.session_state.get('summary_html', "")
        image_html = st.session_state.get('image_html', "")
        
        # Handle different banner types
        if banner_selection == "Upload Custom HTML Banner" and banner_html_file:
            banner_input = banner_html_file
        elif banner_selection in BANNER_FILENAMES:
            # Use the modified HTML directly as HTML content, not as a file path
            banner_input = get_modified_banner_html(banner_selection, st.session_state.banner_text)
        else:
            # Default case
            banner_path = os.path.join(BANNERS_DIR, "corpcomm_banner.html")
            banner_input = banner_path
        
        newsletter_html, output_path = generate_newsletter(
            df,
            column_mapping,
            colors,
            preview_text,
            content_width,
            mobile_friendly,
            banner_input,
            default_banner,
            summary_html,
            image_html
        )
        st.session_state.newsletter_html = newsletter_html
        st.session_state.output_path = output_path
        st.session_state.needs_update = False
        st.session_state.newsletter_error = False
        
        # Reset the updating flag
        st.session_state.preview_updating = False
        return True
        
    except Exception as e:
        st.session_state.newsletter_error = True
        st.session_state.preview_updating = False
        st.error(f"Error generating newsletter: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

def generate_prompt(df, selected_indices):
    """
    Generate a prompt for summarization based on selected articles.
    """
    if not selected_indices or len(selected_indices) == 0:
        return ""
    
    prompt = """You are a senior news editor with 10+ years of experience distilling multiple news stories into concise briefings. Summarize the following table of news headlines, summaries, outlets, and themes in EXACTLY 3 paragraphs, no more and no less:

The first paragraph should provide an overview of the main theme or trend connecting most of the news stories in the table.
The second paragraph should highlight the most significant or impactful stories, including key details like company names and core developments.
The third paragraph should identify any secondary themes or patterns across multiple stories and note any outliers or unique stories that are still noteworthy.

Use professional journalistic language and include the most relevant details from the original sources. Focus on synthesizing information rather than simply listing stories. Maintain appropriate attribution to news outlets when necessary.

"""
    # Create a formatted table of the selected articles
    prompt += "| Title | Company | Source | Date | Content |\n"
    prompt += "| ----- | ------- | ------ | ---- | ------- |\n"
    
    # Get selected rows using boolean indexing for safety
    selected_rows = df.loc[selected_indices]
    
    for _, row in selected_rows.iterrows():
        # Safely handle values, converting to string and handling NaN/None
        def safe_value(value, default=''):
            import pandas as pd
            if pd.isna(value) or value is None:
                return default
            return str(value).replace('|', '-')
        
        # Check for various column names to be flexible with different datasets
        # Title column variations
        title = ""
        for title_col in ['Article_Title', 'header_text', 'Title', 'Headline']:
            if title_col in row and not pd.isna(row.get(title_col)):
                title = safe_value(row.get(title_col))
                break
                
        # If no title found from known columns, use first text column as fallback
        if not title:
            for col in row.index:
                if isinstance(row[col], str) and col != 'selected':
                    title = safe_value(row[col])
                    break
        
        # Company column variations
        company = ""
        for company_col in ['Company', 'search_term', 'Theme']:
            if company_col in row and not pd.isna(row.get(company_col)):
                company = safe_value(row.get(company_col))
                break
        
        # Source column variations
        source = ""
        for source_col in ['Source', 'first_source_name', 'Publisher']:
            if source_col in row and not pd.isna(row.get(source_col)):
                source = safe_value(row.get(source_col))
                break
        
        # Date column variations
        date = ""
        for date_col in ['Date', 'local_time_text', 'Publication_Date']:
            if date_col in row and not pd.isna(row.get(date_col)):
                date = safe_value(row.get(date_col))
                break
        
        # Content column variations
        content = ""
        for content_col in ['Content', 'summary_text', 'body_text', 'Summary']:
            if content_col in row and not pd.isna(row.get(content_col)):
                content = safe_value(row.get(content_col))
                break
        
        # Truncate content for table readability
        if content and len(content) > 100:
            content = content[:97] + "..."
        
        prompt += f"| {title} | {company} | {source} | {date} | {content} |\n"
    
    return prompt

# TAB IMPLEMENTATIONS

def news_search_page():
    st.title("🔍 Company News Search")
    st.write("Search for latest news about companies using the Opoint API")
    
    # Add button to go to analysis page if we have filtered data
    if ("filtered_news_df" in st.session_state and 
        st.session_state.filtered_news_df is not None and 
        not st.session_state.filtered_news_df.empty):
        # Check if any rows are selected
        selected_rows = st.session_state.filtered_news_df[st.session_state.filtered_news_df['selected'] == True]
        if not selected_rows.empty:
            # Use a completely unique key with timestamp
            button_key = f"goto_tagging_btn_{int(time.time() * 1000)}"
            if st.button("→ Go to News Tagging", type="primary", key=button_key):
                # Filter the dataframe to only include selected rows
                st.session_state.selected_news_df = selected_rows.copy()
                # Reset 'selected' column in the analysis tab to allow re-selection
                st.session_state.selected_news_df['selected'] = False
                # Store in tagged_news_df for the newsletter tab
                st.session_state.tagged_news_df = st.session_state.selected_news_df.copy()
                # Update the navigation choice and rerun
                st.session_state.main_navigation = "News Tagging"
                st.rerun()
        else:
            st.warning("Please select at least one article to tag by checking the 'Select' column")
    
    with st.sidebar:
        st.header("Search Parameters")
        
        # Companies input
        st.subheader("Companies")
        default_companies = ["BlackRock", "Tesla", "Microsoft", "Apple"]
        companies_text = st.text_area(
            "Enter company names (one per line):",
            value="\n".join(default_companies),
            height=150,
            key="companies_text_area"
        )
        companies = [c.strip() for c in companies_text.split("\n") if c.strip()]
        
        # Time range
        st.subheader("Time Range")
        days_back_options = [1, 2, 3, 5, 7, 14, 30]
        days_back_select = st.select_slider(
            "Days to look back:",
            options=days_back_options,
            value=3,
            key="days_back_slider"
        )
        # Convert days to hours for the API
        hours_back = days_back_select * 24
        
        # Advanced options in an expander
        with st.expander("Advanced Options"):
            initial_limit = st.number_input(
                "Initial articles limit per company:",
                min_value=10,
                max_value=1000,
                value=500,
                step=10,
                key="initial_limit_input"
            )
            
            use_proxy = st.checkbox("Use Proxy", value=False, key="use_proxy_checkbox")
            
            if use_proxy:
                st.info("Using proxy: http://webproxy.blackrock.com:8080")
        
        # Search button
        search_button = st.button("🔍 Search News", type="primary", use_container_width=True, key="search_news_btn")
    
    # Main content area
    if "news_df" not in st.session_state:
        st.session_state.news_df = None
    
    if search_button:
        if not companies:
            st.error("Please enter at least one company name")
        else:
            with st.status("Searching for news...", expanded=True) as status:
                st.write(f"Looking for news about {', '.join(companies)}")
                st.write(f"Searching the past {hours_back} hours")
                
                # Start timer
                start_time = time.time()
                
                try:
                    # Call the function from the imported module
                    df = get_all_companies_news_sync(
                        companies=companies,
                        hours_back=hours_back,
                        initial_limit=initial_limit,
                        use_proxy=use_proxy
                    )
                    
                    # Store in session state
                    st.session_state.news_df = df
                    
                    # End timer
                    elapsed_time = time.time() - start_time
                    
                    if df is not None and not df.empty:
                        status.update(label=f"✅ Found {len(df)} articles in {elapsed_time:.2f} seconds", state="complete")
                    else:
                        status.update(label="❌ No articles found", state="error")
                
                except Exception as e:
                    st.error(f"Error during search: {str(e)}")
                    status.update(label="❌ Search failed", state="error")
    
    # Display results if we have them
    if st.session_state.news_df is not None and not st.session_state.news_df.empty:
        df = st.session_state.news_df
        
        # Filters section
        st.header("Filters")
        
        # Row 1: Company + Site Rank
        filter_row1_col1, filter_row1_col2 = st.columns(2)
        
        # Filter by company
        with filter_row1_col1:
            if 'search_term' in df.columns:
                company_filter = st.multiselect(
                    "Filter by Company:",
                    options=sorted(df['search_term'].unique()),
                    default=sorted(df['search_term'].unique()),
                    key="company_filter_multiselect"
                )
            else:
                company_filter = None
        
        # Filter by site rank
        with filter_row1_col2:
            if 'site_rank_rank_country' in df.columns:
                # Get max rank for setting appropriate intervals
                max_rank = int(df['site_rank_rank_country'].max())
                # Create intervals (100, 200, 300, etc.)
                rank_intervals = list(range(0, max_rank + 100, 100))
                if rank_intervals[-1] < max_rank:
                    rank_intervals.append(max_rank)
                    
                # Select interval as a range
                rank_min, rank_max = st.select_slider(
                    "Filter by Site Rank:",
                    options=rank_intervals,
                    value=(0, rank_intervals[-1]),
                    key="site_rank_slider"
                )
            else:
                rank_min, rank_max = None, None
        
        # Row 2: Country + Term Matching
        filter_row2_col1, filter_row2_col2 = st.columns(2)
        
        # Filter by country
        with filter_row2_col1:
            if 'countryname' in df.columns:
                # Convert all values to strings and filter out NaN values
                country_values = df['countryname'].dropna()
                country_values = [str(x) for x in country_values.unique()]
                country_values.sort()
                
                country_filter = st.multiselect(
                    "Filter by Country:",
                    options=country_values,
                    default=[],
                    key="country_filter_multiselect"
                )
            else:
                country_filter = None
        
        # Filter by all search terms in header or summary
        with filter_row2_col2:
            search_terms_filter = st.checkbox("Filter for any search term in headline/summary", value=False, key="search_terms_filter_checkbox")
            st.caption("Searches for selected companies in headline/summary")
        
        # Row 3: News Source + Days
        filter_row3_col1, filter_row3_col2 = st.columns(2)
        
        # Filter by first_source_name (news outlet)
        with filter_row3_col1:
            if 'first_source_name' in df.columns:
                # Get top 50 most common sources to avoid overwhelming the UI
                try:
                    top_sources = df['first_source_name'].dropna().value_counts().nlargest(50).index.tolist()
                    # Convert all to strings to avoid sorting issues
                    top_sources = [str(x) for x in top_sources]
                    top_sources.sort()
                    
                    source_filter = st.multiselect(
                        "Filter by News Source (Top 50):",
                        options=top_sources,
                        default=[],
                        key="source_filter_multiselect"
                    )
                except:
                    # Fallback if there's an error with the sorting
                    source_filter = []
                    st.warning("Unable to process news sources")
            else:
                source_filter = None
        
        # Filter by time
        with filter_row3_col2:
            if 'local_time_text' in df.columns:
                # Filter by days back from today
                days_back = st.slider(
                    "Filter by Days (from today):",
                    min_value=1,
                    max_value=30,  # Default to max 30 days
                    value=7,       # Default to 7 days
                    step=1,
                    key="days_filter_slider"
                )
                # Calculate the date range based on days back
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days_back)
                
                try:
                    # Convert string format to datetime - with better error handling
                    df['local_time_datetime'] = pd.to_datetime(df['local_time_text'], format='%Y%m%dT%H:%M:%S%z', errors='coerce')
                except Exception as e:
                    st.warning(f"Could not parse time format: {str(e)}")
                    days_back = None
                    start_date = None
                    end_date = None
            else:
                days_back = None
                start_date = None
                end_date = None
        
        # Apply all filters to create filtered dataframe
        filtered_df = df.copy()
        
        # Apply company filter
        if company_filter and 'search_term' in df.columns:
            filtered_df = filtered_df[filtered_df['search_term'].isin(company_filter)]
        
        # Apply source filter - handle string conversion
        if source_filter and 'first_source_name' in df.columns:
            # Convert source names in DataFrame to strings for proper comparison
            filtered_df['source_str'] = filtered_df['first_source_name'].astype(str)
            filtered_df = filtered_df[filtered_df['source_str'].isin(source_filter)]
            filtered_df = filtered_df.drop('source_str', axis=1)
        
        # Apply country filter - handle string conversion
        if country_filter and 'countryname' in df.columns:
            # Convert country names in DataFrame to strings for proper comparison
            # This prevents type mismatch issues when comparing
            filtered_df['countryname_str'] = filtered_df['countryname'].astype(str)
            filtered_df = filtered_df[filtered_df['countryname_str'].isin(country_filter)]
            filtered_df = filtered_df.drop('countryname_str', axis=1)
        
        # Apply site rank filter with intervals
        if rank_min is not None and rank_max is not None and 'site_rank_rank_country' in df.columns:
            filtered_df = filtered_df[
                (filtered_df['site_rank_rank_country'] >= rank_min) & 
                (filtered_df['site_rank_rank_country'] <= rank_max)
            ]
        
        # Apply date filter based on days back from today
        if start_date is not None and end_date is not None and 'local_time_datetime' in filtered_df.columns:
            try:
                # Convert dates to strings for comparison (to avoid timezone issues)
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Create a date-only string column for comparison
                filtered_df['date_str'] = filtered_df['local_time_datetime'].dt.strftime('%Y-%m-%d')
                
                # Filter based on string dates
                filtered_df = filtered_df[
                    (filtered_df['date_str'] >= start_date_str) & 
                    (filtered_df['date_str'] <= end_date_str)
                ]
                
                # Remove temporary column
                filtered_df = filtered_df.drop('date_str', axis=1)
            except Exception as e:
                st.warning(f"Could not filter by date: {str(e)}")
                # Continue without date filtering if it fails
                pass
        
        # Apply search term filter - using a single checkbox for all terms
        if search_terms_filter and 'search_term' in df.columns:
            # Get all active search terms
            active_search_terms = company_filter if company_filter else []
            
            if active_search_terms:
                # Initialize a Series of False values with the same index as filtered_df
                text_match = pd.Series(False, index=filtered_df.index)
                
                # Check for each term
                for term in active_search_terms:
                    term_match = pd.Series(False, index=filtered_df.index)
                    
                    # Check in header_text
                    if 'header_text' in filtered_df.columns:
                        header_match = filtered_df['header_text'].str.contains(term, case=False, na=False)
                        term_match = term_match | header_match
                    
                    # Check in summary_text
                    if 'summary_text' in filtered_df.columns:
                        summary_match = filtered_df['summary_text'].str.contains(term, case=False, na=False)
                        term_match = term_match | summary_match
                    
                    # Combine with overall match (OR logic between terms)
                    text_match = text_match | term_match
                
                # Apply the combined filter
                filtered_df = filtered_df[text_match]
        
        # Add 'selected' column to the filtered dataframe if it doesn't exist
        if 'selected' not in filtered_df.columns:
            filtered_df['selected'] = False
            
        # Store the filtered dataframe in session state for the analysis page
        st.session_state.filtered_news_df = filtered_df
        
        # RESULTS SECTION
        # Dashboard stats based on filtered data
        st.header("📊 Search Results")
        st.subheader(f"Showing {len(filtered_df)} articles")
        
        # Create two columns for stats and chart
        stats_col, chart_col = st.columns(2)
        
        with stats_col:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Articles", len(filtered_df))
            with col2:
                if 'search_term' in filtered_df.columns:
                    st.metric("Companies", filtered_df['search_term'].nunique())
            
            col3, col4 = st.columns(2)
            with col3:
                if 'datetime' in filtered_df.columns:
                    df_with_dates = filtered_df[filtered_df['datetime'].notna()]
                    if not df_with_dates.empty:
                        earliest = df_with_dates['datetime'].min()
                        st.metric("Earliest", earliest.strftime('%Y-%m-%d %H:%M'))
            with col4:
                if 'datetime' in filtered_df.columns:
                    df_with_dates = filtered_df[filtered_df['datetime'].notna()]
                    if not df_with_dates.empty:
                        latest = df_with_dates['datetime'].max()
                        st.metric("Latest", latest.strftime('%Y-%m-%d %H:%M'))
        
        # Company distribution chart based on filtered data
        with chart_col:
            if 'search_term' in filtered_df.columns:
                company_counts = filtered_df['search_term'].value_counts().reset_index()
                company_counts.columns = ['Company', 'Count']
                
                fig = px.bar(
                    company_counts, 
                    x='Company', 
                    y='Count',
                    color='Company',
                    labels={'Count': 'Number of Articles', 'Company': 'Company Name'},
                    title=f"News Distribution ({len(filtered_df)} articles)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Choose columns to display in the data editor
        display_cols = []
        priority_cols = [
            'selected', 'search_term', 'header_text', 'summary_text', 'first_source_name', 
            'countryname', 'site_rank_rank_country', 'local_time_text'
        ]
        
        # Add columns that exist in the dataframe
        for col in priority_cols:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        # If no columns matched, use all columns
        if not display_cols:
            display_cols = filtered_df.columns.tolist()
        
        # Display data editor - ensure 'selected' is displayed first
        if 'selected' in display_cols:
            display_cols.remove('selected')
            display_cols.insert(0, 'selected')
            
        news_editor = st.data_editor(
            filtered_df[display_cols],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="news_data_editor_search"
        )
        
        # Update filtered_df with any edits from the data editor, especially selected column
        for col in display_cols:
            if col in news_editor.columns:
                filtered_df[col] = news_editor[col]
        
        # Store the updated filtered dataframe in session state
        st.session_state.filtered_news_df = filtered_df
        
        # Calculate how many rows are selected
        selected_count = filtered_df['selected'].sum()
        
        # Add button to navigate to the analysis page
        col1, col2 = st.columns([1, 3])
        with col1:
            button_label = f"→ Tag {int(selected_count)} Selected Articles" if selected_count > 0 else "→ Select Articles to Tag"
            tag_button = st.button(button_label, type="primary", use_container_width=True, key="goto_tagging_btn_search2")
            
            if tag_button:
                if selected_count > 0:
                    # Store only selected rows
                    selected_rows = filtered_df[filtered_df['selected'] == True]
                    st.session_state.selected_news_df = selected_rows.copy()
                    # Reset 'selected' column in the analysis tab to enable re-selection
                    st.session_state.selected_news_df['selected'] = False
                    # Store in tagged_news_df for the newsletter tab
                    st.session_state.tagged_news_df = st.session_state.selected_news_df.copy()
                    st.rerun()
                else:
                    st.warning("Please select at least one article by checking the 'Select' column")
        
        # Download button
        with col2:
            st.download_button(
                label="📥 Download Results as CSV",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"news_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_results_btn_search"
            )

def news_tagging_page():
    st.title("🏷️ News Tagging")
    st.write("Add themes and subheaders to categorize your selected news articles")
    
    # Check if we have selected news data in session state
    if "selected_news_df" not in st.session_state or st.session_state.selected_news_df is None:
        st.error("⚠️ No selected news articles. Please select articles in the Search tab first.")
        
        # Add a button to go back to search page
        button_key = f"goto_search_btn_tagging_{int(time.time() * 1000)}"
        if st.button("← Go to News Search", type="primary", key=button_key):
            # Update the sidebar selection
            st.session_state.main_navigation = "News Search"
            st.rerun()
        return
    
    # Get the selected dataframe directly from session state
    # Use copy to avoid modifying the original
    df = st.session_state.selected_news_df.copy()
    
    # Add Theme and Subheader columns if they don't exist
    if 'Theme' not in df.columns:
        df['Theme'] = ""
    
    if 'Subheader' not in df.columns:
        df['Subheader'] = ""
    
    # Get the selected dataframe directly from session state
    # Use copy to avoid modifying the original
    df = st.session_state.selected_news_df.copy()
    
    # Add Theme and Subheader columns if they don't exist
    if 'Theme' not in df.columns:
        df['Theme'] = ""
    
    if 'Subheader' not in df.columns:
        df['Subheader'] = ""
    
    # Main content
    # Display statistics
    st.header("📈 Tagging Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(df))
    
    with col2:
        # Count articles with any theme
        themed_count = df[df['Theme'] != ""].shape[0]
        st.metric("Themed Articles", themed_count)
    
    with col3:
        # Count selected articles
        selected_count = df['selected'].sum()
        st.metric("Checked Articles", int(selected_count))
    
    # Tag Management Section - Now in main panel instead of sidebar
    st.header("🏷️ Tag Management")
    st.write("Add themes and subheaders to checked articles in the table below")
    
    # Create a single row with 4 columns for theme and subheader inputs
    tag_col1, tag_col2, tag_col3, tag_col4 = st.columns([3, 1, 3, 1])

    with tag_col1:
        theme_options = st.text_input(
            "Enter themes (comma separated):",
            value="GenAI, Energy, Healthcare",
            help="Example: GenAI, Energy, Healthcare",
            key="theme_options_input_tagging"
        )

    with tag_col2:
        apply_theme = st.button("Apply", use_container_width=True, key="apply_theme_btn_tagging")

    with tag_col3:
        subheader_options = st.text_input(
            "Enter subheaders (comma separated):",
            value="Global, AMERS, EMERA, APAC",
            help="Example: Global, AMERS, EMERA, APAC",
            key="subheader_options_input_tagging"
        )

    with tag_col4:
        apply_subheader = st.button("Apply", use_container_width=True, key="apply_subheader_btn_tagging")  
        
    # Additional action buttons in a row
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        clear_selection = st.button("Clear Checks", use_container_width=True, key="clear_checks_btn_tagging")
    
    with btn_col2:
        reset_tags = st.button("Reset All Tags", use_container_width=True, key="reset_tags_btn_tagging")
    
    # Add a separator
    st.markdown("---")
    
    # Helper functions for batch operations
    def apply_theme_to_selected():
        theme_list = [theme.strip() for theme in theme_options.split(",")]
        mask = df['selected'] == True
        if mask.any():
            # For selected rows, append new themes (avoid duplicates)
            for idx in df[mask].index:
                current_themes = set([] if pd.isna(df.at[idx, 'Theme']) or df.at[idx, 'Theme'] == "" else 
                                    [t.strip() for t in df.at[idx, 'Theme'].split(",")])
                new_themes = current_themes.union(set(theme_list))
                df.at[idx, 'Theme'] = ", ".join(new_themes)
            st.success(f"Applied themes to {mask.sum()} checked articles")
        else:
            st.warning("No articles checked. Please check articles first.")
    
    def apply_subheader_to_selected():
        subheader_list = [subheader.strip() for subheader in subheader_options.split(",")]
        mask = df['selected'] == True
        if mask.any():
            # For selected rows, append new subheaders (avoid duplicates)
            for idx in df[mask].index:
                current_subheaders = set([] if pd.isna(df.at[idx, 'Subheader']) or df.at[idx, 'Subheader'] == "" else 
                                       [s.strip() for s in df.at[idx, 'Subheader'].split(",")])
                new_subheaders = current_subheaders.union(set(subheader_list))
                df.at[idx, 'Subheader'] = ", ".join(new_subheaders)
            st.success(f"Applied subheaders to {mask.sum()} checked articles")
        else:
            st.warning("No articles checked. Please check articles first.")
    
    # Execute batch operations based on button clicks
    if apply_theme:
        apply_theme_to_selected()
    
    if apply_subheader:
        apply_subheader_to_selected()
    
    if clear_selection:
        df['selected'] = False
        st.success("All checks cleared")
    
    if reset_tags:
        df['Theme'] = ""
        df['Subheader'] = ""
        st.success("All tags have been reset")
    
    # Data table section header
    st.header("📋 News Articles")
    
    # Create display columns - put selected first, then Theme/Subheader, then priority columns
    priority_cols = ['search_term', 'countryname', 'header_text', 'summary_text', 'body_text']
    display_cols = ['selected', 'Theme', 'Subheader']
    
    # Add available priority columns
    for col in priority_cols:
        if col in df.columns:
            display_cols.append(col)
    
    # Create the data editor for user interaction - ensure Theme and Subheader are editable
    edited_df = st.data_editor(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "selected": st.column_config.CheckboxColumn("Select", help="Check articles for batch editing"),
            "search_term": st.column_config.TextColumn("Company", help="Company name"),
            "countryname": st.column_config.TextColumn("Country", help="Country of publication"),
            "header_text": st.column_config.TextColumn("Headline", help="Article headline"),
            "summary_text": st.column_config.TextColumn("Summary", help="Article summary"),
            "body_text": st.column_config.TextColumn("Content", help="Article content"),
            "Theme": st.column_config.TextColumn("Theme", help="Article themes (e.g., GenAI, Energy)", width="medium"),
            "Subheader": st.column_config.TextColumn("Subheader", help="Article region (e.g., Global, AMERS)", width="medium")
        },
        num_rows="dynamic",
        key="analysis_data_editor_tagging",
        disabled=False  # Ensure nothing is disabled
    )
    
    # Update the displayed columns in the dataframe with edited values
    for col in display_cols:
        if col in edited_df.columns:
            df[col] = edited_df[col]
    
    # Update session state with the edited dataframe
    st.session_state.selected_news_df = df
    
    # Store the edited dataframe for the newsletter tab
    st.session_state.tagged_news_df = df.copy()
    
    # Add buttons to handle newsletter generation
    st.markdown("---")
    
    newsletter_col1, newsletter_col2 = st.columns(2)
    with newsletter_col1:
        st.subheader("Use Tagged Articles for Newsletter")
        st.write("Generate a newsletter using the articles you've tagged above.")
        
        if st.button("Generate Newsletter from Tagged Articles", type="primary", use_container_width=True, key="generate_newsletter_btn_tagging"):
            # Save the tagged data for newsletter generation
            st.session_state.tagged_news_df = df
            st.success("Articles are ready for newsletter generation! Switch to the Newsletter tab.")
    
    with newsletter_col2:
        st.subheader("Export Tagged Articles")
        st.write("Download your tagged articles as a CSV file.")
        
        # Download button
        st.download_button(
            label="📥 Download Tagged Articles as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"tagged_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_tagged_btn_tagging"
        )

def newsletter_generation_page():
    st.title("📧 Newsletter Generator")
    st.write("Create customized newsletters using your tagged articles or upload a CSV")
    
    # Initialize key variables with default values to prevent UnboundLocalError
    # These will be used if user hasn't explicitly set them yet
    colors = {
        'primary': '#0168b1',
        'secondary': '#333333',
        'background': '#e6e6e6',
        'header_bg': '#0168b1',
        'footer_bg': '#000000',
        'highlight': '#0168b1'
    }
    default_banner = "blue"
    content_width = 800
    mobile_friendly = True
    preview_text = "Your newsletter preview text here"
    banner_selection = "BlackRock Corporate (Default)"
    banner_html_file = None
    
    # First, let's check for data sources
    has_tagged_data = (
        "tagged_news_df" in st.session_state 
        and st.session_state.tagged_news_df is not None
        and hasattr(st.session_state.tagged_news_df, 'empty')
        and not st.session_state.tagged_news_df.empty
    )
    
    # Source selection
    st.subheader("Data Source")
    data_source = st.radio(
        "Choose your data source:",
        options=["Tagged News Articles", "Upload CSV", "Use Demo Data"],
        index=0 if has_tagged_data else 2,
        key="data_source_radio_newsletter"
    )
    
    df = None
    
    if data_source == "Tagged News Articles":
        if has_tagged_data:
            df = st.session_state.tagged_news_df.copy()
            st.success(f"Using {len(df)} tagged articles from previous step")
        else:
            st.error("No tagged articles available. Please tag some articles in the News Tagging tab or choose another data source.")
    
    elif data_source == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload your CSV file", 
            type=["csv"], 
            on_change=trigger_update,
            key="csv_uploader_newsletter"
        )
        
        if uploaded_file is not None:
            # Process the uploaded file
            df = pd.read_csv(uploaded_file)
            df = clean_dataframe(df)
            st.success(f"Loaded {len(df)} articles from CSV")
        else:
            st.info("Please upload a CSV file with your news articles")
    
    elif data_source == "Use Demo Data":
        # Check if the demo file exists
        demo_file = "dummy_news.csv"
        
        if os.path.exists(demo_file):
            df = pd.read_csv(demo_file)
            df = clean_dataframe(df)
            st.success(f"Loaded demo dataset with {len(df)} articles")
        else:
            # Create a simple demo dataset if file doesn't exist
            data = [
                {"Company": "Technology Corp", "News_Type": "Product Updates", "Article_Title": "New Product Launch", 
                 "Source": "Tech Insider", "Date": "01 March 2025", 
                 "Content": "A revolutionary product designed to disrupt the industry..."},
                {"Company": "Technology Corp", "News_Type": "Industry News", "Article_Title": "Market Trends", 
                 "Source": "Business Journal", "Date": "02 March 2025", 
                 "Content": "Industry analysis shows significant growth in tech sector..."},
                {"Company": "Finance Inc", "News_Type": "Market Analysis", "Article_Title": "Q1 Results",
                 "Source": "Financial Times", "Date": "03 March 2025",
                 "Content": "First quarter results show strong performance across all sectors..."}
            ]
            
            df = pd.DataFrame(data)
            st.success(f"Created sample dataset with {len(df)} articles")
    
    # Add the dataframe preview right here, after df is initialized from any source
    if df is not None:
        st.subheader("Imported Data Preview")
        
        # Define priority columns to display with both lowercase and capitalized versions
        priority_cols = [
            'selected', 'Selected',
            'theme', 'Theme', 
            'subheader', 'Subheader',
            'company', 'Company', 
            'search_term', 
            'first_source_name', 'Source',
            'countryname', 
            'header_text', 'Article_Title',
            'summary_text', 'Content',
            'body_text', 
            'url', 'Url'
        ]
        
        # Display available columns for debugging
        with st.expander("Debug Available Columns"):
            st.write("Available columns in dataframe:", df.columns.tolist())
        
        # Filter to only include columns that actually exist in the dataframe
        display_cols = [col for col in priority_cols if col in df.columns]
        
        # If none of the priority columns exist, show all columns
        if not display_cols:
            display_cols = df.columns.tolist()
        
        # Show filtered columns
        st.dataframe(df[display_cols], use_container_width=True)
        
        # IMPORTANT: Initialize column_mapping here with the dataframe so it's available throughout the function
        column_mapping = create_column_mapping_interface(df, key_prefix="preview_")
        
        # Add column mapping information to help users understand
        st.info("Note: Columns like 'Theme' and 'Subheader' from the tagging page will be shown here if available.")

    
    if df is None:
        st.warning("Please select a valid data source to continue")
        
        # Show explanation for CSV format
        with st.expander("CSV Format Example"):
            st.write("Your CSV should include the following columns:")
            sample_data = [
                {
                    "Company": "Technology Corp",
                    "News_Type": "Product Updates",
                    "Article_Title": "New Product Launch",
                    "Source": "Tech Insider",
                    "Date": "01 March 2025",
                    "Content": "A revolutionary product designed to disrupt the industry..."
                },
                {
                    "Company": "Technology Corp",
                    "News_Type": "Industry News",
                    "Article_Title": "Market Trends",
                    "Source": "Business Journal",
                    "Date": "02 March 2025",
                    "Content": "Industry analysis shows significant growth in tech sector..."
                }
            ]
            
            sample_df = pd.DataFrame(sample_data)
            st.dataframe(sample_df)
            
            csv = sample_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="sample_newsletter_data.csv">Download sample CSV file</a>'
            st.markdown(href, unsafe_allow_html=True)
        
        st.stop()
    
    # Create columns for configuration and preview
    left_col, right_col = st.columns([6, 6])
    
    with left_col:
        st.subheader("Configuration")
        
        # Create tabs for different content sections
        content_tabs = st.tabs(["Summary", "Image", "Layout", "Banner"])
        
        with content_tabs[0]:  # Summary Tab
            st.subheader("Newsletter Summary")
            
            # Add select for articles
            if 'selected' not in df.columns:
                df['selected'] = False
            
            # Display dataframe for selection
            st.write("Select articles to include in summary")
            
            # Determine which columns to show for article selection
            # First try to find the most relevant title column
            title_column = None
            for possible_title in ['Article_Title', 'header_text', 'Title', 'Headline']:
                if possible_title in df.columns:
                    title_column = possible_title
                    break
            
            # If no title column found, take the first text column that's not 'selected'
            if not title_column:
                text_columns = [col for col in df.columns if col != 'selected' and df[col].dtype == 'object']
                if text_columns:
                    title_column = text_columns[0]
                else:
                    title_column = df.columns[0]  # Fallback to first column
            
            # Try to get a source column too
            source_column = None
            for possible_source in ['Source', 'first_source_name', 'Publisher']:
                if possible_source in df.columns:
                    source_column = possible_source
                    break
            
            # Create display columns list
            display_cols = ['selected', title_column]
            if source_column:
                display_cols.append(source_column)
                
            # Display more columns if available
            extra_info_cols = []
            for possible_info in ['Date', 'Theme', 'Subheader', 'Company', 'search_term']:
                if possible_info in df.columns and possible_info not in display_cols:
                    extra_info_cols.append(possible_info)
            
            # Add up to 2 extra info columns if available
            if extra_info_cols:
                display_cols.extend(extra_info_cols[:2])
            
            # Create column config for better display
            column_config = {
                "selected": st.column_config.CheckboxColumn("Select", help="Check to include in summary")
            }
            
            # Better labels for the columns
            if title_column:
                column_config[title_column] = st.column_config.TextColumn("Article Title", help="Title of the article")
            if source_column:
                column_config[source_column] = st.column_config.TextColumn("Source", help="Source of the article")
            
            edited_df = st.data_editor(
                df[display_cols],
                hide_index=True,
                use_container_width=True,
                key="summary_selector_newsletter",
                column_config=column_config
            )
            
            # Update selection
            df['selected'] = edited_df['selected']
            
            # Get indices of selected rows - use boolean indexing to ensure safety
            selected_rows = df[df['selected'] == True]
            selected_indices = selected_rows.index.tolist()  # These are safe indices from the actual dataframe
            
            if selected_indices:
                st.subheader("Generate Summary")
                prompt_tab, summary_tab = st.tabs(["1. Get Prompt for LLM", "2. Add Generated Summary"])
                
                with prompt_tab:
                    prompt = generate_prompt(df, selected_indices)
                    st.markdown("### Copy this prompt to your preferred LLM:")
                    copy_col1, copy_col2 = st.columns([5, 1])
                    with copy_col2:
                        if st.button("📋 Copy", use_container_width=True, key="copy_prompt_btn_newsletter"):
                            st.toast("Prompt copied to clipboard!", icon="✅")
                    st.code(prompt, language="text")
                    st.caption("""
                    **Two ways to copy:**
                    1. Click the "📋 Copy" button above, or
                    2. Use the copy icon in the top-right corner of the code block
                    """)
                    with st.expander("How to use this prompt"):
                        st.markdown("""
                        1. Copy the entire prompt using one of the copy buttons
                        2. Paste it into ChatGPT, Claude, or your preferred AI tool
                        3. Get the generated summary
                        4. Come back to the "Add Generated Summary" tab to paste your results
                        """)
                
                with summary_tab:
                    st.markdown("**After generating your summary with an external LLM, paste it here:**")
                    user_summary = st.text_area("Paste your generated summary here:", height=200, key="user_summary_newsletter", on_change=trigger_update)
                    
                    # Format summary for display with proper HTML
                    formatted_summary = f"""
                    <div style="color: #333333; font-family: 'BLK Fort', 'Arial', Arial, sans-serif; font-size: 14px; line-height: 22px; padding: 15px 0;">
                        <h3 style="color: #000000; font-size: 18px; margin-bottom: 10px; border-bottom: 1px solid #cccccc; padding-bottom: 5px;">Weekly Summary</h3>
                        {user_summary.replace('\n', '<br>') if user_summary else "No summary provided yet."}
                    </div>
                    """
                    
                    # Always show the Add Summary button
                    if st.button("Add Summary to Newsletter", use_container_width=True, key="add_summary_btn_newsletter"):
                        st.session_state.summary_html = formatted_summary
                        trigger_update()
                        # Force regenerate the newsletter to update the preview
                        regenerate_newsletter(
                            df, 
                            column_mapping,  # This variable is now available
                            colors, 
                            preview_text, 
                            content_width, 
                            mobile_friendly, 
                            banner_selection,
                            banner_html_file,
                            default_banner,
                            force=True
                        )
                        st.success("Summary added to newsletter and preview updated!")
                    
                    st.markdown("**Preview of formatted summary:**")
                    st.markdown(formatted_summary, unsafe_allow_html=True)
                    
                    # Button to remove summary if one exists
                    if 'summary_html' in st.session_state and st.session_state.summary_html:
                        if st.button("Remove Summary", use_container_width=True, key="remove_summary_btn_newsletter"):
                            st.session_state.summary_html = ""
                            trigger_update()
                            # Force regenerate the newsletter to update the preview
                            regenerate_newsletter(
                                df, 
                                column_mapping, 
                                colors, 
                                preview_text, 
                                content_width, 
                                mobile_friendly, 
                                banner_selection,
                                banner_html_file,
                                default_banner,
                                force=True
                            )
            else:
                st.info("Select articles in the table above to generate a summary prompt.")
                
            # Show current summary if it exists
            if 'summary_html' in st.session_state and st.session_state.summary_html:
                st.success("Summary added to newsletter")
                with st.expander("View current summary"):
                    st.markdown(st.session_state.summary_html, unsafe_allow_html=True)
                    
        with content_tabs[1]:  # Image Tab
            st.subheader("Add Image to Newsletter")
            
            # Image upload widget
            uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "gif"], key="image_upload_newsletter", on_change=trigger_update)
            
            # Image caption
            image_caption = st.text_area("Image caption:", height=100, key="image_caption_newsletter", on_change=trigger_update)
            
            if uploaded_image:
                # Display preview
                st.subheader("Image Preview")
                st.image(uploaded_image, width=400)
                
                # Add button to insert image
                if st.button("Add Image to Newsletter", use_container_width=True, key="add_image_btn_newsletter"):
                    # Convert the image to base64 for embedding in HTML
                    try:
                        # Open the image using PIL
                        img = Image.open(uploaded_image)
                        
                        # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
                        if img.mode == 'RGBA':
                            # Create a white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            # Paste the image on the background using alpha as mask
                            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                            img = background
                        
                        # Resize to reasonable dimensions for email
                        max_width = 600
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_width = max_width
                            new_height = int(img.height * ratio)
                            img = img.resize((new_width, new_height))
                        
                        # Save to buffer
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")  # Force JPEG format
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Format the image HTML with caption - centered with margin
                        formatted_image_html = f"""
                        <div style="padding: 15px 0; text-align: center;">
                            <img src="data:image/jpeg;base64,{img_str}" 
                                alt="Newsletter Image" 
                                style="max-width:100%; height:auto; display:block; margin:0 auto; border:1px solid #ddd;">
                            <p style="color: #333333; font-family: 'Arial', sans-serif; font-size: 14px; 
                                    line-height: 22px; font-style:italic; padding: 10px 0; text-align: center;">{image_caption}</p>
                            <hr style="border:0; border-top:1px solid #ddd; margin:15px 0; width: 80%; margin: 15px auto;">
                        </div>
                        """
                        
                        # Store in session state
                        st.session_state.image_html = formatted_image_html
                        trigger_update()
                        
                        # Force regenerate the newsletter to update the preview
                        regenerate_newsletter(
                            df, 
                            column_mapping, 
                            colors, 
                            preview_text, 
                            content_width, 
                            mobile_friendly, 
                            banner_selection,
                            banner_html_file,
                            default_banner,
                            force=True
                        )
                        
                        st.success("Image added to newsletter and preview updated!")
                    except Exception as e:
                        st.error(f"Error processing image: {e}")
            
                # Remove image button if an image exists
                if 'image_html' in st.session_state and st.session_state.image_html:
                    st.success("Image added to newsletter")
                    if st.button("Remove Image", use_container_width=True, key="remove_image_btn_newsletter"):
                        st.session_state.image_html = ""
                        trigger_update()
                        
                        # Force regenerate the newsletter to update the preview
                        regenerate_newsletter(
                            df, 
                            column_mapping, 
                            colors, 
                            preview_text, 
                            content_width, 
                            mobile_friendly, 
                            banner_selection,
                            banner_html_file,
                            default_banner,
                            force=True
                        )
        
        with content_tabs[2]:  # Layout Tab
            st.subheader("Layout Settings")
            
            # Column mapping for newsletter organization
            st.markdown("### Newsletter Organization")
            # Update the current column_mapping variable instead of creating a new one
            column_mapping = create_column_mapping_interface(df, key_prefix="layout_")
            
            # Layout dimensions and settings
            st.markdown("### Dimensions and Preview Text")
            
            # Color scheme selection
            color_theme = st.selectbox(
                "Select a color theme",
                ["Blue (Default)", "Green", "Purple", "Corporate", "Red", "Teal", "Amber", "Indigo", "Cyan", "Brown", "Custom"],
                key="color_theme_newsletter",
                on_change=trigger_update
            )
            
            # Pre-determined color schemes (10 options)
            if color_theme == "Blue (Default)":
                colors = {
                    'primary': '#0168b1',
                    'secondary': '#333333',
                    'background': '#e6e6e6',
                    'header_bg': '#0168b1',
                    'footer_bg': '#000000',
                    'highlight': '#0168b1'
                }
                default_banner = "blue"
            elif color_theme == "Green":
                colors = {
                    'primary': '#2C8B44',
                    'secondary': '#333333',
                    'background': '#F0F7F0',
                    'header_bg': '#1A5D2B',
                    'footer_bg': '#333333',
                    'highlight': '#2C8B44'
                }
                default_banner = "green"
            elif color_theme == "Purple":
                colors = {
                    'primary': '#673AB7',
                    'secondary': '#333333',
                    'background': '#F5F0FF',
                    'header_bg': '#4A148C',
                    'footer_bg': '#333333',
                    'highlight': '#9575CD'
                }
                default_banner = "purple"
            elif color_theme == "Corporate":
                colors = {
                    'primary': '#D74B4B',
                    'secondary': '#333333',
                    'background': '#F5F5F5',
                    'header_bg': '#1D2951',
                    'footer_bg': '#1D2951',
                    'highlight': '#D74B4B'
                }
                default_banner = "corporate"
            elif color_theme == "Red":
                colors = {
                    'primary': '#D32F2F',
                    'secondary': '#333333',
                    'background': '#FFEBEE',
                    'header_bg': '#B71C1C',
                    'footer_bg': '#7F0000',
                    'highlight': '#F44336'
                }
                default_banner = "red"
            elif color_theme == "Teal":
                colors = {
                    'primary': '#00897B',
                    'secondary': '#333333',
                    'background': '#E0F2F1',
                    'header_bg': '#004D40',
                    'footer_bg': '#002B22',
                    'highlight': '#26A69A'
                }
                default_banner = "teal"
            elif color_theme == "Amber":
                colors = {
                    'primary': '#FFB300',
                    'secondary': '#333333',
                    'background': '#FFF8E1',
                    'header_bg': '#FF6F00',
                    'footer_bg': '#B23C00',
                    'highlight': '#FFC107'
                }
                default_banner = "amber"
            elif color_theme == "Indigo":
                colors = {
                    'primary': '#3949AB',
                    'secondary': '#333333',
                    'background': '#E8EAF6',
                    'header_bg': '#1A237E',
                    'footer_bg': '#0D1243',
                    'highlight': '#3F51B5'
                }
                default_banner = "indigo"
            elif color_theme == "Cyan":
                colors = {
                    'primary': '#00ACC1',
                    'secondary': '#333333',
                    'background': '#E0F7FA',
                    'header_bg': '#006064',
                    'footer_bg': '#00363A',
                    'highlight': '#00BCD4'
                }
                default_banner = "cyan"
            elif color_theme == "Brown":
                colors = {
                    'primary': '#795548',
                    'secondary': '#333333',
                    'background': '#EFEBE9',
                    'header_bg': '#3E2723',
                    'footer_bg': '#1B0000',
                    'highlight': '#8D6E63'
                }
                default_banner = "brown"
            elif color_theme == "Custom":
                st.subheader("Custom Color Selection")
                # Allow both HEX code input and color picker
                custom_method = st.radio(
                    "Choose method for custom colors:",
                    ["Color Picker", "HEX Code"],
                    horizontal=True,
                    key="custom_method_newsletter",
                    on_change=trigger_update
                )
                
                if custom_method == "Color Picker":
                    colors = {
                        'primary': st.color_picker("Primary Color", '#0168b1', key="primary_color_newsletter", on_change=trigger_update),
                        'secondary': st.color_picker("Secondary Color", '#333333', key="secondary_color_newsletter", on_change=trigger_update),
                        'background': st.color_picker("Background Color", '#e6e6e6', key="background_color_newsletter", on_change=trigger_update),
                        'header_bg': st.color_picker("Header Background", '#0168b1', key="header_bg_color_newsletter", on_change=trigger_update),
                        'footer_bg': st.color_picker("Footer Background", '#000000', key="footer_bg_color_newsletter", on_change=trigger_update),
                        'highlight': st.color_picker("Highlight Color", '#0168b1', key="highlight_color_newsletter", on_change=trigger_update)
                    }
                else:  # HEX Code input
                    col1, col2 = st.columns(2)
                    with col1:
                        primary = st.text_input("Primary Color (HEX)", "#0168b1", key="primary_hex_newsletter", on_change=trigger_update)
                        secondary = st.text_input("Secondary Color (HEX)", "#333333", key="secondary_hex_newsletter", on_change=trigger_update)
                        background = st.text_input("Background Color (HEX)", "#e6e6e6", key="background_hex_newsletter", on_change=trigger_update)
                    with col2:
                        header_bg = st.text_input("Header Background (HEX)", "#0168b1", key="header_bg_hex_newsletter", on_change=trigger_update)
                        footer_bg = st.text_input("Footer Background (HEX)", "#000000", key="footer_bg_hex_newsletter", on_change=trigger_update)
                        highlight = st.text_input("Highlight Color (HEX)", "#0168b1", key="highlight_hex_newsletter", on_change=trigger_update)
                    
                    colors = {
                        'primary': primary,
                        'secondary': secondary,
                        'background': background,
                        'header_bg': header_bg,
                        'footer_bg': footer_bg,
                        'highlight': highlight
                    }
                
                default_banner = "blue"
                
            # Common layout settings
            content_width = st.slider(
                "Content Width (px)", 
                600, 1000, 800,
                key="content_width_newsletter",
                on_change=trigger_update
            )
            
            mobile_friendly = st.checkbox(
                "Mobile-friendly design", 
                value=True,
                key="mobile_friendly_newsletter",
                on_change=trigger_update
            )
            
            preview_text = st.text_input(
                "Preview Text (shown in email clients)", 
                "Your newsletter preview text here",
                key="preview_text_newsletter",
                on_change=trigger_update
            )
        
        with content_tabs[3]:  # Banner Tab
            st.subheader("Banner Selection")
            
            # Banner options now include preloaded banners from the banners directory
            banner_options = list(BANNER_FILENAMES.keys()) + ["Upload Custom HTML Banner"]
            
            banner_selection = st.radio(
                "Choose a banner style:",
                banner_options,
                horizontal=True,
                index=0,  # Default to the corpcomm_banner
                key="banner_selection_newsletter",
                on_change=trigger_update
            )
            
            # Text editing fields for each banner type
            st.subheader("Edit Banner Text")
            
            if banner_selection == "BlackRock Corporate (Default)":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['corporate_top'] = st.text_input(
                        "Top Bar Text", 
                        st.session_state.banner_text['corporate_top'],
                        key="corporate_top_text_newsletter",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['corporate_middle'] = st.text_input(
                        "Middle Bar Text", 
                        st.session_state.banner_text['corporate_middle'],
                        key="corporate_middle_text_newsletter",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "GIPS Infrastructure":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gips_brand'] = st.text_input(
                        "Brand Name", 
                        st.session_state.banner_text['gips_brand'],
                        key="gips_brand_text_newsletter",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['gips_subtitle'] = st.text_input(
                        "Brand Subtitle", 
                        st.session_state.banner_text['gips_subtitle'],
                        key="gips_subtitle_text_newsletter",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['gips_headline'] = st.text_input(
                        "Headline Text", 
                        st.session_state.banner_text['gips_headline'],
                        key="gips_headline_text_newsletter",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Modern Design":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['modern_brand'] = st.text_input(
                        "Brand Text", 
                        st.session_state.banner_text['modern_brand'],
                        key="modern_brand_text_newsletter",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['modern_date'] = st.text_input(
                        "Date Text", 
                        st.session_state.banner_text['modern_date'],
                        key="modern_date_text_newsletter",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['modern_tagline'] = st.text_input(
                        "Tagline Text", 
                        st.session_state.banner_text['modern_tagline'],
                        key="modern_tagline_text_newsletter",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Gradient Style":
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.banner_text['gradient_title'] = st.text_input(
                        "Title", 
                        st.session_state.banner_text['gradient_title'],
                        key="gradient_title_text_newsletter",
                        on_change=trigger_update
                    )
                    st.session_state.banner_text['gradient_subtitle'] = st.text_input(
                        "Subtitle", 
                        st.session_state.banner_text['gradient_subtitle'],
                        key="gradient_subtitle_text_newsletter",
                        on_change=trigger_update
                    )
                with col2:
                    st.session_state.banner_text['gradient_edition'] = st.text_input(
                        "Edition Text", 
                        st.session_state.banner_text['gradient_edition'],
                        key="gradient_edition_text_newsletter",
                        on_change=trigger_update
                    )
                selected_banner = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                
            elif banner_selection == "Upload Custom HTML Banner":
                banner_html_file = st.file_uploader(
                    "Upload your HTML banner file", 
                    type=["html", "htm"],
                    key="custom_banner_newsletter",
                    on_change=trigger_update
                )
                if banner_html_file:
                    st.success("HTML banner uploaded successfully!")
                    selected_banner = banner_html_file
                else:
                    # Default to corpcomm_banner if no upload
                    banner_path = os.path.join(BANNERS_DIR, "corpcomm_banner.html")
                    st.info("No custom banner uploaded. Using default BlackRock Corporate banner.")
                    selected_banner = banner_path
            
            # Debug checkbox for banner content
            debug_mode = st.checkbox("Debug Mode (Show HTML content)", value=False, key="debug_mode_newsletter", on_change=trigger_update)
            if debug_mode:
                if banner_selection != "Upload Custom HTML Banner" or (banner_selection == "Upload Custom HTML Banner" and not banner_html_file):
                    # For preloaded banners, show their content
                    html_content = get_modified_banner_html(banner_selection, st.session_state.banner_text)
                    
                    st.subheader(f"HTML Content for {banner_selection}")
                    st.code(html_content, language="html")
                elif banner_html_file:
                    banner_html, banner_styles = extract_banner_from_html(banner_html_file)
                    if banner_html:
                        st.subheader("Extracted Banner HTML")
                        st.code(banner_html, language="html")
                        if banner_styles:
                            st.subheader("Extracted Banner Styles")
                            st.code(banner_styles, language="css")
                    else:
                        st.error("Failed to extract banner HTML from the file.")
        
        # Email functionality
        st.subheader("Email Your Newsletter")
        with st.expander("Send Newsletter via Email", expanded=False):
            st.markdown("""
            <div style="background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin-top: 20px;">
                <h3>Send Newsletter</h3>
                <p>Send your newsletter directly via email to your recipients.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input(
                    "From Email", 
                    placeholder="your.name@company.com",
                    key="sender_email_newsletter"
                )
            
            with col2:
                email_subject = st.text_input(
                    "Subject", 
                    f"Newsletter: {datetime.now().strftime('%B %d, %Y')}",
                    key="email_subject_newsletter"
                )
            
            # Email recipients
            to_emails = st.text_area(
                "To Emails (comma separated)", 
                placeholder="recipient1@company.com, recipient2@company.com",
                key="to_emails_newsletter"
            )
            
            # Optional CC and BCC
            col1, col2 = st.columns(2)
            with col1:
                cc_emails = st.text_area(
                    "CC", 
                    placeholder="cc1@company.com, cc2@company.com",
                    key="cc_emails_newsletter",
                    height=80
                )
            
            with col2:
                bcc_emails = st.text_area(
                    "BCC", 
                    placeholder="bcc1@company.com, bcc2@company.com",
                    key="bcc_emails_newsletter",
                    height=80
                )
            
            # Send button
            if st.button("Send Newsletter Email", use_container_width=True, key="send_email_btn_newsletter"):
                if 'newsletter_html' not in st.session_state:
                    st.error("Please generate the newsletter first.")
                elif not sender_email:
                    st.error("Please enter your email address.")
                elif not to_emails:
                    st.error("Please enter at least one recipient email address.")
                else:
                    # Get the HTML content
                    newsletter_html = st.session_state.newsletter_html
                    
                    with st.spinner("Sending email ..."):
                        # Create email sender
                        email_sender = EmailSender()
                        
                        # Send the email
                        success, message = email_sender.send_html_email(
                            from_email=sender_email,
                            to_emails=to_emails,
                            subject=email_subject,
                            html_content=newsletter_html,
                            cc_emails=cc_emails,
                            bcc_emails=bcc_emails
                        )
                        
                        if success:
                            st.success(message)
                            # Add to history
                            to_count = len([email.strip() for email in to_emails.split(',') if email.strip()])
                            cc_count = len([email.strip() for email in cc_emails.split(',') if email.strip()]) if cc_emails else 0
                            bcc_count = len([email.strip() for email in bcc_emails.split(',') if email.strip()]) if bcc_emails else 0
                            
                            st.session_state.email_history.append({
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'recipients': to_count + cc_count + bcc_count,
                                'subject': email_subject
                            })
                        else:
                            st.error(f"Failed to send email: {message}")
        
        # IMPROVED: Clearer manual generation button
        st.subheader("Manual Generation")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("If the preview doesn't update automatically, click this button.")
        with col2:
            # Access banner_html_file which might be defined in the banner tab
            if st.button("Force Regenerate", use_container_width=True, key="force_regenerate_btn_manual"):
                regenerate_newsletter(
                    df, 
                    column_mapping, 
                    colors, 
                    preview_text, 
                    content_width, 
                    mobile_friendly, 
                    banner_selection,
                    banner_html_file,
                    default_banner,
                    force=True
                )
                st.success("Newsletter regenerated successfully!")
                
    # Add the newsletter preview on the right column
    with right_col:
        st.subheader("Newsletter Preview")
        
        # Add controls for preview
        preview_controls_col1, preview_controls_col2 = st.columns([3, 1])
        
        with preview_controls_col1:
            # Add slider to adjust preview height
            preview_height = st.slider(
                "Preview Height (px)",
                min_value=400,
                max_value=2000,
                value=800,
                step=100,
                key="preview_height_slider",
                on_change=trigger_update
            )
        
        with preview_controls_col2:
            # Force regenerate button
            if st.button("Force Regenerate", type="primary", use_container_width=True, key="force_regenerate_btn_preview"):
                regenerate_newsletter(
                    df, 
                    column_mapping, 
                    colors, 
                    preview_text, 
                    content_width, 
                    mobile_friendly, 
                    banner_selection,
                    banner_html_file,
                    default_banner,
                    force=True
                )
                st.success("Newsletter regenerated successfully!")
        
        # Then modify the HTML preview code to use the user-defined height:
        if 'newsletter_html' in st.session_state and st.session_state.newsletter_html:
            preview_container = st.container()
            with preview_container:
                try:
                    import streamlit.components.v1 as components
                    
                    # Use the user-defined preview height
                    components.html(
                        st.session_state.newsletter_html, 
                        height=preview_height,  # Use the slider value
                        scrolling=True
                    )
                    
                except ImportError:
                    st.error("Unable to import streamlit.components.v1 for HTML preview.")
                    with st.expander("View Newsletter HTML Code"):
                        st.code(st.session_state.newsletter_html, language='html')
                    
                st.caption("Note: The preview above shows how your newsletter will look. You can scroll to see the entire content.")
        else:
            # If no newsletter has been generated yet
            # Auto-generate newsletter on first load if data is available
            # and there are no errors in any required config
            try:
                if df is not None and not st.session_state.newsletter_error:
                    # Generate default values if not available
                    if 'colors' not in locals():
                        colors = {
                            'primary': '#0168b1',
                            'secondary': '#333333',
                            'background': '#e6e6e6',
                            'header_bg': '#0168b1',
                            'footer_bg': '#000000',
                            'highlight': '#0168b1'
                        }
                    
                    if 'default_banner' not in locals():
                        default_banner = "blue"
                        
                    if 'column_mapping' not in locals():
                        column_mapping = create_column_mapping_interface(df)
                        
                    if 'preview_text' not in locals():
                        preview_text = "Your newsletter preview text here"
                        
                    if 'content_width' not in locals():
                        content_width = 800
                        
                    if 'mobile_friendly' not in locals():
                        mobile_friendly = True
                        
                    if 'banner_selection' not in locals():
                        banner_selection = "BlackRock Corporate (Default)"
                    
                    # Try to generate the newsletter
                    with st.spinner("Generating initial newsletter preview..."):
                        success = regenerate_newsletter(
                            df, 
                            column_mapping, 
                            colors, 
                            preview_text, 
                            content_width, 
                            mobile_friendly, 
                            banner_selection,
                            banner_html_file,
                            default_banner,
                            force=True
                        )
                        
                        if success and 'newsletter_html' in st.session_state:
                            # Force a rerun to show the preview
                            st.rerun()
                        else:
                            st.info("Configure your newsletter using the options on the left, then click 'Force Regenerate' to preview it.")
                else:
                    st.info("Configure your newsletter using the options on the left, then click 'Force Regenerate' to preview it.")
            except Exception as e:
                st.error(f"Error trying to generate initial preview: {str(e)}")
                st.info("Configure your newsletter using the options on the left, then click 'Force Regenerate' to preview it.")
                
# Add this at the end of your file
if __name__ == "__main__":
    # Create sidebar navigation
    tab1, tab2, tab3 = st.tabs(["🔍 News Search", "🏷️ News Tagging", "📧 Newsletter Generator"])

    with tab1:
        news_search_page()
        
    with tab2:
        news_tagging_page()
        
    with tab3:
        newsletter_generation_page()
