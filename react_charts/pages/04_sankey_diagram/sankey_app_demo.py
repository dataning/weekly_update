import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import traceback
from sankey_component import SankeyComponent

# Set page configuration
st.set_page_config(
    page_title="Flow Diagram Generator",
    page_icon="📊",
    layout="wide"
)

def read_file_to_dataframe(uploaded_file):
    """
    Read an uploaded file into a pandas DataFrame.
    Supports CSV, Excel, Parquet, and JSON formats.
    
    Parameters:
    -----------
    uploaded_file : UploadedFile
        Streamlit uploaded file object
        
    Returns:
    --------
    DataFrame or None
        Pandas DataFrame or None if the file type is unsupported
    """
    try:
        # Get file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Read file based on extension
        if file_extension == '.csv':
            return pd.read_csv(uploaded_file)
        elif file_extension in ['.xls', '.xlsx']:
            return pd.read_excel(uploaded_file)
        elif file_extension in ['.parquet', '.pq']:
            try:
                # Need to save to a BytesIO object first
                bytes_data = io.BytesIO(uploaded_file.getvalue())
                return pd.read_parquet(bytes_data)
            except ImportError:
                st.error("Parquet support requires 'pyarrow' or 'fastparquet' packages.")
                st.info("Install with: pip install pyarrow")
                return None
        elif file_extension == '.json':
            return pd.read_json(uploaded_file)
        else:
            st.error(f"Unsupported file format: {file_extension}")
            st.info("Supported formats: CSV, Excel (.xls, .xlsx), Parquet (.parquet, .pq), JSON")
            return None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        if st.checkbox("Show Error Details"):
            st.write(traceback.format_exc())
        return None

def create_financial_flow_sample():
    """
    Create a financial flow sample dataset for visualization.
    Based on simplified company financial data.
    """
    data = [
        # Revenue sources
        ['SaaS/PaaS', 'Revenue', 4.9],
        ['Cloud', 'Revenue', 5.0],
        ['IaaS', 'Revenue', 0.1],
        ['Software Licenses', 'Revenue', 0.1],
        ['Licenses & Support', 'Revenue', 2.9],
        ['Software Support', 'Revenue', 2.8],
        ['Services', 'Revenue', 1.1],
        
        # Revenue splits to Gross Profit and Cost of Revenue
        ['Revenue', 'Gross profit', 6.6],
        ['Revenue', 'Cost of revenue', 2.4],
        
        # Gross Profit splits to Operating Profit and Operating Expenses
        ['Gross profit', 'Operating profit', 2.3],
        ['Gross profit', 'Operating expenses', 4.3],
        
        # Operating expenses breakdown
        ['Operating expenses', 'S&M', 2.2],
        ['Operating expenses', 'R&D', 1.7],
        ['Operating expenses', 'G&A', 0.4],
        
        # Operating profit to final results
        ['Operating profit', 'Net profit', 1.8],
        ['Operating profit', 'Tax', 0.7],
        ['Other', 'Net profit', 0.1]
    ]
    
    df = pd.DataFrame(data, columns=['Source', 'Target', 'Value'])
    return df

