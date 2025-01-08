import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class CompensationAnalyzer:
    """Handle compensation data analysis and calculations for a single organization"""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize the analyzer with compensation data"""
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['year'].unique()) if not self.df.empty else []
        
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the compensation dataframe"""
        try:
            df = df.copy()
            
            # Convert year to numeric
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            
            # Convert compensation columns to numeric
            comp_columns = ['base_compensation', 'bonus', 'other_compensation', 
                          'deferred_compensation', 'nontaxable_benefits', 'total_compensation']
            for col in comp_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Fill NaN values with 0 for compensation columns
            df[comp_columns] = df[comp_columns].fillna(0)
            
            return df.sort_values('year', ascending=True)
        except Exception as e:
            raise Exception(f"Error preprocessing data: {str(e)}")
    
    def get_yearly_aggregated_data(self) -> List[Dict[str, Any]]:
        """Get aggregated yearly compensation data"""
        if self.df.empty:
            return []
        
        comp_types = {
            'base_compensation': ('Base Compensation', '#4ECDC4'),
            'bonus': ('Bonus', '#FF6B6B'),
            'other_compensation': ('Other Compensation', '#FFD93D'),
            'deferred_compensation': ('Deferred Compensation', '#95D5B2'),
            'nontaxable_benefits': ('Nontaxable Benefits', '#C792DF')
        }

        series_data = []
        
        # Group by year and sum all compensation types
        yearly_sums = self.df.groupby('year')[list(comp_types.keys())].sum().reset_index()
        
        # Shift years back by 1 and format as fiscal years
        yearly_sums['year'] = yearly_sums['year'] - 1
        
        for comp_type, (name, color) in comp_types.items():
            if comp_type in yearly_sums.columns:
                data = []
                for _, row in yearly_sums.iterrows():
                    year_val = int(row['year']) if hasattr(row['year'], 'item') else row['year']
                    data.append({
                        'y': float(row[comp_type]),
                        'year': f"FY {year_val}"
                    })
                
                series_data.append({
                    'name': name,
                    'data': data,
                    'color': color
                })

        return series_data

