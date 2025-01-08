import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts financial visualizations"""
    
    COLORS = {
        'revenue': '#059669',
        'expense': '#EC4899',
        'profit': '#3B82F6',
        'revenue_types': {
            'CONTRIBUTIONS': '#4ECDC4',
            'INVESTMENT': '#FFD93D',
            'OTHER': '#95D5B2'
        },
        'expense_types': {
            'SALARIES': '#FF6B6B',
            'GRANTS': '#C792DF',
            'FEES': '#779BE7',
            'OTHER': '#E49AB0'
        }
    }
    
    CDN_URLS = {
        'base': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/highcharts.min.js',
        'exporting': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/exporting.js'
    }
    
    @staticmethod
    def get_common_settings(years: List[str]) -> Dict[str, Any]:
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
                'categories': years,
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

class FinancialAnalyzer:
    """Handle financial data analysis and calculations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['year'].unique())
        self.metrics = self._calculate_financial_metrics()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the financial dataframe"""
        df = df.copy()
        
        # Convert year and financial columns to numeric
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        # financial_columns = [
        #     'total_revenue', 'contributions', 'investment_income', 
        #     'total_expenses', 'grants', 'salaries',
        #     'investment_fees'
        # ]
        
        # for col in financial_columns:
        #     df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate other revenue (total - contributions - investment)
        df['OtherRevenue'] = (df['total_revenue'] - 
                             df['contributions'] - 
                             df['investment_income'])
        
        # Calculate other expenses
        df['OtherExpenses'] = (df['total_expenses'] - 
                              df['grants'] - 
                              df['salaries'] -
                              df['investment_fees'])
        
        return df.sort_values('year', ascending=True)
    
    def _calculate_financial_metrics(self) -> Dict[str, List[float]]:
        """Calculate key financial metrics"""
        return {
            'total_revenue': self.df['total_revenue'].tolist(),
            'total_expenses': self.df['total_expenses'].tolist(),
            'net_income': (self.df['total_revenue'] - 
                          self.df['total_expenses']).tolist(),
            'revenue_growth': self.df['total_revenue'].pct_change().multiply(100).tolist(),
            'expense_growth': self.df['total_expenses'].pct_change().multiply(100).tolist()
        }
    
    def get_revenue_breakdown_data(self) -> List[Dict[str, Any]]:
        """Get series data for revenue breakdown chart"""
        return [
            {
                'name': 'Contributions & Grants',
                'data': self.df['contributions'].tolist(),
                'color': ChartConfig.COLORS['revenue_types']['CONTRIBUTIONS']
            },
            {
                'name': 'Investment Income',
                'data': self.df['investment_income'].tolist(),
                'color': ChartConfig.COLORS['revenue_types']['INVESTMENT']
            },
            {
                'name': 'Other Revenue',
                'data': self.df['OtherRevenue'].tolist(),
                'color': ChartConfig.COLORS['revenue_types']['OTHER']
            }
        ]
    
    def get_expense_breakdown_data(self) -> List[Dict[str, Any]]:
        """Get series data for expense breakdown chart"""
        return [
            {
                'name': 'Salaries & Benefits',
                'data': self.df['salaries'].tolist(),
                'color': ChartConfig.COLORS['expense_types']['SALARIES']
            },
            {
                'name': 'Grants',
                'data': self.df['grants'].tolist(),
                'color': ChartConfig.COLORS['expense_types']['GRANTS']
            },
            {
                'name': 'Investment Fees',
                'data': self.df['investment_fees'].tolist(),
                'color': ChartConfig.COLORS['expense_types']['FEES']
            },
            {
                'name': 'Other Expenses',
                'data': self.df['OtherExpenses'].tolist(),
                'color': ChartConfig.COLORS['expense_types']['OTHER']
            }
        ]
    
    def create_revenue_config(self) -> Dict:
        """Create revenue breakdown chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        # Convert data to millions for display
        revenue_data = self.get_revenue_breakdown_data()
        for series in revenue_data:
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
                'text': 'Revenue Breakdown by Source'
            },
            'yAxis': {
                'title': {'text': 'Amount (millions $)'},
                'labels': {'format': '${value:.0f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:.0f}M'
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
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
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': revenue_data
        }

    def create_expense_config(self) -> Dict:
        """Create expense breakdown chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        # Convert data to millions for display
        expense_data = self.get_expense_breakdown_data()
        for series in expense_data:
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
                'text': 'Expense Breakdown by Category'
            },
            'yAxis': {
                'title': {'text': 'Amount (millions $)'},
                'labels': {'format': '${value:.0f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:.0f}M'
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valuePrefix': '$',
                'valueSuffix': 'M',
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
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': expense_data
        }

    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        latest_year = self.years[-1]
        latest_data = self.df[self.df['year'] == latest_year].iloc[0]
        
        revenue_growth = ((latest_data['total_revenue'] / 
                          self.df[self.df['year'] == self.years[-2]].iloc[0]['total_revenue'] - 1) * 100)
        
        # Convert to millions and format
        revenue_millions = latest_data['total_revenue'] / 1_000_000
        expenses_millions = latest_data['total_expenses'] / 1_000_000
        
        return f"""
        <div style="grid-column: 1 / -1; text-align: center; margin: 10px auto; padding: 10px; background-color: #f8f9fa; border-radius: 5px; max-width: 500px;">
            <strong>Financial Summary ({latest_year})</strong><br>
            <span style="color: {ChartConfig.COLORS['revenue']}">
                Total Revenue: ${revenue_millions:.1f}m 
                ({revenue_growth:+.1f}% YoY)</span><br>
            <span style="color: {ChartConfig.COLORS['expense']}">
                Total Expenses: ${expenses_millions:.1f}m</span>
        </div>
        """

    def create_charts(self) -> str:
        """Create all financial charts with synchronized hovering"""
        revenue_config = self.create_revenue_config()
        expense_config = self.create_expense_config()
        return self._create_html(revenue_config, expense_config)
    
    def _create_html(self, revenue_config: Dict, expense_config: Dict) -> str:
        """Create HTML with charts and synchronized hovering"""
        return f"""
        <div id="charts-container" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div id="revenue-breakdown-chart" style="min-width: 200px;"></div>
            <div id="expense-breakdown-chart" style="min-width: 200px;"></div>
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
                // Create revenue chart
                const revenueOptions = {json.dumps(revenue_config)};
                const revenueChart = Highcharts.chart('revenue-breakdown-chart', revenueOptions);
                charts.push(revenueChart);

                // Create expense chart
                const expenseOptions = {json.dumps(expense_config)};
                const expenseChart = Highcharts.chart('expense-breakdown-chart', expenseOptions);
                charts.push(expenseChart);
                
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

def display_financial_analysis(df: pd.DataFrame) -> None:
    """Display financial analysis using Streamlit components."""
    try:
        # Create analyzer and generate charts
        analyzer = FinancialAnalyzer(df)
        html_content = analyzer.create_charts()
        
        # Display charts
        st.components.v1.html(html_content, height=600)
        
        # Display methodology explanation
        with st.expander("💰 Financial Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Charts

            #### 1. Revenue Breakdown
            Shows the composition of revenue sources over time:
            * Contributions & Grants
            * Investment Income
            * Other Revenue
            * Stacked columns show total revenue
            * Hover for detailed values

            #### 2. Expense Breakdown
            Displays expense categories over time:
            * Salaries & Benefits
            * Grants
            * Investment Fees
            * Other Expenses
            * Stacked columns show total expenses

            ### Financial Metrics
            * All values shown in USD
            * Year-over-year growth calculations
            * Revenue and expense trends
            * Category breakdowns

            ### Data Processing Notes
            * Financial values converted to numeric format
            * Categories standardized
            * Other revenue/expenses calculated as residuals
            * Growth rates calculated year-over-year

            ### Interactive Features
            * Synchronized hovering between charts
            * Download options for charts (PNG, JPG, PDF, SVG)
            * Detailed tooltips
            * Expandable methodology explanation
            """)
    except Exception as e:
        st.error(f"Error displaying financial analysis: {str(e)}")