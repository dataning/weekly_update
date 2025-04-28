import React from "react"
import ReactDOM from "react-dom"
import DataGridComponent from "./DataGridComponent"

// Attach the Streamlit component
ReactDOM.render(
  <React.StrictMode>
    <DataGridComponent />
  </React.StrictMode>,
  document.getElementById("root")
)