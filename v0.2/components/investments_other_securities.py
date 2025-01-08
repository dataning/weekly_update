import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List, Optional, Tuple

class ChartConfig:
    """Base configuration for Highcharts"""
    
    COLORS = {
        'positive': '#059669',
        'negative': '#EC4899',
        'default': '#E0FBFC',
        'asset_classes': {
            'FIXED_INCOME': '#FF6B6B',
            'EQUITY': '#4ECDC4',
            'CASH': '#FFD93D',
            'REAL_ESTATE': '#95D5B2',
            'ALTERNATIVES': '#C792DF',
            'COMMODITIES': '#F7A072',
            'DERIVATIVES': '#779BE7',
            'STRUCTURED': '#E49AB0',
            'INSURANCE': '#98E2C6'
        }
    }
    
    ASSET_CLASS_KEYWORDS = {
        'FIXED_INCOME': ['bond', 'treasury', 'note', 'fixed income', 'debt', 'debenture', 'fixed-income'],
        'EQUITY': ['equity', 'stock', 'share', 'common stock', 'preferred stock'],
        'CASH': ['cash', 'money market', 'deposit', 'liquid', 'short-term'],
        'REAL_ESTATE': ['real estate', 'property', 'reit', 'land', 'building'],
        'ALTERNATIVES': ['hedge', 'private equity', 'venture', 'alternative', 'private', 'partnerships'],
        'COMMODITIES': ['commodity', 'gold', 'silver', 'metal', 'oil', 'natural resource'],
        'DERIVATIVES': ['option', 'future', 'swap', 'forward', 'derivative'],
        'STRUCTURED': ['structured', 'certificate', 'note', 'hybrid'],
        'INSURANCE': ['insurance', 'annuity', 'policy']
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
                'title': {'text': 'Year'},
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

class InvestmentAnalyzer:
    """Handle investment data analysis and calculations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['actual_year'].unique())
        self.categories = self.df['description'].unique()
        self.yearly_totals = self._calculate_yearly_totals()
        
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the dataframe"""
        df = df.copy()
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['actual_year'] = (df['year'] - 1).astype(int)
        df['book_value'] = pd.to_numeric(
            df['book_value'], 
            errors='coerce'
        )
        df = df[
            df['book_value'].notna() & 
            (df['book_value'] != 0)
        ]
        df['description'] = df[
            'description'
        ].apply(lambda x: ' '.join(word.capitalize() for word in x.lower().split()))
        return df.sort_values('actual_year')
    
    def _calculate_yearly_totals(self) -> pd.DataFrame:
        """Calculate yearly totals and growth metrics"""
        totals = self.df.groupby('actual_year')[
            'book_value'
        ].sum().reset_index()
        totals.columns = ['year', 'total_value']
        totals['yoy_change'] = totals['total_value'].pct_change() * 100
        return totals
    
    def calculate_rolling_cagr(self, window=3) -> List[float]:
        """Calculate rolling CAGR for the series"""
        cagr_values = []
        totals = self.yearly_totals['total_value'].tolist()
        
        for i in range(len(totals)):
            if i < window-1:
                cagr_values.append(None)
                continue
            
            start_value = totals[i - (window-1)]
            end_value = totals[i]
            
            try:
                cagr = ((end_value / start_value) ** (1/window) - 1) * 100
                cagr_values.append(round(cagr, 1))
            except (ValueError, ZeroDivisionError):
                cagr_values.append(None)
        
        return cagr_values
    
    def calculate_overall_cagr(self) -> float:
        """Calculate overall CAGR"""
        if len(self.yearly_totals) < 2:
            return 0.0
            
        start_value = self.yearly_totals['total_value'].iloc[0]
        end_value = self.yearly_totals['total_value'].iloc[-1]
        n_years = len(self.yearly_totals) - 1
        
        try:
            return ((end_value / start_value) ** (1/n_years) - 1) * 100
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def get_category_series_data(self) -> List[Dict[str, Any]]:
        """Get series data for category chart with consistent colors"""
        series_data = []
        
        for category in self.categories:
            data = []
            for year in self.years:
                value = self.df[
                    (self.df['description'] == category) & 
                    (self.df['actual_year'] == year)
                ]['book_value'].values
                data.append(float(value[0])/1e6 if len(value) > 0 else None)
            
            series_data.append({
                'name': category,
                'data': data,
                'color': self._get_category_color(category)
            })
        
        return series_data
    
    def _get_category_color(self, category: str) -> str:
        """Determine color based on asset class keywords"""
        category_lower = category.lower()
        
        for asset_class, keywords in ChartConfig.ASSET_CLASS_KEYWORDS.items():
            if any(keyword in category_lower for keyword in keywords):
                return ChartConfig.COLORS['asset_classes'][asset_class]
        
        return ChartConfig.COLORS['default']
    
    def create_categories_config(self) -> Dict:
        """Create investment categories chart configuration"""
        common_settings = ChartConfig.get_common_settings([f"FY {year}" for year in self.years])
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': 'Investment - Other Securities'
            },
            'yAxis': {
                'title': {'text': 'Value (millions $)'},
                'labels': {'format': '${value:.1f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:.1f}M'
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'valueSuffix': ' million $',
                'valueDecimals': 1
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': self.get_category_series_data()
        }
    
    def create_growth_config(self) -> Dict:
        """Create growth analysis chart configuration"""
        common_settings = ChartConfig.get_common_settings([f"FY {year}" for year in self.years])
        rolling_cagr = self.calculate_rolling_cagr(window=3)
        overall_cagr = self.calculate_overall_cagr()
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': f'Growth Rate (Overall CAGR: {overall_cagr:.1f}%)'
            },
            'yAxis': [{
                'title': {'text': 'Growth Rate (%)'},
                'labels': {'format': '{value:.1f}%'},
                'plotLines': [{
                    'value': 0,
                    'color': '#666',
                    'width': 1,
                    'zIndex': 5
                }]
            }],
            'tooltip': {
                'shared': True,
                'useHTML': True
            },
            'series': [
                {
                    'name': 'YoY Change',
                    'type': 'column',
                    'data': self.yearly_totals['yoy_change'].round(1).tolist(),
                    'color': ChartConfig.COLORS['positive'],
                    'tooltip': {
                        'valueSuffix': '%'
                    }
                },
                {
                    'name': '3-Year Rolling CAGR',
                    'type': 'line',
                    'data': rolling_cagr,
                    'color': ChartConfig.COLORS['negative'],
                    'tooltip': {
                        'valueSuffix': '%'
                    },
                    'marker': {
                        'enabled': True,
                        'radius': 4
                    }
                }
            ]
        }

    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        overall_cagr = self.calculate_overall_cagr()
        start_year = str(self.years[0])
        end_year = str(self.years[-1])
        
        # Determine the color based on CAGR value
        color = ChartConfig.COLORS['positive'] if overall_cagr >= 0 else ChartConfig.COLORS['negative']
        
        return f"""
        <div style="
            grid-column: 1 / -1; 
            text-align: center; 
            margin: 10px auto; 
            padding: 10px; 
            background-color: #f8f9fa; 
            border-radius: 5px; 
            max-width: 500px;
        ">
            <strong>Analysis Period: FY {start_year}–{end_year}</strong><br>
            <strong>Overall Portfolio Growth: <span style="color: {color};">CAGR: {overall_cagr:.1f}%</span></strong><br>
        </div>
        """

    def create_charts(self) -> str:
        """Create all investment charts with synchronized hovering"""
        categories_config = self.create_categories_config()
        growth_config = self.create_growth_config()
        return self._create_html(categories_config, growth_config)
    
    def _create_html(self, categories_config: Dict, growth_config: Dict) -> str:
        """Create HTML with charts and synchronized hovering"""
        return f"""
        <div id="charts-container" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div id="investment-categories-chart" style="min-width: 200px;"></div>
            <div id="investment-growth-chart" style="min-width: 200px;"></div>
            {self.create_summary_stats_html()}
        </div>
        
        <script src="{ChartConfig.CDN_URLS['base']}"></script>
        <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
        <script>
            const charts = [];
            let hoverTimeout;
            
            const COLORS = {{
                positive: '{ChartConfig.COLORS["positive"]}',
                negative: '{ChartConfig.COLORS["negative"]}'
            }};
            
            function createTooltipFormatter(valueSuffix, isCategory = false) {{
                return function() {{
                    if (!this.points || this.points.length === 0) {{
                        return '';
                    }}
                    
                    let total = 0;
                    let tooltip = `<div style="font-size: 12px;">
                        <b style="font-size: 13px;">${{this.x}}</b><br/>`;
                    
                    this.points.forEach(point => {{
                        if (!point || typeof point.y === 'undefined' || point.y === null) {{
                            return; // Skip points with undefined or null y-values
                        }}
                        
                        const isValidNumber = typeof point.y === 'number' && !isNaN(point.y);
                        const value = isValidNumber ? point.y.toFixed(1) : 'N/A';
                        const isPositive = isValidNumber ? (point.y >= 0) : true; // Default to positive if not a number
                        const valueColor = isPositive ? COLORS.positive : COLORS.negative;
                        
                        tooltip += `<div style="display: flex; justify-content: space-between; margin: 3px 0;">
                            <span><span style="color:${{point.series.color}}">●</span> ${{point.series.name}}:</span>
                            <span style="color:${{valueColor}}; margin-left: 15px;">${{isCategory ? '$' : ''}}${{value}}${{valueSuffix}}</span>
                        </div>`;
                        
                        if (isCategory && isValidNumber) {{
                            total += point.y;
                        }}
                    }});
                    
                    if (isCategory && !isNaN(total)) {{
                        tooltip += `<div style="border-top: 1px solid #ddd; margin-top: 3px; padding-top: 3px;">
                            <b>Total: $${{total.toFixed(1)}}${{valueSuffix}}</b>
                        </div>`;
                    }}
                    
                    tooltip += '</div>';
                    return tooltip;
                }};
            }}

            function syncHover(e) {{
                clearTimeout(hoverTimeout);
                const pointIndex = e.target.index;
                
                charts.forEach(chart => {{
                    if (chart && chart !== e.target.series.chart) {{
                        // Collect valid points for the same index
                        const pointsToShow = chart.series.map(series => {{
                            const point = series.points[pointIndex];
                            return (point && point.y !== null) ? point : null;
                        }}).filter(point => point !== null);
                        
                        if (pointsToShow.length > 0) {{
                            chart.tooltip.refresh(pointsToShow);
                            // Optionally, draw crosshairs if needed
                            // chart.xAxis[0].drawCrosshair(e, pointsToShow[0]);
                        }}
                    }}
                }});
            }}

            function syncMouseOut(e) {{
                hoverTimeout = setTimeout(() => {{
                    charts.forEach(chart => {{
                        if (chart && chart.tooltip) {{
                            chart.tooltip.hide();
                            chart.xAxis[0].hideCrosshair();
                        }}
                    }});
                }}, 50);
            }}

            document.addEventListener('DOMContentLoaded', function() {{
                // Create categories chart
                const categoriesOptions = {json.dumps(categories_config)};
                categoriesOptions.tooltip.formatter = createTooltipFormatter(' million $', true);
                categoriesOptions.plotOptions = {{
                    column: {{
                        stacking: 'normal',
                        borderWidth: 0,
                        borderRadius: 4,
                        point: {{
                            events: {{
                                mouseOver: syncHover,
                                mouseOut: syncMouseOut
                            }}
                        }}
                    }}
                }};
                charts.push(Highcharts.chart('investment-categories-chart', categoriesOptions));

                // Create growth chart
                const growthOptions = {json.dumps(growth_config)};
                growthOptions.tooltip.formatter = createTooltipFormatter('%');
                growthOptions.plotOptions = {{
                    column: {{
                        point: {{
                            events: {{
                                mouseOver: syncHover,
                                mouseOut: syncMouseOut
                            }}
                        }}
                    }},
                    line: {{
                        point: {{
                            events: {{
                                mouseOver: syncHover,
                                mouseOut: syncMouseOut
                            }}
                        }}
                    }}
                }};
                charts.push(Highcharts.chart('investment-growth-chart', growthOptions));

                // Fix for tooltip positioning
                charts.forEach(chart => {{
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
                            x: x,
                            y: y - labelHeight - 10
                        }};
                    }};
                }});
            }});
        </script>
        """


