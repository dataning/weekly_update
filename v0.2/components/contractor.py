import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts contractor visualizations"""
    
    COLORS = {
        'spending': '#059669',
        'trend': '#3B82F6',
        'service_types': {
            'MARKETING': '#4ECDC4',
            'ADVERTISING': '#FFD93D',
            'CONSULTING': '#95D5B2',
            'LEGAL': '#C792DF',
            'CONSTRUCTION': '#FF6B6B',
            'OTHER': '#779BE7'
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

class ContractorAnalyzer:
    """Handle contractor spending analysis and calculations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['year'].unique())
        self.latest_year = max(self.years)
        self.metrics = self._calculate_spending_metrics()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the contractor dataframe"""
        df = df.copy()
        
        # Convert year and compensation to numeric
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['compensation'] = pd.to_numeric(df['compensation'], errors='coerce')
        
        # Clean and standardize service categories
        df['service_category'] = df['services'].apply(self._categorize_service)
        
        # Fill null contractor names with 'Unnamed Contractor'
        df['contractor_name'] = df['contractor_name'].fillna('Unnamed Contractor')
        
        return df.sort_values(['year', 'compensation'], ascending=[True, False])
    
    def _categorize_service(self, service: str) -> str:
        """Categorize services into standardized categories"""
        if pd.isna(service):
            return 'Other Services'
            
        service_lower = service.lower()
        
        if any(word in service_lower for word in ['advertising', 'ad ', 'ads']):
            return 'Advertising'
        elif any(word in service_lower for word in ['marketing', 'media']):
            return 'Marketing'
        elif 'consulting' in service_lower:
            return 'Consulting'
        elif any(word in service_lower for word in ['legal', 'law']):
            return 'Legal Services'
        elif 'construction' in service_lower:
            return 'Construction'
        else:
            return 'Other Services'
    
    def _calculate_spending_metrics(self) -> Dict[str, Any]:
        """Calculate key spending metrics"""
        # Group by year and calculate metrics
        yearly_metrics = self.df.groupby('year').agg({
            'compensation': ['sum', 'count'],
            'contractor_name': 'nunique'
        }).reset_index()
        
        yearly_metrics.columns = ['year', 'total_spend', 'contract_count', 'unique_contractors']
        
        return {
            'yearly_totals': yearly_metrics['total_spend'].tolist(),
            'contract_counts': yearly_metrics['contract_count'].tolist(),
            'contractor_counts': yearly_metrics['unique_contractors'].tolist()
        }
    
    def get_service_breakdown_data(self) -> List[Dict[str, Any]]:
        """Get series data for service category breakdown chart"""
        yearly_services = self.df.pivot_table(
            index='year',
            columns='service_category',
            values='compensation',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        series_data = []
        for category in yearly_services.columns:
            if category == 'year':
                continue
                
            color_key = category.upper().replace(' ', '_')
            color = (ChartConfig.COLORS['service_types'].get(color_key) or 
                    ChartConfig.COLORS['service_types']['OTHER'])
            
            series_data.append({
                'name': category,
                'data': yearly_services[category].tolist(),
                'color': color
            })
        
        return series_data
    
    def get_top_contractors_data(self) -> List[Dict[str, Any]]:
        """Get data for top contractors in the latest year"""
        latest_data = self.df[self.df['year'] == self.latest_year]
        top_contractors = latest_data.nlargest(10, 'compensation')
        
        return [{
            'name': row['contractor_name'],
            'y': row['compensation'],
            'color': ChartConfig.COLORS['spending']
        } for _, row in top_contractors.iterrows()]
    
    def create_services_config(self) -> Dict:
        """Create service breakdown chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        # Convert data to millions for display
        series_data = self.get_service_breakdown_data()
        for series in series_data:
            series['data'] = [val/1_000_000 if val is not None else None for val in series['data']]
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': 'Contractor Spending by Service Category'
            },
            'yAxis': {
                'title': {'text': 'Amount (millions $)'},
                'labels': {'format': '${value:.1f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:.1f}M'
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
                'valueDecimals': 1,
                'headerFormat': '<b>{point.x}</b><br/>',
                'pointFormat': '<span style="color:{series.color}">●</span> {series.name}: ${point.y:.1f}M<br/>',
                'footerFormat': '<b>Total: ${point.total:.1f}M</b>'
            },
            'plotOptions': {
                'series': {
                    'point': {
                        'events': {
                            'mouseOver': 'function(e) { syncHover(e); }',
                            'mouseOut': 'function() { syncMouseOut(); }'
                        }
                    }
                },
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': series_data
        }

    def create_contractors_config(self) -> Dict:
        """Create top contractors chart configuration"""
        common_settings = ChartConfig.get_common_settings([])
        
        # Convert data to millions
        top_contractors_data = self.get_top_contractors_data()
        for item in top_contractors_data:
            item['y'] = item['y'] / 1_000_000 if item['y'] is not None else None
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'bar',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': f'Top 10 Contractors by Spend ({self.latest_year})'
            },
            'xAxis': {
                'type': 'category',
                'labels': {'style': {'fontSize': '11px'}}
            },
            'yAxis': {
                'title': {'text': 'Amount (millions $)'},
                'labels': {'format': '${value:.1f}M'}
            },
            'tooltip': {
                'headerFormat': '<b>{point.key}</b><br/>',
                'pointFormat': '<span style="color:{point.color}">●</span> Spend: ${point.y:.1f}M',
                'valueDecimals': 1
            },
            'plotOptions': {
                'series': {
                    'point': {
                        'events': {
                            'mouseOver': 'function(e) { syncHover(e); }',
                            'mouseOut': 'function() { syncMouseOut(); }'
                        }
                    }
                },
                'bar': {
                    'dataLabels': {
                        'enabled': True,
                        'format': '${y:.1f}M'
                    }
                }
            },
            'series': [{
                'name': 'Spending',
                'data': top_contractors_data
            }]
        }

    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        latest_spend = self.metrics['yearly_totals'][-1]
        prev_spend = self.metrics['yearly_totals'][-2]
        spend_growth = ((latest_spend / prev_spend - 1) * 100) if prev_spend > 0 else 0
        
        # Convert to millions for display
        latest_spend_m = latest_spend / 1_000_000
        
        return f"""
        <div style="grid-column: 1 / -1; text-align: center; margin: 10px auto; padding: 10px; background-color: #f8f9fa; border-radius: 5px; max-width: 500px;">
            <strong>Contractor Spending Summary ({self.latest_year})</strong><br>
            <span style="color: {ChartConfig.COLORS['spending']}">
                Total Spend: ${latest_spend_m:.1f}M ({spend_growth:+.1f}% YoY)<br>
                Active Contractors: {self.metrics['contractor_counts'][-1]}
            </span>
        </div>
        """

    def create_charts(self) -> str:
        """Create all contractor analysis charts with synchronized hovering"""
        services_config = self.create_services_config()
        contractors_config = self.create_contractors_config()
        return self._create_html(services_config, contractors_config)
    
    def _create_html(self, services_config: Dict, contractors_config: Dict) -> str:
        """Create HTML with charts and synchronized hovering"""
        return f"""
        <div id="charts-container" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div id="services-breakdown-chart" style="min-width: 200px;"></div>
            <div id="top-contractors-chart" style="min-width: 200px;"></div>
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
                // Create services chart
                const servicesOptions = {json.dumps(services_config)};
                const servicesChart = Highcharts.chart('services-breakdown-chart', servicesOptions);
                charts.push(servicesChart);

                // Create contractors chart
                const contractorsOptions = {json.dumps(contractors_config)};
                const contractorsChart = Highcharts.chart('top-contractors-chart', contractorsOptions);
                charts.push(contractorsChart);
                
                // Fix tooltip positioning
                charts.forEach(chart => {{
                    if (chart && chart.tooltip) {{
                        chart.tooltip.options.positioner = function (labelWidth, labelHeight, point) {{
                            const chart = this.chart;
                            const plotLeft = chart.plotLeft;
                            const plotTop = chart.plotTop;
                            const plotWidth = chart.plotWidth;
                            
                            let x = point.plotX + plotLeft;
                            const y = point.plotY + plotTop;
                            
                            if (x + labelWidth > plotLeft + plotWidth) {{
                                x = plotLeft + plotWidth - labelWidth;
                            }}
                            if (x < plotLeft) {{
                                x = plotLeft;
                            }}
                            
                            return {{
                                'x': x,
                                'y': y - labelHeight - 10
                            }};
                        }};
                    }}
                }});
            }});
        </script>
        """

