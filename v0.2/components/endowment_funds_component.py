import streamlit as st
import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for Highcharts endowment visualizations"""
    
    COLORS = {
        'balance': '#059669',      # Deep emerald green for beginning balance
        'contributions': '#3B82F6', # Bright blue for contributions
        'earnings': '#10B981',     # Medium green for earnings
        'expenditures': '#EC4899', # Pink for expenditures
        'other': '#9333EA',        # Purple for other metrics
        
        # New composition-specific colors
        'composition': {
            'board': '#EC4899',   
            'permanent': '#059669', # Emerald green for permanent endowment
            'term': '#7C3AED'      # Rich purple for term endowment
        }
    }

    CDN_URLS = {
        'base': 'https://code.highcharts.com/highcharts.js',
        'exporting': 'https://code.highcharts.com/modules/exporting.js',
        'accessibility': 'https://code.highcharts.com/modules/accessibility.js'  # Accessibility Module
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
            'accessibility': {  # Accessibility Settings
                'enabled': True,
                'description': 'Endowment Financial Analysis Charts'
            }
        }

class EndowmentAnalyzer:
    """Handle endowment data analysis and calculations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.years = sorted(self.df['year'].unique())
        self.metrics = self._calculate_endowment_metrics()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the endowment dataframe"""
        df = df.copy()
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        financial_columns = [
            'beginning_balance', 'end_balance', 'investment_earnings',
            'contributions', 'other_expenditures'
        ]
        for col in financial_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        pct_columns = [
            'board_designated_pct', 'permanent_endowment_pct',
            'term_endowment_pct'
        ]
        for col in pct_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce') * 100
        
        # Calculate return rates
        df['return_rate'] = (
            df['investment_earnings'] / df['beginning_balance'] * 100
        )
        
        return df.sort_values('year', ascending=True)
    
    def _calculate_endowment_metrics(self) -> Dict[str, Any]:
        """Calculate key endowment metrics"""
        latest_data = self.df.iloc[-1]
        first_data = self.df.iloc[0]
        
        # Calculate time-weighted return metrics
        return_rates = self.calculate_return_rates()
        
        return {
            'current_balance': latest_data['end_balance'],
            'avg_return_rate': np.mean([r for r in return_rates if r is not None]),
            'total_contributions': self.df['contributions'].sum(),
            'total_earnings': self.df['investment_earnings'].sum(),
            'growth_rate': (
                (latest_data['end_balance'] / first_data['beginning_balance']) 
                ** (1/len(self.df)) - 1
            ) * 100,
            'current_composition': {
                'board_designated': latest_data['board_designated_pct'],
                'permanent': latest_data['permanent_endowment_pct'],
                'term': latest_data['term_endowment_pct']
            }
        }

    def calculate_return_rates(self) -> List[float]:
        """Calculate annual return rates based on beginning balance"""
        return (
            self.df['investment_earnings'] / self.df['beginning_balance'] * 100
        ).tolist()

    def calculate_yoy_return_change(self) -> List[float]:
        """Calculate year-over-year change in return rates"""
        return_rates = self.calculate_return_rates()
        yoy_changes = []
        
        for i in range(len(return_rates)):
            if i == 0:
                yoy_changes.append(None)
                continue
                
            yoy_change = return_rates[i] - return_rates[i-1]
            yoy_changes.append(yoy_change)
            
        return yoy_changes

    def calculate_rolling_return_cagr(self, window: int = 2) -> List[float]:
        """Calculate rolling CAGR of return rates"""
        return_rates = self.calculate_return_rates()
        rolling_cagr = []
        
        for i in range(len(return_rates)):
            if i < window - 1:
                rolling_cagr.append(None)
                continue
                
            # Convert return rates to decimals and add 1
            period_returns = [1 + (r/100) for r in return_rates[i-window+1:i+1]]
            # Calculate geometric mean
            cagr = (np.prod(period_returns) ** (1/window) - 1) * 100
            rolling_cagr.append(cagr)
            
        return rolling_cagr
    
    def get_balance_series_data(self) -> List[Dict[str, Any]]:
        """Get series data for balance breakdown chart"""
        return [
            {
                'name': 'Beginning Balance',
                'data': [val/1e6 for val in self.df['beginning_balance'].tolist()],
                'color': ChartConfig.COLORS['balance']
            },
            {
                'name': 'Contributions',
                'data': [val/1e6 for val in self.df['contributions'].tolist()],
                'color': ChartConfig.COLORS['contributions']
            },
            {
                'name': 'Investment Earnings',
                'data': [val/1e6 for val in self.df['investment_earnings'].tolist()],
                'color': ChartConfig.COLORS['earnings']
            },
            {
                'name': 'Other Expenditures',
                'data': [-val/1e6 for val in self.df['other_expenditures'].tolist()],
                'color': ChartConfig.COLORS['expenditures']
            }
        ]
    
    def create_balance_config(self) -> Dict:
        """Create endowment balance chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500,
                'marginTop': 50
            },
            'title': {
                **common_settings['title'],
                'text': 'Endowment Balance Components'
            },
            'yAxis': {
                'title': {'text': 'Amount (Millions $)'},
                'labels': {'format': '${value:,.0f}M'},
                'stackLabels': {
                    'enabled': True,
                    'format': '${total:,.0f}M'
                }
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                # Use {point.key} instead of {point.x}
                'headerFormat': '<div style="font-size: 14px; font-weight: 500; margin-bottom: 8px;">{point.key}</div>',
                'pointFormat': (
                    '<span style="color:{series.color};">\u2022</span> '
                    '<strong>{series.name}:</strong> '
                    '<span>${point.y:,.1f}M</span><br/>'
                ),
                'valueDecimals': 1,
                'shadow': True,
                'style': {
                    'fontSize': '12px',
                    'fontFamily': 'Inter, sans-serif'
                }
            },
            'plotOptions': {
                'column': {
                    'stacking': 'normal',
                    'borderWidth': 0,
                    'borderRadius': 4
                }
            },
            'series': self.get_balance_series_data()
        }

    def create_return_analysis_config(self) -> Dict:
        """Create investment return analysis chart configuration (with fixed tooltip)."""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'line',
                'height': 300,
                'marginTop': 50
            },
            'title': {
                **common_settings['title'],
                'text': 'Investment Return Analysis'
            },
            'yAxis': {
                'title': {'text': 'Return Rate (%)'},
                'labels': {'format': '{value:.1f}%'}
            },
            # FIXED TOOLTIP: now shows percentages instead of $M
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                'headerFormat': (
                    '<div style="font-size: 14px; font-weight: 500; '
                    'margin-bottom: 8px;">{point.key}</div>'
                ),
                'pointFormat': (
                    '<span style="color:{series.color};">\u2022</span> '
                    '<strong>{series.name}:</strong> '
                    '<span>{point.y:.1f}%</span><br/>'
                ),
                'valueDecimals': 1,
                'shadow': True,
                'style': {
                    'fontSize': '12px',
                    'fontFamily': 'Inter, sans-serif'
                }
            },
            'plotOptions': {
                'line': {
                    'marker': {'enabled': True},
                    'lineWidth': 2
                }
            },
            'series': [
                {
                    'name': 'Return Rate',
                    'data': self.calculate_return_rates(),
                    'color': ChartConfig.COLORS['earnings'],
                    'zIndex': 3
                },
                {
                    'name': '2-Year Rolling CAGR',
                    'data': self.calculate_rolling_return_cagr(window=2),
                    'color': ChartConfig.COLORS['balance'],
                    'dashStyle': 'shortdot',
                    'zIndex': 2
                },
                {
                    'name': 'YoY Change',
                    'data': self.calculate_yoy_return_change(),
                    'color': ChartConfig.COLORS['other'],
                    'dashStyle': 'shortdash',
                    'zIndex': 1
                }
            ]
        }
    
    def create_composition_config(self) -> Dict:
        """Create endowment composition chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'area',
                'height': 500,
                'marginTop': 50
            },
            'title': {
                **common_settings['title'],
                'text': 'Endowment Composition Analysis'
            },
            'yAxis': {
                'title': {'text': 'Percentage (%)'},
                'labels': {'format': '{value}%'},
                'min': 0,
                'max': 100,
                'tickInterval': 20,
                'gridLineWidth': 1
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                'headerFormat': (
                    '<div style="font-size: 14px; font-weight: 500; '
                    'margin-bottom: 8px;">{point.key}</div>'
                ),
                'pointFormat': (
                    '<span style="color:{series.color};">•</span> '
                    '<strong>{series.name}:</strong> '
                    '<span>{point.y:.1f}%</span><br/>'
                ),
                'valueDecimals': 1,
                'shadow': True,
                'style': {
                    'fontSize': '12px',
                    'fontFamily': 'Inter, sans-serif'
                }
            },
            'plotOptions': {
                'area': {
                    'stacking': 'percent',
                    'lineWidth': 1,
                    'marker': {
                        'enabled': False,
                        'radius': 2,
                        'states': {
                            'hover': {
                                'enabled': True
                            }
                        }
                    },
                    'states': {
                        'hover': {
                            'lineWidth': 2
                        }
                    }
                }
            },
            'series': [
                {
                    'name': 'Board Designated',
                    'data': self.df['board_designated_pct'].tolist(),
                    'color': ChartConfig.COLORS['composition']['board'],
                    'fillOpacity': 0.8
                },
                {
                    'name': 'Permanent',
                    'data': self.df['permanent_endowment_pct'].tolist(),
                    'color': ChartConfig.COLORS['composition']['permanent'],
                    'fillOpacity': 0.8
                },
                {
                    'name': 'Term',
                    'data': self.df['term_endowment_pct'].tolist(),
                    'color': ChartConfig.COLORS['composition']['term'],
                    'fillOpacity': 0.8
                }
            ]
        }

    def calculate_contribution_metrics(self) -> Dict[str, List[float]]:
        """Calculate contribution-related metrics"""
        metrics = {
            'contribution_ratio': [],
            'expenditure_ratio': [],  # Added expenditure_ratio
            'total_return': [],
            'irr': []
        }
        
        for i in range(len(self.df)):
            end_balance = self.df.iloc[i]['end_balance']
            contributions = self.df.iloc[i]['contributions']
            expenditures = self.df.iloc[i]['other_expenditures']
            
            # Avoid division by zero
            if end_balance != 0 and not np.isnan(end_balance):
                metrics['contribution_ratio'].append((contributions / end_balance) * 100)
                metrics['expenditure_ratio'].append((expenditures / end_balance) * 100)
            else:
                metrics['contribution_ratio'].append(None)
                metrics['expenditure_ratio'].append(None)
            
            # Calculate total return (capital gains + income)
            investment_earnings = self.df.iloc[i]['investment_earnings']
            beginning_balance = self.df.iloc[i]['beginning_balance']
            total_return = (
                (investment_earnings + (end_balance - beginning_balance - contributions)) 
                / beginning_balance * 100
            )
            metrics['total_return'].append(total_return)
            
            # Calculate simplified IRR 
            # (using a basic approximation for demonstration)
            if i == 0:
                metrics['irr'].append(None)
            else:
                prev_balance = self.df.iloc[i-1]['end_balance']
                curr_balance = end_balance
                if prev_balance != 0 and not np.isnan(prev_balance):
                    periodic_irr = ((curr_balance / prev_balance) ** (1/1) - 1) * 100
                    metrics['irr'].append(periodic_irr)
                else:
                    metrics['irr'].append(None)
        
        return metrics


    def create_contribution_analysis_config(self) -> Dict:
        """Create contribution analysis chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        metrics = self.calculate_contribution_metrics()
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 300
            },
            'title': {
                **common_settings['title'],
                'text': 'Contribution and Expenditure Analysis'
            },
            'yAxis': {
                'title': {'text': 'Ratio (%)'},  # Updated title to reflect multiple ratios
                'labels': {'format': '{value:.1f}%'},
                'min': 0
            },
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                'headerFormat': (
                    '<div style="font-size: 14px; font-weight: 500; '
                    'margin-bottom: 8px;">{point.key}</div>'
                ),
                'pointFormat': (
                    '<span style="color:{series.color};">•</span> '
                    '<strong>{series.name}:</strong> '
                    '<span>{point.y:.1f}%</span><br/>'
                )
            },
            'plotOptions': {
                'column': {
                    'borderRadius': 4,
                    'borderWidth': 0
                }
            },
            'series': [
                {
                    'name': 'Contribution Ratio',
                    'data': metrics['contribution_ratio'],
                    'color': ChartConfig.COLORS['contributions']
                },
                {
                    'name': 'Expenditure Ratio',  # New series for Expenditure Ratio
                    'data': metrics['expenditure_ratio'],
                    'color': ChartConfig.COLORS['expenditures']
                }
            ]
        }


    def create_total_return_config(self) -> Dict:
        """Create total return analysis chart configuration"""
        years = [f"FY {year}" for year in self.years]
        common_settings = ChartConfig.get_common_settings(years)
        metrics = self.calculate_contribution_metrics()
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'line',
                'height': 300
            },
            'title': {
                **common_settings['title'],
                'text': 'Total Return Investment Analysis'
            },
            'yAxis': {
                'title': {'text': 'Return (%)'},
                'labels': {'format': '{value:.1f}%'}
            },
            # FIXED TOOLTIP for % data
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'backgroundColor': '#ffffff',
                'borderColor': '#e5e7eb',
                'borderRadius': 8,
                'padding': 12,
                'headerFormat': (
                    '<div style="font-size: 14px; font-weight: 500; '
                    'margin-bottom: 8px;">{point.key}</div>'
                ),
                'pointFormat': (
                    '<span style="color:{series.color};">•</span> '
                    '<strong>{series.name}:</strong> '
                    '<span>{point.y:.1f}%</span><br/>'
                )
            },
            'plotOptions': {
                'line': {
                    'marker': {'enabled': True},
                    'lineWidth': 2
                }
            },
            'series': [
                {
                    'name': 'Total Return',
                    'data': metrics['total_return'],
                    'color': ChartConfig.COLORS['earnings'],
                    'zIndex': 2
                },
                {
                    'name': 'Internal Rate of Return',
                    'data': metrics['irr'],
                    'color': ChartConfig.COLORS['other'],
                    'dashStyle': 'shortdot',
                    'zIndex': 1
                }
            ]
        }

    def create_summary_stats_html(self) -> str:
        """Create HTML for the summary statistics container"""
        metrics = self.metrics
        composition = metrics['current_composition']
        
        return f"""
        <div style="grid-column: 1 / -1; text-align: center; margin: 10px auto; 
                    padding: 10px; background-color: #f8f9fa; border-radius: 5px; 
                    max-width: 800px;">
            <strong>Endowment Summary</strong><br>
            <span style="color: {ChartConfig.COLORS['balance']}">
                Current Balance: ${metrics['current_balance']/1e6:,.1f}M</span> | 
            <span style="color: {ChartConfig.COLORS['earnings']}">
                Average Return Rate: {metrics['avg_return_rate']:.1f}% | 
                CAGR: {metrics['growth_rate']:.1f}%</span><br>
            <span style="color: {ChartConfig.COLORS['contributions']}">
                Total Contributions: ${metrics['total_contributions']/1e6:,.1f}M | 
                Total Earnings: ${metrics['total_earnings']/1e6:,.1f}M</span><br>
            Current Composition: 
            Board Designated: {composition['board_designated']:.1f}% | 
            Permanent: {composition['permanent']:.1f}% | 
            Term: {composition['term']:.1f}%
        </div>
        """

    def create_charts(self) -> str:
        """Create all endowment charts with synchronized hovering"""
        balance_config = self.create_balance_config()
        composition_config = self.create_composition_config()
        return_analysis_config = self.create_return_analysis_config()
        contribution_config = self.create_contribution_analysis_config()
        total_return_config = self.create_total_return_config()
        
        return self._create_html(
            balance_config, 
            composition_config, 
            return_analysis_config,
            contribution_config,
            total_return_config
        )

    def _create_html(self, 
                    balance_config: Dict, 
                    composition_config: Dict, 
                    return_analysis_config: Dict,
                    contribution_config: Dict,
                    total_return_config: Dict) -> str:
        """
        Create HTML with synchronized charts and custom tooltips.
        
        Args:
            balance_config: Configuration for the balance chart
            composition_config: Configuration for the composition chart
            return_analysis_config: Configuration for the return analysis chart
            contribution_config: Configuration for the contribution analysis chart
            total_return_config: Configuration for the total return analysis chart
            
        Returns:
            str: Complete HTML document with embedded charts
        """
        charts_container = """
            <div id="charts-container">
                <div id="balance-composition-chart" style="min-width: 200px;"></div>
                <div id="endowment-composition-chart" style="min-width: 200px;"></div>
                <div id="return-analysis-chart" style="grid-column: 1 / -1; min-width: 200px;"></div>
                <div id="contribution-analysis-chart" style="min-width: 200px;"></div>
                <div id="total-return-chart" style="min-width: 200px;"></div>
                {self.create_summary_stats_html()}
            </div>
        """
        
        # Add initialization for new charts
        charts_init = """
            charts.push(Highcharts.chart('contribution-analysis-chart', contributionConfig));
            charts.push(Highcharts.chart('total-return-chart', totalReturnConfig));
        """
                
        def prepare_chart_data():
            """Prepare the chart data and configurations."""
            # Convert end balance to millions and round to 2 decimal places
            end_balance_millions = [round(val/1e6, 2) for val in self.df['end_balance'].tolist()]
            # Prepare fiscal years array
            fiscal_years = [f"FY {year}" for year in self.df['year'].tolist()]
            
            # Remove tooltip from balance config for custom implementation
            balance_tooltip = balance_config.pop('tooltip', {})
            
            return {
                'end_balance': json.dumps(end_balance_millions),
                'fiscal_years': json.dumps(fiscal_years),
                'balance_config': json.dumps(balance_config),
                'composition_config': json.dumps(composition_config),
                'return_analysis_config': json.dumps(return_analysis_config),
                # We also include contribution & total_return configs 
                # if you'd like to unify them in the same container
                'contribution_config': json.dumps(contribution_config),
                'total_return_config': json.dumps(total_return_config)
            }
        
        def get_custom_tooltip_formatter():
            """Return the custom tooltip formatter JavaScript function."""
            return """
            function() {
                // Get the current index and corresponding fiscal year
                if (!this.points || !this.points.length) {
                    return '';
                }
                const idx = this.points[0].point.index;
                const fiscalYear = fiscalYears[idx];
                
                // Format header with fiscal year
                let s = `<div style="font-size:14px; font-weight:500; margin-bottom:8px;">${fiscalYear}</div>`;
                
                // Add each data point
                this.points.forEach(point => {
                    s += `<span style="color:${point.series.color}">•</span> `
                        + `<strong>${point.series.name}:</strong> `
                        + `<span>$${Highcharts.numberFormat(point.y, 1)}M</span><br/>`;
                });
                
                // Add separator and end balance
                s += '<hr style="margin:6px 0;"/>';
                const balance = endBalanceData[idx];
                s += `<span>• <strong>End Balance:</strong> $${Highcharts.numberFormat(balance, 1)}M</span>`;
                
                return s;
            }
            """
        
        def get_balance_chart_config(chart_data):
            """Generate the balance chart configuration with custom tooltip."""
            return f"""
            (function() {{
                const cfg = {chart_data['balance_config']};
                
                cfg.tooltip = {{
                    shared: true,
                    useHTML: true,
                    backgroundColor: '#ffffff',
                    borderColor: '#e5e7eb',
                    borderRadius: 8,
                    padding: 12,
                    shadow: true,
                    style: {{
                        fontSize: '12px',
                        fontFamily: 'Inter, sans-serif'
                    }},
                    formatter: {get_custom_tooltip_formatter()}
                }};
                
                return cfg;
            }})()
            """
        
        def get_styles():
            """Return the CSS styles for the charts container."""
            return """
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
        
        def get_charts_initialization_script(chart_data):
            """Generate the JavaScript for initializing and synchronizing charts."""
            return f"""
                const endBalanceData = {chart_data['end_balance']};
                const fiscalYears = {chart_data['fiscal_years']};
                const compositionConfig = {chart_data['composition_config']};
                const returnAnalysisConfig = {chart_data['return_analysis_config']};
                const contributionConfig = {chart_data['contribution_config']};
                const totalReturnConfig = {chart_data['total_return_config']};
                const balanceConfig = {get_balance_chart_config(chart_data)};

                document.addEventListener('DOMContentLoaded', function() {{
                    const initializeCharts = () => {{
                        if (typeof Highcharts === 'undefined') {{
                            setTimeout(initializeCharts, 100);
                            return;
                        }}
                        
                        const charts = [];
                        charts.push(Highcharts.chart('balance-composition-chart', balanceConfig));
                        charts.push(Highcharts.chart('endowment-composition-chart', compositionConfig));
                        charts.push(Highcharts.chart('return-analysis-chart', returnAnalysisConfig));
                        charts.push(Highcharts.chart('contribution-analysis-chart', contributionConfig));
                        charts.push(Highcharts.chart('total-return-chart', totalReturnConfig));

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
            """
        
        # Prepare all components
        chart_data = prepare_chart_data()
        
        # Construct the final HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{get_styles()}</style>
        </head>
        <body>
            <div id="charts-container">
                <div id="balance-composition-chart" style="min-width: 200px;"></div>
                <div id="endowment-composition-chart" style="min-width: 200px;"></div>
                <div id="return-analysis-chart" style="grid-column: 1 / -1; min-width: 200px;"></div>
                <div id="contribution-analysis-chart" style="min-width: 200px;"></div>
                <div id="total-return-chart" style="min-width: 200px;"></div>
                {self.create_summary_stats_html()}
            </div>
            
            <!-- Load Highcharts scripts -->
            <script src="{ChartConfig.CDN_URLS['base']}"></script>
            <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
            <script src="{ChartConfig.CDN_URLS['accessibility']}"></script>
            
            <!-- Initialize charts -->
            <script>{get_charts_initialization_script(chart_data)}</script>
        </body>
        </html>
        """

def display_endowment_analysis(df: pd.DataFrame) -> None:
    """Display endowment analysis using Streamlit components."""
    try:
        # Create analyzer and generate charts
        analyzer = EndowmentAnalyzer(df)
        html_content = analyzer.create_charts()
        
        # Display charts in Streamlit
        st.components.v1.html(html_content, height=1300, scrolling=False)
        
        # Display methodology explanation
        with st.expander("💰 Endowment Analysis Methodology", expanded=False):
            st.markdown("""
            ### Understanding the Analysis
            
            This analysis provides a comprehensive view of the endowment's performance and composition through several visualizations:

            **1. Balance Components Chart**  
            Breaks down the endowment's financial components:
            - Beginning Balance  
            - Contributions  
            - Investment Earnings  
            - Other Expenditures  

            **2. Composition Analysis Chart**  
            Distribution of funds across three categories:
            - Board Designated  
            - Permanent Endowment  
            - Term Endowment  

            **3. Investment Return Analysis Chart**  
            Shows key metrics:  
            - Return Rate (% of beginning balance)  
            - YoY Change in return rates (percentage points)  
            - 2-Year Rolling CAGR  

            **4. Contribution Analysis**  
            Highlights contribution ratio relative to end-balance.  

            **5. Total Return Analysis**  
            Combines capital gains + income and a simplified IRR approximation.  

            **Key Performance Metrics**:  
            - Current Balance  
            - Average Return Rate  
            - CAGR (Compound Annual Growth Rate)  
            - Total Contributions & Earnings  

            **Data Processing Notes**:  
            - Financial values normalized to millions of dollars.  
            - Return rates use beginning balance as denominator.  
            - Missing/invalid data handled gracefully.
            """)
    except Exception as e:
        st.error(f"Error displaying endowment analysis: {str(e)}")
