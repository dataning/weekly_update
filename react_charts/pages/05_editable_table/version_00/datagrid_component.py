# datagrid_component.py
import pandas as pd
import streamlit.components.v1 as components
import streamlit as st
import numpy as np
from jinja2 import Template
import json
import time
import logging
from typing import Dict, List, Optional, Union, Any

class DataGridComponent:
    """
    A reusable DataGrid component for Streamlit
    
    This component creates an interactive, editable data grid visualization 
    using Highcharts DataGrid. It supports cell editing with event tracking.
    """
    
    def __init__(self, title="Interactive Data Grid", subtitle="Source: Data visualization"):
        """
        Initialize the DataGrid component
        
        Parameters:
        -----------
        title : str
            Grid title
        subtitle : str
            Grid subtitle
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
    
    def create_grid_data(self, df: pd.DataFrame, editable_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Creates DataGrid data structure from a DataFrame.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the grid data
        editable_columns : list of str, optional
            List of column names that should be editable. If None, all columns are editable.
            
        Returns:
        --------
        dict
            Dictionary with columns data for the DataGrid
        """
        # Validate input dataframe
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
            
        start_time = time.time()
        
        # Create columns data structure
        columns_data = {}
        for column in df.columns:
            columns_data[column] = df[column].tolist()
        
        # Create column definitions
        column_defs = []
        for column in df.columns:
            column_def = {
                "id": column,
            }
            
            # If specific columns are set as editable, configure accordingly
            if editable_columns is not None:
                if column not in editable_columns:
                    column_def["cells"] = {"editable": False}
                    
            column_defs.append(column_def)
        
        self.logger.info(f"Grid data created in {time.time() - start_time:.2f} seconds")
        return {
            "columns_data": columns_data,
            "column_defs": column_defs
        }

    def render(self, df: pd.DataFrame, height: int = 400, 
               editable_columns: Optional[List[str]] = None,
               key: Optional[str] = None,
               on_edit_callback: Optional[callable] = None):
        """
        Renders the DataGrid visualization.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the grid data
        height : int
            Height of the visualization in pixels
        editable_columns : list of str, optional
            List of column names that should be editable. If None, all columns are editable.
        key : str, optional
            A unique key for the component to maintain state across re-renders
        on_edit_callback : callable, optional
            A callback function that will be called when a cell is edited
        
        Returns:
        --------
        pandas.DataFrame or None
            If changes were made to the grid, returns the updated DataFrame, otherwise None
        """
        try:
            # Make a copy to avoid modifying the original
            df_copy = df.copy()
            
            # Check if dataframe is empty
            if df_copy.empty:
                st.error("The provided dataframe is empty. Please provide data to visualize.")
                return None
            
            # Create a unique key for session state if not provided
            if key is None:
                key = f"datagrid_{id(df)}"
            
            # Store the dataframe in session state
            if key not in st.session_state:
                st.session_state[key] = df_copy
            
            # Create grid data
            grid_data = self.create_grid_data(df_copy, editable_columns)
            
            # Create an empty container for the changelog
            if f"{key}_changelog" not in st.session_state:
                st.session_state[f"{key}_changelog"] = []
            
            # Create container for edited data
            if f"{key}_edited_data" not in st.session_state:
                st.session_state[f"{key}_edited_data"] = None
            
            # Serialize to JSON, then replace Python booleans with JS ones
            grid_data_json = json.dumps(
                grid_data, 
                default=self._numpy_safe_encoder
            )
            # Convert Python literals to JS literals
            grid_data_json = (
                grid_data_json
                .replace('true', 'true')
                .replace('false', 'false')
                .replace('null', 'null')
            )
                    
            # Render the grid
            html = Template(self.html_template).render(
                CHART_JS=self.js_template,
                GRID_DATA_JSON=grid_data_json,
                TITLE=self.title,
                SUBTITLE=self.subtitle,
                COMPONENT_KEY=key
            )
            
            # Display in Streamlit
            component_value = components.html(html, height=height, scrolling=True)
            
            # Display changelog
            if st.session_state[f"{key}_changelog"]:
                with st.expander("Edit History", expanded=True):
                    for log_entry in st.session_state[f"{key}_changelog"]:
                        st.write(log_entry)
            
            # Check if there's edited data to return
            if isinstance(component_value, dict) and 'edited_data' in component_value:
                try:
                    # Convert the edited data back to DataFrame
                    edited_data = pd.DataFrame(component_value['edited_data'])
                    st.session_state[f"{key}_edited_data"] = edited_data
                    return edited_data
                except Exception as e:
                    self.logger.error(f"Error converting edited data to DataFrame: {str(e)}", exc_info=True)
            
            # Return the original DataFrame if no edits were made
            return df_copy
            
        except Exception as e:
            st.error(f"Error rendering DataGrid: {str(e)}")
            self.logger.error(f"Error rendering DataGrid: {str(e)}", exc_info=True)
            return None
            
    def get_edited_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """
        This method is a placeholder for future implementation.
        
        In a full custom component implementation, this would retrieve the edited data.
        Currently, Streamlit's components.html() doesn't provide a built-in way to return
        data from JavaScript to Python without creating a custom component.
        
        Parameters:
        -----------
        key : str
            The unique key used when rendering the grid
            
        Returns:
        --------
        None
            This method returns None as it's currently a placeholder
        """
        return None
    
    def get_edited_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """
        Get the current state of the edited DataFrame.
        
        Parameters:
        -----------
        key : str
            The unique key used when rendering the grid
            
        Returns:
        --------
        pandas.DataFrame or None
            The current state of the edited DataFrame, or None if no edits or key not found
        """
        if f"{key}_edited_data" in st.session_state and st.session_state[f"{key}_edited_data"] is not None:
            return st.session_state[f"{key}_edited_data"]
        return None
    
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
        """Returns the default JavaScript template for the DataGrid component"""
        return """
// Initialize the grid when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    const gridData = GRID_DATA;
    const containerElement = document.getElementById('container');
    const changelogElement = document.getElementById('changelog');
    const exportButtonElement = document.getElementById('export-btn');
    
    // Create the grid
    const grid = Grid.grid('container', {
        dataTable: {
            columns: gridData.columns_data
        },
        events: {
            cell: {
                afterEdit: function() {
                    // Log the change to the UI
                    const timestamp = new Date().toLocaleTimeString();
                    const message = `<strong>${timestamp}</strong>: <strong>${this.column.id}</strong> for row ${this.row.index} was updated from <strong>${this.oldValue}</strong> to <strong>${this.value}</strong>`;
                    
                    changelogElement.innerHTML = message + '<br>' + changelogElement.innerHTML;
                    
                    // Limit changelog length
                    if (changelogElement.childElementCount > 20) {
                        changelogElement.lastChild.remove();
                    }
                    
                    // Send current data to Streamlit
                    try {
                        // Get current data from the grid
                        const columns = grid.dataTable.columns;
                        const columnData = {};
                        
                        // Convert to column-oriented format expected by pandas
                        Object.keys(columns).forEach(colName => {
                            columnData[colName] = columns[colName];
                        });
                        
                        // Send to Streamlit
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {
                                edited_data: columnData
                            }
                        }, '*');
                    } catch (err) {
                        console.error('Error sending data to Streamlit:', err);
                    }
                }
            }
        },
        columnDefaults: {
            cells: {
                editable: true,
                className: 'hc-dg-cell'
            },
            headerCell: {
                className: 'hc-dg-header-cell'
            }
        },
        columns: gridData.column_defs,
        // Disable Highcharts credits/logo
        credits: {
            enabled: false
        }
    });
    
    // Export data to CSV
    exportButtonElement.addEventListener('click', function() {
        // Get current data from the grid
        const columns = grid.dataTable.columns;
        const columnIds = Object.keys(columns);
        
        // Create CSV header row
        let csvContent = columnIds.join(',') + '\\n';
        
        // Determine number of rows (using the first column)
        const rowCount = columns[columnIds[0]].length;
        
        // Create data rows
        for (let i = 0; i < rowCount; i++) {
            const row = columnIds.map(columnId => {
                let cellValue = columns[columnId][i];
                
                // Handle special data types
                if (cellValue === null || cellValue === undefined) {
                    return '';
                }
                
                // Quote strings with commas and escape quotes
                if (typeof cellValue === 'string') {
                    if (cellValue.includes(',') || cellValue.includes('"')) {
                        return '"' + cellValue.replace(/"/g, '""') + '"';
                    }
                }
                
                return cellValue;
            }).join(',');
            
            csvContent += row + '\\n';
        }
        
        // Create and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'datagrid_export.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
    
    // Make the grid responsive
    function resizeGrid() {
        if (grid && grid.update) {
            grid.update({
                width: containerElement.offsetWidth
            });
        }
    }
    
    // Initial resize and add listener
    resizeGrid();
    window.addEventListener('resize', resizeGrid);
});
        """
    
    def _get_default_html_template(self):
        """Returns the default HTML template for the DataGrid component"""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Interactive DataGrid</title>

    <!-- Highcharts DataGrid and dependencies -->
    <script src="https://code.highcharts.com/dashboards/datagrid.js"></script>
    <link rel="stylesheet" href="https://code.highcharts.com/dashboards/css/datagrid.css">

    <style>
      html, body {
        margin: 0;
        padding: 0;
        background-color: transparent;
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        height: 100%;
      }
      .content {
        padding: 8px;
        display: flex;
        flex-direction: column;
        height: 100%;
        box-sizing: border-box;
      }
      #container {
        flex: 1;
        width: 100%;
      }
      .highcharts-description {
        padding: 0 10px;
        color: #666666;
        margin: 8px 0;
        font-size: 0.9em;
      }
      /* Hide Highcharts logo */
      .highcharts-credits {
        display: none !important;
      }
      .grid-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }
      .grid-title {
        margin: 0;
        font-size: 1.2em;
        font-weight: bold;
      }
      .grid-subtitle {
        margin: 4px 0 0 0;
        font-size: 0.9em;
        color: #666;
      }
      #changelog {
        margin-top: 10px;
        padding: 8px;
        background: #fbfbfb;
        border-radius: 4px;
        border: 1px solid #eee;
        max-height: 120px;
        overflow-y: auto;
        font-size: 0.85em;
      }
      #changelog:empty {
        display: none;
      }
      
      /* Export button */
      .export-button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        transition: background-color 0.3s;
      }
      .export-button:hover {
        background-color: #45a049;
      }
      
      /* Style customizations for the grid */
      .hc-dg-cell {
        transition: background-color 0.2s;
      }
      .hc-dg-cell:hover {
        background-color: #f5f5f5;
      }
      .hc-dg-header-cell {
        background-color: #e9e9e9;
        font-weight: bold;
      }
      
      @media (prefers-color-scheme: dark) {
        body {
          color: #f0f0f0;
        }
        .highcharts-description {
          color: #ccc;
        }
        #changelog {
          background-color: #292929;
          border-color: #444;
          color: #f0f0f0;
        }
        .hc-dg-cell:hover {
          background-color: #444;
        }
        .hc-dg-header-cell {
          background-color: #333;
        }
        .grid-subtitle {
          color: #aaa;
        }
      }
    </style>
  </head>

  <body>
          <div class="content">
      <div class="grid-toolbar">
        <div>
          <h3 class="grid-title">{{TITLE}}</h3>
          <p class="grid-subtitle">{{SUBTITLE}}</p>
        </div>
        <div>
          <button id="export-btn" class="export-button">Export to CSV</button>
        </div>
      </div>
      
      <div id="container"></div>
      
      <div id="changelog"></div>
      
      <p class="highcharts-description">
        Double-click on editable cells to modify values. Edit history will appear above.
      </p>
    </div>

    <!-- Inject the data and initialize the grid -->
    <script>
      // Define data for the grid
      const GRID_DATA = {{GRID_DATA_JSON}};
      
      // Execute the JS when document is ready
      {{CHART_JS}}
    </script>
  </body>
</html>"""