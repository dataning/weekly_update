import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

# Constants
HIGHCHARTS_CDN = {
    'base': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/highcharts.min.js',
    'xrange': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/xrange.js',
    'exporting': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/exporting.js'
}

CSS_STYLES = """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #1E293B;
            --secondary-color: #64748B;
            --shadow-color: rgba(30, 41, 59, 0.1);
        }
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .metric-container {
            border-radius: 10px;
            padding: 20px;
            box-shadow: 2px 2px 5px var(--shadow-color);
            margin-bottom: 10px;
        }
        
        .metric-container.centered {
            text-align: center;
        }
        
        .metric-container.box1 {
            background-color: #EFF6FF;
        }
        
        .metric-container.box2 {
            background-color: #F0FDF4;
        }
        
        .metric-container.box3 {
            background-color: #FEF2F2;
        }
        
        .metric-value {
            font-size: 16px;
            font-weight: 600;
            margin: 10px 0;
            line-height: 1.5;
            color: #000000;
        }

        .metric-value a {
            color: inherit;
            text-decoration: none;
            border-bottom: 1px solid currentColor;
            transition: opacity 0.2s ease;
        }

        .metric-value a:hover {
            opacity: 0.8;
        }
        
        .metric-label {
            font-size: 12px;
            font-weight: 500;
            color: var(--secondary-color);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .citation {
            font-size: 10px;
            color: var(--secondary-color);
            font-style: italic;
            margin-top: 5px;
        }
        
        .stTitle {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            color: var(--primary-color) !important;
        }

        .row-spacer {
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
    </style>
"""

@dataclass
class MetricConfig:
    """Configuration for metric display"""
    label: str
    value: str
    source: str
    box_class: str = "box1"

class ExpanderState:
    """Manages the state of expanders"""
    def __init__(self):
        if 'expander_state' not in st.session_state:
            st.session_state.expander_state = False

    def toggle(self):
        st.session_state.expander_state = not st.session_state.expander_state

    @property
    def is_expanded(self) -> bool:
        return st.session_state.expander_state

def safe_get_value(df: pd.DataFrame, column: str, default: str = "Not Available") -> str:
    """Safely retrieve a value from DataFrame.
    
    :param df: Input DataFrame containing the data
    :type df: pd.DataFrame
    :param column: Name of the column to retrieve value from
    :type column: str
    :param default: Default value to return if column doesn't exist or value is null
    :type default: str
    :return: Value from DataFrame or default value
    :rtype: str
    :raises: No exceptions (handles all internally)
    """
    try:
        value = df[column].iloc[0]
        return str(value) if pd.notna(value) else default
    except (KeyError, IndexError):
        return default

def load_css():
    """Load custom CSS styles"""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)

def get_schedule_type(df: pd.DataFrame) -> str:
    """Get the name from the last column in the DataFrame"""
    try:
        if df.empty or len(df.columns) == 0:
            return "Not Available"
        
        last_col = df.columns[-1]
        return last_col.split('_')[-1] if '_' in last_col else last_col
    except Exception:
        return "Not Available"

def create_highcharts_container(chart_config: Dict[str, Any], container_id: str) -> str:
    """Create HTML container for Highcharts visualization.
    
    :param chart_config: Highcharts configuration dictionary
    :type chart_config: Dict[str, Any]
    :param container_id: Unique identifier for the chart container
    :type container_id: str
    :return: HTML string containing the chart container and scripts
    :rtype: str
    :raises: No exceptions (handles all internally)
    """
    return f"""
        <div id="{container_id}" style="min-width: 200px;"></div>
        <script src="{HIGHCHARTS_CDN['base']}"></script>
        <script src="{HIGHCHARTS_CDN['xrange']}"></script>
        <script src="{HIGHCHARTS_CDN['exporting']}"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                try {{
                    Highcharts.chart('{container_id}', {json.dumps(chart_config, default=str)});
                }} catch (e) {{
                    document.getElementById('{container_id}').innerHTML = 
                        '<div style="color: red;">Error creating chart: ' + e.message + '</div>';
                }}
            }});
        </script>
    """

