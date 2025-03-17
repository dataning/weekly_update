"""
Email sending utilities for the Gravity app
"""
import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:
    """
    Class for sending HTML-templated emails via mail server.
    """
    
    def __init__(self, internal_mail_server='mailhub.blackrock.com'):
        """
        Initialize email sender with mail server
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
        Send an HTML email via mail server
        
        Args:
            from_email (str): Sender's email address
            to_emails (str or list): Recipient email(s) - can be a string or list
            subject (str): Email subject
            html_content (str): HTML content as a string
            cc_emails (str or list): CC recipients - can be a string or list
            bcc_emails (str or list): BCC recipients - can be a string or list
            
        Returns:
            tuple: (success, message) - success is True/False, message is a status message
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