class MultiCompensationAnalyzer:
    """Handle compensation analysis for multiple organizations"""
    
    CDN_URLS = {
        'base': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/highcharts.min.js',
        'exporting': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/exporting.js'
    }

    def __init__(self, data_dict: Dict[str, Dict], selected_eins: List[str]):
        """Initialize with multiple organizations' data"""
        self.data_dict = data_dict
        self.selected_eins = selected_eins
        self.org_names = self._get_org_names()
        self.analyzers = self._create_analyzers()
        self.all_years = self._get_all_years()
    
    def _get_org_names(self) -> Dict[str, str]:
        """Get organization names for each EIN"""
        org_names = {}
        for ein in self.selected_eins:
            if ein in self.data_dict:
                profile_df = self.data_dict[ein].get('profile', pd.DataFrame())
                if not profile_df.empty:
                    # Try DBA name first, then fall back to Filer name
                    if 'DoingBusinessAsName_BusinessNameLine1Txt' in profile_df.columns:
                        dba_name = profile_df['DoingBusinessAsName_BusinessNameLine1Txt'].iloc[0]
                        if pd.notna(dba_name):
                            org_names[ein] = dba_name
                            continue
                            
                    if 'Filer_BusinessName_BusinessNameLine1Txt' in profile_df.columns:
                        filer_name = profile_df['Filer_BusinessName_BusinessNameLine1Txt'].iloc[0]
                        if pd.notna(filer_name):
                            org_names[ein] = filer_name
                            continue
                
                # Fall back to EIN if no name is found
                org_names[ein] = ein
        return org_names

    def _create_analyzers(self) -> Dict[str, CompensationAnalyzer]:
        """Create individual analyzers for each EIN"""
        analyzers = {}
        for ein in self.selected_eins:
            if ein in self.data_dict and 'compensation' in self.data_dict[ein]:
                df = self.data_dict[ein]['compensation']
                if not df.empty:
                    analyzers[ein] = CompensationAnalyzer(df)
        return analyzers

    def _get_all_years(self) -> List[str]:
        """Get all unique years across all organizations"""
        years = set()
        for analyzer in self.analyzers.values():
            # First convert to int and shift back one year
            shifted_years = [int(year) - 1 if hasattr(year, 'item') else int(year) - 1 for year in analyzer.years]
            # Then format as fiscal years
            fiscal_years = [f"FY {year}" for year in shifted_years]
            years.update(fiscal_years)
        return sorted(list(years))

    def create_multi_org_config(self) -> Dict:
        """Create yearly aggregated compensation chart for all organizations"""
        all_series_data = []

        for ein in self.selected_eins:
            if ein in self.analyzers:
                analyzer = self.analyzers[ein]
                series_data = analyzer.get_yearly_aggregated_data()
                
                # Modify series names to include organization name
                org_name = self.org_names[ein]
                for series in series_data:
                    series['name'] = f"{org_name} - {series['name']}"
                    series['stack'] = org_name  # Stack by organization name
                
                all_series_data.extend(series_data)

        chart_config = {
            'chart': {
                'type': 'column',
                'height': 600,
                'style': {'fontFamily': 'Inter, sans-serif'},
            },
            'title': {
                'text': 'Yearly Aggregated Compensation by Organization',
                'align': 'center',
                'style': {'fontSize': '16px', 'fontWeight': '500'},
            },
            'xAxis': {
                'categories': self.all_years,
                'title': {'text': 'Year'},
                'labels': {
                    'style': {'fontSize': '12px'},
                    'rotation': 0
                },
            },
            'yAxis': {
                'title': {'text': 'Total Compensation ($)'},
                'labels': {'format': '${value:,.0f}'},
                'stackLabels': {
                    'enabled': True,
                    'style': {
                        'fontWeight': 'bold'
                    }
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valuePrefix': '$',
                'valueDecimals': 0
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4,
                    'groupPadding': 0.1
                }
            },
            'series': all_series_data,
            'credits': {'enabled': False},
            'legend': {
                'align': 'center',
                'verticalAlign': 'bottom',
                'layout': 'horizontal',
                'floating': False,
            }
        }
        
        return chart_config

    def create_multi_org_charts(self) -> str:
        """Create HTML for all charts"""
        chart_config = self.create_multi_org_config()
        
        return f"""
        <div id="multi-org-compensation-chart" style="width: 100%; min-height: 600px;"></div>
        
        <script src="{self.CDN_URLS['base']}"></script>
        <script src="{self.CDN_URLS['exporting']}"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const options = {json.dumps(chart_config)};
                
                // Add formatters after JSON parsing
                options.yAxis.stackLabels.formatter = function() {{
                    return '$' + (this.total / 1000000).toFixed(1) + 'M';
                }};
                
                options.tooltip.formatter = function() {{
                    let s = '<div style="font-size: 12px;">';
                    s += '<div style="font-size: 14px; font-weight: bold; margin-bottom: 8px;">' + this.x + '</div>';
                    
                    // Group points by organization
                    let orgGroups = {{}};
                    let orgTotal = {{}};
                    
                    this.points.forEach(function(point) {{
                        let org = point.series.userOptions.stack;
                        if (!orgGroups[org]) {{
                            orgGroups[org] = [];
                        }}
                        if (!orgTotal[org]) {{
                            orgTotal[org] = 0;
                        }}
                        orgGroups[org].push(point);
                        orgTotal[org] += point.y;
                    }});
                    
                    // Display each organization's breakdown
                    Object.entries(orgGroups).forEach(([org, points], index) => {{
                        if (index > 0) {{
                            s += '<div style="margin: 8px 0; border-top: 1px solid #ddd;"></div>';
                        }}
                        
                        s += '<div style="font-weight: bold; margin: 8px 0;">' + org + '</div>';
                        
                        points.forEach(point => {{
                            if (point.y > 0) {{  // Only show non-zero values
                                s += '<div style="display: flex; justify-content: space-between; margin: 4px 0;">';
                                s += '<span><span style="color:' + point.color + '">●</span> ' 
                                    + point.series.name.split(' - ').pop() + ':</span>';
                                s += '<span style="margin-left: 12px;">$' 
                                    + Highcharts.numberFormat(point.y, 0) + '</span>';
                                s += '</div>';
                            }}
                        }});
                        
                        s += '<div style="display: flex; justify-content: space-between; margin-top: 6px; font-weight: bold;">';
                        s += '<span>Total:</span>';
                        s += '<span style="margin-left: 12px;">$' 
                            + Highcharts.numberFormat(orgTotal[org], 0) + '</span>';
                        s += '</div>';
                    }});
                    
                    s += '</div>';
                    return s;
                }};
                
                // Create chart
                Highcharts.chart('multi-org-compensation-chart', options);
            }});
        </script>
        """

def display_multi_compensation_analysis(data_dict: Dict[str, Dict], selected_eins: List[str]) -> None:
    """Display compensation analysis for multiple organizations"""
    try:
        analyzer = MultiCompensationAnalyzer(data_dict, selected_eins)
        html_content = analyzer.create_multi_org_charts()
        
        # Display charts
        st.components.v1.html(html_content, height=600)
        
        # Add methodology explanation
        with st.expander("💰 Yearly Aggregated Compensation Analysis", expanded=False):
            st.markdown("""
            ### Understanding the Yearly Comparison Chart

            - Shows total yearly compensation for each organization
            - Compensation is broken down by type:
                * Base Compensation
                * Bonus
                * Other Compensation
                * Deferred Compensation
                * Nontaxable Benefits
            - Each organization's data is stacked to show total yearly compensation
            - Hover over bars for detailed breakdowns by year and organization
            - Values are shown in millions ($M) for better readability
            - Download options available for further analysis
            """)
            
    except Exception as e:
        st.error(f"Error displaying multi-organization compensation analysis: {str(e)}")