def create_filing_calendar_strip(df: pd.DataFrame, container_id: Optional[str] = None) -> str:
    """Create a simplified calendar strip visualization of filing dates using Highcharts.
    
    :param df: DataFrame containing filing dates in 'Filing_Date' column
    :type df: pd.DataFrame
    :param container_id: Optional custom container ID for the chart
    :type container_id: Optional[str]
    :return: HTML string containing the calendar visualization
    :rtype: str
    :raises: No exceptions (handles errors and returns error message as HTML)
    
    The function creates a horizontal bar chart showing filing dates across years.
    Each bar represents a filing date, with color intensity based on the day of the month.
    """
    if container_id is None:
        container_id = f"filing-calendar-{pd.util.hash_pandas_object(df).sum()}"

    filing_dates = process_filing_dates(df)
    if not filing_dates:
        return "<div>No filing dates available</div>"

    chart_data = prepare_calendar_data(filing_dates)
    chart_config = create_calendar_config(chart_data)
    
    return create_highcharts_container(chart_config, container_id)

def process_filing_dates(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process filing dates from DataFrame into a structured format.
    
    :param df: DataFrame containing 'Filing_Date' column with filing dates
    :type df: pd.DataFrame
    :return: List of dictionaries containing structured date information
    :rtype: List[Dict[str, Any]]
    :raises: No exceptions (handles errors with warnings)
    
    Each dictionary in the returned list contains:
        - year: The filing year
        - month: The filing month (1-12)
        - day: The day of the month
        - date: Formatted date string (YYYY-MM-DD)
    """
    filing_dates = []
    for _, date_str in df['Filing_Date'].items():
        try:
            if pd.notna(date_str):
                date = pd.to_datetime(date_str)
                filing_dates.append({
                    'year': date.year,
                    'month': date.month,
                    'day': date.day,
                    'date': date.strftime('%Y-%m-%d')
                })
        except (ValueError, TypeError) as e:
            st.warning(f"Error processing date {date_str}: {str(e)}")
    return sorted(filing_dates, key=lambda x: x['year'])

def prepare_calendar_data(filing_dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare filing dates data for calendar visualization.
    
    :param filing_dates: List of processed filing dates
    :type filing_dates: List[Dict[str, Any]]
    :return: List of formatted data points for Highcharts visualization
    :rtype: List[Dict[str, Any]]
    
    Each input dictionary should contain:
        - year: The filing year
        - month: The filing month
        - day: The day of the month
        - date: Formatted date string
    
    Returns data formatted for Highcharts visualization with calculated
    color intensities and proper date formatting.
    """
    all_years = list(range(
        max(d['year'] for d in filing_dates),
        min(d['year'] for d in filing_dates) - 1,
        -1
    ))
    
    return [create_year_data(year, filing_dates) for year in all_years]

def create_year_data(year: int, filing_dates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create visualization data for a specific year.
    
    :param year: The year to create data for
    :type year: int
    :param filing_dates: List of all available filing dates
    :type filing_dates: List[Dict[str, Any]]
    :return: Dictionary containing formatted data for the specified year
    :rtype: Dict[str, Any]
    
    Returns a dictionary containing:
        - name: Year as string
        - y: Day of month (0 if no filing)
        - color: Calculated color based on day
        - date: Full date string or None
        - month: Month name or None
    """
    filing = next((d for d in filing_dates if d['year'] == year), None)
    if filing:
        intensity = (filing['day'] - 1) / 31
        return {
            'name': str(year),
            'y': filing['day'],
            'color': f'rgba(79, 70, 229, {intensity})',
            'date': filing['date'],
            'month': get_month_name(filing['month'])
        }
    return {
        'name': str(year),
        'y': 0,
        'color': '#e5e7eb',
        'date': None,
        'month': None
    }

def get_month_name(month: int) -> str:
    """Get month name from month number"""
    return pd.Timestamp(year=2000, month=month, day=1).strftime('%B')

def create_calendar_config(chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create Highcharts configuration for calendar visualization"""
    return {
        'chart': {
            'type': 'bar',
            'height': max(200, len(chart_data) * 30 + 50),
            'style': {'fontFamily': '-apple-system, system-ui, sans-serif'}
        },
        'title': {'text': None},
        'xAxis': {
            'categories': [d['name'] for d in chart_data],
            'labels': {'style': {'fontSize': '12px'}}
        },
        'yAxis': {
            'min': 0,
            'max': 31,
            'title': {'text': 'Day in Month'},
            'labels': {'format': '{value}'}
        },
        'tooltip': {
            'useHTML': True,
            'headerFormat': '',
            'pointFormat': '<b>{point.name}</b><br/>{point.month} {point.y}, {point.name}'
        },
        'plotOptions': {
            'bar': {
                'horizontal': True,
                'dataLabels': {
                    'enabled': True,
                    'format': '{y}'
                }
            },
            'series': {
                'pointWidth': 20,
                'animation': False
            }
        },
        'legend': {'enabled': False},
        'credits': {'enabled': False},
        'series': [{
            'name': 'Filing Date',
            'data': chart_data
        }]
    }

def create_highcharts_timeline(df: pd.DataFrame, timeline_var: Optional[str] = None, container_id: Optional[str] = None) -> str:
    """Create a horizontal timeline visualization using Highcharts.
    
    :param df: DataFrame containing timeline data
    :type df: pd.DataFrame
    :param timeline_var: Column name for timeline variable, defaults to 'IRS990_PrincipalOfficerName'
    :type timeline_var: Optional[str]
    :param container_id: Custom container ID for the chart
    :type container_id: Optional[str]
    :return: HTML string containing the timeline visualization
    :rtype: str
    :raises ValueError: If required columns are missing from DataFrame
    
    The function creates an x-range chart showing timeline data across years.
    Each bar represents a continuous period for a specific entry in the timeline_var column.
    """
    timeline_var = timeline_var or 'IRS990_PrincipalOfficerName'
    container_id = container_id or f"{timeline_var.lower().replace('_', '-')}-timeline"

    if not {'year', timeline_var}.issubset(df.columns):
        return f"<div>Error: Missing required columns 'year' or '{timeline_var}'</div>"

    timeline_data = process_timeline_data(df, timeline_var)
    chart_config = create_timeline_config(timeline_data, df[timeline_var].dropna().unique())
    
    return create_highcharts_container(chart_config, container_id)

def process_timeline_data(df: pd.DataFrame, timeline_var: str) -> List[Dict[str, Any]]:
    """Process data for timeline visualization"""
    entries = sorted(df[timeline_var].dropna().unique())
    timeline_data = []

    for entry in entries:
        entry_years = sorted(df[df[timeline_var] == entry]['year'].dropna())
        ranges = create_year_ranges(entry_years)
        
        for start_year, end_year in ranges:
            timeline_data.append({
                'x': int(start_year),
                'x2': int(end_year) + 1,
                'y': list(entries).index(entry),
                'name': entry
            })
    
    return timeline_data

def create_year_ranges(years: List[Union[int, float]]) -> List[List[Union[int, float]]]:
    """Create consecutive year ranges from a list of years"""
    if not years:
        return []

    ranges = []
    range_start = years[0]
    prev_year = years[0]

    for year in years[1:]:
        if int(year) - int(prev_year) > 1:
            ranges.append([range_start, prev_year])
            range_start = year
        prev_year = year
    
    ranges.append([range_start, prev_year])
    return ranges

def create_timeline_config(timeline_data: List[Dict[str, Any]], categories: List[str]) -> Dict[str, Any]:
    """Create Highcharts configuration for timeline visualization"""
    return {
        'chart': {
            'type': 'xrange',
            'height': max(150, len(categories) * 30 + 50),
            'style': {'fontFamily': 'Inter, sans-serif'},
            'spacing': [10, 10, 10, 10]
        },
        'title': {
            'text': 'Timeline',
            'align': 'center',
            'style': {'fontSize': '14px', 'fontWeight': '500'},
            'margin': 5
        },
        'xAxis': {
            'type': 'linear',
            'title': {'text': ''},
            'labels': {'style': {'fontSize': '11px'}},
            'tickLength': 0
        },
        'yAxis': {
            'categories': list(categories),
            'title': {'text': ''},
            'labels': {'style': {'fontSize': '11px'}},
            'reversed': True,
            'tickLength': 0
        },
        'tooltip': {
            'formatter': 'function() { return "<b>" + this.point.name + "</b><br/>" + "Period: " + Math.floor(this.x) + " - " + Math.floor(this.x2 - 1); }'
        },
        'series': [{
            'name': 'Timeline',
            'borderColor': 'gray',
            'pointWidth': 15,
            'data': timeline_data,
            'colorByPoint': False,
            'color': '#4169E1',
            'dataLabels': {'enabled': False}
        }],
        'credits': {'enabled': False},
        'legend': {'enabled': False},
        'plotOptions': {'series': {'animation': False}}
    }

def display_metric(config: MetricConfig):
    """Display a metric container with consistent styling"""
    st.markdown(f"""
        <div class="metric-container {config.box_class}">
            <div class="metric-label">{config.label}</div>
            <div class="metric-value {config.box_class}">{config.value}</div>
            <div class="citation">Source: {config.source}</div>
        </div>
    """, unsafe_allow_html=True)

def display_profile(profile_df: pd.DataFrame, filtered_df: pd.DataFrame):
    """Display comprehensive organization profile with visualizations.
    
    :param profile_df: DataFrame containing organization profile data from IRS forms
    :type profile_df: pd.DataFrame
    :param filtered_df: DataFrame containing additional organization data
    :type filtered_df: pd.DataFrame
    :raises: No exceptions (handles errors with appropriate UI messages)
    """
    load_css()
    expander_state = ExpanderState()
    
    # Sidebar controls
    with st.sidebar:
        st.toggle('Show All Details', 
                 value=expander_state.is_expanded, 
                 key='expander_toggle')
        st.session_state.expander_state = st.session_state.expander_toggle

    # Header section - using filtered_df for organization name if available
    organization_name = (
        safe_get_value(filtered_df, 'name') 
        if not filtered_df.empty 
        else safe_get_value(profile_df, 'Filer_BusinessName_BusinessNameLine1Txt', "Organization Profile")
    )
    st.header(organization_name)

    # Load NTEE data from filtered_df 
    try:
        ntee_code = filtered_df['ntee_code_std'].iloc[0] if not filtered_df.empty else "Not Available"
        ntee_description = filtered_df['Description'].iloc[0] if not filtered_df.empty else ""
        ntee_definition = filtered_df['Definition'].iloc[0] if not filtered_df.empty else ""
    except Exception as e:
        st.error(f"Error loading NTEE data: {str(e)}")
        ntee_code = "Not Available"
        ntee_description = ""
        ntee_definition = ""

    # Basic information row
    col1, col2, col3 = st.columns([3, 3, 3])
    with col1:
        ein_value = filtered_df['ein'].iloc[0] if not filtered_df.empty else "Not Available"
        st.markdown(f"**EIN:** {ein_value}")

    with col2:
        ruling_date = (
            filtered_df['ruling'].iloc[0] 
            if not filtered_df.empty and 'ruling' in filtered_df.columns 
            else "Not Available"
        )
        st.markdown(f"**Since:** {ruling_date}")

    with col3:
        website_url = safe_get_value(profile_df, 'WebsiteAddressTxt')
        if website_url != "Not Available":
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'http://' + website_url
            website_display = website_url.replace('http://', '').replace('https://', '')
            st.markdown(f"**Website:** {website_display}")
        else:
            st.markdown("**Website:** Not Available")

        st.divider()

    # Mission and Address section
    col1, col2 = st.columns([5, 5])
    with col1:
        mission_desc = get_mission_description(profile_df, filtered_df)
        display_metric(MetricConfig(
            label="Mission",
            value=mission_desc,
            source="ActivityOrMissionDescription, MissionDescription fields",
            box_class="box1"
        ))

        with st.expander("See details about Mission", expanded=expander_state.is_expanded):
            st.write("**ActivityOrMissionDescription:** A brief description of the organization's activities or mission")
            st.write("**MissionDescription:** Detailed description of the organization's mission statement")
            st.write("### Raw Data")
            st.write(f"ActivityOrMissionDescription: {safe_get_value(profile_df, 'ActivityOrMissionDescription')}")
            st.write(f"MissionDescription: {safe_get_value(profile_df, 'MissionDescription')}")

    # Filing Information Row
    col1, col2, col3 = st.columns([3, 3, 4])
    with col1:
        filing_date = get_filing_date(profile_df)
        display_metric(MetricConfig(
            label="Filing Date",
            value=filing_date,
            source="Filing_Date field",
            box_class="box1"
        ))

        with st.expander("See details about Filing Date", expanded=expander_state.is_expanded):
            st.write("Timestamp when the return was filed")
            if 'Filing_Date' in profile_df.columns:
                highcharts_html = create_filing_calendar_strip(profile_df)
                st.components.v1.html(highcharts_html, height=350)

    with col2:
        principal_officer = safe_get_value(profile_df, 'PrincipalOfficerNm')
        display_metric(MetricConfig(
            label="Principal Officer",
            value=principal_officer,
            source="PrincipalOfficerNm field",
            box_class="box1"
        ))
        with st.expander("See details about Principal Officer", expanded=expander_state.is_expanded):
            st.write("Name of the organization's principal officer")
            if 'PrincipalOfficerNm' in profile_df.columns:
                highcharts_html = create_highcharts_timeline(profile_df, 'PrincipalOfficerNm')
                st.components.v1.html(highcharts_html, height=350)

    with col3:
        preparer_firm = safe_get_value(profile_df, 'PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt')
        display_metric(MetricConfig(
            label="Preparer Firm",
            value=preparer_firm,
            source="PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt field",
            box_class="box2"
        ))

        with st.expander("See details about Preparer Firm", expanded=expander_state.is_expanded):
            st.write("Name of the firm that prepared the tax return")
            if 'PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt' in profile_df.columns:
                # Create a copy of the DataFrame to avoid modifying the original
                chart_df = profile_df.copy()
                chart_df['PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt'] = (
                    chart_df['PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt'].str.upper()
                )
                highcharts_html = create_highcharts_timeline(
                    chart_df, 'PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt'
                )
            st.components.v1.html(highcharts_html, height=350)

    st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)

    # Organization Type and NTEE Row
    col1, col2, col3 = st.columns([3, 3, 4])
    with col1:
        schedule_type = get_schedule_type(profile_df)
        display_metric(MetricConfig(
            label="Organization Type",
            value=schedule_type,
            source="IRS990ScheduleA field",
            box_class="box2"
        ))

        with st.expander("See details about Organization Type", expanded=expander_state.is_expanded):
            st.markdown(f"**{schedule_type}** indicates:")
            explanation = get_organization_type_explanation(schedule_type)
            if explanation:
                st.info(explanation)
            st.markdown("---\n*Reference: IRS Form 990 Schedule A, Part I*")

    with col2:
        display_metric(MetricConfig(
            label="NTEE",
            value=ntee_code,
            source="National Taxonomy of Exempt Entities Code",
            box_class="box3"
        ))

        with st.expander("See details about NTEE", expanded=expander_state.is_expanded):
            st.write("**NTEE:** National Taxonomy of Exempt Entities - A classification system for nonprofit organizations")
            if ntee_description:
                st.write(f"**Description**: {ntee_description}")
            if ntee_definition:
                st.write(f"**Definition**: {ntee_definition}")

    with col3:
        address = (
            safe_get_value(filtered_df, 'address')
            if not filtered_df.empty and 'address' in filtered_df.columns
            else safe_get_value(profile_df, 'FullAddress')
        )
        display_metric(MetricConfig(
            label="Business Address",
            value=address,
            source="FullAddress field",
            box_class="box2"
        ))

        with st.expander("See details about Business Address", expanded=expander_state.is_expanded):
            st.write("**FullAddress:** Complete mailing address of the organization")
            if 'FullAddress' in profile_df.columns:
                highcharts_html = create_highcharts_timeline(profile_df, 'FullAddress')
                st.components.v1.html(highcharts_html, height=200)

    st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)

