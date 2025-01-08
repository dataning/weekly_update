import streamlit as st
import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts portfolio visualizations"""
    
    COLORS = {
        'public_securities': '#3B82F6',
        'other_securities': '#059669',
        'cash': '#F59E0B',
        'total': '#6366F1',
        'positive': '#10B981',
        'negative': '#EF4444',
        'cagr': '#8B5CF6'  # Added CAGR color
    }
    
    CDN_URLS = {
        'base': 'https://code.highcharts.com/highcharts.js',
        'exporting': 'https://code.highcharts.com/modules/exporting.js',
        'accessibility': 'https://code.highcharts.com/modules/accessibility.js'
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
            },
            'accessibility': {
                'enabled': True,
                'description': 'Portfolio Analysis Charts'
            }
        }

class PortfolioAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['year'].unique())
        self.portfolio_metrics = self._calculate_portfolio_metrics()
        
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the data with proper handling of YoY calculations"""
        df = df.copy()
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        investment_columns = [
            'public_securities_boy', 'public_securities_eoy',
            'other_securities_boy', 'other_securities_eoy',
            'cash_and_savings_boy', 'cash_and_savings_eoy',
            'total_investments_boy', 'total_investments_eoy'
        ]
        
        # Convert to numeric and handle NaN values
        for col in investment_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Sort by year before calculating YoY changes
        df = df.sort_values('year', ascending=True)
        
        # Calculate YoY changes with proper handling of zero values
        def safe_pct_change(series):
            pct_change = series.pct_change() * 100
            # Replace infinity values with 0 or a large value depending on the sign
            pct_change = pct_change.replace([np.inf, -np.inf], 0)
            # Replace NaN with 0 for the first year
            return pct_change.fillna(0)
        
        df['public_securities_yoy'] = safe_pct_change(df['public_securities_eoy'])
        df['other_securities_yoy'] = safe_pct_change(df['other_securities_eoy'])
        df['cash_and_savings_yoy'] = safe_pct_change(df['cash_and_savings_eoy'])
        df['total_yoy'] = safe_pct_change(df['total_investments_eoy'])
        
        return df

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        """
        Calculate Compound Annual Growth Rate with proper handling of edge cases
        """
        # Handle edge cases
        if years <= 0:
            return 0.0
        if start_value <= 0:
            return 0.0 if end_value <= 0 else 100.0
        if end_value <= 0:
            return -100.0
        
        try:
            cagr = (pow(end_value / start_value, 1 / years) - 1) * 100
            # Handle extreme values
            if np.isnan(cagr) or np.isinf(cagr):
                return 0.0
            return cagr
        except Exception:
            return 0.0

    def _calculate_rolling_3yr_cagr(self, series: pd.Series) -> List[float]:
        """Calculate rolling 3-year CAGR for each point"""
        cagr_values = []
        
        for i in range(len(series)):
            if i < 2:  # First two years don't have enough history
                cagr_values.append(None)
                continue
                
            # Get 3-year window
            window = series[max(0, i-2):i+1]
            if len(window) < 3:
                cagr_values.append(None)
                continue
                
            start_value = float(window.iloc[0])
            end_value = float(window.iloc[-1])
            
            try:
                if start_value <= 0 or end_value <= 0:
                    cagr_values.append(None)
                    continue
                    
                cagr = (pow(end_value / start_value, 1/3) - 1) * 100
                if np.isnan(cagr) or np.isinf(cagr):
                    cagr_values.append(None)
                    continue
                    
                cagr_values.append(np.clip(cagr, -100, 100))
            except:
                cagr_values.append(None)
        
        return cagr_values

    def _calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio metrics including rolling 3-year CAGR"""
        # Calculate rolling CAGR for each asset class
        public_cagr = self._calculate_rolling_3yr_cagr(self.df['public_securities_eoy'])
        other_cagr = self._calculate_rolling_3yr_cagr(self.df['other_securities_eoy'])
        cash_cagr = self._calculate_rolling_3yr_cagr(self.df['cash_and_savings_eoy'])
        total_cagr = self._calculate_rolling_3yr_cagr(self.df['total_investments_eoy'])
        
        # For the summary stats, use the latest CAGR values
        return {
            'cagr': {
                'total': total_cagr[-1] if total_cagr and total_cagr[-1] is not None else 0.0,
                'public': public_cagr[-1] if public_cagr and public_cagr[-1] is not None else 0.0,
                'other': other_cagr[-1] if other_cagr and other_cagr[-1] is not None else 0.0,
                'cash': cash_cagr[-1] if cash_cagr and cash_cagr[-1] is not None else 0.0
            },
            'rolling_cagr': {
                'public': public_cagr,
                'other': other_cagr,
                'cash': cash_cagr,
                'total': total_cagr
            }
        }
    
    def get_composition_data(self) -> List[Dict[str, Any]]:
        """Get series data for portfolio composition chart"""
        return [
            {
                'name': 'Public Securities',
                'data': [val/1e6 for val in self.df['public_securities_eoy'].tolist()],
                'color': ChartConfig.COLORS['public_securities'],
                'yoy': self.df['public_securities_yoy'].tolist()
            },
            {
                'name': 'Other Securities',
                'data': [val/1e6 for val in self.df['other_securities_eoy'].tolist()],
                'color': ChartConfig.COLORS['other_securities'],
                'yoy': self.df['other_securities_yoy'].tolist()
            },
            {
                'name': 'Cash & Equivalents',
                'data': [val/1e6 for val in self.df['cash_and_savings_eoy'].tolist()],
                'color': ChartConfig.COLORS['cash'],
                'yoy': self.df['cash_and_savings_yoy'].tolist()
            }
        ]
    
    def create_composition_config(self) -> Dict:
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)

        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': 'Portfolio Composition Over Time'
            },
            'yAxis': {
                'title': {'text': 'Value (Millions $)'},
                'labels': {'format': '${value:,.0f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:,.0f}M'
                }
            },
            # Remove the inline JS function from 'formatter'; just define 'tooltip' styling
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12
            },
            'plotOptions': {
                'series': {
                    'point': {
                        'events': {
                            # Remove or comment out the JS strings here
                            # 'mouseOver': 'function(e) { syncHover(e); }',
                            # 'mouseOut': 'function() { syncMouseOut(); }'
                        }
                    }
                },
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': self.get_composition_data()
        }


    def create_total_value_config(self) -> Dict:
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        # Get rolling CAGR values
        cagr_data = self.portfolio_metrics['rolling_cagr']

        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'height': 500,
                'type': 'line'
            },
            'title': {
                **common_settings['title'],
                'text': 'Year-over-Year Growth and Rolling 3-Year CAGR'
            },
            'yAxis': {
                'title': {'text': 'Growth Rate (%)'},
                'labels': {'format': '{value}%'}
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                'valueDecimals': 1,
                'valueSuffix': '%'
            },
            'plotOptions': {
                'line': {
                    'marker': {
                        'enabled': True,
                        'symbol': 'circle',
                        'radius': 4
                    }
                }
            },
            'series': [
                {
                    'name': 'Public Securities YoY',
                    'data': self.df['public_securities_yoy'].tolist(),
                    'color': ChartConfig.COLORS['public_securities'],
                    'dashStyle': 'Solid',
                    'zIndex': 3
                },
                {
                    'name': 'Other Securities YoY',
                    'data': self.df['other_securities_yoy'].tolist(),
                    'color': ChartConfig.COLORS['other_securities'],
                    'dashStyle': 'Solid',
                    'zIndex': 2
                },
                {
                    'name': 'Cash & Equivalents YoY',
                    'data': self.df['cash_and_savings_yoy'].tolist(),
                    'color': ChartConfig.COLORS['cash'],
                    'dashStyle': 'Solid',
                    'zIndex': 1
                },
                {
                    'name': 'Public Securities 3Y-CAGR',
                    'data': cagr_data['public'],
                    'color': ChartConfig.COLORS['public_securities'],
                    'dashStyle': 'Dash',
                    'zIndex': 0
                },
                {
                    'name': 'Other Securities 3Y-CAGR',
                    'data': cagr_data['other'],
                    'color': ChartConfig.COLORS['other_securities'],
                    'dashStyle': 'Dash',
                    'zIndex': 0
                },
                {
                    'name': 'Cash & Equivalents 3Y-CAGR',
                    'data': cagr_data['cash'],
                    'color': ChartConfig.COLORS['cash'],
                    'dashStyle': 'Dash',
                    'zIndex': 0
                }
            ]
        }


    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        latest_year = self.years[-1]
        latest_data = self.df[self.df['year'] == latest_year].iloc[0]
        cagr_data = self.portfolio_metrics['cagr']
        
        return f"""
        <div style="grid-column: 1 / -1; text-align: center; margin: 10px auto; padding: 10px; 
                    background-color: #f8f9fa; border-radius: 5px; max-width: 800px;">
            <strong>Portfolio Summary (FY {latest_year})</strong><br>
            <span style="color: {ChartConfig.COLORS['total']}">
                Total Portfolio Value: ${latest_data['total_investments_eoy']/1e6:,.1f}M 
                ({latest_data['total_yoy']:+.1f}% YoY)</span><br>
            <small>
                CAGR by Asset Class:<br>
                <span style="color: {ChartConfig.COLORS['public_securities']}">
                    Public Securities: {cagr_data['public']:.1f}%</span> | 
                <span style="color: {ChartConfig.COLORS['other_securities']}">
                    Other Securities: {cagr_data['other']:.1f}%</span> | 
                <span style="color: {ChartConfig.COLORS['cash']}">
                    Cash & Equivalents: {cagr_data['cash']:.1f}%</span>
            </small>
        </div>
        """

    def create_charts(self) -> str:
        """Create all portfolio charts"""
        composition_config = self.create_composition_config()
        value_config = self.create_total_value_config()
        return self._create_html(composition_config, value_config)
    
    def _create_html(self, composition_config: Dict, value_config: Dict) -> str:
        """Create HTML with synchronized charts and custom tooltips"""
        
        styles = """
            #charts-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            #charts-container.loaded {
                opacity: 1;
            }
        """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{styles}</style>
        </head>
        <body>
            <div id="charts-container">
                <div id="portfolio-composition-chart" style="min-width: 200px;"></div>
                <div id="portfolio-value-chart" style="min-width: 200px;"></div>
                {self.create_summary_stats_html()}
            </div>
            
            <!-- Load Highcharts scripts -->
            <script src="{ChartConfig.CDN_URLS['base']}"></script>
            <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
            <script src="{ChartConfig.CDN_URLS['accessibility']}"></script>
            
            <script>
                const compositionConfig = {json.dumps(composition_config)};
                const valueConfig = {json.dumps(value_config)};
                
                document.addEventListener('DOMContentLoaded', function() {{
                    const initializeCharts = () => {{
                        if (typeof Highcharts === 'undefined') {{
                            setTimeout(initializeCharts, 100);
                            return;
                        }}
                        
                        const charts = [];
                        charts.push(Highcharts.chart('portfolio-composition-chart', compositionConfig));
                        charts.push(Highcharts.chart('portfolio-value-chart', valueConfig));
                        
                        // Synchronize tooltips and crosshairs
                        charts.forEach(function (chart) {{
                            chart.container.addEventListener('mousemove', function (e) {{
                                const event = chart.pointer.normalize(e);
                                const hoverPoint = chart.series[0].searchPoint(event, true);
                                if (!hoverPoint) return;
                                
                                const hoverIndex = hoverPoint.index;
                                charts.forEach(function (otherChart) {{
                                    const pointsAtIndex = otherChart.series
                                        .map(s => s.data[hoverIndex])
                                        .filter(Boolean);
                                    
                                    if (pointsAtIndex.length > 0) {{
                                        otherChart.tooltip.refresh(pointsAtIndex);
                                        otherChart.xAxis[0].drawCrosshair(e, pointsAtIndex[0]);
                                    }}
                                }});
                            }});
                            
                            chart.container.addEventListener('mouseleave', function () {{
                                charts.forEach(function (otherChart) {{
                                    otherChart.tooltip.hide();
                                    otherChart.xAxis[0].hideCrosshair();
                                }});
                            }});
                        }});
                        
                        document.getElementById('charts-container').classList.add('loaded');
                    }};
                    
                    initializeCharts();
                }});
            </script>
        </body>
        </html>
        """

