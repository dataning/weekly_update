# sankey_component.py
import pandas as pd
import streamlit.components.v1 as components
import streamlit as st
import numpy as np
from jinja2 import Template
import json
import time
import logging
from typing import Dict, List, Optional, Union, Any

class SankeyComponent:
    """
    A reusable Sankey diagram component for Streamlit
    
    This component creates a Sankey flow diagram visualization from a pandas DataFrame
    using Highcharts. It supports visualizing flow between nodes with customizable
    colors and sizing.
    """
    
    def __init__(self, title="Energy Flow Diagram", subtitle="Source: Data visualization"):
        """
        Initialize the Sankey diagram component
        
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
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
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
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def create_sankey_data(self, df: pd.DataFrame, from_column: str, to_column: str, 
                           weight_column: str, node_colors: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Creates Sankey diagram data structure from a DataFrame.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the flow data
        from_column : str
            Column name for the source nodes
        to_column : str
            Column name for the target nodes
        weight_column : str
            Column name for the flow weight/value
        node_colors : dict, optional
            Dictionary mapping node names to color values
            
        Returns:
        --------
        dict
            Dictionary with nodes and links for Sankey diagram
        """
        # Validate input columns exist
        required_columns = [from_column, to_column, weight_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
        start_time = time.time()
        
        # Extract unique nodes
        all_nodes = pd.concat([df[from_column], df[to_column]]).unique()
        
        # Create nodes list with colors if provided
        nodes = []
        for i, node in enumerate(all_nodes):
            node_data = {
                "id": node,
                "name": node
            }
            
            # Add color if provided for this node
            if node_colors and node in node_colors:
                node_data["color"] = node_colors[node]
                
            # Add custom positioning or other attributes if needed
            nodes.append(node_data)
        
        # Create links
        links = []
        for _, row in df.iterrows():
            # Basic link data
            link = {
                "from": row[from_column],
                "to": row[to_column],
                "weight": float(row[weight_column])
            }
            links.append(link)
        
        self.logger.info(f"Sankey data created in {time.time() - start_time:.2f} seconds")
        return {
            "nodes": nodes,
            "links": links
        }

    def render(self, df: pd.DataFrame, from_column: str, to_column: str, 
               weight_column: str, height: int = 600, 
               validate_data: bool = True, node_colors: Optional[Dict] = None,
               curveness: float = 0.5, node_width: int = 20,
               node_padding: int = 10, link_opacity: float = 0.5):
        """
        Renders the Sankey diagram visualization.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the flow data
        from_column : str
            Column name for the source nodes
        to_column : str
            Column name for the target nodes
        weight_column : str
            Column name for the flow weight/value
        height : int
            Height of the visualization in pixels
        validate_data : bool
            Whether to validate and display data statistics
        node_colors : dict, optional
            Dictionary mapping node names to color values
        curveness : float
            Curvature of the links (0 to 1)
        node_width : int
            Width of the nodes in pixels
        node_padding : int
            Vertical padding between nodes in pixels
        link_opacity : float
            Opacity of the links (0 to 1)
        """
        try:
            # Make a copy to avoid modifying the original
            df_copy = df.copy()
            
            # Check if dataframe is empty
            if df_copy.empty:
                st.error("The provided dataframe is empty. Please provide data to visualize.")
                return
            
            # Ensure weight column is float type
            if weight_column in df_copy.columns:
                df_copy[weight_column] = df_copy[weight_column].astype(float)
            
            # Create default node colors if not provided
            if node_colors is None:
                # Extract unique node names
                all_nodes = pd.concat([df_copy[from_column], df_copy[to_column]]).unique()
                
                # Default colors for different categories
                default_colors = {
                    'Energy Sources': ['#989898', '#1a8dff', '#009c00'],
                    'Sectors': ['#ffa500', '#74ffe7', '#8cff74', '#ff8da1', '#f4c0ff'],
                    'Endpoints': ['#e6e6e6', '#F9E79F']
                }
                
                # Map nodes to colors
                node_colors = {}
                color_idx = 0
                
                for node in all_nodes:
                    # Try to categorize the node
                    category = None
                    node_lower = node.lower()
                    
                    if any(keyword in node_lower for keyword in 
                         ['coal', 'nuclear', 'gas', 'petroleum', 'oil', 'import']):
                        category = 'Energy Sources'
                    elif any(keyword in node_lower for keyword in 
                          ['residential', 'commercial', 'industrial', 'transportation', 'sector']):
                        category = 'Sectors'
                    elif any(keyword in node_lower for keyword in 
                          ['rejected', 'services', 'electricity', 'heat']):
                        category = 'Endpoints'
                    
                    # Assign color based on category
                    if category:
                        colors = default_colors[category]
                        node_colors[node] = colors[color_idx % len(colors)]
                        color_idx += 1
                    else:
                        # Default fallback color
                        node_colors[node] = '#7cb5ec'
            
            # Create Sankey data
            sankey_data = self.create_sankey_data(
                df_copy, from_column, to_column, weight_column, node_colors
            )
            
            # Serialize to JSON, then replace Python booleans with JS ones
            sankey_data_json = json.dumps(
                sankey_data, 
                default=self._numpy_safe_encoder
            )
            # Convert Python literals to JS literals
            sankey_data_json = (
                sankey_data_json
                .replace('True', 'true')
                .replace('False', 'false')
                .replace('NaN', 'null')
            )
            
            # Optionally validate data for discrepancies
            if validate_data:
                # Changed from expander to checkbox
                if st.checkbox("Show Data Validation"):
                    self._validate_sankey_data(df_copy, from_column, to_column, weight_column)
            
            # Customize the chart settings
            chart_settings = {
                'title': self.title,
                'subtitle': self.subtitle,
                'curveness': curveness,
                'node_width': node_width,
                'node_padding': node_padding,
                'link_opacity': link_opacity
            }
            
            # Render the chart
            js_with_settings = self._customize_js(chart_settings)
            html = Template(self.html_template).render(
                CHART_JS=js_with_settings,
                SANKEY_DATA_JSON=sankey_data_json
            )
            
            # Display in Streamlit
            components.html(html, height=height, scrolling=True)
            
        except Exception as e:
            st.error(f"Error rendering Sankey diagram: {str(e)}")
            self.logger.error(f"Error rendering Sankey diagram: {str(e)}", exc_info=True)
    
    def _validate_sankey_data(self, df: pd.DataFrame, from_column: str, 
                             to_column: str, weight_column: str) -> None:
        """
        Validates the Sankey diagram data and displays summary statistics.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Source dataframe
        from_column : str
            Column name for source nodes
        to_column : str
            Column name for target nodes
        weight_column : str
            Column name for flow weights
        """
        import streamlit as st
        
        st.subheader("Data Validation")
        
        # Count total links
        total_links = len(df)
        
        # Count unique source and target nodes
        unique_sources = df[from_column].nunique()
        unique_targets = df[to_column].nunique()
        unique_nodes = pd.concat([df[from_column], df[to_column]]).nunique()
        
        # Calculate total flow
        total_flow = df[weight_column].sum()
        min_flow = df[weight_column].min()
        max_flow = df[weight_column].max()
        
        # Display statistics
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Total Links: {total_links}")
            st.info(f"Unique Source Nodes: {unique_sources}")
            st.info(f"Unique Target Nodes: {unique_targets}")
            st.info(f"Total Unique Nodes: {unique_nodes}")
            
        with col2:
            st.info(f"Total Flow: {total_flow:.2f}")
            st.info(f"Minimum Flow: {min_flow:.2f}")
            st.info(f"Maximum Flow: {max_flow:.2f}")
        
        # Display top sources and targets by flow
        top_sources = df.groupby(from_column)[weight_column].sum().sort_values(ascending=False).head(5)
        top_targets = df.groupby(to_column)[weight_column].sum().sort_values(ascending=False).head(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Sources")
            source_df = pd.DataFrame({
                'Source': top_sources.index,
                'Flow Out': top_sources.values
            })
            st.dataframe(source_df)
            
        with col2:
            st.subheader("Top Targets")
            target_df = pd.DataFrame({
                'Target': top_targets.index,
                'Flow In': top_targets.values
            })
            st.dataframe(target_df)
        
        # Check for any issues
        issues = []
        
        # Check for zero or negative flows
        zero_neg_flows = df[df[weight_column] <= 0]
        if not zero_neg_flows.empty:
            issues.append({
                'Issue Type': 'Zero/Negative Flow',
                'Count': len(zero_neg_flows),
                'Details': 'Links with zero or negative flow values'
            })
            
        # Check for self-loops
        self_loops = df[df[from_column] == df[to_column]]
        if not self_loops.empty:
            issues.append({
                'Issue Type': 'Self Loop',
                'Count': len(self_loops),
                'Details': 'Links where source and target are the same node'
            })
        
        # Display issues if any
        if issues:
            st.subheader("Potential Issues")
            st.dataframe(pd.DataFrame(issues))
        else:
            st.success("No data issues detected")
        
        # Option to show sample data
        # Changed this to avoid using key parameter
        show_sample_data = st.checkbox("Show Sample Data")
        if show_sample_data:
            st.dataframe(df.head(10))
    
    def _customize_js(self, settings: Dict[str, Any]) -> str:
        """
        Customize the JavaScript with provided settings
        
        Parameters:
        -----------
        settings : dict
            Dictionary of chart settings
            
        Returns:
        --------
        str
            Customized JavaScript code
        """
        js = self.js_template
        
        # Replace placeholders with actual values
        js = js.replace('__CHART_TITLE__', settings['title'])
        js = js.replace('__CHART_SUBTITLE__', settings['subtitle'])
        js = js.replace('__CURVENESS__', str(settings['curveness']))
        js = js.replace('__NODE_WIDTH__', str(settings['node_width']))
        js = js.replace('__NODE_PADDING__', str(settings['node_padding']))
        js = js.replace('__LINK_OPACITY__', str(settings['link_opacity']))
        
        return js
        
    @staticmethod
    def load_dataframe(file_path: str) -> pd.DataFrame:
        """
        Load a dataframe from various file formats
        
        Parameters:
        -----------
        file_path : str
            Path to the file
            
        Returns:
        --------
        pandas.DataFrame
            Loaded dataframe
        
        Raises:
        -------
        ValueError
            If file format is unsupported
        """
        import os
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return pd.read_csv(file_path)
        elif file_ext in ['.parquet', '.pq']:
            try:
                return pd.read_parquet(file_path)
            except ImportError:
                raise ImportError("Parquet support requires 'pyarrow' or 'fastparquet'. "
                                 "Install with 'pip install pyarrow' or 'pip install fastparquet'.")
        elif file_ext == '.xlsx':
            return pd.read_excel(file_path)
        elif file_ext == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _get_default_js_template(self):
        """Returns the default JavaScript template for the Sankey diagram chart"""
        return """
const renderChart = data => {
    // Log data to check formatting
    console.log('Rendering Sankey data:', data);
    
    Highcharts.chart('container', {
        chart: {
            backgroundColor: '#f2f2f2',
            spacing: [10, 10, 0, 10],
            spacingBottom: 0,
            marginTop: 60,
            marginRight: 20,
        },
  
        credits: { enabled: false },
  
        title: {
            text: '__CHART_TITLE__',
            align: 'left'
        },
  
        subtitle: {
            text: '__CHART_SUBTITLE__',
            align: 'left'
        },
  
        accessibility: {
            point: {
                valueDescriptionFormat: '{index}. {point.from} to {point.to}, {point.weight}.'
            }
        },
  
        tooltip: {
            headerFormat: null,
            pointFormat:
                '{point.fromNode.name} → {point.toNode.name}: <b>{point.weight:.2f}</b>',
            nodeFormat: '{point.name}: <b>{point.sum:.2f}</b>'
        },
  
        series: [{
            keys: ['from', 'to', 'weight'],
            nodes: data.nodes,
            data: data.links,
            type: 'sankey',
            name: 'Energy Flow',
            curveFactor: __CURVENESS__,
            nodeWidth: __NODE_WIDTH__,
            nodePadding: __NODE_PADDING__,
            fillOpacity: __LINK_OPACITY__,
            dataLabels: {
                enabled: true,
                linkFormat: '',
                style: {
                    textOutline: 'none'
                }
            }
        }],
  
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
                    fill: '#f2f2f2',
                    style: { color: '#333333', whiteSpace: 'nowrap' },
                    states: {
                        hover: { fill: '#e6e6e6', style: { color: '#000000' } }
                    }
                },
                symbolStroke: '#666666',
                useHTML: true
            }
        }
    });
};
        """
    
    def _get_default_html_template(self):
        """Returns the default HTML template for the Sankey diagram chart"""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Sankey Diagram</title>

    <!-- Highcharts core + modules -->
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/offline-exporting.js"></script>
    <script src="https://code.highcharts.com/modules/export-data.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>

    <style>
      html, body {
        margin: 0;
        padding: 0;
        background-color: #f2f2f2;
        color: #333333;
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
        padding-top: 30px;  /* create space at top for buttons */
        box-sizing: border-box;
      }
      .highcharts-description {
        padding: 0 10px;
        color: #666666;
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
      <p class="highcharts-description">
        Sankey diagrams visualize the flow magnitude between nodes.
        The width of each link is proportional to the flow volume.
      </p>
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
      
      const sankeyData = {{SANKEY_DATA_JSON}};
      renderChart(sankeyData);
    </script>
  </body>
</html>"""