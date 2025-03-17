"""
HTML processing utilities for the Gravity app
"""
import re
from bs4 import BeautifulSoup

def apply_summary_at_position(html_content, summary_html, position="after_banner"):
    """
    Apply the summary at a specific position in the newsletter.
    Works entirely in memory - no file operations.
    
    Args:
        html_content: The newsletter HTML content
        summary_html: The HTML content of the summary to add
        position: Where to add the summary (after_banner, top, before_articles)
        
    Returns:
        str: Modified HTML with summary injected
    """
    if not summary_html or not html_content:
        return html_content
    
    # First priority: Always look for the Please submit any feedback section
    feedback_container_patterns = [
        r'(<div[^>]*>\s*Please submit any feedback.*?<\/div>)',  # Standard pattern
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
    
    Args:
        html_content: The newsletter HTML content
        image_html: The HTML content of the image to add
        
    Returns:
        str: Modified HTML with image injected
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