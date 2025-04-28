import React, { useEffect, useRef, useState } from 'react'
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps
} from "streamlit-component-lib"

/**
 * DataGrid Component
 * 
 * This component wraps the Highcharts DataGrid to create an editable
 * grid interface that can communicate bidirectionally with Streamlit.
 */
function DataGridComponent({ args }) {
  // Get the component arguments from Streamlit
  const { gridData, title, subtitle, height } = args
  
  // Container ref for the DataGrid
  const containerRef = useRef(null)
  
  // Store the grid reference
  const [grid, setGrid] = useState(null)
  
  // Store changelog for sync with Streamlit
  const [changelog, setChangelog] = useState([])
  
  // Notify Streamlit that the component has mounted
  useEffect(() => {
    Streamlit.setFrameHeight(height || 400)
  }, [height])
  
  // Initialize the DataGrid
  useEffect(() => {
    // Skip if no gridData or container not ready
    if (!gridData || !containerRef.current) return
    
    // Load required scripts if not already loaded
    const loadRequiredScripts = async () => {
      // Check if Highcharts DataGrid is already loaded
      if (window.Grid) return
      
      // Load the DataGrid script
      const scriptElement = document.createElement('script')
      scriptElement.src = 'https://code.highcharts.com/dashboards/datagrid.js'
      scriptElement.async = true
      
      // Create a promise to wait for script to load
      return new Promise((resolve, reject) => {
        scriptElement.onload = resolve
        scriptElement.onerror = reject
        document.head.appendChild(scriptElement)
        
        // Also load the CSS
        const linkElement = document.createElement('link')
        linkElement.rel = 'stylesheet'
        linkElement.href = 'https://code.highcharts.com/dashboards/css/datagrid.css'
        document.head.appendChild(linkElement)
      })
    }
    
    // Create and initialize the grid
    const initializeGrid = async () => {
      try {
        // Load scripts if needed
        await loadRequiredScripts()
        
        // Create the grid
        const newGrid = window.Grid.grid(containerRef.current, {
          dataTable: {
            columns: gridData.columns_data
          },
          events: {
            cell: {
              afterEdit: function() {
                // Create a log entry
                const timestamp = new Date().toLocaleTimeString()
                const message = `${timestamp}: ${this.column.id} for row ${this.row.index} was updated from ${this.oldValue} to ${this.value}`
                
                // Update changelog
                setChangelog(prev => [message, ...prev].slice(0, 20))
                
                // Get current data from the grid
                const columns = this.dataGrid.dataTable.columns
                const columnData = {}
                
                // Convert to column-oriented format expected by pandas
                Object.keys(columns).forEach(colName => {
                  columnData[colName] = columns[colName]
                })
                
                // Send updated data to Streamlit
                Streamlit.setComponentValue({
                  edited_data: columnData,
                  changelog: [message]
                })
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
          credits: {
            enabled: false
          }
        })
        
        setGrid(newGrid)
        
        // Fix grid size after initialization
        window.setTimeout(() => {
          if (newGrid && newGrid.update) {
            newGrid.update({ width: containerRef.current.offsetWidth })
          }
        }, 200)
        
        // Make the grid responsive
        const resizeGrid = () => {
          if (newGrid && newGrid.update) {
            newGrid.update({ width: containerRef.current.offsetWidth })
          }
        }
        
        window.addEventListener('resize', resizeGrid)
        
        // Return cleanup function
        return () => {
          window.removeEventListener('resize', resizeGrid)
          if (newGrid && newGrid.destroy) {
            newGrid.destroy()
          }
        }
      } catch (error) {
        console.error('Error initializing DataGrid:', error)
      }
    }
    
    // Initialize the grid
    const cleanup = initializeGrid()
    
    // Cleanup when component unmounts
    return () => {
      if (cleanup && typeof cleanup === 'function') {
        cleanup()
      }
    }
  }, [gridData])
  
  return (
    <div className="datagrid-component">
      <div className="grid-toolbar">
        <div>
          <h3 className="grid-title">{title || 'Interactive Data Grid'}</h3>
          <p className="grid-subtitle">{subtitle || 'Source: Data visualization'}</p>
        </div>
        <div>
          <button 
            className="export-button" 
            onClick={() => {
              if (!grid) return
              
              // Get current data from the grid
              const columns = grid.dataTable.columns
              const columnIds = Object.keys(columns)
              
              // Create CSV header row
              let csvContent = columnIds.join(',') + '\n'
              
              // Determine number of rows (using the first column)
              const rowCount = columns[columnIds[0]].length
              
              // Create data rows
              for (let i = 0; i < rowCount; i++) {
                const row = columnIds.map(columnId => {
                  let cellValue = columns[columnId][i]
                  
                  // Handle special data types
                  if (cellValue === null || cellValue === undefined) {
                    return ''
                  }
                  
                  // Quote strings with commas and escape quotes
                  if (typeof cellValue === 'string') {
                    if (cellValue.includes(',') || cellValue.includes('"')) {
                      return '"' + cellValue.replace(/"/g, '""') + '"'
                    }
                  }
                  
                  return cellValue
                }).join(',')
                
                csvContent += row + '\n'
              }
              
              // Create and trigger download
              const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
              const url = URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.setAttribute('href', url)
              link.setAttribute('download', 'datagrid_export.csv')
              link.style.visibility = 'hidden'
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
            }}
          >
            Export to CSV
          </button>
        </div>
      </div>
      
      <div 
        id="container" 
        ref={containerRef}
        style={{ 
          width: '100%', 
          height: (height - 150) + 'px',
          position: 'relative'
        }}
      ></div>
      
      {changelog.length > 0 && (
        <div className="changelog">
          {changelog.map((log, index) => (
            <div key={index} className="log-entry">{log}</div>
          ))}
        </div>
      )}
      
      <style jsx>{`
        .datagrid-component {
          padding: 8px;
          display: flex;
          flex-direction: column;
          width: 100%;
          box-sizing: border-box;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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
        
        .changelog {
          margin-top: 10px;
          padding: 8px;
          background: #fbfbfb;
          border-radius: 4px;
          border: 1px solid #eee;
          max-height: 120px;
          overflow-y: auto;
          font-size: 0.85em;
        }
        
        .log-entry {
          margin-bottom: 4px;
        }
        
        .log-entry:first-child {
          font-weight: bold;
        }
      `}</style>
    </div>
  )
}

// Wrap the component for Streamlit
export default withStreamlitConnection(DataGridComponent)