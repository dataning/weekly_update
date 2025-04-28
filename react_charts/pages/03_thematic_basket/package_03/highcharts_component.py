# highcharts_component.py
import streamlit.components.v1 as components
import streamlit as st
from jinja2 import Template
import json
import pandas as pd
import numpy as np
from typing import List, Union, Optional, Dict, Any

class HighchartsBarComponent:
    """
    A reusable bar/column chart component for Streamlit using Highcharts
    """
    
    def __init__(self, title="Distribution Chart", subtitle=""):
        """
        Initialize the bar chart component
        
        Parameters:
        -----------
        title : str
            Chart title
        subtitle : str
            Chart subtitle
        """
        self.title = title
        self.subtitle = subtitle
        self.js_template = self._get_default_js_template()
        self.html_template = self._get_default_html_template()
    
    def render_histogram(self, values: Union[List[float], np.ndarray, pd.Series],
                         bins: int = 30, 
                         nan_count: int = 0, 
                         height: int = 400, 
                         color_neg: str = "#d40000", 
                         color_pos: str = "#00b52a",
                         bin_width: Optional[float] = None, 
                         bar_width_factor: float = 0.9,  # Controls bar width (0-1)
                         x_label: str = "Value", 
                         y_label: str = "Count", 
                         x_min: Optional[float] = None, 
                         x_max: Optional[float] = None):
        """
        Renders a histogram using Highcharts
        
        Parameters:
        -----------
        values : array-like
            Values to create histogram from
        bins : int
            Number of bins for the histogram
        nan_count : int
            Number of NaN values (will be displayed in the chart)
        height : int
            Height of the chart in pixels
        color_neg : str
            Color for negative values
        color_pos : str
            Color for positive values
        bin_width : float, optional
            Width of each bin. If None, calculated from data range and bins
        x_label : str
            Label for the x-axis
        y_label : str
            Label for the y-axis
        x_min : float, optional
            Minimum value for x-axis. If None, calculated from data
        x_max : float, optional
            Maximum value for x-axis. If None, calculated from data
        """
        # Clean input values (ensure no NaN or inf)
        clean_values = [float(v) for v in values if not pd.isna(v) and not np.isinf(v)]
        
        if not clean_values:
            st.warning("No valid data to create histogram.")
            return
        
        # Calculate histogram bins
        if x_min is None:
            x_min = min(clean_values)
        if x_max is None:
            x_max = max(clean_values)
            
        # Add a small buffer to min and max
        buffer = (x_max - x_min) * 0.1
        x_min -= buffer
        x_max += buffer
        
        if bin_width is None:
            bin_width = (x_max - x_min) / bins
        
        # Calculate histogram
        hist_bins = np.linspace(x_min, x_max, bins + 1)
        hist, bin_edges = np.histogram(clean_values, bins=hist_bins)
        
        # Create data for Highcharts
        histogram_data = []
        for i in range(len(hist)):
            # Use bin midpoints for x values
            x = (bin_edges[i] + bin_edges[i+1]) / 2
            histogram_data.append([x, float(hist[i])])
        
        # Chart settings
        chart_settings = {
            'title': self.title,
            'subtitle': self.subtitle,
            'x_label': x_label,
            'y_label': y_label,
            'color_neg': color_neg,
            'color_pos': color_pos,
            'x_min': x_min,
            'x_max': x_max,
            'bin_width': bin_width,
            'bar_width_factor': bar_width_factor,
            'nan_count': nan_count
        }
        
        # Convert data to JSON
        data_json = json.dumps(histogram_data)
        
        # Customize the JS with settings
        js_with_settings = self._customize_js(chart_settings)
        
        # Render the HTML
        html = Template(self.html_template).render(
            CHART_JS=js_with_settings,
            HISTOGRAM_DATA=data_json
        )
        
        # Display in Streamlit
        components.html(html, height=height, scrolling=False)
    
    def render_column_chart(self, categories: List[str], 
                          series_data: List[Dict[str, Any]], 
                          height: int = 400,
                          x_label: str = "Categories",
                          y_label: str = "Values",
                          stack: bool = False):
        """
        Renders a column chart using Highcharts
        
        Parameters:
        -----------
        categories : list
            List of category names for x-axis
        series_data : list of dict
            List of series data, each with 'name' and 'data' keys
        height : int
            Height of the chart in pixels
        x_label : str
            Label for the x-axis
        y_label : str
            Label for the y-axis
        stack : bool
            Whether to stack the columns
        """
        if not categories or not series_data:
            st.warning("Not enough data to create chart.")
            return
            
        # Chart settings
        chart_settings = {
            'title': self.title,
            'subtitle': self.subtitle,
            'x_label': x_label,
            'y_label': y_label,
            'stack': 'true' if stack else 'false'
        }
        
        # Convert data to JSON
        categories_json = json.dumps(categories)
        series_json = json.dumps(series_data)
        
        # Customize the JS
        js = self._get_column_chart_js_template()
        js = js.replace('__CHART_TITLE__', chart_settings['title'])
        js = js.replace('__CHART_SUBTITLE__', chart_settings['subtitle'])
        js = js.replace('__X_LABEL__', chart_settings['x_label'])
        js = js.replace('__Y_LABEL__', chart_settings['y_label'])
        js = js.replace('__STACK__', chart_settings['stack'])
        
        # Render the HTML
        html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Column Chart</title>

    <!-- Highcharts core + modules -->
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/export-data.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>

    <style>
      html, body {
        margin: 0;
        padding: 0;
        background-color: #252931;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      }
      .highcharts-figure {
        margin: 0;
        padding: 0;
      }
      #container {
        width: 100%;
        height: 100%;
        min-height: 350px;
      }
      .highcharts-description {
        margin: 0.5em 0;
        color: #ccc;
        text-align: center;
        font-size: 0.9em;
      }
    </style>
  </head>

  <body>
    <figure class="highcharts-figure">
      <div id="container"></div>
    </figure>

    <script>
      // Define the data
      const categories = %s;
      const seriesData = %s;
      
      // Render the chart
      %s
    </script>
  </body>