def display_investment_categories(df: pd.DataFrame) -> None:
    """Display investment categories analysis using Streamlit components."""
    try:
        # Create analyzer and generate charts
        analyzer = InvestmentAnalyzer(df)
        html_content = analyzer.create_charts()
        
        # Display charts
        st.components.v1.html(html_content, height=600)
        
        # Display methodology explanation
        with st.expander("📈 Investment Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Charts

            #### 1. Investment Portfolio Distribution
            Shows the breakdown of investments by category over time:
            * Stacked columns represent different investment types
            * Values are shown in millions of dollars
            * Categories are color-coded by asset class
            * Hover to see detailed values for each category

            #### 2. Growth Analysis
            Shows two complementary growth metrics:
            * **Year-over-Year (YoY) Change**: Immediate annual changes (columns)
            * **3-Year Rolling CAGR**: Smoothed growth trend over 3-year periods (line)
            * Overall CAGR shown in title provides long-term perspective

            ### Notes on Interpretation
            * **Green values** indicate positive returns/growth
            * **Pink values** indicate negative returns/decline
            * **CAGR** smooths out short-term volatility to show trend
            * **YoY** helps identify specific strong/weak periods

            ### Asset Class Categories
            Categories are automatically classified into:
            * Fixed Income (Bonds, Treasury Securities, Notes)
            * Equity (Stocks, Shares)
            * Cash and Equivalents (Money Market, Short-term Deposits)
            * Real Estate (Properties, REITs)
            * Alternative Investments (Hedge Funds, Private Equity)
            * Commodities (Gold, Oil, Natural Resources)
            * Derivatives (Options, Futures, Swaps)
            * Structured Products (Certificates, Hybrid Securities)
            * Insurance Products (Annuities, Policies)

            ### Data Processing Notes
            * Values are converted to millions for better readability
            * Zero and missing values are excluded from calculations
            * Categories are standardized and capitalized
            * Years shown reflect the actual investment period (one year before filing)
            * CAGR calculations handle both positive and negative growth periods

            ### Interactive Features
            * Hover over any data point to see detailed values
            * Charts are synchronized - hovering on one chart highlights the same year in both
            * Use the download menu to export charts as PNG, JPG, PDF, or SVG
            * Click legend items to show/hide specific categories or series
            """)
    except Exception as e:
        st.error(f"Error displaying investment analysis: {str(e)}")