def create_endowment_flow_sample():
    """
    Create a university endowment flow sample dataset for visualization.
    Shows flows from funding sources through investments to spending categories.
    """
    data = [
        # Sources to Investment Pool
        ['Alumni Donations', 'Endowment Pool', 5.2],
        ['Corporate Donations', 'Endowment Pool', 2.8],
        ['Foundation Grants', 'Endowment Pool', 3.1],
        ['Investment Returns', 'Endowment Pool', 7.5],
        ['Planned Giving', 'Endowment Pool', 1.7],
        ['Other Gifts', 'Endowment Pool', 0.9],
        
        # Endowment Pool to Investment Categories
        ['Endowment Pool', 'Equities', 8.4],
        ['Endowment Pool', 'Fixed Income', 4.3],
        ['Endowment Pool', 'Real Estate', 3.2],
        ['Endowment Pool', 'Hedge Funds', 2.6],
        ['Endowment Pool', 'Private Equity', 2.1],
        ['Endowment Pool', 'Cash Reserves', 0.6],
        
        # Investment Returns
        ['Equities', 'Annual Payout', 1.6],
        ['Fixed Income', 'Annual Payout', 0.8],
        ['Real Estate', 'Annual Payout', 0.6],
        ['Hedge Funds', 'Annual Payout', 0.5],
        ['Private Equity', 'Annual Payout', 0.4],
        ['Cash Reserves', 'Annual Payout', 0.1],
        
        # Annual Payout to Usage Categories
        ['Annual Payout', 'Scholarships', 1.4],
        ['Annual Payout', 'Faculty Support', 1.0],
        ['Annual Payout', 'Research', 0.8],
        ['Annual Payout', 'Facilities', 0.5],
        ['Annual Payout', 'Academic Programs', 0.2],
        ['Annual Payout', 'Library', 0.1]
    ]
    
    df = pd.DataFrame(data, columns=['Source', 'Target', 'Value'])
    return df

def generate_code_snippet(
    df_name,
    from_column,
    to_column,
    value_column,
    height=600,
    title="Flow Diagram",
    subtitle="Source: Data visualization",
    curveness=0.5,
    node_width=20,
    node_padding=10,
    link_opacity=0.5
):
    """Generate a code snippet for Sankey visualization"""
    code = f"""
# Import the SankeyComponent
from sankey_component import SankeyComponent

# Create a Sankey diagram component
sankey = SankeyComponent(
    title="{title}",
    subtitle="{subtitle}"
)

# Render the Sankey diagram
sankey.render(
    df={df_name},
    from_column='{from_column}',
    to_column='{to_column}',
    weight_column='{value_column}',
    height={height},
    curveness={curveness},
    node_width={node_width},
    node_padding={node_padding},
    link_opacity={link_opacity}
)
"""
    return code

def display_data_summary(df, from_column, to_column, value_column):
    """Display summary statistics for the dataframe"""
    # Data metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Flows", len(df))
        
    with col2:
        unique_nodes = pd.concat([df[from_column], df[to_column]]).nunique()
        st.metric("Unique Nodes", unique_nodes)
        
    with col3:
        total_value = df[value_column].sum()
        st.metric("Total Flow Value", f"{total_value:.2f}")
    
    # Sample Data
    st.subheader("Sample Data")
    st.dataframe(df.head(10))
    
    # Summary of sources and targets
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Sources")
        top_sources = df.groupby(from_column)[value_column].sum().sort_values(ascending=False).head(5)
        source_df = pd.DataFrame({
            'Source': top_sources.index,
            'Total Output': top_sources.values
        })
        st.dataframe(source_df)
        
    with col2:
        st.subheader("Top Targets")
        top_targets = df.groupby(to_column)[value_column].sum().sort_values(ascending=False).head(5)
        target_df = pd.DataFrame({
            'Target': top_targets.index,
            'Total Input': top_targets.values
        })
        st.dataframe(target_df)

# --- App Header ---
st.title("Flow Diagram Generator")
st.markdown("""
This app helps you create interactive Sankey diagrams to visualize flows between nodes.
Upload a CSV, Excel, Parquet, or JSON file, or use a sample dataset.
""")

# --- Main Navigation ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Upload Your Data", 
    "Financial Flow Sample", 
    "University Endowment", 
    "About & Documentation"
])

