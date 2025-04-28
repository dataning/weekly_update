# treemap_component.py
import pandas as pd
import streamlit.components.v1 as components
from jinja2 import Template
import json

class TreemapComponent:
    """
    A reusable treemap component for Streamlit
    
    This component creates a hierarchical treemap visualization from a pandas DataFrame
    using Highcharts. It supports a three-level hierarchy with performance metrics
    determining the color of each node.
    """
    
    def __init__(self, title="Hierarchical Performance Treemap", subtitle="Click to drill down"):
        """
        Initialize the treemap component
        
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
    
    def _numpy_safe_encoder(self, obj):
        """
        Helper method to convert NumPy types to native Python types for JSON serialization
        
        Parameters:
        -----------
        obj : any
            Object to convert
            
        Returns:
        --------
        any
            Converted object
        """
        import numpy as np
        
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def create_treemap_data(self, df, level1_column, level2_column, level3_column, value_column):
        """
        Creates treemap data structure from a DataFrame.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the data
        level1_column : str
            Column name for the top level of hierarchy
        level2_column : str
            Column name for the middle level of hierarchy
        level3_column : str
            Column name for the bottom level of hierarchy (leaf nodes)
        value_column : str
            Column name for performance/color values
            
        Returns:
        --------
        list
            List of dictionaries structured for Highcharts treemap
        """
        treemap = []
        
        # Calculate the number of rows for each level1 and level2 - this will be used for size
        level1_counts = df[level1_column].value_counts().to_dict()
        level2_counts = {}
        for level1 in df[level1_column].unique():
            level1_mask = df[level1_column] == level1
            level2_for_level1 = df.loc[level1_mask, level2_column]
            for level2 in level2_for_level1.unique():
                key = f"{level1}|{level2}"
                count = ((df[level1_column] == level1) & (df[level2_column] == level2)).sum()
                level2_counts[key] = count
        
        # Get unique level 1 items
        level1_items = df[level1_column].unique()
        level2_by_level1 = {}
        
        # Step 1: Add level 1 nodes (top level)
        for level1 in level1_items:
            # Calculate average value for this level1
            level1_mask = df[level1_column] == level1
            
            # Safely calculate mean, handling NaN values
            level1_values = df.loc[level1_mask, value_column]
            if level1_values.isna().all():
                level1_avg = float('nan')  # All values are NaN
            else:
                level1_avg = float(level1_values.mean())
            
            # Convert to percentage if needed
            pct_value = level1_avg * 100 if -1 <= level1_avg <= 1 else level1_avg
            
            # Use count for size, value for color
            size = float(level1_counts.get(level1, 1))
            
            treemap.append({
                "id": level1,
                "name": level1,
                "value": size,  # Use size for the box area
                "colorValue": float(pct_value),  # Use value for color
                "custom": {"fullName": level1, "performance_value": float(pct_value)}
            })
            
            # Get unique level 2 items for this level 1
            level2_items = df.loc[level1_mask, level2_column].unique()
            level2_by_level1[level1] = level2_items
        
        # Step 2: Add level 2 nodes (middle level)
        for level1, level2_items in level2_by_level1.items():
            for level2 in level2_items:
                node_id = f"{level1}|{level2}"
                
                # Calculate average value for this level2, safely handling NaN
                mask = (df[level1_column] == level1) & (df[level2_column] == level2)
                level2_values = df.loc[mask, value_column]
                
                if level2_values.isna().all():
                    level2_avg = float('nan')  # All values are NaN
                else:
                    level2_avg = float(level2_values.mean())
                
                # Convert to percentage if needed
                pct_value = level2_avg * 100 if -1 <= level2_avg <= 1 else level2_avg
                
                # Use count for size, value for color
                size = float(level2_counts.get(node_id, 1))
                
                treemap.append({
                    "id": node_id,
                    "name": level2,
                    "parent": level1,
                    "value": size,  # Use size for the box area
                    "colorValue": float(pct_value),  # Use value for color
                    "custom": {"fullName": level2, "performance_value": float(pct_value)}
                })
        
        # Step 3: Add level 3 nodes (bottom level with values)
        for _, row in df.iterrows():
            level1 = row[level1_column]
            level2 = row[level2_column]
            level3 = row[level3_column]
            
            # Handle NaN values
            if pd.isna(row[value_column]):
                value = float('nan')
                pct_value = float('nan')
                performance_text = "N/A"
            else:
                value = float(row[value_column])  # Convert to native Python float
                # Convert to percentage if needed
                pct_value = value * 100 if -1 <= value <= 1 else value
                # Create the performance text with proper sign
                sign = "" if pct_value < 0 else "+"
                performance_text = f"{sign}{pct_value:.2f}%"
            
            parent_id = f"{level1}|{level2}"
            treemap.append({
                "id": level3,
                "name": level3,
                "parent": parent_id,
                "value": 1.0,  # Fixed size of 1 for all leaf nodes for equal representation
                "colorValue": float(pct_value),  # Use value for color
                "custom": {
                    "fullName": level3,
                    "performance": performance_text,
                    "performance_value": float(pct_value),
                    "isNaN": pd.isna(row[value_column])  # Flag to indicate NaN
                }
            })
        
        return treemap

    def render(self, df, level1_column, level2_column, level3_column, value_column, 
               height=800, value_min=-30, value_max=30, color_min='#d40000', color_max='#00b52a',
               validate_data=True, nan_color='#333333', nan_label='N/A', handle_nan='show'):
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Handle NaN values according to the option chosen
        if handle_nan == 'hide':
            df_copy = df_copy.dropna(subset=[value_column])
        elif handle_nan == 'zero':
            df_copy[value_column] = df_copy[value_column].fillna(0)
        
        # Ensure numeric column is float type
        if value_column in df_copy.columns:
            mask = ~df_copy[value_column].isna()
            if mask.any():
                df_copy.loc[mask, value_column] = df_copy.loc[mask, value_column].astype(float)
        
        # Create treemap data
        treemap_data = self.create_treemap_data(
            df_copy, level1_column, level2_column, level3_column, value_column
        )
        
        # Serialize to JSON, then replace Python booleans with JS ones
        treemap_data_json = json.dumps(
            treemap_data, 
            default=self._numpy_safe_encoder
        )
        # CLEANER FIX: convert Python literals to JS literals
        treemap_data_json = (
            treemap_data_json
            .replace('True', 'true')
            .replace('False', 'false')
            .replace('NaN', 'null')  # optional: map NaN to null
        )
        # Load back or keep as string for injection
        # If you prefer working with Python objects:
        treemap_data = json.loads(treemap_data_json)
        
        # Optionally validate data for discrepancies
        if validate_data:
            self._validate_treemap_data(df_copy, value_column, treemap_data)
        
        # Customize the chart settings
        chart_settings = {
            'title': self.title,
            'subtitle': self.subtitle,
            'value_min': float(value_min),
            'value_max': float(value_max),
            'color_min': color_min,
            'color_max': color_max,
            'nan_color': nan_color,
            'nan_label': nan_label
        }
        
        # Render the chart
        js_with_settings = self._customize_js(chart_settings)
        html = Template(self.html_template).render(
            CHART_JS=js_with_settings,
            # Inject the cleaned JSON string directly
            TREE_DATA_JSON=treemap_data_json
        )
        
        # Display in Streamlit
        components.html(html, height=height, scrolling=True)
    
    def _validate_treemap_data(self, df, value_column, treemap_data):
        """
        Validates that the treemap data matches the source dataframe
        and reports any discrepancies between value and display text.
        """
        import streamlit as st
        
        st.subheader("Data Validation")
        
        # Count negative values in original data
        source_negatives = df[value_column].apply(lambda x: x < 0 if not pd.isna(x) else False).sum()
        source_total = len(df)
        source_negative_pct = (source_negatives / source_total) * 100 if source_total > 0 else 0
        
        # Count NaN values in original data
        source_nan = df[value_column].isna().sum()
        source_nan_pct = (source_nan / source_total) * 100 if source_total > 0 else 0
        
        # Count leaf nodes in treemap data
        leaf_nodes = [node for node in treemap_data if '|' in node.get('parent', '')]
        leaf_total = len(leaf_nodes)
        
        # Count leaf nodes with negative values
        leaf_negatives = sum(1 for node in leaf_nodes if node.get('colorValue', 0) < 0)
        leaf_negative_pct = (leaf_negatives / leaf_total) * 100 if leaf_total > 0 else 0
        
        # Count leaf nodes with NaN values
        leaf_nan = sum(1 for node in leaf_nodes if node.get('custom', {}).get('isNaN', False))
        leaf_nan_pct = (leaf_nan / leaf_total) * 100 if leaf_total > 0 else 0
        
        # Check for discrepancies between value and displayed performance
        discrepancies = []
        for node in leaf_nodes:
            # Skip NaN values for discrepancy check
            if node.get('custom', {}).get('isNaN', False):
                continue
                
            value = node.get('colorValue', 0)
            performance = node.get('custom', {}).get('performance', '')
            
            # Extract numeric value from performance string (remove % sign and any + prefix)
            try:
                perf_value = float(performance.replace('%', '').replace('+', ''))
            except ValueError:
                perf_value = 0
            
            # Check if the signs match
            value_is_negative = value < 0
            perf_is_negative = performance.startswith('-')
            
            if value_is_negative != perf_is_negative:
                discrepancies.append({
                    'id': node.get('id', ''),
                    'value': value,
                    'performance': performance,
                    'issue': "Sign mismatch"
                })
            elif abs(abs(value) - abs(perf_value)) > 0.1:
                discrepancies.append({
                    'id': node.get('id', ''),
                    'value': value,
                    'performance': performance,
                    'issue': "Value mismatch"
                })
        
        # Display validation results
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Source Dataframe: {source_negative_pct:.1f}% negative values")
            if source_nan > 0:
                st.info(f"Source Dataframe: {source_nan_pct:.1f}% NaN values ({source_nan} rows)")
        with col2:
            st.info(f"Treemap Data: {leaf_negative_pct:.1f}% negative values")
            if leaf_nan > 0:
                st.info(f"Treemap Data: {leaf_nan_pct:.1f}% NaN values ({leaf_nan} nodes)")
        
        if discrepancies:
            st.warning(f"Found {len(discrepancies)} discrepancies between value and display text")
            st.dataframe(pd.DataFrame(discrepancies))
        else:
            st.success("No discrepancies found between values and display text")
        
        # Display the first few treemap nodes for inspection
        with st.expander("View Sample Treemap Nodes"):
            sample_size = min(5, len(leaf_nodes))
            for i, node in enumerate(leaf_nodes[:sample_size]):
                st.write(f"Node {i+1}:", node)
    
    def _customize_js(self, settings):
        """Customize the JavaScript with provided settings"""
        js = self.js_template
        
        # Replace placeholders with actual values
        js = js.replace('__CHART_TITLE__', settings['title'])
        js = js.replace('__CHART_SUBTITLE__', settings['subtitle'])
        js = js.replace('__COLOR_MIN__', settings['color_min'])
        js = js.replace('__COLOR_MAX__', settings['color_max'])
        js = js.replace('__VALUE_MIN__', str(settings['value_min']))
        js = js.replace('__VALUE_MAX__', str(settings['value_max']))
        js = js.replace('__NAN_COLOR__', settings['nan_color'])
        js = js.replace('__NAN_LABEL__', settings['nan_label'])
        
        return js
    
    def _get_default_js_template(self):
        """Returns the default JavaScript template for the treemap chart"""
        return """