def get_mission_description(profile_df: pd.DataFrame, filtered_df: pd.DataFrame) -> str:
    """Extract and combine mission description fields from DataFrame.
    
    :param profile_df: DataFrame containing IRS form data
    :type profile_df: pd.DataFrame
    :param filtered_df: DataFrame containing additional organization data
    :type filtered_df: pd.DataFrame
    :return: Combined mission description or "Not Available"
    :rtype: str
    """
    # First try to get mission from filtered_df if available
    if not filtered_df.empty and 'mission_statement' in filtered_df.columns:
        mission = safe_get_value(filtered_df, 'mission_statement', "")
        if mission:
            return mission

    # Fall back to profile_df if no mission found in filtered_df
    activity = safe_get_value(profile_df, 'ActivityOrMissionDesc', "")
    mission = safe_get_value(profile_df, 'MissionDesc', "")
    combined = f"{activity} {mission}".strip()
    return combined or "Not Available"

def get_filing_date(df: pd.DataFrame) -> str:
    """Format filing date with proper error handling"""
    try:
        date_str = df['Filing_Date'].iloc[0]
        if pd.notna(date_str):
            return pd.to_datetime(date_str).strftime('%B %d, %Y')
    except (KeyError, IndexError, ValueError) as e:
        st.warning(f"Error processing filing date: {str(e)}")
    return "Not Available"