# Tab 1: Upload Your Data
with tab1:
    st.header("Create a Sankey Diagram from Your Data")
    
    # File uploader
    st.subheader("Step 1: Upload Your Data File")
    supported_formats = "CSV, Excel, Parquet, or JSON"
    uploaded_file = st.file_uploader(
        f"Upload a file ({supported_formats})",
        type=["csv", "xlsx", "xls", "parquet", "pq", "json"],
        key="data_upload"
    )
    
    if uploaded_file:
        try:
            with st.spinner("Reading file..."):
                user_df = read_file_to_dataframe(uploaded_file)
                
            if user_df is not None:
                st.success(f"Successfully loaded data with {len(user_df)} rows and {len(user_df.columns)} columns")
                
                # Column selection
                st.subheader("Step 2: Select Flow Columns")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    from_col = st.selectbox("Source column:", user_df.columns, key="upload_from")
                
                with col2:
                    to_col = st.selectbox("Target column:", user_df.columns, key="upload_to")
                
                with col3:
                    numeric_cols = user_df.select_dtypes(include='number').columns.tolist()
                    if not numeric_cols:
                        st.error("No numeric columns found in your data. The value column must be numeric.")
                        value_col = None
                    else:
                        value_col = st.selectbox(
                            "Value column (flow magnitude):",
                            numeric_cols,
                            key="upload_value"
                        )
                
                # Display data summary
                if value_col:
                    display_data_summary(user_df, from_col, to_col, value_col)
                
                # Visualization settings
                st.subheader("Step 3: Customize Visualization")
                
                col1, col2 = st.columns(2)
                with col1:
                    chart_title = st.text_input("Chart title:", "My Flow Diagram", key="upload_title")
                    chart_sub = st.text_input("Chart subtitle:", "Source: Custom Data", key="upload_sub")
                    chart_height = st.slider("Chart height:", 400, 1000, 600, key="upload_height")
                    
                with col2:
                    curveness = st.slider("Link curvature:", 0.0, 1.0, 0.5, 0.1, key="upload_curve")
                    node_width = st.slider("Node width:", 10, 50, 20, key="upload_width")
                    node_padding = st.slider("Node padding:", 5, 30, 10, key="upload_padding")
                    link_opacity = st.slider("Link opacity:", 0.1, 1.0, 0.5, 0.1, key="upload_opacity")
                
                # Node color customization option
                custom_colors = st.checkbox("Customize node colors", key="upload_custom_colors")
                node_colors = None
                
                if custom_colors:
                    st.write("Select colors for specific nodes (leave blank for default colors)")
                    
                    # Get unique node names
                    all_nodes = pd.concat([user_df[from_col], user_df[to_col]]).unique()
                    
                    # Create a multi-column layout for color pickers
                    cols = st.columns(3)
                    node_colors = {}
                    
                    for i, node in enumerate(all_nodes):
                        with cols[i % 3]:
                            color = st.color_picker(f"{node}", "#1f77b4", key=f"color_{i}")
                            node_colors[node] = color
                
                # Generate visualization
                if st.button("Generate Sankey Diagram", key="upload_generate") and value_col:
                    with st.spinner("Creating Sankey diagram..."):
                        try:
                            # Create the Sankey component
                            sankey = SankeyComponent(title=chart_title, subtitle=chart_sub)
                            
                            # Render the diagram
                            sankey.render(
                                df=user_df,
                                from_column=from_col,
                                to_column=to_col,
                                weight_column=value_col,
                                height=chart_height,
                                validate_data=True,
                                node_colors=node_colors,
                                curveness=curveness,
                                node_width=node_width,
                                node_padding=node_padding,
                                link_opacity=link_opacity
                            )
                            
                            # Show code snippet for replicating the visualization
                            if st.checkbox("📋 Code to Replicate This Visualization"):
                                st.subheader("Python Code")
                                code = generate_code_snippet(
                                    df_name="your_dataframe", 
                                    from_column=from_col,
                                    to_column=to_col,
                                    value_column=value_col,
                                    height=chart_height,
                                    title=chart_title,
                                    subtitle=chart_sub,
                                    curveness=curveness,
                                    node_width=node_width,
                                    node_padding=node_padding,
                                    link_opacity=link_opacity
                                )
                                st.code(code, language="python")
                                
                                st.caption("Copy this code and replace 'your_dataframe' with your actual DataFrame variable.")
                        except Exception as e:
                            st.error(f"Error creating Sankey diagram: {str(e)}")
                            if st.checkbox("Show Error Details for Diagram"):
                                st.write(traceback.format_exc())
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            if st.checkbox("Show File Processing Error Details"):
                st.write(traceback.format_exc())
    else:
        st.info(f"Upload a file to get started. Supported formats: {supported_formats}")
        
        if st.checkbox("Show Expected Data Format"):
            st.markdown("""
            ### Data Requirements
            
            Your data should have at least 3 columns:
            
            1. **Source Column**: Origin nodes of the flow (e.g., Revenue, Investments, Income)
            2. **Target Column**: Destination nodes of the flow (e.g., Expenses, Departments, Categories)
            3. **Value Column**: Numeric values representing the magnitude of flow
            
            ### Example:
            
            | Source       | Target         | Value  |
            |--------------|----------------|--------|
            | Revenue      | Marketing      | 8.9    |
            | Investments  | R&D            | 5.17   |
            | Operations   | Expenses       | 3.44   |
            | Funding      | Development    | 0.16   |
            | Sales        | Revenue        | 24.6   |
            
            The Sankey diagram will show flows between nodes, with the width of each link proportional to the value.
            """)