</html>""" % (categories_json, series_json, js)
        
        # Display in Streamlit
        components.html(html, height=height, scrolling=False)
    
    def _customize_js(self, settings: Dict[str, Any]) -> str:
        """Customize the JavaScript with provided settings"""
        js = self.js_template
        
        # Replace placeholders with actual values
        js = js.replace('__CHART_TITLE__', settings['title'])
        js = js.replace('__CHART_SUBTITLE__', settings['subtitle'])
        js = js.replace('__X_LABEL__', settings['x_label'])
        js = js.replace('__Y_LABEL__', settings['y_label'])
        js = js.replace('__COLOR_NEG__', settings['color_neg'])
        js = js.replace('__COLOR_POS__', settings['color_pos'])
        js = js.replace('__X_MIN__', str(settings['x_min']))
        js = js.replace('__X_MAX__', str(settings['x_max']))
        js = js.replace('__BIN_WIDTH__', str(settings['bin_width']))
        js = js.replace('__BAR_WIDTH_FACTOR__', str(settings['bar_width_factor']))
        js = js.replace('__NAN_COUNT__', str(settings['nan_count']))
        
        return js
    
    def _get_default_js_template(self) -> str:
        """Returns the default JavaScript template for the histogram chart"""
        return """
Highcharts.chart('container', {
    chart: {
        type: 'column',
        backgroundColor: '#252931',
        style: {
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            color: 'white'
        }
    },
    title: {
        text: '__CHART_TITLE__',
        style: { color: 'white' }
    },
    subtitle: {
        text: '__CHART_SUBTITLE__',
        style: { color: 'silver' }
    },
    xAxis: {
        title: {
            text: '__X_LABEL__',
            style: { color: 'white' }
        },
        min: __X_MIN__,
        max: __X_MAX__,
        gridLineWidth: 0,
        tickColor: '#606060',
        lineColor: '#606060',
        labels: {
            style: { color: 'white' }
        },
        plotLines: [{
            color: 'red',
            width: 2,
            value: 0,
            zIndex: 5,
            dashStyle: 'shortdash',
            label: {
                text: '0',
                align: 'right',
                style: { color: 'red' }
            }
        }]
    },
    yAxis: {
        title: {
            text: '__Y_LABEL__',
            style: { color: 'white' }
        },
        gridLineColor: '#505050',
        tickColor: '#606060',
        lineColor: '#606060',
        labels: {
            style: { color: 'white' }
        }
    },
    legend: {
        enabled: false
    },
    tooltip: {
        headerFormat: '<b>{point.key:.2f}</b><br/>',
        pointFormat: '{point.y} items'
    },
    plotOptions: {
        column: {
            pointPadding: 0.05,
            borderWidth: 0,
            groupPadding: 0.05,
            shadow: false,
            // Calculate width based on the chart size and number of bars
            pointWidth: null, // Let Highcharts calculate based on paddings
            maxPointWidth: __BIN_WIDTH__ * 20, // Limit maximum width
            pointRange: __BIN_WIDTH__ * __BAR_WIDTH_FACTOR__, // Control the bar width
            colorByPoint: true,
            zones: [
                {
                    value: 0,
                    color: '__COLOR_NEG__' // Red for negative values
                },
                {
                    color: '__COLOR_POS__' // Green for positive values
                }
            ]
        }
    },
    series: [{
        name: 'Distribution',
        data: HISTOGRAM_DATA
    }],
    credits: {
        enabled: false
    },
    exporting: {
        sourceWidth: 1200,
        sourceHeight: 800,
        buttons: {
            contextButton: {
                menuItems: ['downloadPNG', 'downloadJPEG', 'downloadPDF', 'downloadSVG'],
                text: 'Export'
            }
        }
    },
    navigation: {
        buttonOptions: {
            theme: {
                fill: '#252931',
                style: { color: 'silver', whiteSpace: 'nowrap' },
                states: {
                    hover: { fill: '#333', style: { color: 'white' } }
                }
            },
            symbolStroke: 'silver',
            useHTML: true
        }
    }
});

