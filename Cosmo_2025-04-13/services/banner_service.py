"""
Banner service for handling banner templates and customization
"""
import os
import re
from bs4 import BeautifulSoup

# --------------------------------------------------------------------------------
# Banner type-to-file & template mappings
# --------------------------------------------------------------------------------

BANNER_FILENAMES = {
    "BlackRock Classic": "blackrock_classic.html",
    "BlackRock Modern": "blackrock_modern.html",
    "Yellow Accent": "yellow_accent.html",
    "Gradient Header": "gradient_header.html",
    "Minimalist": "minimalist.html",
    "Two-Column": "two_column.html",
    "Bold Header": "bold_header.html",
    "Split Design": "split_design.html",
    "Boxed Design": "boxed_design.html",
    "Double Border": "double_border.html",
    "Corner Accent": "corner_accent.html",
    "Stacked Elements": "stacked_elements.html",
    "Executive Style": "executive_style.html"
}

BANNER_HTML_TEMPLATES = {
    "BlackRock Classic": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width banner-container" bgcolor="#000000">
        <tr>
            <td style="font-family:'BLK Fort', 'Arial', Arial, sans-serif; padding:0; font-size:15px; line-height:15px; background-color:#000000;" width="40" class="mobile-spacer">&nbsp;</td>
            <td style="color:#ffffff; background-color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; padding-top:25px; padding-bottom:25px;" valign="middle">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td>
                            <span class="title" style="font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block; margin-bottom:5px;">{title}</span>
                            <span class="subtitle" style="font-size:18px; line-height:22px; font-weight:normal; font-family:'FortBook', 'BLK Fort', 'Arial'; letter-spacing:0;">{subtitle}</span>
                        </td>
                    </tr>
                </table>
            </td>
            <td align="right" valign="middle" width="25%" style="color:#ffffff; font-family:'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; background-color:#000000; vertical-align:middle; text-align:right; padding-top:25px; padding-bottom:25px;" class="date">
                {date}
            </td>
            <td style="font-family:'BLK Fort', 'Arial', Arial, sans-serif; padding:0; font-size:15px; line-height:15px; background-color:#000000;" width="40" class="mobile-spacer">&nbsp;</td>
        </tr>
    </table>
    """,
    
    "BlackRock Modern": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width" style="border-bottom:4px solid #ffce00;">
        <tr>
            <td style="background-color:#000000; padding:30px 40px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="color:#ffffff; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; padding-bottom:5px;">
                            <span class="title" style="font-size:42px; line-height:46px; letter-spacing:-1.5px; font-weight:bold; display:block;">{title}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#ffffff; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif;">
                            <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding-right:40px;" width="60%">
                                        <span class="subtitle" style="font-size:18px; line-height:24px;">{subtitle}</span>
                                    </td>
                                    <td align="right" style="color:#ffce00; font-family:'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; text-align:right; vertical-align:bottom;" class="date">
                                        {date}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Yellow Accent": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#ffce00; height:6px;" colspan="3"></td>
        </tr>
        <tr>
            <td style="background-color:#ffffff; padding:25px 40px; border-bottom:1px solid #e0e0e0;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="vertical-align:top; padding-right:20px;">
                            <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                            <span class="subtitle" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; margin-top:5px; display:block;">{subtitle}</span>
                        </td>
                        <td align="right" style="color:#666666; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; vertical-align:top; text-align:right;" class="date">
                            {date}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td style="background-color:#000000; height:2px;" colspan="3"></td>
        </tr>
    </table>
    """,
    
    "Gradient Header": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background: linear-gradient(90deg, #000000 0%, #444444 100%); padding:30px 40px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td>
                            <span class="title" style="color:#ffffff; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:38px; line-height:42px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                            <span class="subtitle" style="color:#ffce00; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:18px; line-height:24px; margin-top:8px; display:block;">{subtitle}</span>
                        </td>
                        <td align="right" style="color:#ffffff; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; vertical-align:bottom; text-align:right; padding-left:20px;" class="date">
                            <span style="display:inline-block; background-color:#ffce00; color:#000000; padding:6px 12px; font-weight:bold;">{date}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Minimalist": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#f8f8f8; padding:35px 40px; border-bottom:1px solid #e0e0e0;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="vertical-align:middle;">
                            <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:32px; line-height:36px; letter-spacing:-0.5px; font-weight:bold; display:block;">{title}</span>
                        </td>
                        <td align="right" style="color:#666666; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; vertical-align:middle; text-align:right; padding-left:20px;" class="date">
                            {date}
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding-top:5px;">
                            <span class="subtitle" style="color:#666666; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:20px;">{subtitle}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Two-Column": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="padding:0; margin:0;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="background-color:#000000; color:#ffffff; padding:30px 40px; width:65%;" class="content-width">
                            <span class="title" style="font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                            <span class="subtitle" style="font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; margin-top:8px; display:block;">{subtitle}</span>
                        </td>
                        <td style="background-color:#ffce00; color:#000000; padding:30px; text-align:center; width:35%;" class="content-width">
                            <span class="date" style="font-family:'BLK Fort', 'Arial', Arial, sans-serif; font-size:18px; line-height:22px; font-weight:bold; display:block;">{date}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Bold Header": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#000000; padding:25px 40px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td align="center" style="text-align:center; padding-bottom:3px;">
                            <span class="title" style="color:#ffffff; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:42px; line-height:46px; letter-spacing:-1.5px; font-weight:bold;">{title}</span>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="text-align:center; padding-top:3px; padding-bottom:3px;">
                            <span class="subtitle" style="color:#ffce00; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:18px; line-height:22px;">{subtitle}</span>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="text-align:center; padding-top:8px;">
                            <span class="date" style="color:#ffffff; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; background-color:#333333; padding:4px 12px; display:inline-block;">{date}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td style="background-color:#ffce00; height:4px;"></td>
        </tr>
    </table>
    """,
    
    "Split Design": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#000000; height:10px;"></td>
        </tr>
        <tr>
            <td style="background-color:#ffffff; padding:25px 40px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="border-left:4px solid #ffce00; padding-left:15px;">
                            <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                            <span class="subtitle" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; margin-top:5px; display:block;">{subtitle}</span>
                        </td>
                        <td align="right" style="color:#666666; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; vertical-align:top; text-align:right; padding-left:20px;" class="date">
                            {date}
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td style="background-color:#ffce00; height:3px;"></td>
        </tr>
    </table>
    """,
    
    "Boxed Design": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="padding:0px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%" style="border:3px solid #000000; background-color:#ffffff;">
                    <tr>
                        <td style="border-bottom:3px solid #ffce00; padding:0px;">
                            <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="padding:25px 30px 15px 30px;">
                                        <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:34px; line-height:38px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:0px 30px 10px 30px;">
                                        <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <span class="subtitle" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:20px;">{subtitle}</span>
                                                </td>
                                                <td align="right" style="text-align:right;">
                                                    <span class="date" style="display:inline-block; color:#000000; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; border:1px solid #000000; padding:3px 10px;">{date}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Double Border": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="padding:5px; background-color:#ffce00;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="background-color:#000000; padding:5px;">
                            <table cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#ffffff;">
                                <tr>
                                    <td style="padding:25px 30px;">
                                        <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                                                    <span class="subtitle" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; margin-top:8px; display:block;">{subtitle}</span>
                                                </td>
                                                <td align="right" style="vertical-align:top; text-align:right; padding-left:20px;" width="100">
                                                    <span class="date" style="display:inline-block; background-color:#000000; color:#ffffff; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; padding:5px 10px;">{date}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Corner Accent": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#ffffff; padding:0px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td style="padding:0;">
                            <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td width="80" style="background-color:#ffce00; width:80px; height:80px;"></td>
                                    <td style="border-top:5px solid #000000;">
                                        <span class="title" style="font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:34px; line-height:38px; letter-spacing:-1px; font-weight:bold; display:block; padding:20px 30px 0 15px;">{title}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:0 0 10px 10px; background-color:#ffffff;">
                                        <span class="date" style="font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; color:#666666; display:block; transform:rotate(-90deg); transform-origin:left top;">{date}</span>
                                    </td>
                                    <td style="padding:0 30px 15px 15px;">
                                        <span class="subtitle" style="font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; color:#333333; display:block;">{subtitle}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="background-color:#000000; height:2px;"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """,
    
    "Stacked Elements": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#000000; padding:20px 30px 5px 30px;">
                <span class="title" style="color:#ffffff; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:38px; line-height:42px; letter-spacing:-1px; font-weight:bold; display:block; text-align:center;">{title}</span>
            </td>
        </tr>
        <tr>
            <td style="background-color:#ffce00; padding:8px 30px; text-align:center;">
                <span class="subtitle" style="color:#000000; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:20px; font-weight:bold; display:block;">{subtitle}</span>
            </td>
        </tr>
        <tr>
            <td style="background-color:#f5f5f5; padding:6px 30px; text-align:right; border-bottom:2px solid #000000;">
                <span class="date" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; display:block;">{date}</span>
            </td>
        </tr>
    </table>
    """,
    
    "Executive Style": """
    <table cellspacing="0" cellpadding="0" border="0" width="{width}" align="center" class="content-width">
        <tr>
            <td style="background-color:#ffffff; padding:0px;">
                <table cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                        <td width="10" style="width:10px; background-color:#ffce00;">&nbsp;</td>
                        <td style="padding:25px 30px;">
                            <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="border-bottom:1px solid #dddddd; padding-bottom:12px;">
                                                    <span class="date" style="color:#666666; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:14px; line-height:18px; display:block; text-transform:uppercase;">{date}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding:15px 0 10px 0;">
                                                    <span class="title" style="color:#000000; font-family:'BLK Fort Extrabold','FortExtraBold','BLK Fort', 'Arial', Arial, sans-serif; font-size:36px; line-height:40px; letter-spacing:-1px; font-weight:bold; display:block;">{title}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding-bottom:5px;">
                                                    <span class="subtitle" style="color:#333333; font-family:'FortBook', 'BLK Fort', 'Arial', Arial, sans-serif; font-size:16px; line-height:22px; display:block; font-style:italic;">{subtitle}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="border-bottom:2px solid #000000;">&nbsp;</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """
}

COLOR_BANNER_TEMPLATES = {
    "blue": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #e6f2ff; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #0168b1;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #0168b1; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "green": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #F0F7F0; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #2C8B44;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #1A5D2B; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "purple": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #F5F0FF; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #673AB7;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #4A148C; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "corporate": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #1D2951; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #D74B4B;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #FFFFFF; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "red": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #FFEBEE; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #D32F2F;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #B71C1C; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "teal": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E0F2F1; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #00897B;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #004D40; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "amber": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #FFF8E1; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #FFB300;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #FF6F00; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "indigo": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E8EAF6; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #3949AB;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #1A237E; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "cyan": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #E0F7FA; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #00ACC1;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #006064; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """,
    "brown": """
    <div class="banner" style="width: 800px; height: 250px; background-color: #EFEBE9; display: flex; align-items: center; justify-content: center; border-bottom: 2px solid #795548;">
        <div class="title" style="font-family: Arial, sans-serif; font-size: 38px; font-weight: bold; color: #3E2723; margin-left: 20px;">
            Skywalker Newsletter
        </div>
    </div>
    """
}

DEFAULT_BANNER_TEXTS = {
    'classic_title': 'BlackRock Daily News',
    'classic_subtitle': 'Market Updates & Investment Insights',
    'classic_date': 'April 5, 2025',
    
    'modern_title': 'BlackRock Insights',
    'modern_subtitle': 'The latest news and analysis for investors',
    'modern_date': 'April 5, 2025',
    
    'accent_title': 'Daily Market Report',
    'accent_subtitle': 'Analysis, insights, and key developments',
    'accent_date': 'April 5, 2025',
    
    'gradient_title': 'BlackRock Newsletter',
    'gradient_subtitle': 'Weekly Market Updates & Analysis',
    'gradient_date': 'April 2025 Edition',
    
    'minimalist_title': 'BlackRock News',
    'minimalist_subtitle': 'Market insights and investment perspectives',
    'minimalist_date': 'April 5, 2025',
    
    'two_column_title': 'BlackRock Daily',
    'two_column_subtitle': 'Your comprehensive source for market news',
    'two_column_date': 'April 5, 2025',
    
    'bold_title': 'BLACKROCK INSIGHTS',
    'bold_subtitle': 'Financial News & Market Analysis',
    'bold_date': 'April 5, 2025',
    
    'split_title': 'BlackRock Market Report',
    'split_subtitle': 'Investment insights from our global experts',
    'split_date': 'April 5, 2025',
    
    'boxed_title': 'BlackRock Market Insights',
    'boxed_subtitle': 'Weekly insights from our global investment team',
    'boxed_date': 'April 5, 2025',
    
    'double_border_title': 'The Daily Brief',
    'double_border_subtitle': 'Key market updates and investment perspectives',
    'double_border_date': 'April 2025 Edition',
    
    'corner_title': 'BlackRock Investment Outlook',
    'corner_subtitle': 'Strategic insights and market analysis for investors',
    'corner_date': 'April 5, 2025',
    
    'stacked_title': 'BLACKROCK DAILY',
    'stacked_subtitle': 'Market Intelligence for Informed Decisions',
    'stacked_date': 'Saturday, April 5, 2025',
    
    'executive_title': 'BlackRock Executive Summary',
    'executive_subtitle': 'Key insights and analysis from our research team',
    'executive_date': 'April 5, 2025',
    
    # Legacy values (retained for compatibility)
    'corporate_top': 'BlackRock',
    'corporate_middle': 'BlackRock Daily News',
    'gips_brand': 'Global Infrastructure Partners',
    'gips_subtitle': 'a part of BlackRock',
    'gips_headline': 'BGIF EMEA + Asia Weekly News',
    'modern_brand': 'BlackRock Insights',
    'modern_date': 'Weekly Digest',
    'modern_tagline': 'Market Analysis & Investment Strategy',
    'gradient_edition': 'March 2025 Edition',
    'minimalist_title': 'Minimalist Newsletter',
    'minimalist_subtitle': 'Clean design for modern communications',
    'minimalist_date': 'March 2025',
    'split_brand': 'Split Design',
    'split_tagline': 'Distinctive newsletters that stand out',
    'split_description': 'Analysis and insights for financial professionals',
    'bordered_title': 'Bordered Newsletter Design',
    'bordered_subtitle': 'Elegant framing for your important communications',
    'geometric_title': 'Geometric Design',
    'geometric_subtitle': 'Modern patterns for creative communications',
    'wave_title': 'Wave Design Newsletter',
    'wave_subtitle': 'Flowing information with style',
    'wave_date': 'March 2025',
    'boxed_badge': 'EXCLUSIVE',
    'skywalker_title': 'Skywalker Newsletter',
    'skywalker_subtitle': 'Latest updates from across the galaxy',
    'skywalker_date': 'April 2025'
}

# --------------------------------------------------------------------------------
# Loading the base banner HTML
# --------------------------------------------------------------------------------

def load_banner_html(banner_type, content_width=800):
    """
    Load the banner HTML content for a given banner type.
    
    Returns either a template from BANNER_HTML_TEMPLATES or
    reads from BANNER_FILENAMES. Falls back to "BlackRock Classic" if not found.
    """
    print(f"[DEBUG] load_banner_html() called with banner_type='{banner_type}', content_width={content_width}")
    
    # If banner_type is in BANNER_HTML_TEMPLATES (dictionary in memory)
    if banner_type in BANNER_HTML_TEMPLATES:
        print("[DEBUG] Banner found in BANNER_HTML_TEMPLATES.")
        template = BANNER_HTML_TEMPLATES[banner_type]
        filled_template = template.replace("{width}", str(content_width))
        print(f"[DEBUG] Template length (post-width-replacement) = {len(filled_template)}")
        return filled_template
    
    # If not, but is in BANNER_FILENAMES (HTML file on disk)
    elif banner_type in BANNER_FILENAMES:
        print("[DEBUG] Banner found in BANNER_FILENAMES, reading from file.")
        filename = BANNER_FILENAMES[banner_type]
        template_path = os.path.join("templates", "banners", filename)
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('{width}', str(content_width))
            print(f"[DEBUG] Loaded from file: {filename}, length = {len(content)}")
            return content
        else:
            print(f"[WARNING] Banner file '{template_path}' not found. Falling back to BlackRock Classic.")
    
    else:
        print("[DEBUG] banner_type not recognized. Falling back to 'BlackRock Classic'.")
    
    # Fallback to BlackRock Classic
    fallback_template = BANNER_HTML_TEMPLATES["BlackRock Classic"]
    fallback_filled = fallback_template.replace("{width}", str(content_width))
    print(f"[DEBUG] Fallback (BlackRock Classic) length = {len(fallback_filled)}")
    return fallback_filled

# --------------------------------------------------------------------------------
# Modify banner HTML by injecting user text
# --------------------------------------------------------------------------------

def get_modified_banner_html(banner_type, banner_text, content_width=800):
    """
    Modifies banner HTML based on the banner type and user input text.
    
    Returns a string of HTML with placeholders replaced (title, subtitle, date, etc.)
    """
    print(f"\n[DEBUG] get_modified_banner_html() -> banner_type='{banner_type}', content_width={content_width}")
    # Load the original banner HTML
    html_content = load_banner_html(banner_type, content_width)
    print(f"[DEBUG] Base banner HTML loaded. Length = {len(html_content)}")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    found_title = soup.select_one('.title')
    found_subtitle = soup.select_one('.subtitle')
    found_date = soup.select_one('.date')
    
    print(f"[DEBUG] Found .title? {'Yes' if found_title else 'No'}")
    print(f"[DEBUG] Found .subtitle? {'Yes' if found_subtitle else 'No'}")
    print(f"[DEBUG] Found .date? {'Yes' if found_date else 'No'}")
    
    # Update the content based on banner type
    if banner_type == "BlackRock Classic":
        if found_title:
            found_title.string = banner_text.get('classic_title', DEFAULT_BANNER_TEXTS['classic_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('classic_subtitle', DEFAULT_BANNER_TEXTS['classic_subtitle'])
        if found_date:
            found_date.string = banner_text.get('classic_date', DEFAULT_BANNER_TEXTS['classic_date'])
    
    elif banner_type == "BlackRock Modern":
        if found_title:
            found_title.string = banner_text.get('modern_title', DEFAULT_BANNER_TEXTS['modern_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('modern_subtitle', DEFAULT_BANNER_TEXTS['modern_subtitle'])
        if found_date:
            found_date.string = banner_text.get('modern_date', DEFAULT_BANNER_TEXTS['modern_date'])
    
    elif banner_type == "Yellow Accent":
        if found_title:
            found_title.string = banner_text.get('accent_title', DEFAULT_BANNER_TEXTS['accent_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('accent_subtitle', DEFAULT_BANNER_TEXTS['accent_subtitle'])
        if found_date:
            found_date.string = banner_text.get('accent_date', DEFAULT_BANNER_TEXTS['accent_date'])
    
    elif banner_type == "Gradient Header":
        if found_title:
            found_title.string = banner_text.get('gradient_title', DEFAULT_BANNER_TEXTS['gradient_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('gradient_subtitle', DEFAULT_BANNER_TEXTS['gradient_subtitle'])
        if found_date:
            found_date.string = banner_text.get('gradient_date', DEFAULT_BANNER_TEXTS['gradient_date'])
    
    elif banner_type == "Minimalist":
        if found_title:
            found_title.string = banner_text.get('minimalist_title', DEFAULT_BANNER_TEXTS['minimalist_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('minimalist_subtitle', DEFAULT_BANNER_TEXTS['minimalist_subtitle'])
        if found_date:
            found_date.string = banner_text.get('minimalist_date', DEFAULT_BANNER_TEXTS['minimalist_date'])
    
    elif banner_type == "Two-Column":
        if found_title:
            found_title.string = banner_text.get('two_column_title', DEFAULT_BANNER_TEXTS['two_column_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('two_column_subtitle', DEFAULT_BANNER_TEXTS['two_column_subtitle'])
        if found_date:
            found_date.string = banner_text.get('two_column_date', DEFAULT_BANNER_TEXTS['two_column_date'])
    
    elif banner_type == "Bold Header":
        if found_title:
            found_title.string = banner_text.get('bold_title', DEFAULT_BANNER_TEXTS['bold_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('bold_subtitle', DEFAULT_BANNER_TEXTS['bold_subtitle'])
        if found_date:
            found_date.string = banner_text.get('bold_date', DEFAULT_BANNER_TEXTS['bold_date'])
    
    elif banner_type == "Split Design":
        if found_title:
            found_title.string = banner_text.get('split_title', DEFAULT_BANNER_TEXTS['split_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('split_subtitle', DEFAULT_BANNER_TEXTS['split_subtitle'])
        if found_date:
            found_date.string = banner_text.get('split_date', DEFAULT_BANNER_TEXTS['split_date'])
    
    elif banner_type == "Boxed Design":
        if found_title:
            found_title.string = banner_text.get('boxed_title', DEFAULT_BANNER_TEXTS['boxed_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('boxed_subtitle', DEFAULT_BANNER_TEXTS['boxed_subtitle'])
        if found_date:
            found_date.string = banner_text.get('boxed_date', DEFAULT_BANNER_TEXTS['boxed_date'])
    
    elif banner_type == "Double Border":
        if found_title:
            found_title.string = banner_text.get('double_border_title', DEFAULT_BANNER_TEXTS['double_border_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('double_border_subtitle', DEFAULT_BANNER_TEXTS['double_border_subtitle'])
        if found_date:
            found_date.string = banner_text.get('double_border_date', DEFAULT_BANNER_TEXTS['double_border_date'])
    
    elif banner_type == "Corner Accent":
        if found_title:
            found_title.string = banner_text.get('corner_title', DEFAULT_BANNER_TEXTS['corner_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('corner_subtitle', DEFAULT_BANNER_TEXTS['corner_subtitle'])
        if found_date:
            found_date.string = banner_text.get('corner_date', DEFAULT_BANNER_TEXTS['corner_date'])
    
    elif banner_type == "Stacked Elements":
        if found_title:
            found_title.string = banner_text.get('stacked_title', DEFAULT_BANNER_TEXTS['stacked_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('stacked_subtitle', DEFAULT_BANNER_TEXTS['stacked_subtitle'])
        if found_date:
            found_date.string = banner_text.get('stacked_date', DEFAULT_BANNER_TEXTS['stacked_date'])
    
    elif banner_type == "Executive Style":
        if found_title:
            found_title.string = banner_text.get('executive_title', DEFAULT_BANNER_TEXTS['executive_title'])
        if found_subtitle:
            found_subtitle.string = banner_text.get('executive_subtitle', DEFAULT_BANNER_TEXTS['executive_subtitle'])
        if found_date:
            found_date.string = banner_text.get('executive_date', DEFAULT_BANNER_TEXTS['executive_date'])
    
    elif banner_type == "BlackRock Corporate (Default)":
        # Legacy placeholders
        pass
    
    elif banner_type == "GIPS Infrastructure":
        # Legacy placeholders
        pass
    
    final_html = str(soup)
    final_length = len(final_html)
    print(f"[DEBUG] Final banner HTML length after substitution: {final_length}")
    
    return final_html

# --------------------------------------------------------------------------------
# Extract banner from custom HTML
# --------------------------------------------------------------------------------

def extract_banner_from_html(html_file_or_content, content_width=800):
    """
    Extract banner HTML from an uploaded HTML file, file path, or HTML content string
    and adjust its width. Returns (banner_html, style_content).
    """
    if html_file_or_content is None:
        return None, None
    
    print(f"[DEBUG] extract_banner_from_html() called. Content type: {type(html_file_or_content)}")
    
    try:
        # Determine what type of input we have
        if isinstance(html_file_or_content, str):
            if html_file_or_content.strip().startswith('<!DOCTYPE') or html_file_or_content.strip().startswith('<html'):
                content = html_file_or_content
            elif os.path.exists(html_file_or_content):
                with open(html_file_or_content, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = html_file_or_content
        else:
            # This is an uploaded file
            try:
                content = html_file_or_content.getvalue().decode('utf-8')
            except AttributeError:
                content = str(html_file_or_content)
        
        soup = BeautifulSoup(content, 'html.parser')
        
        style_content = ""
        style_tags = soup.find_all('style')
        for style in style_tags:
            if style.string:
                style_content += style.string
        
        # Try to find <div class="banner">
        banner_div = soup.select_one('.banner')
        
        if banner_div:
            banner_html = str(banner_div)
        elif soup.body and soup.body.div:
            banner_html = str(soup.body.div)
        else:
            # Last fallback: regex search for <div class="banner"
            if '<div class="banner"' in content:
                banner_match = re.search(r'<div class="banner".*?>(.*?</div>)\s*</div>', content, re.DOTALL)
                if banner_match:
                    banner_html = f'<div class="banner">{banner_match.group(1)}</div>'
                else:
                    banner_html = None
            else:
                banner_html = None
        
        if not banner_html:
            print("[DEBUG] No banner found in uploaded HTML.")
            return None, None
        
        # Standardize px usage
        style_content = re.sub(r'(\d+)px', r'\1px', style_content)
        
        # Replace banner width in CSS
        style_content = re.sub(
            r'(\.banner\s*\{[^}]*?)width\s*:\s*\d+px',
            f'\\1width: {content_width}px',
            style_content
        )
        
        # Optionally add a media query for responsiveness
        if '@media' not in style_content:
            style_content += f"""
            @media only screen and (max-width: 480px) {{
                .banner {{
                    width: 100% !important;
                    max-width: 100% !important;
                }}
            }}
            """
        
        # Adjust the inline widths in the banner_html
        banner_html = re.sub(r'width\s*=\s*["\']\d+["\']', f'width="{content_width}"', banner_html)
        banner_html = re.sub(
            r'style\s*=\s*(["\'])(.*?)width\s*:\s*\d+px(.*?)(["\'])',
            f'style=\\1\\2width: {content_width}px\\3\\4',
            banner_html,
            flags=re.DOTALL
        )
        
        # If class="banner" exists but no 'content-width', add it
        if 'class="banner"' in banner_html and 'content-width' not in banner_html:
            banner_html = banner_html.replace('class="banner"', 'class="banner content-width"')
        
        print(f"[DEBUG] extract_banner_from_html() -> final banner_html length={len(banner_html)}")
        return banner_html, style_content
    
    except Exception as e:
        print(f"[ERROR] extract_banner_from_html: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None, None

# --------------------------------------------------------------------------------
# Inject banner into the newsletter HTML
# --------------------------------------------------------------------------------

def inject_banner_into_newsletter(html_content, banner_html, banner_styles=None, content_width=800):
    """
    Injects the custom banner HTML directly into the newsletter HTML.
    """
    print("\n===== BANNER INJECTION DEBUG =====")
    print(f"BANNER HTML LENGTH: {len(banner_html) if banner_html else 0}")
    print(f"NEWSLETTER HTML LENGTH: {len(html_content) if html_content else 0}")
    print(f"NEWSLETTER CONTAINS BANNER-CONTAINER: {'banner-container' in html_content if html_content else False}")
    print(f"NEWSLETTER CONTAINS BANNER HEADER COMMENT: {'<!-- Banner header -->' in html_content if html_content else False}")
    print("===================================\n")
    
    if not banner_html or not html_content:
        print("Missing banner or HTML content")
        return html_content
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1) Try table.banner-container
    existing_banner = soup.select_one('table.banner-container')
    if existing_banner:
        print("Found banner via table.banner-container")
    
    # 2) If not found, search for comment marker
    if not existing_banner:
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!-- Banner header -->' in text):
            existing_banner = comment.find_next('table')
            if existing_banner:
                print("Found banner via comment marker")
                break
    
    # 3) If still not found, look for BlackRock logo
    if not existing_banner:
        img_tag = soup.find('img', alt=lambda x: x and ('BlackRock' in x if x else False))
        if img_tag:
            existing_banner = img_tag.find_parent('table')
            if existing_banner:
                print("Found banner via BlackRock logo")
    
    # 4) Fallback: second table in the body
    if not existing_banner:
        tables = soup.select('body table')
        if len(tables) > 2:
            existing_banner = tables[1]
            print("Using fallback banner detection - second table in body")
    
    print(f"Injecting banner: length of banner_html = {len(banner_html)}")
    
    if existing_banner:
        print(f"Found existing banner of type: {existing_banner.name}, class: {existing_banner.get('class')}")
        new_banner_html = f"<!-- Banner header -->\n{banner_html}"
        new_banner = BeautifulSoup(new_banner_html, 'html.parser')
        
        existing_banner.replace_with(new_banner)
        
        # If we have banner styles, append to <head>
        if banner_styles:
            head = soup.head
            if head:
                style_tag = soup.new_tag('style')
                style_tag['type'] = 'text/css'
                style_tag.string = f"\n/* Custom Banner Styles */\n{banner_styles}\n"
                head.append(style_tag)
        
        print("Successfully replaced banner!")
    else:
        print("FAILED to find banner in template! Inserting at the beginning of <body> as last resort.")
        body = soup.body
        if body and body.contents:
            first_child = next((c for c in body.contents if c.name), None)
            if first_child:
                new_banner = BeautifulSoup(f"<!-- Banner header -->\n{banner_html}", 'html.parser')
                first_child.insert_before(new_banner)
                print("Inserted banner at beginning of body.")
    
    return str(soup)

def update_html_dimensions(html_content, width):
    """
    Updates all occurrences of 'width:800px' and 'width="800"' in HTML content,
    adjusting other references as well.
    """
    html_content = re.sub(r'width:800px', f'width:{width}px', html_content)
    html_content = re.sub(r'width="800"', f'width="{width}"', html_content)
    html_content = re.sub(r'width:800px !important;', f'width:{width}px !important;', html_content)
    html_content = re.sub(r'max-width:800px !important;', f'max-width:{width}px !important;', html_content)
    html_content = re.sub(
        r'style="(.*?)width:800px(.*?)"',
        f'style="\\1width:{width}px\\2"',
        html_content
    )
    html_content = re.sub(
        r'style="background-color:#ffffff; width:800px;"',
        f'style="background-color:#ffffff; width:{width}px;"',
        html_content
    )
    return html_content