def display_portfolio_analysis(df: pd.DataFrame) -> None:
    """Display portfolio analysis using Streamlit components."""
    try:
        analyzer = PortfolioAnalyzer(df)
        html_content = analyzer.create_charts()
        
        st.components.v1.html(html_content, height=650, scrolling=False)
        
        with st.expander("📊 Portfolio Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Charts

            #### 1. Portfolio Composition
            Shows the allocation of investments across three main categories:
            * Public Securities: Publicly traded stocks, bonds, and other market securities
            * Other Securities: Alternative investments, private equity, and other non-public holdings
            * Cash & Equivalents: Liquid assets and short-term investments
            
            The stacked columns provide a visual representation of both the absolute value 
            and relative proportion of each investment category over time. Year-over-Year (YoY) 
            changes are shown for each asset class in the tooltip.

            #### 2. Total Portfolio Value and Growth
            Displays three key metrics:
            * Total Portfolio Value: Combined value of all investment categories (line)
            * Year-over-Year Growth: Net investment change percentage (columns)
            * Compound Annual Growth Rate (CAGR): Overall portfolio growth rate and by asset class
            
            ### Data Processing Notes
            * Investment values converted to numeric format and displayed in millions
            * End-of-year (EOY) values used for composition analysis
            * YoY changes calculated as percentage change from previous year
            * CAGR calculated using the formula: (End Value/Start Value)^(1/n) - 1
            * All monetary values shown in USD
            
            ### Interactive Features
            * Synchronized hovering between charts
            * Download options for charts (PNG, JPG, PDF, SVG)
            * Detailed tooltips showing exact values and YoY changes
            * Cross-chart highlighting and data comparison
            """)
    except Exception as e:
        st.error(f"Error displaying portfolio analysis: {str(e)}")