// Add NaN count annotation if there are any
if (__NAN_COUNT__ > 0) {
    setTimeout(() => {
        const chart = Highcharts.charts[0];
        chart.renderer.label('NaN: __NAN_COUNT__', chart.chartWidth - 100, 10)
            .attr({
                padding: 5,
                r: 5,
                fill: 'rgba(255, 255, 255, 0.8)',
                zIndex: 8
            })
            .css({
                color: '#333',
                fontSize: '0.8em',
                fontWeight: 'bold'
            })
            .add();
    }, 100);
}
        """
    
    def _get_column_chart_js_template(self) -> str:
        """Returns the JavaScript template for column charts"""
        return """
Highcharts.chart('container', {
    chart: {
        type: 'column',
        backgroundColor: '#252931',
        style: {
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            color: 'white'
        }
    },
    title: {
        text: '__CHART_TITLE__',
        style: { color: 'white' }
    },
    subtitle: {
        text: '__CHART_SUBTITLE__',
        style: { color: 'silver' }
    },
    xAxis: {
        categories: categories,
        crosshair: true,
        title: {
            text: '__X_LABEL__',
            style: { color: 'white' }
        },
        tickColor: '#606060',
        lineColor: '#606060',
        labels: {
            style: { color: 'white' }
        }
    },
    yAxis: {
        min: 0,
        title: {
            text: '__Y_LABEL__',
            style: { color: 'white' }
        },
        gridLineColor: '#505050',
        tickColor: '#606060',
        lineColor: '#606060',
        labels: {
            style: { color: 'white' }
        }
    },
    legend: {
        itemStyle: {
            color: 'white'
        },
        itemHoverStyle: {
            color: '#DDD'
        }
    },
    tooltip: {
        shared: true,
        useHTML: true,
        headerFormat: '<table><tr><th colspan="2">{point.key}</th></tr>',
        pointFormat: '<tr><td style="color: {series.color}">{series.name}: </td>' +
            '<td style="text-align: right"><b>{point.y}</b></td></tr>',
        footerFormat: '</table>'
    },
    plotOptions: {
        column: {
            pointPadding: 0.2,
            borderWidth: 0,
            stacking: __STACK__ === 'true' ? 'normal' : null
        },
        series: {
            borderWidth: 0,
            dataLabels: {
                enabled: false
            }
        }
    },
    series: seriesData,
    credits: {
        enabled: false
    },
    exporting: {
        sourceWidth: 1200,
        sourceHeight: 800,
        buttons: {
            contextButton: {
                menuItems: ['downloadPNG', 'downloadJPEG', 'downloadPDF', 'downloadSVG'],
                text: 'Export'
            }
        }
    },
    navigation: {
        buttonOptions: {
            theme: {
                fill: '#252931',
                style: { color: 'silver', whiteSpace: 'nowrap' },
                states: {
                    hover: { fill: '#333', style: { color: 'white' } }
                }
            },
            symbolStroke: 'silver',
            useHTML: true
        }
    }
});
        """
    
    def _get_default_html_template(self) -> str:
        """Returns the default HTML template for the histogram chart"""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Distribution Chart</title>

    <!-- Highcharts core + modules -->
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/export-data.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>

    <style>
      html, body {
        margin: 0;
        padding: 0;
        background-color: #252931;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      }
      .highcharts-figure {
        margin: 0;
        padding: 0;
      }
      #container {
        width: 100%;
        height: 100%;
        min-height: 350px;
      }
      .highcharts-description {
        margin: 0.5em 0;
        color: #ccc;
        text-align: center;
        font-size: 0.9em;
      }
    </style>
  </head>

  <body>
    <figure class="highcharts-figure">
      <div id="container"></div>
    </figure>

    <script>
      // Define the histogram data
      const HISTOGRAM_DATA = {{HISTOGRAM_DATA}};
      
      // Render the chart
      {{CHART_JS}}
    </script>
  </body>
</html>"""