# Tab 2: Financial Flow Sample
with tab2:
    st.header("Financial Flow Dataset")
    st.markdown("""
    This example shows a Sankey diagram of a company's financial flows,
    from revenue sources through to net profit.
    """)
    
    with st.spinner("Generating sample data..."):
        financial_df = create_financial_flow_sample()

    # Display data summary
    display_data_summary(financial_df, 'Source', 'Target', 'Value')

    # Visualization settings
    st.subheader("Customize Visualization")
    
    col1, col2 = st.columns(2)
    with col1:
        chart_title = st.text_input("Chart title:", "Company Financial Flow", key="financial_title")
        chart_sub = st.text_input("Chart subtitle:", "Revenue to Net Profit Flow", key="financial_sub")
        chart_height = st.slider("Chart height:", 400, 1000, 600, key="financial_height")
        
    with col2:
        curveness = st.slider("Link curvature:", 0.0, 1.0, 0.5, 0.1, key="financial_curve")
        node_width = st.slider("Node width:", 10, 50, 20, key="financial_width")
        node_padding = st.slider("Node padding:", 5, 30, 10, key="financial_padding")
        link_opacity = st.slider("Link opacity:", 0.1, 1.0, 0.5, 0.1, key="financial_opacity")

    # Define financial node colors
    node_colors = {
        'Revenue': '#4CAF50',  # Green
        'Gross profit': '#8BC34A',  # Light green
        'Operating profit': '#CDDC39',  # Lime
        'Net profit': '#FFEB3B',  # Yellow
        'Cost of revenue': '#F44336',  # Red
        'Operating expenses': '#FF9800',  # Orange
        'S&M': '#FF5722',  # Deep orange
        'R&D': '#E91E63',  # Pink
        'G&A': '#9C27B0',  # Purple
        'Tax': '#795548',  # Brown
        'SaaS/PaaS': '#2196F3',  # Blue
        'Cloud': '#03A9F4',  # Light blue
        'IaaS': '#00BCD4',  # Cyan
        'Software Licenses': '#009688',  # Teal
        'Licenses & Support': '#3F51B5',  # Indigo
        'Software Support': '#673AB7',  # Deep purple
        'Services': '#607D8B',  # Blue grey
        'Other': '#9E9E9E'  # Grey
    }

    # Sankey diagram
    st.subheader("Sankey Diagram")
    
    with st.spinner("Creating Sankey diagram..."):
        sankey = SankeyComponent(
            title=chart_title,
            subtitle=chart_sub
        )
        sankey.render(
            df=financial_df,
            from_column='Source',
            to_column='Target',
            weight_column='Value',
            height=chart_height,
            validate_data=True,
            node_colors=node_colors,
            curveness=curveness,
            node_width=node_width,
            node_padding=node_padding,
            link_opacity=link_opacity
        )

    if st.checkbox("📋 Code to Replicate This Visualization", False, key="financial_code"):
        st.subheader("Python Code")
        code = generate_code_snippet(
            df_name="financial_df", 
            from_column='Source',
            to_column='Target',
            value_column='Value',
            height=chart_height,
            title=chart_title,
            subtitle=chart_sub,
            curveness=curveness,
            node_width=node_width,
            node_padding=node_padding,
            link_opacity=link_opacity
        )
        st.code(code, language="python")
        
    # Option to download sample data
    csv = financial_df.to_csv(index=False)
    st.download_button(
        label="Download Financial Flow Data as CSV",
        data=csv,
        file_name="financial_flow_data.csv",
        mime="text/csv",
        key="download_financial"
    )