const renderChart = data => {
    // Log data to check formatting
    console.log('Rendering treemap data:', data);
    
    Highcharts.chart('container', {
      chart: {
        backgroundColor: '#252931',
        spacing: [10, 10, 0, 10],
        spacingBottom: 0,
        marginTop: 60,
        marginRight: 20,
      },
  
      credits: { enabled: false },
  
      series: [{
        name: 'All',
        type: 'treemap',
        layoutAlgorithm: 'squarified',
        allowDrillToNode: true,
        animationLimit: 1000,
        borderColor: '#252931',
        color: '#252931',
        colorKey: 'colorValue',  // Use colorValue for coloring
        nodeSizeBy: 'value',     // Use value for sizing
        dataLabels: {
          enabled: false,
          allowOverlap: true,
          style: { fontSize: '0.9em', textOutline: 'none' }
        },
        levels: [
          {
            // Level 1: Top level
            level: 1,
            borderWidth: 3,
            dataLabels: {
              enabled: true,
              headers: true,
              align: 'left',
              padding: 3,
              style: {
                fontWeight: 'bold',
                fontSize: '0.75em',
                textTransform: 'uppercase',
                color: 'white'
              },
              formatter: function() {
                // Get the performance value for coloring
                const perfValue = this.point.custom ? this.point.custom.performance_value : 0;
                const isNaN = this.point.custom && this.point.custom.isNaN === true;
                
                // Handle NaN values
                if (isNaN || !perfValue && perfValue !== 0 || Number.isNaN(perfValue)) {
                  return `<div>${this.point.name}<br><span style="font-size:0.7em; color: #ffffff">__NAN_LABEL__</span></div>`;
                }
                
                // Determine text color based on performance value sign
                const textColor = (perfValue < 0) ? '#ff9999' : '#99ff99';
                const sign = (perfValue < 0) ? "" : "+";
                const perfText = `${sign}${perfValue.toFixed(2)}%`;
                return `<div>${this.point.name}<br><span style="font-size:0.7em; color: ${textColor}">${perfText}</span></div>`;
              }
            }
          },
          {
            // Level 2: Middle level
            level: 2,
            groupPadding: 1,
            dataLabels: {
              enabled: true,
              headers: true,
              align: 'center',
              shape: 'callout',
              backgroundColor: 'gray',
              borderWidth: 1,
              borderColor: '#252931',
              padding: 0,
              style: {
                color: 'white',
                fontSize: '0.6em',
                textTransform: 'uppercase'
              },
              formatter: function() {
                // Get the performance value for coloring
                const perfValue = this.point.custom ? this.point.custom.performance_value : 0;
                const isNaN = this.point.custom && this.point.custom.isNaN === true;
                
                // Handle NaN values
                if (isNaN || !perfValue && perfValue !== 0 || Number.isNaN(perfValue)) {
                  return `<div>${this.point.name}<br><span style="font-size:0.7em; color: #ffffff">__NAN_LABEL__</span></div>`;
                }
                
                // Determine text color based on performance value sign
                const textColor = (perfValue < 0) ? '#ff9999' : '#99ff99';
                const sign = (perfValue < 0) ? "" : "+";
                const perfText = `${sign}${perfValue.toFixed(2)}%`;
                return `<div>${this.point.name}<br><span style="font-size:0.7em; color: ${textColor}">${perfText}</span></div>`;
              }
            }
          },
          {
            // Level 3: Bottom level (leaf nodes)
            level: 3,
            dataLabels: {
              enabled: true,
              align: 'center',
              formatter: function() {
                // Get the performance value for coloring
                const perfValue = this.point.custom ? this.point.custom.performance_value : 0;
                const perf = this.point.custom && this.point.custom.performance ? this.point.custom.performance : '';
                const isNaN = this.point.custom && this.point.custom.isNaN === true;
                
                // Handle NaN values
                if (isNaN || !perfValue && perfValue !== 0 || Number.isNaN(perfValue)) {
                  return `<div>${this.point.name}<br><span style="font-size:0.7em; color: #ffffff">__NAN_LABEL__</span></div>`;
                }
                
                // Determine text color based on performance value sign
                const textColor = (perfValue < 0) ? '#ff9999' : '#99ff99';
                return `<div>${this.point.name}<br><span style="font-size:0.7em; color: ${textColor}">${perf}</span></div>`;
              },
              style: { color: 'white' }
            }
          }
        ],
        data
      }],
  
      title: {
        text: '__CHART_TITLE__',
        align: 'left',
        style: { color: 'white' }
      },
  
      subtitle: {
        text: '__CHART_SUBTITLE__',
        align: 'left',
        style: { color: 'silver' }
      },
  
      tooltip: {
        followPointer: true,
        outside: true,
        formatter: function() {
          const full = this.point.custom && this.point.custom.fullName ? this.point.custom.fullName : this.point.name;
          const level = this.point.node ? this.point.node.level : 0;
          const perf = this.point.custom && this.point.custom.performance ? this.point.custom.performance : '';
          const perfValue = this.point.custom && this.point.custom.performance_value !== undefined ? this.point.custom.performance_value : 0;
          const isNaN = this.point.custom && this.point.custom.isNaN === true;
          
          // Handle NaN values
          if (isNaN || !perfValue && perfValue !== 0 || Number.isNaN(perfValue)) {
            if (level === 1) {
              return `<span style="font-size:0.9em">Level 1: ${full}</span><br/>
                      <b>Average:</b> <span style="color:#ffffff">__NAN_LABEL__</span>`;
            } else if (level === 2) {
              return `<span style="font-size:0.9em">Level 2: ${full}</span><br/>
                      <b>Average:</b> <span style="color:#ffffff">__NAN_LABEL__</span>`;
            } else {
              return `<span style="font-size:0.9em">${full}</span><br/>
                      <b>Performance:</b> <span style="color:#ffffff">__NAN_LABEL__</span>`;
            }
          }
          
          // Customize tooltip based on level
          if (level === 1) {
            const textColor = (perfValue < 0) ? '#d40000' : '#00b52a';
            const sign = (perfValue < 0) ? "" : "+";
            const perfText = `${sign}${perfValue.toFixed(2)}%`;
            return `<span style="font-size:0.9em">Level 1: ${full}</span><br/>
                    <b>Average:</b> <span style="color:${textColor}">${perfText}</span>`;
          } else if (level === 2) {
            const textColor = (perfValue < 0) ? '#d40000' : '#00b52a';
            const sign = (perfValue < 0) ? "" : "+";
            const perfText = `${sign}${perfValue.toFixed(2)}%`;
            return `<span style="font-size:0.9em">Level 2: ${full}</span><br/>
                    <b>Average:</b> <span style="color:${textColor}">${perfText}</span>`;
          } else {
            // For leaf nodes, show value and highlight negative values
            const textColor = (perfValue < 0) ? '#d40000' : '#00b52a';
            return `<span style="font-size:0.9em">${full}</span><br/>
                    <b>Performance:</b> <span style="color:${textColor}">${perf}</span>`;
          }
        }
      },
  
      colorAxis: {
        minColor: '__COLOR_MIN__',
        maxColor: '__COLOR_MAX__',
        stops: [
          [0,   '__COLOR_MIN__'],   // deep red
          [0.475, '#414555'], // gray appears only right around the middle
          [0.525, '#414555'],
          [1,   '__COLOR_MAX__']    // deep green
        ],
        min: __VALUE_MIN__,
        max: __VALUE_MAX__,
        gridLineWidth: 0,
        labels: {
          overflow: 'allow',
          format: '{value}%',
          style: { color: 'white' }
        },
  
        legend: {
          align: 'center',
          layout: 'horizontal',
          verticalAlign: 'bottom',
          floating: true,
          y: -40,
          margin: 0,
          symbolHeight: 12
        }
      },
  
      exporting: {
        sourceWidth: 1200,
        sourceHeight: 800,
        buttons: {
          fullscreen: {
            text: 'Fullscreen',
            onclick: function() { this.fullscreen.toggle(); }
          },
          contextButton: {
            menuItems: ['downloadPNG','downloadJPEG','downloadPDF','downloadSVG'],
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
  };
  
  // Dynamic header-color & font-size plugin
  Highcharts.addEvent(Highcharts.Series, 'drawDataLabels', function () {
    if (this.type === 'treemap') {
      this.points.forEach(pt => {
        // Check for NaN values
        const isNaN = pt.custom && pt.custom.isNaN === true;
        const perfValue = pt.custom && pt.custom.performance_value !== undefined ? pt.custom.performance_value : 0;
        const hasValidValue = !isNaN && perfValue !== undefined && !Number.isNaN(perfValue);
        
        // For level 2 nodes
        if (pt.node && pt.node.level === 2) {
          if (hasValidValue) {
            // Use performance value to color the node
            pt.dlOptions.backgroundColor = this.colorAxis.toColor(perfValue);
          } else {
            // Use special color for NaN values
            pt.dlOptions.backgroundColor = '__NAN_COLOR__';
          }
        }
        
        // For level 3 nodes (leaf nodes)
        if (pt.node && pt.node.level === 3 && pt.shapeArgs) {
          // Adjust font size based on area
          const area = pt.shapeArgs.width * pt.shapeArgs.height;
          pt.dlOptions.style.fontSize = Math.min(32, 7 + Math.round(area * 0.0008)) + 'px';
          
          if (hasValidValue) {
            // Use value for color
            pt.colorValue = perfValue;
          } else {
            // Use special color for NaN
            pt.color = '__NAN_COLOR__';
            // Override the default color mapping
            pt.dlOptions.useHTML = true;
            pt.dlOptions.backgroundColor = '__NAN_COLOR__';
          }
        }
      });
    }
  });
        """
    
    def _get_default_html_template(self):
        """Returns the default HTML template for the treemap chart"""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Hierarchical Treemap</title>

    <!-- Highcharts core + modules -->
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/treemap.js"></script>
    <script src="https://code.highcharts.com/modules/data.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/offline-exporting.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>
    <script src="https://code.highcharts.com/modules/coloraxis.js"></script>

    <style>
      html, body {
        margin: 0;
        padding: 0;
        background-color: #252931;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        height: 100%;
      }
      .highcharts-figure {
        margin: 0;
        padding-bottom: 0;
      }
      #container {
        width: 100%;
        height: 100vh;
        min-height: 600px;
        margin-bottom: 0;
        padding-bottom: 0;
        padding-top: 30px;
        box-sizing: border-box;
      }
      .highcharts-description {
        padding: 0 10px;
        color: #ccc;
        margin: 0;
      }
      @media (max-width: 600px) {
        #container {
          height: 400px;
        }
      }
    </style>
  </head>

  <body>
    <figure class="highcharts-figure">
      <div id="container"></div>
    </figure>

    <!-- 1) JS template gets injected here -->
    <script>
        {{CHART_JS}}
    </script>

    <!-- 2) Inject the data and call renderChart -->
    <script>
      // Define NaN to avoid reference errors if it's referenced with lowercase 'nan'
      if (typeof nan === 'undefined') {
        var nan = NaN;
      }
      
      const treeData = {{TREE_DATA_JSON}};
      renderChart(treeData);
    </script>
  </body>
</html>"""