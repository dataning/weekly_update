# simple_editable_grid.py - A super simple implementation with basic editing
import streamlit as st
import pandas as pd
import numpy as np
import json
from typing import List, Optional

class SimpleEditableGrid:
    """
    A very simple editable grid component that uses Highcharts DataGrid
    """
    
    def __init__(self, title="Editable Data Grid", subtitle="Edit data in the grid"):
        self.title = title
        self.subtitle = subtitle
    
    def render(self, df: pd.DataFrame, height: int = 400, 
               editable_columns: Optional[List[str]] = None,
               key: Optional[str] = None) -> pd.DataFrame:
        """
        Render the editable grid
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame to display
        height : int
            Grid height in pixels
        editable_columns : list of str or None
            List of column names that should be editable. If None, all columns are editable.
        key : str
            Unique key for this grid instance
            
        Returns:
        --------
        pandas.DataFrame
            The DataFrame with any edits made by the user
        """
        # Generate a key if not provided
        if key is None:
            key = f"grid_{id(df)}"
            
        # Store the DataFrame in session state
        if f"{key}_df" not in st.session_state:
            st.session_state[f"{key}_df"] = df.copy()
        
        # Create column data in the format Highcharts expects
        columns_data = {}
        for col in df.columns:
            # Convert to Python native types and handle NaN values
            columns_data[col] = []
            for val in df[col]:
                if pd.isna(val):
                    columns_data[col].append(None)
                elif isinstance(val, (np.integer, np.floating)):
                    columns_data[col].append(float(val) if isinstance(val, np.floating) else int(val))
                else:
                    columns_data[col].append(str(val))
        
        # Create column definitions with editable settings
        column_defs = []
        for col in df.columns:
            col_def = {"id": col}
            if editable_columns is not None and col not in editable_columns:
                col_def["cells"] = {"editable": False}
            column_defs.append(col_def)
            
        # Convert to JSON for JS
        grid_data = json.dumps({
            "columns_data": columns_data,
            "column_defs": column_defs
        })
        
        # Create container for the grid
        st.markdown(f"<h3>{self.title}</h3><p>{self.subtitle}</p>", unsafe_allow_html=True)
        
        # Create columns for the buttons and grid
        col1, col2 = st.columns([6, 1])
        
        with col2:
            # Add an "Export to CSV" button
            if st.button("Export to CSV", key=f"{key}_export"):
                csv = st.session_state[f"{key}_df"].to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="data_export.csv",
                    mime="text/csv",
                    key=f"{key}_download"
                )
        
        # Create the grid component with Highcharts DataGrid
        html = f"""
        <div id="grid-container" style="height: {height}px; width: 100%; margin-bottom: 20px;"></div>
        <div id="edit-log" style="font-size: 14px; padding: 10px; background: #f9f9f9; 
             border-radius: 4px; max-height: 150px; overflow-y: auto;"></div>
             
        <!-- Load Highcharts DataGrid -->
        <script src="https://code.highcharts.com/dashboards/datagrid.js"></script>
        <link rel="stylesheet" href="https://code.highcharts.com/dashboards/css/datagrid.css">
        
        <script>
            // Grid data from Python
            const gridData = {grid_data};
            
            // Track edits
            const editLog = document.getElementById('edit-log');
            let editedData = null;
            
            // Create the grid
            const grid = Grid.grid('grid-container', {{
                dataTable: {{
                    columns: gridData.columns_data
                }},
                events: {{
                    cell: {{
                        afterEdit: function() {{
                            // Log the edit
                            const time = new Date().toLocaleTimeString();
                            const message = `${{time}}: Changed ${{this.column.id}} in row ${{this.row.index}} from "${{this.oldValue}}" to "${{this.value}}"`;
                            
                            // Add to log
                            const logEntry = document.createElement('div');
                            logEntry.textContent = message;
                            logEntry.style.marginBottom = '5px';
                            editLog.insertBefore(logEntry, editLog.firstChild);
                            
                            // Get updated data
                            editedData = this.dataGrid.dataTable.columns;
                            
                            // Store in localStorage for retrieval
                            localStorage.setItem('grid_{key}_data', JSON.stringify(editedData));
                        }}
                    }}
                }},
                columnDefaults: {{
                    cells: {{
                        editable: true,
                        className: 'hc-dg-cell'
                    }},
                    headerCell: {{
                        className: 'hc-dg-header-cell'
                    }}
                }},
                columns: gridData.column_defs,
                credits: {{
                    enabled: false
                }}
            }});
            
            // Make responsive
            window.addEventListener('resize', function() {{
                if (grid && grid.update) {{
                    grid.update({{ width: document.getElementById('grid-container').offsetWidth }});
                }}
            }});
            
            // Initial resize
            setTimeout(function() {{
                grid.update({{ width: document.getElementById('grid-container').offsetWidth }});
            }}, 100);
        </script>
        """
        
        # Render the grid
        st.components.v1.html(html, height=height+200, scrolling=False)
        
        # Add button to save changes 
        if st.button("Save Changes", type="primary", key=f"{key}_save"):
            # Add JavaScript to retrieve edited data
            retrieve_js = f"""
            <script>
                // Get data from localStorage
                const editedData = localStorage.getItem('grid_{key}_data');
                
                if (editedData) {{
                    // Create a form to submit the data
                    const form = document.createElement('form');
                    form.method = 'GET';
                    
                    // Add the data as URL parameters
                    const params = new URLSearchParams(window.location.search);
                    params.set('grid_data_{key}', editedData);
                    
                    // Navigate to the same page with data in params
                    window.location.href = window.location.pathname + '?' + params.toString();
                }}
            </script>
            """
            st.components.v1.html(retrieve_js, height=0)
        
        # Check for data in query parameters
        query_params = st.query_params
        data_param = f"grid_data_{key}"
        
        if data_param in query_params:
            try:
                # Parse the data
                data_json = query_params[data_param]
                data = json.loads(data_json)
                
                # Convert to DataFrame
                updated_df = pd.DataFrame(data)
                st.session_state[f"{key}_df"] = updated_df
                
                # Show success message
                st.success("Changes saved successfully!")
                
                # Clear parameters and rerun
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error saving changes: {str(e)}")
        
        # Return the current state
        return st.session_state[f"{key}_df"]