# Tab 3: University Endowment Sample
with tab3:
    st.header("University Endowment Flow Dataset")
    st.markdown("""
    This example shows a Sankey diagram of a university endowment,
    from funding sources through investments to spending categories.
    """)
    
    with st.spinner("Generating sample data..."):
        endowment_df = create_endowment_flow_sample()

    # Display data summary
    display_data_summary(endowment_df, 'Source', 'Target', 'Value')

    # Visualization settings
    st.subheader("Customize Visualization")
    
    col1, col2 = st.columns(2)
    with col1:
        chart_title = st.text_input("Chart title:", "University Endowment Flow", key="endow_title")
        chart_sub = st.text_input("Chart subtitle:", "Sources to Spending Categories", key="endow_sub")
        chart_height = st.slider("Chart height:", 400, 1000, 600, key="endow_height")
        
    with col2:
        curveness = st.slider("Link curvature:", 0.0, 1.0, 0.5, 0.1, key="endow_curve")
        node_width = st.slider("Node width:", 10, 50, 20, key="endow_width")
        node_padding = st.slider("Node padding:", 5, 30, 10, key="endow_padding")
        link_opacity = st.slider("Link opacity:", 0.1, 1.0, 0.5, 0.1, key="endow_opacity")

    # Define endowment node colors
    node_colors = {
        # Sources
        'Alumni Donations': '#4285F4',  # Google Blue
        'Corporate Donations': '#34A853',  # Google Green
        'Foundation Grants': '#FBBC05',  # Google Yellow
        'Investment Returns': '#EA4335',  # Google Red
        'Planned Giving': '#9C27B0',  # Purple
        'Other Gifts': '#607D8B',  # Blue Grey
        
        # Pool and Investment Categories
        'Endowment Pool': '#FF9800',  # Orange
        'Equities': '#3F51B5',  # Indigo
        'Fixed Income': '#009688',  # Teal
        'Real Estate': '#E91E63',  # Pink
        'Hedge Funds': '#00BCD4',  # Cyan
        'Private Equity': '#8BC34A',  # Light Green
        'Cash Reserves': '#FFC107',  # Amber
        
        # Payout and Usage
        'Annual Payout': '#673AB7',  # Deep Purple
        'Scholarships': '#2196F3',  # Blue
        'Faculty Support': '#4CAF50',  # Green
        'Research': '#FF5722',  # Deep Orange
        'Facilities': '#795548',  # Brown
        'Academic Programs': '#CDDC39',  # Lime
        'Library': '#03A9F4',  # Light Blue
    }

    # Sankey diagram
    st.subheader("Sankey Diagram")
    
    with st.spinner("Creating Sankey diagram..."):
        sankey = SankeyComponent(
            title=chart_title,
            subtitle=chart_sub
        )
        sankey.render(
            df=endowment_df,
            from_column='Source',
            to_column='Target',
            weight_column='Value',
            height=chart_height,
            validate_data=True,
            node_colors=node_colors,
            curveness=curveness,
            node_width=node_width,
            node_padding=node_padding,
            link_opacity=link_opacity
        )

    if st.checkbox("📋 Code to Replicate This Visualization", False, key="endow_code"):
        st.subheader("Python Code")
        code = generate_code_snippet(
            df_name="endowment_df", 
            from_column='Source',
            to_column='Target',
            value_column='Value',
            height=chart_height,
            title=chart_title,
            subtitle=chart_sub,
            curveness=curveness,
            node_width=node_width,
            node_padding=node_padding,
            link_opacity=link_opacity
        )
        st.code(code, language="python")
        
    # Option to download sample data
    csv = endowment_df.to_csv(index=False)
    st.download_button(
        label="Download Endowment Flow Data as CSV",
        data=csv,
        file_name="endowment_flow_data.csv",
        mime="text/csv",
        key="download_endowment"
    )

