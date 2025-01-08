import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts NTEE visualizations"""
    
    COLORS = {
        'net_assets': {
            'total': '#2E294E',
            'assets': '#4ECDC4',
            'liabilities': '#FF6B6B'
        },
        'revenue_types': {
            'program_service_revenue': '#FFD93D',
            'contributions_grants': '#FF6B6B',
            'investment_income': '#4ECDC4',
            'remaining': '#adb5bd'
        },
        'expense_types': {
            'officer_compensation': '#4ECDC4',
            'other_salaries': '#FF6B6B',
            'payroll_tax': '#95D5B2',
            'remaining': '#adb5bd'
        }
    }
    
    # Use the same Highcharts scripts as in your Endowment example
    CDN_URLS = {
        'base': 'https://code.highcharts.com/highcharts.js',
        'exporting': 'https://code.highcharts.com/modules/exporting.js',
        'accessibility': 'https://code.highcharts.com/modules/accessibility.js'
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
                },
                'height': 600
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
            },
            'accessibility': {  # Just as in your sample
                'enabled': True,
                'description': 'NTEE Financial Charts'
            }
        }

class NTEEAnalyzer:
    """Handle NTEE data analysis and chart generation"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        # Get top 30 by net assets to maintain consistent order
        self.top_30_orgs = self.df.nlargest(30, 'net_assets')['name'].tolist()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        
        df = df.copy()

        # Define column mapping from source to target names
        column_mapping = {
            'totnetassetend': 'net_assets',
            'totassetsend': 'assets',
            'totliabend': 'liabilities',
            'totrevenue': 'total_revenue',
            'invstmntinc': 'investment_income',
            'totcntrbgfts': 'contributions_grants',
            'totprgmrevnue': 'program_service_revenue',
            'totfuncexpns': 'total_expenses',
            'compnsatncurrofcr': 'officer_compensation', 
            'othrsalwages': 'other_salaries',
            'payrolltx': 'payroll_tax'
        }
        
        # Rename columns using the mapping
        df = df.rename(columns=column_mapping)
        
        # List of target column names after renaming
        numeric_columns = [
            'net_assets', 'assets', 'liabilities',
            'total_revenue', 'investment_income', 'contributions_grants',
            'program_service_revenue', 'total_expenses', 'officer_compensation',
            'other_salaries', 'payroll_tax'
        ]
        
        # Convert to numeric and fill NA values
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
        
        return df
    
    def get_net_assets_series_data(self) -> tuple:
        net_assets_df = self.df[self.df['name'].isin(self.top_30_orgs)]
        net_assets_df = net_assets_df.set_index('name').loc[self.top_30_orgs].reset_index()
        
        series_data = [
            {
                'type': 'line',
                'name': 'Net Assets',
                'data': (net_assets_df['net_assets'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['net_assets']['total'],
                'zIndex': 2,
                'marker': {
                    'lineWidth': 2,
                    'lineColor': ChartConfig.COLORS['net_assets']['total'],
                    'fillColor': 'white'
                }
            },
            {
                'type': 'column',
                'name': 'Assets',
                'data': (net_assets_df['assets'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['net_assets']['assets']
            },
            {
                'type': 'column',
                'name': 'Liabilities',
                'data': (net_assets_df['liabilities'] / -1_000_000).tolist(),  # Negative for visual clarity
                'color': ChartConfig.COLORS['net_assets']['liabilities']
            }
        ]
        
        return series_data, self.top_30_orgs
    
    def get_revenue_series_data(self) -> tuple:
        revenue_df = self.df[self.df['name'].isin(self.top_30_orgs)]
        revenue_df = revenue_df.set_index('name').loc[self.top_30_orgs].reset_index()
        
        # Calculate 'remaining' revenue
        revenue_df['remaining'] = (
            revenue_df['total_revenue'] 
            - (revenue_df['program_service_revenue'] 
               + revenue_df['contributions_grants'] 
               + revenue_df['investment_income'])
        ).clip(lower=0)
        
        series_data = [
            {
                'type': 'column',
                'name': 'Program Service Revenue',
                'data': (revenue_df['program_service_revenue'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['revenue_types']['program_service_revenue']
            },
            {
                'type': 'column',
                'name': 'Contributions & Grants',
                'data': (revenue_df['contributions_grants'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['revenue_types']['contributions_grants']
            },
            {
                'type': 'column',
                'name': 'Investment Income',
                'data': (revenue_df['investment_income'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['revenue_types']['investment_income']
            },
            {
                'type': 'column',
                'name': 'Remaining',
                'data': (revenue_df['remaining'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['revenue_types']['remaining']
            }
        ]
        
        return series_data, self.top_30_orgs
    
    def get_expense_series_data(self) -> tuple:
        expense_df = self.df[self.df['name'].isin(self.top_30_orgs)]
        expense_df = expense_df.set_index('name').loc[self.top_30_orgs].reset_index()
        
        # Calculate 'remaining' expense
        expense_df['remaining'] = (
            expense_df['total_expenses']
            - (expense_df['officer_compensation']
               + expense_df['other_salaries']
               + expense_df['payroll_tax'])
        ).clip(lower=0)
        
        series_data = [
            {
                'type': 'column',
                'name': 'Officer Compensation',
                'data': (expense_df['officer_compensation'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['expense_types']['officer_compensation']
            },
            {
                'type': 'column',
                'name': 'Other Salaries',
                'data': (expense_df['other_salaries'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['expense_types']['other_salaries']
            },
            {
                'type': 'column',
                'name': 'Payroll Tax',
                'data': (expense_df['payroll_tax'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['expense_types']['payroll_tax']
            },
            {
                'type': 'column',
                'name': 'Remaining',
                'data': (expense_df['remaining'] / 1_000_000).tolist(),
                'color': ChartConfig.COLORS['expense_types']['remaining']
            }
        ]
        
        return series_data, self.top_30_orgs
    
    def create_net_assets_config(self) -> Dict:
        series_data, categories = self.get_net_assets_series_data()
        common_settings = ChartConfig.get_common_settings(categories)
        
        return {
            **common_settings,
            'title': {
                **common_settings['title'],
                'text': 'Net Assets Composition (Top 30)'
            },
            'yAxis': {
                'title': {'text': 'Millions USD'},
                'labels': {'format': '${value}M'}
            },
            'tooltip': {
                'shared': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
                'valueDecimals': 1
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': series_data
        }
    
    def create_revenue_config(self) -> Dict:
        series_data, categories = self.get_revenue_series_data()
        common_settings = ChartConfig.get_common_settings(categories)
        
        return {
            **common_settings,
            'title': {
                **common_settings['title'],
                'text': 'Revenue Distribution (Top 30)'
            },
            'yAxis': {
                'title': {'text': 'Millions USD'},
                'labels': {'format': '${value}M'}
            },
            'tooltip': {
                'shared': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
                'valueDecimals': 1
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': series_data
        }
    
    def create_expense_config(self) -> Dict:
        series_data, categories = self.get_expense_series_data()
        common_settings = ChartConfig.get_common_settings(categories)
        
        return {
            **common_settings,
            'title': {
                **common_settings['title'],
                'text': 'Expense Distribution (Top 30)'
            },
            'yAxis': {
                'title': {'text': 'Millions USD'},
                'labels': {'format': '${value}M'}
            },
            'tooltip': {
                'shared': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
                'valueDecimals': 1
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': series_data
        }

    def create_charts(self) -> str:
        net_assets_config = self.create_net_assets_config()
        revenue_config = self.create_revenue_config()
        expense_config = self.create_expense_config()
        return self._create_html(net_assets_config, revenue_config, expense_config)
    
    def _create_html(self, net_assets_config: Dict, revenue_config: Dict, expense_config: Dict) -> str:
        """
        Create HTML with multiple Highcharts figures and 
        synchronized tooltips via 'mousemove' events on each chart container.
        """
        
        # Convert configurations to JSON
        net_assets_json = json.dumps(net_assets_config)
        revenue_json = json.dumps(revenue_config)
        expense_json = json.dumps(expense_config)
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
            #charts-container {{
                display: grid;
                grid-template-areas: 
                    "net-assets"
                    "bottom-charts";
                gap: 40px;
                width: 100%;
                margin: 0 auto;
                padding: 20px;
            }}
            #net-assets-chart {{
                grid-area: net-assets;
                width: 100%;
            }}
            #bottom-charts {{
                grid-area: bottom-charts;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                width: 100%;
            }}
            @media (max-width: 768px) {{
                #bottom-charts {{
                    grid-template-columns: 1fr;
                }}
            }}
            .chart-container {{
                width: 100%;
                min-width: 200px;
            }}
            </style>
        </head>
        <body>
        
        <div id="charts-container">
            <div id="net-assets-chart" class="chart-container"></div>
            <div id="bottom-charts">
                <div id="revenue-chart" class="chart-container"></div>
                <div id="expense-chart" class="chart-container"></div>
            </div>
        </div>
        
        <!-- Load Highcharts scripts -->
        <script src="{ChartConfig.CDN_URLS['base']}"></script>
        <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
        <script src="{ChartConfig.CDN_URLS['accessibility']}"></script>
        
        <script>
        document.addEventListener('DOMContentLoaded', function () {{
            const charts = [];
            
            // Function to handle responsive resizing
            function handleResize() {{
                charts.forEach(chart => {{
                    chart.reflow();
                }});
            }}

            // Add window resize listener
            window.addEventListener('resize', handleResize);
            
            // Initialize each chart with responsive options
            const commonChartOptions = {{
                chart: {{
                    reflow: true,
                    animation: false
                }}
            }};
            
            const netAssetsChart = Highcharts.chart('net-assets-chart', 
                Highcharts.merge(commonChartOptions, {net_assets_json})
            );
            const revenueChart = Highcharts.chart('revenue-chart', 
                Highcharts.merge(commonChartOptions, {revenue_json})
            );
            const expenseChart = Highcharts.chart('expense-chart', 
                Highcharts.merge(commonChartOptions, {expense_json})
            );
            
            charts.push(netAssetsChart);
            charts.push(revenueChart);
            charts.push(expenseChart);
            
            // For each chart, listen to mouse move on the container
            charts.forEach(chart => {{
                chart.container.addEventListener('mousemove', function(e) {{
                    const event = chart.pointer.normalize(e);
                    let hoverPoint = null;
                    for (const s of chart.series) {{
                        if (!s.visible) continue;
                        const candidate = s.searchPoint(event, true);
                        if (candidate) {{
                            if (!hoverPoint || Math.abs(candidate.plotX - event.chartX) < 
                                            Math.abs(hoverPoint.plotX - event.chartX)) {{
                                hoverPoint = candidate;
                            }}
                        }}
                    }}
                    
                    if (!hoverPoint) return;
                    
                    const hoverIndex = hoverPoint.index;
                    
                    charts.forEach(otherChart => {{
                        if (otherChart === chart) return;
                        
                        const pointsAtIndex = [];
                        otherChart.series.forEach(s => {{
                            if (!s.visible) return;
                            const pt = s.points[hoverIndex];
                            if (pt) pointsAtIndex.push(pt);
                        }});
                        
                        if (pointsAtIndex.length > 0) {{
                            otherChart.tooltip.refresh(pointsAtIndex);
                            otherChart.xAxis[0].drawCrosshair(event, pointsAtIndex[0]);
                        }}
                    }});
                }});
                
                chart.container.addEventListener('mouseleave', function() {{
                    charts.forEach(otherChart => {{
                        otherChart.tooltip.hide();
                        otherChart.xAxis[0].hideCrosshair();
                    }});
                }});
            }});

            // Initial resize
            handleResize();
        }});
        </script>
        </body>
        </html>
        """
        
        return html_template

# Change this function name
def create_charts(filtered_df: pd.DataFrame) -> None:
    """Display NTEE analysis using Streamlit components."""
    try:
        analyzer = NTEEAnalyzer(filtered_df)
        html_content = analyzer.create_charts()
        st.components.v1.html(html_content, height=1200, scrolling=False)
        
        with st.expander("📊 NTEE Analysis Methodology", expanded=False):
            st.markdown("""
            **1. Net Assets (Line + Columns)**  
            * Net Assets (line)
            * Assets & Liabilities (stacked columns)
            
            **2. Revenue Distribution (Stacked Bar)**  
            * Program Service Revenue
            * Contributions & Grants
            * Investment Income
            * Remaining (to match total revenue)
            
            **3. Expense Distribution (Stacked Bar)**  
            * Officer Compensation
            * Other Salaries
            * Payroll Tax
            * Remaining (to match total expenses)
            
            **Synchronized Hover**:
            - We track mouse movement in each chart
            - Identify the nearest data point
            - Refresh tooltips in the other charts at the same index
            """)
    except Exception as e:
        st.error(f"Error displaying NTEE analysis: {str(e)}")
        st.error(f"Error displaying NTEE analysis: {str(e)}")