def get_organization_type_explanation(status: str) -> Optional[str]:
    """Get explanation text for a given charity status code"""
    status_lower = status.lower()
    
    if '170' in status_lower:
        if 'vi' in status_lower:
            return "An organization that normally receives a substantial part of its support from a governmental unit or from the general public."
        elif 'ix' in status_lower:
            return "An agricultural research organization operated in conjunction with a land-grant college or university or a non-land grant college of agriculture."
        elif 'iv' in status_lower:
            return "An organization operated for the benefit of a college or university owned or operated by a governmental unit."
        elif 'iii' in status_lower:
            return "A hospital or a cooperative hospital service organization."
        elif 'ii' in status_lower:
            return "A school. (Requires Schedule E of Form 990)"
        elif 'i' in status_lower:
            return "A church, convention of churches, or association of churches."
        elif 'v' in status_lower:
            return "A federal, state, or local government or governmental unit."
            
    elif '509' in status_lower:
        if '1' in status_lower:
            return "A publicly supported organization."
        elif '2' in status_lower:
            return "An organization that normally receives: (1) more than 33 1/3% of its support from contributions, membership fees, and related activities, and (2) no more than 33 1/3% of its support from investment income and unrelated business activities."
        elif '3' in status_lower:
            return "A supporting organization that benefits one or more publicly supported organizations."
        elif '4' in status_lower:
            return "An organization organized and operated exclusively to test for public safety."
            
    return None