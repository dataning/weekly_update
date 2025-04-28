# direct_datagrid.py - A direct approach with no URL parameters
import streamlit as st
import pandas as pd
import numpy as np
import json
import uuid
import base64
from typing import Dict, List, Optional, Any

class DirectDataGrid:
    """
    A direct DataGrid component that uses hidden widgets for state passing
    """
    
    def __init__(self, title="Interactive Data Grid", subtitle="Edit data in the grid"):
        self.title = title
        self.subtitle = subtitle
    
    def _safe_json_serialize(self, obj):
        """Convert Python objects to JSON-serializable types"""
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    def render(self, df: pd.DataFrame, height: int = 400, 
               editable_columns: Optional[List[str]] = None,
               key: Optional[str] = None) -> pd.DataFrame:
        """Render the DataGrid and handle data synchronization"""
        
        # Default key if none provided
        if key is None:
            key = f"grid_{uuid.uuid4().hex[:8]}"
            
        # Store dataframe in session state
        if f"{key}_df" not in st.session_state:
            st.session_state[f"{key}_df"] = df.copy()
            
        # Store changelog
        if f"{key}_log" not in st.session_state:
            st.session_state[f"{key}_log"] = []
        
        # Create keys for state management 
        storage_key = f"{key}_storage"
        update_key = f"{key}_update"
        
        # Define callback for updates
        def update_from_storage():
            try:
                # Get the encoded data from session state
                encoded_data = st.session_state[storage_key]
                
                # Decode the data
                data_json = base64.b64decode(encoded_data).decode('utf-8')
                data = json.loads(data_json)
                
                # Convert to DataFrame
                if 'columns' in data:
                    updated_df = pd.DataFrame(data['columns'])
                    st.session_state[f"{key}_df"] = updated_df
                    
                    # Update changelog
                    if 'changelog' in data and data['changelog']:
                        st.session_state[f"{key}_log"] = data['changelog']
                        
                    # Show success message
                    st.success("Changes saved successfully!")
                    st.session_state[update_key] = True
                    
                    # Force a rerun to update the UI
                    st.rerun()
            except Exception as e:
                st.error(f"Error updating data: {str(e)}")
        
        # Format the data for the grid
        columns_data = {}
        for col in df.columns:
            # Convert values to JSON-serializable types
            columns_data[col] = [self._safe_json_serialize(x) for x in df[col].tolist()]
            
        # Create column definitions
        column_defs = []
        for col in df.columns:
            # Define editable status for this column
            is_editable = editable_columns is None or col in editable_columns
            column_defs.append({
                "id": col,
                "cells": {"editable": is_editable}
            })
        
        # Create a unique instance ID for this render
        instance_id = f"grid_instance_{uuid.uuid4().hex}"
        
        # Create a hidden text input for data storage - this is the key component
        st.text_input(
            "Hidden Data Storage", 
            value="", 
            key=storage_key,
            on_change=update_from_storage,
            label_visibility="collapsed",
            disabled=True
        )
        
        # JavaScript code to load and render Highcharts DataGrid
        component_html = f"""
        <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; font-size: 1.2em;">{self.title}</h3>
                <p style="margin: 4px 0 0 0; font-size: 0.9em; color: #666;">{self.subtitle}</p>
            </div>
            <div>
                <button id="save-btn" style="background-color: #2196F3; color: white; 
                       border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 8px;">
                    Save Changes
                </button>
                <button id="export-btn" style="background-color: #4CAF50; color: white; 
                       border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    Export to CSV
                </button>
            </div>
        </div>
        
        <div id="grid-container" style="height: {height-80}px; width: 100%;"></div>
        
        <div id="log-container" style="margin-top: 10px; max-height: 120px; overflow-y: auto; 
                font-size: 0.9em; padding: 8px; background: #f9f9f9; border-radius: 4px;"></div>
        
        <script>
        // Function to load Highcharts DataGrid
        function loadDependencies() {{
            return new Promise((resolve, reject) => {{
                // Load CSS
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://code.highcharts.com/dashboards/css/datagrid.css';
                document.head.appendChild(link);
                
                // Load JS
                const script = document.createElement('script');
                script.src = 'https://code.highcharts.com/dashboards/datagrid.js';
                script.onload = resolve;  // Resolve promise when script loads
                script.onerror = reject;  // Reject if there's an error
                document.head.appendChild(script);
            }});
        }}
        
        // Main function to initialize everything
        async function initialize() {{
            try {{
                // Load dependencies first
                await loadDependencies();
                
                // Grid data from Python
                const gridData = {json.dumps({
                    "columns_data": columns_data,
                    "column_defs": column_defs
                }, default=self._safe_json_serialize)};
                
                const logContainer = document.getElementById('log-container');
                const saveButton = document.getElementById('save-btn');
                const exportButton = document.getElementById('export-btn');
                const storageField = parent.document.querySelector('input[key="{storage_key}"]');
                
                // Initialize changelog
                let changelog = [];
                let hasChanges = false;
                
                // Create the grid
                const grid = Grid.grid('grid-container', {{
                    dataTable: {{
                        columns: gridData.columns_data
                    }},
                    events: {{
                        cell: {{
                            afterEdit: function() {{
                                // Create log entry
                                const timestamp = new Date().toLocaleTimeString();
                                const message = `${{timestamp}}: ${{this.column.id}} for row ${{this.row.index}} was updated from ${{this.oldValue}} to ${{this.value}}`;
                                
                                // Add to changelog
                                changelog.unshift(message);
                                if (changelog.length > 20) changelog.pop();
                                
                                // Update display
                                updateLogDisplay();
                                
                                // Update save button to indicate changes
                                saveButton.style.backgroundColor = '#ff9800';
                                saveButton.innerHTML = 'Save Changes *';
                                hasChanges = true;
                            }}
                        }}
                    }},
                    columnDefaults: {{
                        cells: {{
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
                
                // Function to update the log display
                function updateLogDisplay() {{
                    logContainer.innerHTML = changelog.map(entry => 
                        `<div style="margin-bottom: 4px;">${{entry}}</div>`
                    ).join('');
                }}
                
                // Add save button handler
                saveButton.addEventListener('click', function() {{
                    if (!hasChanges) return;
                    
                    // Get current data from the grid
                    const columns = grid.dataTable.columns;
                    
                    // Prepare data for storage
                    const data = {{
                        columns: columns,
                        changelog: changelog
                    }};
                    
                    // Convert to JSON and encode to base64
                    const jsonData = JSON.stringify(data);
                    const encoded = btoa(jsonData);
                    
                    // Update the hidden input field
                    if (storageField) {{
                        storageField.value = encoded;
                        
                        // Trigger the change event to notify Streamlit
                        const event = new Event('input', {{ bubbles: true }});
                        storageField.dispatchEvent(event);
                        
                        // Reset button state
                        saveButton.style.backgroundColor = '#2196F3';
                        saveButton.innerHTML = 'Save Changes';
                        hasChanges = false;
                    }}
                }});
                
                // Add export button handler
                exportButton.addEventListener('click', function() {{
                    // Get current data from the grid
                    const columns = grid.dataTable.columns;
                    const columnIds = Object.keys(columns);
                    
                    // Create CSV content
                    let csvContent = columnIds.join(',') + '\\n';
                    const rowCount = columns[columnIds[0]].length;
                    
                    for (let i = 0; i < rowCount; i++) {{
                        const row = columnIds.map(columnId => {{
                            let cellValue = columns[columnId][i];
                            
                            if (cellValue === null || cellValue === undefined) {{
                                return '';
                            }}
                            
                            if (typeof cellValue === 'string' && (cellValue.includes(',') || cellValue.includes('"'))) {{
                                return '"' + cellValue.replace(/"/g, '""') + '"';
                            }}
                            
                            return cellValue;
                        }}).join(',');
                        
                        csvContent += row + '\\n';
                    }}
                    
                    // Trigger download
                    const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'datagrid_export.csv';
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }});
                
                // Make responsive
                window.addEventListener('resize', function() {{
                    if (grid && grid.update) {{
                        grid.update({{ width: document.getElementById('grid-container').offsetWidth }});
                    }}
                }});
                
                // Initial resize
                setTimeout(function() {{
                    if (grid && grid.update) {{
                        grid.update({{ width: document.getElementById('grid-container').offsetWidth }});
                    }}
                }}, 100);
                
            }} catch (error) {{
                console.error('Error initializing grid:', error);
                document.getElementById('grid-container').innerHTML = 
                    `<div style="color: red; padding: 20px;">Error loading grid: ${{error.message}}</div>`;
            }}
        }}
        
        // Start initialization
        initialize();
        </script>
        """
        
        # Render the component
        st.components.v1.html(component_html, height=height, scrolling=False)
        
        # Show changelog if available
        if st.session_state[f"{key}_log"]:
            with st.expander("Edit History", expanded=False):
                for entry in st.session_state[f"{key}_log"]:
                    st.write(entry)
        
        # Return the current state
        return st.session_state[f"{key}_df"]