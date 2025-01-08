import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List

class ChartConfig:
    """Base configuration for employee visualization charts"""
    
    COLORS = {
        'primary': '#059669',
        'secondary': '#3B82F6',
        'compensation': '#FF6B6B',
        'tenure': '#A855F7',
        'historical': '#4B5563'
    }
    
    CDN_URLS = {
        'base': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/highcharts.min.js',
        'exporting': 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/9.0.1/modules/exporting.js'
    }
    
    @staticmethod
    def get_common_settings() -> Dict[str, Any]:
        return {
            'chart': {
                'style': {'fontFamily': 'Inter, sans-serif'},
                'spacing': [10, 10, 10, 10],
                'backgroundColor': '#ffffff'
            },
            'title': {
                'align': 'center',
                'style': {'fontSize': '14px', 'fontWeight': '500'},
            },
            'credits': {'enabled': False},
            'legend': {
                'align': 'center',
                'verticalAlign': 'bottom',
                'layout': 'horizontal',
                'borderWidth': 0
            }
        }

class EmployeeMetricsAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.latest_year = self.df['year'].max()
        self.current_employees = self._get_current_employees()
        self.category_metrics = self._calculate_category_metrics()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Convert numeric columns
        numeric_cols = ['year', 'comp_org', 'comp_related', 'other_comp', 'total_compensation']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean text columns and handle missing values
        text_cols = ['name', 'title', 'role_category']
        for col in text_cols:
            df[col] = df[col].str.strip()
        
        df['role_category'] = df['role_category'].fillna('Other')
        
        # Print unique role categories to debug
        print("Unique role categories in data:", sorted(df['role_category'].unique()))
        
        return df.sort_values(['year', 'total_compensation'], ascending=[True, False])
    
    def _get_current_employees(self) -> pd.DataFrame:
        return self.df[self.df['year'] == self.latest_year].copy()
    
    def _calculate_category_metrics(self) -> Dict[str, Dict]:
        category_metrics = {}
        
        for category in sorted(self.current_employees['role_category'].unique()):
            # Current year metrics
            category_df_current = self.current_employees[self.current_employees['role_category'] == category]
            employee_names = category_df_current['name'].unique()
            
            # Historical metrics (excluding current year)
            category_df_historical = self.df[
                (self.df['role_category'] == category) & 
                (self.df['year'] < self.latest_year)
            ]
            
            # Print debugging information
            print(f"\nCategory: {category}")
            print(f"Historical data available: {len(category_df_historical)} records")
            if len(category_df_historical) > 0:
                print(f"Years available: {sorted(category_df_historical['year'].unique())}")
                print(f"Compensation values: {sorted(category_df_historical['total_compensation'].dropna())}")
            
            historical_median = (
                category_df_historical['total_compensation'].median()
                if len(category_df_historical) > 0 else 0
            )
            
            category_metrics[category] = {
                'count': len(category_df_current),
                'median_comp_org': category_df_current['comp_org'].median(),
                'median_total': category_df_current['total_compensation'].median(),
                'historical_median': historical_median,
                'avg_tenure': self._calculate_avg_tenure(employee_names)
            }
        
        return category_metrics
    
    def _calculate_avg_tenure(self, names: List[str]) -> float:
        tenures = []
        for name in names:
            employee_history = self.df[self.df['name'] == name]
            first_year = employee_history['year'].min()
            tenure_years = self.latest_year - first_year + 1
            tenures.append(tenure_years)
        return sum(tenures) / len(tenures) if tenures else 0
    
    def create_category_metrics_chart(self) -> Dict:
        categories = list(self.category_metrics.keys())
        common_settings = ChartConfig.get_common_settings()
        
        return {
            **common_settings,
            'chart': {
                **common_settings['chart'],
                'type': 'column',
                'height': 500
            },
            'title': {
                **common_settings['title'],
                'text': f'Employee Metrics by Role Category ({self.latest_year})'
            },
            'xAxis': {
                'categories': categories,
                'labels': {
                    'style': {'fontSize': '12px'},
                    'rotation': 0
                },
                'crosshair': True
            },
            'yAxis': [{
                'title': {'text': 'Count / Tenure (Years)'},
                'min': 0
            }, {
                'title': {'text': 'Compensation ($k)'},
                'opposite': True,
                'min': 0,
                'labels': {'format': '${value}k'}
            }],
            'tooltip': {
                'shared': True,
                'useHTML': True,
                'headerFormat': '<b>{point.key}</b><br/>',
                'pointFormat': '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y}</b><br/>'
            },
            'plotOptions': {
                'column': {
                    'grouping': True,
                    'pointPadding': 0.1
                }
            },
            'series': [
                {
                    'name': 'Employee Count',
                    'data': [self.category_metrics[cat]['count'] for cat in categories],
                    'color': ChartConfig.COLORS['primary'],
                    'tooltip': {'valueSuffix': ' employees'}
                },
                {
                    'name': 'Average Tenure',
                    'data': [round(self.category_metrics[cat]['avg_tenure'], 1) for cat in categories],
                    'color': ChartConfig.COLORS['tenure'],
                    'tooltip': {'valueSuffix': ' years'}
                },
                {
                    'name': f'Current Median ({self.latest_year})',
                    'data': [round(self.category_metrics[cat]['median_total']/1000, 1) for cat in categories],
                    'yAxis': 1,
                    'type': 'column',
                    'color': ChartConfig.COLORS['compensation'],
                    'tooltip': {
                        'valuePrefix': '$',
                        'valueSuffix': 'k'
                    }
                },
                {
                    'name': 'Historical Median',
                    'data': [round(self.category_metrics[cat]['historical_median']/1000, 1) for cat in categories],
                    'yAxis': 1,
                    'type': 'column',
                    'color': ChartConfig.COLORS['historical'],
                    'tooltip': {
                        'valuePrefix': '$',
                        'valueSuffix': 'k'
                    }
                }
            ]
        }

    def create_summary_stats_html(self) -> str:
        total_employees = sum(data['count'] for data in self.category_metrics.values())
        median_total = self.current_employees['total_compensation'].median()
        avg_tenure = self._calculate_avg_tenure(self.current_employees['name'].unique())
        
        role_counts = {
            category: metrics['count']
            for category, metrics in self.category_metrics.items()
        }
        
        return f"""
        <div style="text-align: center; margin: 10px auto; padding: 15px; background-color: #f8f9fa; border-radius: 5px; max-width: 800px;">
            <strong>Current Employee Summary ({self.latest_year})</strong><br>
            <span style="color: {ChartConfig.COLORS['primary']}">
                Total Employees: {total_employees}<br>
                {' | '.join(f"{cat}: {count}" for cat, count in role_counts.items())}<br>
                Median Total: ${median_total/1000:.1f}k | 
                Average Tenure: {avg_tenure:.1f} years
            </span>
        </div>
        """

    def create_visualization(self) -> str:
        chart_config = self.create_category_metrics_chart()
        
        return f"""
        <div style="padding: 10px;">
            <div id="category-metrics-chart" style="min-width: 200px;"></div>
            {self.create_summary_stats_html()}
        </div>
        
        <script src="{ChartConfig.CDN_URLS['base']}"></script>
        <script src="{ChartConfig.CDN_URLS['exporting']}"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const chartOptions = {json.dumps(chart_config)};
                Highcharts.chart('category-metrics-chart', chartOptions);
            }});
        </script>
        """

def display_employee_metrics(df: pd.DataFrame) -> None:
    try:
        analyzer = EmployeeMetricsAnalyzer(df)
        html_content = analyzer.create_visualization()
        st.components.v1.html(html_content, height=600)
        
        with st.expander("📊 Metrics Analysis Methodology", expanded=False):
            st.markdown(f"""
            ### Metrics Overview
            
            #### Role Categories
            The analysis groups employees by their role categories as defined in the original data.
            
            #### Calculated Metrics
            * Employee Count: Total employees per role category
            * Average Tenure: Years of service (from first appearance)
            * Current Median ({analyzer.latest_year}): Current year's median total compensation
            * Historical Median: Median compensation across all previous years
            
            #### Compensation Components
            * Organization Compensation (comp_org)
            * Related Organization Compensation (comp_related)
            * Other Compensation (other_comp)
            * Total = Sum of all components
            
            ### Analysis Notes
            * Current metrics shown for {analyzer.latest_year}
            * Historical data excludes current year
            * Compensation shown in thousands (k = $1,000)
            * Tenure calculated from earliest record
            """)
            
    except Exception as e:
        st.error(f"Error displaying metrics analysis: {str(e)}")