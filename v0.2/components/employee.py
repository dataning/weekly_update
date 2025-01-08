import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts compensation visualizations"""
    
    COLORS = {
        'positive': '#059669',
        'negative': '#EC4899',
        'default': '#E0FBFC',
        'compensation_types': {
            'BASE_COMP': '#4ECDC4',
            'BONUS': '#FF6B6B',
            'OTHER_COMP': '#FFD93D',
            'DEFERRED_COMP': '#95D5B2',
            'NONTAXABLE_BENEFITS': '#C792DF'
        }
    }
    
    CDN_URLS = {
        'base': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/highcharts.min.js',
        'exporting': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/exporting.js'
    }
    
    @staticmethod
    def get_common_settings(categories: List[str]) -> Dict[str, Any]:
        """Return common chart settings"""
        return {
            'chart': {
                'style': {'fontFamily': 'Inter, sans-serif'},
                'spacing': [10, 10, 10, 10],
                'backgroundColor': {
                    'linearGradient': { 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 1 },
                    'stops': [
                        [0, '#ffffff'],
                        [1, '#f8f9fa']
                    ]
                }
            },
            'title': {
                'align': 'center',
                'style': {'fontSize': '14px', 'fontWeight': '500'},
            },
            'exporting': {
                'enabled': True,
                'buttons': {
                    'contextButton': {
                        'menuItems': ['downloadPNG', 'downloadJPEG', 'downloadPDF', 'downloadSVG']
                    }
                }
            },
            'xAxis': {
                'categories': categories,
                'labels': {
                    'style': {'fontSize': '11px'},
                    'rotation': -45
                },
                'tickLength': 0,
                'lineWidth': 1,
                'crosshair': True
            },
            'credits': {'enabled': False},
            'legend': {
                'align': 'center',
                'verticalAlign': 'bottom',
                'layout': 'horizontal',
                'floating': False,
                'borderWidth': 0,
                'backgroundColor': 'none',
                'shadow': False
            }
        }

class CompensationAnalyzer:
    """Handle compensation data analysis and calculations"""

    def __init__(self, df: pd.DataFrame):
        """Initialize the analyzer with compensation data"""
        self.df = self._preprocess_data(df)
        self.latest_year = self.df['year'].max()
        self.current_employees = self._get_current_employees()
        self.tenure_data = self._calculate_tenure()

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the compensation dataframe"""
        try:
            df = df.copy()
            
            # Rename columns to match expected format
            column_mapping = {
                'total_compensation': 'TotalComp',
                'base_compensation': 'BaseComp',
                'bonus': 'Bonus',
                'other_compensation': 'OtherComp',
                'deferred_compensation': 'DeferredComp',
                'nontaxable_benefits': 'NontaxableBenefits'
            }
            df = df.rename(columns=column_mapping)
            
            # Convert year to numeric
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            
            # Convert compensation columns to numeric
            comp_columns = ['BaseComp', 'Bonus', 'OtherComp', 'DeferredComp', 
                            'NontaxableBenefits', 'TotalComp']
            for col in comp_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Fill NaN values with 0 for compensation columns
            df[comp_columns] = df[comp_columns].fillna(0)
            
            # Clean person names and titles
            df['person_name'] = df['person_name'].apply(
                lambda x: ' '.join(word.capitalize() for word in str(x).lower().split())
            )
            df['title'] = df['title'].apply(
                lambda x: ' '.join(word.capitalize() for word in str(x).lower().split())
            )
            
            return df.sort_values(['year', 'TotalComp'], ascending=[False, False])
        except Exception as e:
            raise Exception(f"Error preprocessing data: {str(e)}")
    
    def _get_current_employees(self) -> pd.DataFrame:
        """Get employees from the latest year"""
        return self.df[self.df['year'] == self.latest_year]
    
    def _calculate_tenure(self) -> pd.DataFrame:
        """Calculate tenure for each employee"""
        valid_years_df = self.df[pd.notna(self.df['year'])]
        
        if valid_years_df.empty:
            return pd.DataFrame(columns=['person_name', 'start_year', 'end_year', 'years_of_service'])
            
        # Group by employee and get their first and last year
        tenure = valid_years_df.groupby('person_name').agg({
            'year': ['min', 'max']
        }).reset_index()
        
        tenure.columns = ['person_name', 'start_year', 'end_year']
        
        # Calculate years of service
        tenure['years_of_service'] = tenure.apply(
            lambda x: int(x['end_year'] - x['start_year'] + 1), axis=1
        )
        
        tenure['years_of_service'] = tenure['years_of_service'].clip(lower=1)
        
        return tenure.sort_values('years_of_service', ascending=False)
    
    def get_compensation_series_data(self) -> List[Dict[str, Any]]:
        """Get series data for compensation chart, embedding title in each point."""
        series_data = []
        comp_types = {
            'BaseComp': ('Base Compensation', ChartConfig.COLORS['compensation_types']['BASE_COMP']),
            'Bonus': ('Bonus', ChartConfig.COLORS['compensation_types']['BONUS']),
            'OtherComp': ('Other Compensation', ChartConfig.COLORS['compensation_types']['OTHER_COMP']),
            'DeferredComp': ('Deferred Compensation', ChartConfig.COLORS['compensation_types']['DEFERRED_COMP']),
            'NontaxableBenefits': ('Nontaxable Benefits', ChartConfig.COLORS['compensation_types']['NONTAXABLE_BENEFITS'])
        }

        # Build a lookup so we can get the title by (person_name)
        title_lookup = self.current_employees.set_index('person_name')['title'].to_dict()
        current_employees = self.current_employees['person_name'].unique()

        for comp_type, (name, color) in comp_types.items():
            data = []
            for employee in current_employees:
                # Compensation value
                value = self.current_employees[self.current_employees['person_name'] == employee][comp_type].values
                comp_val = float(value[0]) if len(value) > 0 else 0
                
                # Get the title
                employee_title = title_lookup.get(employee, '')

                data.append({
                    'y': comp_val,
                    'title': employee_title,
                    'person_name': employee
                })

            series_data.append({
                'name': name,
                'data': data,
                'color': color
            })

        return series_data
    
    def create_distribution_config(self) -> Dict:
        """Create compensation distribution chart for latest year"""
        current_employees = self.current_employees['person_name'].unique()
        common_settings = ChartConfig.get_common_settings(current_employees.tolist())
        
        distribution_config = {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': f'Current Year ({self.latest_year}) Compensation Distribution'
            },
            'yAxis': {
                'title': {'text': 'Compensation ($)'},
                'labels': {'format': '${value:,.0f}'},
                'stackLabels': {
                    'enabled': True,
                    'useHTML': True,
                    'formatter': 'function() { return "$" + (this.total / 1000).toFixed(0) + "k"; }'
                }
            },
            # We'll override the tooltip in JS, but keep some defaults
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valuePrefix': '$',
                'valueDecimals': 0
            },
            'plotOptions': {
                'series': {
                    'point': {
                        'events': {}
                    }
                },
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': self.get_compensation_series_data()
        }
        
        return distribution_config
    
    def create_tenure_config(self) -> Dict:
        """Create tenure comparison chart configuration (with title in tooltip)."""
        current_employees = self.current_employees['person_name'].unique()
        tenure_data = self.tenure_data[self.tenure_data['person_name'].isin(current_employees)]
        
        # Merge to get the title from self.current_employees
        merged_df = pd.merge(
            tenure_data,
            self.current_employees[['person_name', 'title']],
            on='person_name',
            how='left'
        )
        
        # Reindex to keep the same order
        merged_df = merged_df.set_index('person_name').reindex(current_employees).reset_index()

        common_settings = ChartConfig.get_common_settings(merged_df['person_name'].tolist())

        # Build data with {y, title, person_name}
        chart_data = []
        for _, row in merged_df.iterrows():
            chart_data.append({
                'y': row['years_of_service'],
                'title': row['title'],
                'person_name': row['person_name']
            })

        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'bar',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': 'Years of Service for Current Employees'
            },
            'yAxis': {
                'title': {'text': 'Years of Service'},
                'labels': {'format': '{value}'},
                'min': 0
            },
            # We'll override the tooltip in JS
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valueSuffix': ' years'
            },
            'plotOptions': {
                'series': {
                    'point': {
                        'events': {}
                    }
                },
                'bar': {
                    'dataLabels': {
                        'enabled': True,
                        'format': '{y} years'
                    }
                }
            },
            'series': [{
                'name': 'Years of Service',
                'data': chart_data,
                'color': ChartConfig.COLORS['positive']
            }]
        }

    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        avg_tenure = self.tenure_data[
            self.tenure_data['person_name'].isin(self.current_employees['person_name'])
        ]['years_of_service'].mean()
        
        return f"""
        <div style="grid-column: 1 / -1; text-align: center; margin: 10px auto; padding: 10px; background-color: #f8f9fa; border-radius: 5px; max-width: 500px;">
            <strong>Current Employee Statistics ({self.latest_year})</strong><br>
            <span style="color: {ChartConfig.COLORS['positive']}">
                Average Tenure: {avg_tenure:.1f} years | 
                Total Listed Employees: {len(self.current_employees['person_name'].unique())}
            </span>
        </div>
        """

    def create_charts(self) -> str:
        """Create all compensation charts with synchronized hovering and custom tooltip for titles."""
        distribution_config = self.create_distribution_config()
        tenure_config = self.create_tenure_config()
        return self._create_html(distribution_config, tenure_config)
    
    def _create_html(self, distribution_config: Dict, tenure_config: Dict) -> str:
        """
        Create HTML with charts and synchronized hovering.
        
        Includes custom tooltip formatter that displays each employee's title.
        """
        distribution_config_json = json.dumps(distribution_config)
        tenure_config_json = json.dumps(tenure_config)

        # A custom JS tooltip formatter that shows each series + employee title
        # We'll inject this after we parse the config JSON.
        CUSTOM_TOOLTIP_FORMATTER = """
            function() {
                // "this.points" contains an array of points for the hovered category (employee)
                // because it's a shared tooltip. We only need to show the title once, so let's
                // get it from the first point.
                const firstPoint = this.points[0];
                const employeeTitle = firstPoint.point.options.title || '';
                const personName = firstPoint.point.options.person_name || this.x; 

                // Start building the tooltip string
                let s = '<b>' + personName + '</b><br/>';
                s += '<em style="color: #666;">Title: ' + employeeTitle + '</em><br/>';

                // Now loop over the stacked points to show each series's data
                this.points.forEach(function(point) {
                    const seriesName = point.series.name;
                    const value = point.y;
                    if (point.series.chart.options.chart.type === 'column') {
                        // Distribution chart
                        s += '<span style="color:' + point.color + '">●</span> '
                            + seriesName + ': <b>$' + Highcharts.numberFormat(value, 0) + '</b><br/>';
                    } else {
                        // Tenure chart
                        s += '<span style="color:' + point.color + '">●</span> '
                            + seriesName + ': <b>' + value + ' years</b><br/>';
                    }
                });
                return s;
            }
        """

        return f"""
        <div id="charts-container" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div id="compensation-distribution-chart" style="min-width: 200px;"></div>
            <div id="tenure-comparison-chart" style="min-width: 200px;"></div>
            {self.create_summary_stats_html()}
        </div>
        
        <script src="{ChartConfig.CDN_URLS['base']}"></script>
        <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
        <script>
            const charts = [];
            let hoverTimeout;
            
            // Define sync functions in global scope
            window.syncHover = function(e) {{
                clearTimeout(hoverTimeout);
                const pointIndex = e.target.index;
                
                charts.forEach(chart => {{
                    if (chart && chart !== e.target.series.chart) {{
                        const points = chart.series.map(s => s.points[pointIndex]).filter(p => p);
                        if (points.length) {{
                            chart.tooltip.refresh(points);
                        }}
                    }}
                }});
            }};

            window.syncMouseOut = function() {{
                hoverTimeout = setTimeout(() => {{
                    charts.forEach(chart => {{
                        if (chart && chart.tooltip) {{
                            chart.tooltip.hide();
                        }}
                    }});
                }}, 50);
            }};

            document.addEventListener('DOMContentLoaded', function() {{
                // 1. Parse distribution config JSON
                const distributionOptions = {distribution_config_json};
                
                // Modify the stack labels formatter (already in the config, but let's ensure it's a function)
                if (distributionOptions.yAxis && distributionOptions.yAxis.stackLabels) {{
                    distributionOptions.yAxis.stackLabels.formatter = function() {{
                        return '$' + (this.total / 1000).toFixed(0) + 'k';
                    }};
                }}

                // Apply our custom JS tooltip formatter
                if (!distributionOptions.tooltip) distributionOptions.tooltip = {{}};
                distributionOptions.tooltip.formatter = {CUSTOM_TOOLTIP_FORMATTER};

                // 2. Attach real JS functions for mouseOver/mouseOut
                if (distributionOptions.plotOptions?.series?.point?.events) {{
                    distributionOptions.plotOptions.series.point.events.mouseOver = function(e) {{
                        syncHover(e);
                    }};
                    distributionOptions.plotOptions.series.point.events.mouseOut = function() {{
                        syncMouseOut();
                    }};
                }}

                // 3. Create the distribution chart
                const distributionChart = Highcharts.chart('compensation-distribution-chart', distributionOptions);
                charts.push(distributionChart);

                // 4. Parse and create tenure chart
                const tenureOptions = {tenure_config_json};

                // Add custom JS tooltip formatter for tenure
                if (!tenureOptions.tooltip) tenureOptions.tooltip = {{}};
                tenureOptions.tooltip.formatter = {CUSTOM_TOOLTIP_FORMATTER};

                if (tenureOptions.plotOptions?.series?.point?.events) {{
                    tenureOptions.plotOptions.series.point.events.mouseOver = function(e) {{
                        syncHover(e);
                    }};
                    tenureOptions.plotOptions.series.point.events.mouseOut = function() {{
                        syncMouseOut();
                    }};
                }}

                const tenureChart = Highcharts.chart('tenure-comparison-chart', tenureOptions);
                charts.push(tenureChart);
                
                // Fix tooltip positioning for both charts
                charts.forEach(chart => {{
                    if (chart && chart.tooltip) {{
                        chart.tooltip.options.positioner = function (labelWidth, labelHeight, point) {{
                            const plotLeft = this.chart.plotLeft;
                            const plotTop = this.chart.plotTop;
                            const plotWidth = this.chart.plotWidth;
                            
                            let x = point.plotX + plotLeft;
                            const y = point.plotY + plotTop;
                            
                            if (x + labelWidth > plotLeft + plotWidth) {{
                                x = plotLeft + plotWidth - labelWidth;
                            }}
                            if (x < plotLeft) {{
                                x = plotLeft;
                            }}
                            
                            return {{
                                x: x,
                                y: y - labelHeight - 10
                            }};
                        }};
                    }}
                }});
            }});
        </script>
        """

