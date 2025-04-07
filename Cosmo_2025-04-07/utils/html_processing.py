"""
HTML processing utilities for the Gravity app
"""
import re
from bs4 import BeautifulSoup

def apply_summary_at_position(html_content, summary_html, position="after_tagline"):
    """
    Insert summary HTML at a specified position in the newsletter HTML
    
    Args:
        html_content: The original newsletter HTML
        summary_html: The summary HTML to insert
        position: Where to insert the summary ('after_banner', 'after_tagline', 'top')
    
    Returns:
        str: Modified HTML with summary inserted
    """
    # Look for specific markers based on position
    if position == "after_banner":
        # Find the end of the banner/navigation section
        nav_pattern = re.compile(r'(</table>\s*<!-- Navigation -->)', re.DOTALL)
        match = nav_pattern.search(html_content)
        if match:
            insert_position = match.end()
            return html_content[:insert_position] + "\n\n" + summary_html + "\n\n" + html_content[insert_position:]
    
    elif position == "after_tagline" or position == "default":
        # Look for the summary marker comment
        marker_pattern = re.compile(r'(<!-- SUMMARY INSERTION MARKER - DO NOT REMOVE THIS COMMENT -->)', re.DOTALL)
        match = marker_pattern.search(html_content)
        if match:
            insert_position = match.end()
            return html_content[:insert_position] + "\n\n" + summary_html + "\n\n" + html_content[insert_position:]
        
        # Fallback: look for the end of the top message section
        top_msg_pattern = re.compile(r'(</table>\s*<!-- Top Message -->)', re.DOTALL)
        match = top_msg_pattern.search(html_content)
        if match:
            insert_position = match.end()
            return html_content[:insert_position] + "\n\n" + summary_html + "\n\n" + html_content[insert_position:]
    
    elif position == "top":
        # Insert at the beginning of the content area
        content_pattern = re.compile(r'(<table cellspacing="0" cellpadding="0" border="0" width="100%" align="center" class="full-width">)', re.DOTALL)
        match = content_pattern.search(html_content)
        if match:
            insert_position = match.start()
            return html_content[:insert_position] + summary_html + "\n\n" + html_content[insert_position:]
    
    # If we didn't find a suitable position, insert before the content sections
    sections_pattern = re.compile(r'(<!-- Content Sections -->)', re.DOTALL)
    match = sections_pattern.search(html_content)
    if match:
        insert_position = match.start()
        return html_content[:insert_position] + summary_html + "\n\n" + html_content[insert_position:]
    
    # Fallback: just append to the end of the body
    body_end = html_content.rfind('</body>')
    if body_end != -1:
        return html_content[:body_end] + summary_html + html_content[body_end:]
    
    # Last resort: just return the original with summary appended
    return html_content + summary_html

def apply_image_content(html_content, image_html):
    """
    Insert image HTML in the newsletter
    
    Args:
        html_content: The original newsletter HTML
        image_html: The image HTML to insert
    
    Returns:
        str: Modified HTML with image inserted
    """
    # Try to insert the image after the first content section header
    section_header_pattern = re.compile(r'(<td class="section-header">.*?</td>.*?</tr>)', re.DOTALL)
    match = section_header_pattern.search(html_content)
    if match:
        insert_position = match.end()
        return html_content[:insert_position] + "\n<tr><td>" + image_html + "</td></tr>\n" + html_content[insert_position:]
    
    # Fallback: insert before the first article
    article_pattern = re.compile(r'(<tr class="article-row">)', re.DOTALL)
    match = article_pattern.search(html_content)
    if match:
        insert_position = match.start()
        return html_content[:insert_position] + "\n<tr><td>" + image_html + "</td></tr>\n" + html_content[insert_position:]
    
    # Last resort: insert before closing body tag
    body_end = html_content.rfind('</body>')
    if body_end != -1:
        # Create a proper container for the image
        wrapped_image = f'''
        <table cellpadding="0" cellspacing="0" border="0" width="100%">
            <tr>
                <td style="font-family:'BLK Fort','Arial',Arial,sans-serif; font-size:1px; line-height:1px;" width="40" class="mobile-spacer">&nbsp;</td>
                <td>{image_html}</td>
                <td style="font-family:'BLK Fort','Arial',Arial,sans-serif; font-size:1px; line-height:1px;" width="40" class="mobile-spacer">&nbsp;</td>
            </tr>
        </table>
        '''
        return html_content[:body_end] + wrapped_image + html_content[body_end:]
    
    return html_content