def display_contractor_analysis(df: pd.DataFrame) -> None:
    """Display contractor analysis using Streamlit components."""
    try:
        # Create analyzer and generate charts
        analyzer = ContractorAnalyzer(df)
        html_content = analyzer.create_charts()
        
        # Display charts
        st.components.v1.html(html_content, height=600)
        
        # Display methodology explanation
        with st.expander("💼 Contractor Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Charts

            #### 1. Service Category Breakdown
            Shows the distribution of spending across service categories over time:
            * Marketing
            * Advertising
            * Consulting
            * Legal Services
            * Construction
            * Other Services
            * Stacked columns show total spend per year

            #### 2. Top Contractors
            Displays the highest-paid contractors for the most recent year:
            * Top 10 contractors by total compensation
            * Includes contractor names and exact amounts
            * Horizontal bars for easy comparison

            ### Analysis Notes
            * All monetary values are in USD (millions)
            * Service categories are standardized based on service descriptions
            * Year-over-year growth calculations
            * Unnamed contractors are labeled as 'Unnamed Contractor'
            * Multiple contracts with the same contractor are aggregated

            ### Data Processing
            The analysis standardizes service categories through keyword matching and classification. Marketing and advertising services are distinguished based on specific service descriptions, while consulting services are identified through explicit consulting-related terms. The system handles missing contractor names by using a standardized placeholder, ensuring continuity in the analysis.

            ### Interactive Features
            The visualization includes several interactive elements:
            * Synchronized hovering between charts
            * Download options for charts (PNG, JPG, PDF, SVG)
            * Detailed tooltips showing exact values with color indicators
            * Expandable methodology explanation

            ### Calculations and Metrics
            The analysis includes several key metrics:
            * Total annual spending by service category
            * Year-over-year spending growth
            * Number of active contractors
            * Individual contractor spending totals
            """)
    except Exception as e:
        st.error(f"Error displaying contractor analysis: {str(e)}")