def display_compensation_analysis(df: pd.DataFrame) -> None:
    """Display compensation analysis using Streamlit components."""
    try:
        # Create analyzer and generate charts
        analyzer = CompensationAnalyzer(df)
        html_content = analyzer.create_charts()
        
        # Display charts in Streamlit
        st.components.v1.html(html_content, height=600)
        
        # Display methodology explanation
        with st.expander("💰 Compensation Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Charts

            #### 1. Current Year Compensation Distribution
            Shows the breakdown of compensation by type for current employees:
            * Stacked columns represent different compensation components
            * Values are shown in dollars
            * Components are color-coded by type
            * Only shows data for the latest year

            #### 2. Years of Service Comparison
            Shows tenure information for current employees:
            * Horizontal bars show years of service
            * Sorted by tenure length
            * Includes data labels for easy reading

            ### Notes on Interpretation
            * Compensation values are in USD
            * Years of service calculated from first appearance to latest year
            * Only current employees (latest year) are shown
            * Hover over bars for exact values
            * Charts are synchronized for easier comparison

            ### Compensation Components
            Categories include:
            * Base Compensation (Salary/Wages)
            * Bonus (Performance Incentives)
            * Other Compensation
            * Deferred Compensation
            * Nontaxable Benefits

            ### Interactive Features
            * Synchronized hovering between charts
            * Download options for charts (PNG, JPG, PDF, SVG)
            * Expandable methodology explanation
            * Responsive layout
            """)
    except Exception as e:
        st.error(f"Error displaying compensation analysis: {str(e)}")