# Tab 4: About & Documentation
with tab4:
    st.header("About the Sankey Diagram Component")
    
    st.markdown("""
    ## What is a Sankey Diagram?
    
    A Sankey diagram is a flow diagram where the width of the arrows or links between nodes is proportional to the flow quantity.
    Sankey diagrams are particularly useful for visualizing financial flows, investment portfolios, material flows, or any process with transfers between 
    different stages or categories.
    
    ## Features
    
    - **Interactive**: Hover to see flow details
    - **Customizable**: Adjust colors, node width, link curvature
    - **Export**: Download as PNG, JPEG, PDF, or SVG
    - **Fullscreen**: Expand the diagram to fullscreen for better viewing
    """)
    
    if st.checkbox("Show Installation Instructions"):
        st.markdown("""
        ## Installation
        
        To use this component in your own projects:
        
        ```bash
        pip install streamlit
        pip install pandas numpy jinja2
        ```
        
        Copy the `sankey_component.py` file to your project directory.
        """)
    
    if st.checkbox("Show Basic Usage"):
        st.markdown("""
        ## Basic Usage
        
        ```python
        import pandas as pd
        import streamlit as st
        from sankey_component import SankeyComponent
        
        # Load your data
        df = pd.read_csv('your_flow_data.csv')
        
        # Create and render Sankey diagram
        sankey = SankeyComponent(
            title="Your Flow Diagram",
            subtitle="Data source information"
        )
        
        sankey.render(
            df=df,
            from_column='source_column',
            to_column='target_column',
            weight_column='value_column'
        )
        ```
        """)
    
    st.subheader("Customization Options")
    
    if st.checkbox("Show Appearance Options"):
        st.markdown("""
        ### Appearance
        
        - **Title and Subtitle**: Set custom title and subtitle text
        - **Height**: Adjust the height of the diagram in pixels
        - **Node Colors**: Customize colors for specific nodes
        - **Curvature**: Adjust the curvature of the links
        - **Node Width**: Set the width of the nodes in pixels
        - **Node Padding**: Set the vertical spacing between nodes
        - **Link Opacity**: Adjust the transparency of the links
        """)
    
    if st.checkbox("Show Data Format Information"):
        st.markdown("""
        ### Data Format
        
        Your data should be structured with three main columns:
        
        1. **Source**: The origin node of the flow
        2. **Target**: The destination node of the flow
        3. **Value**: The magnitude of the flow
        
        For example:
        
        | Source     | Target      | Value |
        |------------|-------------|-------|
        | Donations  | Endowment   | 10.5  |
        | Endowment  | Investments | 8.2   |
        | Investments| Scholarships| 2.1   |
        | Tuition    | Facilities  | 4.5   |
        
        The component will automatically extract all unique node names and create appropriate 
        connections based on the flows defined in your data.
        """)