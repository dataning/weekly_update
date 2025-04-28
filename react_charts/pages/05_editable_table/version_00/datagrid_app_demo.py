import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import traceback
from datagrid_component import DataGridComponent

# Set page configuration
st.set_page_config(
    page_title="Interactive DataGrid Demo",
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

def create_product_sample():
    """
    Create a sample product dataset for demonstration.
    """
    data = {
        'product': ['Apples', 'Pears', 'Plums', 'Bananas', 'Oranges', 'Grapes'],
        'weight': [100, 40, 0.5, 200, 180, 120],
        'price': [1.5, 2.53, 5, 4.5, 3.2, 8.75],
        'stock': [150, 85, 10, 200, 275, 50],
        'category': ['Fruit', 'Fruit', 'Fruit', 'Fruit', 'Fruit', 'Fruit']
    }
    
    return pd.DataFrame(data)

def create_sales_sample():
    """
    Create a sample sales dataset for demonstration.
    """
    np.random.seed(42)
    data = {
        'date': pd.date_range(start='2024-01-01', periods=20),
        'customer': np.random.choice(['Smith Inc.', 'Johnson LLC', 'Brown & Co.', 'Davis Group', 'Wilson Ltd.'], 20),
        'product': np.random.choice(['Widget A', 'Widget B', 'Service C', 'Product D', 'Tool E'], 20),
        'quantity': np.random.randint(1, 50, 20),
        'unit_price': np.round(np.random.uniform(10, 200, 20), 2),
        'discount': np.round(np.random.uniform(0, 0.3, 20), 2)
    }
    
    df = pd.DataFrame(data)
    df['total'] = np.round(df['quantity'] * df['unit_price'] * (1 - df['discount']), 2)
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    return df

def generate_code_snippet(
    df_name,
    height=400,
    editable_columns=None,
    title="Interactive Data Grid",
    subtitle="Source: Data visualization"
):
    """Generate a code snippet for DataGrid visualization"""
    editable_str = "None" if editable_columns is None else str(editable_columns)
    
    code = f"""
# Import the DataGridComponent
from datagrid_component import DataGridComponent

# Create a DataGrid component
grid = DataGridComponent(
    title="{title}",
    subtitle="{subtitle}"
)

# Render the DataGrid
grid.render(
    df={df_name},
    height={height},
    editable_columns={editable_str}
)
"""
    return code

def display_data_summary(df):
    """Display summary statistics for the dataframe"""
    # Data metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(df))
        
    with col2:
        st.metric("Total Columns", len(df.columns))
        
    num_cols = len(df.select_dtypes(include=['number']).columns)
    with col3:
        st.metric("Numeric Columns", num_cols)
    
    # Summary
    st.subheader("Data Summary")
    
    if len(df) > 0 and len(df.columns) > 0:
        summary_df = pd.DataFrame({
            'Column': df.columns,
            'Type': [str(df[col].dtype) for col in df.columns],
            'Non-Null Count': [df[col].count() for col in df.columns],
            'Null Count': [df[col].isna().sum() for col in df.columns]
        })
        
        # Add sample values for each column
        summary_df['Sample Values'] = [
            ', '.join(str(x) for x in df[col].dropna().head(3).tolist()) 
            for col in df.columns
        ]
        
        st.dataframe(summary_df)
    else:
        st.info("No data available for summary")

# --- App Header ---
st.title("Interactive DataGrid Demo")
st.markdown("""
This app demonstrates an interactive data grid component with editable cells.
Upload your own data or use one of the sample datasets.
""")

# --- Main Navigation ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Upload Your Data", 
    "Products Sample", 
    "Sales Sample", 
    "About & Documentation"
])

# Tab 1: Upload Your Data
with tab1:
    st.header("Create a DataGrid from Your Data")
    
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
                
                # Display data summary
                display_data_summary(user_df)
                
                # Column selection for editing
                st.subheader("Step 2: Configure Editable Columns")
                
                edit_option = st.radio(
                    "Select which columns should be editable:",
                    ["All columns", "Only specific columns", "No columns"],
                    index=0,
                    key="edit_option"
                )
                
                editable_columns = None
                if edit_option == "Only specific columns":
                    editable_columns = st.multiselect(
                        "Select editable columns:",
                        options=list(user_df.columns),
                        default=list(user_df.select_dtypes(include=['number']).columns),
                        key="editable_cols"
                    )
                elif edit_option == "No columns":
                    editable_columns = []
                
                # Visualization settings
                st.subheader("Step 3: Customize Visualization")
                
                col1, col2 = st.columns(2)
                with col1:
                    chart_title = st.text_input("Grid title:", "My Interactive DataGrid", key="upload_title")
                    chart_height = st.slider("Grid height:", 300, 800, 400, key="upload_height")
                    
                with col2:
                    chart_sub = st.text_input("Grid subtitle:", "Source: Custom Data", key="upload_sub")
                
                # Generate visualization
                if st.button("Generate DataGrid", key="upload_generate"):
                    with st.spinner("Creating DataGrid..."):
                        try:
                            # Create the DataGrid component
                            grid = DataGridComponent(title=chart_title, subtitle=chart_sub)
                            
                            # Render the grid
                            grid.render(
                                df=user_df,
                                height=chart_height,
                                editable_columns=editable_columns,
                                key="user_grid"
                            )
                            
                            # Show code snippet for replicating the visualization
                            if st.checkbox("📋 Code to Replicate This Visualization"):
                                st.subheader("Python Code")
                                code = generate_code_snippet(
                                    df_name="your_dataframe", 
                                    height=chart_height,
                                    editable_columns=editable_columns,
                                    title=chart_title,
                                    subtitle=chart_sub
                                )
                                st.code(code, language="python")
                                
                                st.caption("Copy this code and replace 'your_dataframe' with your actual DataFrame variable.")
                        except Exception as e:
                            st.error(f"Error creating DataGrid: {str(e)}")
                            if st.checkbox("Show Error Details for Grid"):
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
            
            Your data should be well-structured with:
            
            - Clear column headers
            - Consistent data types within columns
            - At least one column
            
            The grid will allow editing of numeric values by default, but you can customize which
            columns are editable.
            
            ### Example:
            
            | Name   | Category | Price | Stock |
            |--------|----------|-------|-------|
            | Item A | Food     | 12.99 | 100   |
            | Item B | Drink    | 5.99  | 250   |
            | Item C | Food     | 8.50  | 75    |
            | Item D | Other    | 19.99 | 30    |
            
            The grid will display your data and track any edits made during the session.
            """)

# Tab 2: Products Sample
with tab2:
    st.header("Product Dataset")
    st.markdown("""
    This sample demonstrates a simple product inventory DataGrid with 
    editable weights, prices, and stock quantities.
    """)
    
    with st.spinner("Generating sample data..."):
        products_df = create_product_sample()

    # Display data summary
    display_data_summary(products_df)

    # Visualization settings
    st.subheader("Customize Visualization")
    
    col1, col2 = st.columns(2)
    with col1:
        chart_title = st.text_input("Grid title:", "Product Inventory", key="products_title")
        chart_height = st.slider("Grid height:", 300, 800, 500, key="products_height")
        
    with col2:
        chart_sub = st.text_input("Grid subtitle:", "Edit product details", key="products_sub")
        editable_cols = st.multiselect(
            "Select editable columns:",
            options=['product', 'weight', 'price', 'stock', 'category'],
            default=['product', 'weight', 'price', 'stock'],
            key="products_editable"
        )

    # DataGrid
    st.subheader("DataGrid")
    
    with st.spinner("Creating DataGrid..."):
        grid = DataGridComponent(
            title=chart_title,
            subtitle=chart_sub
        )
        edited_df = grid.render(
            df=products_df,
            height=chart_height,
            editable_columns=editable_cols,
            key="products_grid"
        )
        
        # Add a button to show the edited DataFrame
        if st.button("Show Current DataFrame State"):
            # For now, just display the original DataFrame
            st.subheader("Current DataFrame State")
            st.dataframe(products_df)
            
            # Option to download the current state as CSV
            csv = products_df.to_csv(index=False)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="products_data.csv",
                mime="text/csv",
                key="download_edited_products"
            )

    if st.checkbox("📋 Code to Replicate This Visualization", False, key="products_code"):
        st.subheader("Python Code")
        code = generate_code_snippet(
            df_name="products_df", 
            height=chart_height,
            editable_columns=editable_cols,
            title=chart_title,
            subtitle=chart_sub
        )
        st.code(code, language="python")
        
    # Option to download sample data
    csv = products_df.to_csv(index=False)
    st.download_button(
        label="Download Products Data as CSV",
        data=csv,
        file_name="products_data.csv",
        mime="text/csv",
        key="download_products"
    )

# Tab 3: Sales Sample
with tab3:
    st.header("Sales Transactions Dataset")
    st.markdown("""
    This example shows a more complex sales transactions DataGrid with
    editable quantities, prices, and discounts.
    """)
    
    with st.spinner("Generating sample data..."):
        sales_df = create_sales_sample()

    # Display data summary
    display_data_summary(sales_df)

    # Visualization settings
    st.subheader("Customize Visualization")
    
    col1, col2 = st.columns(2)
    with col1:
        chart_title = st.text_input("Grid title:", "Sales Transactions", key="sales_title")
        chart_height = st.slider("Grid height:", 300, 800, 500, key="sales_height")
        
    with col2:
        chart_sub = st.text_input("Grid subtitle:", "Edit sales details", key="sales_sub")
        editable_cols = st.multiselect(
            "Select editable columns:",
            options=['quantity', 'unit_price', 'discount'],
            default=['quantity', 'unit_price', 'discount'],
            key="sales_editable"
        )

    # DataGrid
    st.subheader("DataGrid")
    
    with st.spinner("Creating DataGrid..."):
        grid = DataGridComponent(
            title=chart_title,
            subtitle=chart_sub
        )
        edited_df = grid.render(
            df=sales_df,
            height=chart_height,
            editable_columns=editable_cols,
            key="sales_grid"
        )
        
        # Add a button to show the edited DataFrame
        if st.button("Show Current DataFrame State", key="show_sales_df"):
            # For now, just display the original DataFrame
            st.subheader("Current DataFrame State")
            st.dataframe(sales_df)
            
            # Option to download the current state as CSV
            csv = sales_df.to_csv(index=False)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="sales_data.csv",
                mime="text/csv",
                key="download_edited_sales"
            )

    if st.checkbox("📋 Code to Replicate This Visualization", False, key="sales_code"):
        st.subheader("Python Code")
        code = generate_code_snippet(
            df_name="sales_df", 
            height=chart_height,
            editable_columns=editable_cols,
            title=chart_title,
            subtitle=chart_sub
        )
        st.code(code, language="python")
        
    # Option to download sample data
    csv = sales_df.to_csv(index=False)
    st.download_button(
        label="Download Sales Data as CSV",
        data=csv,
        file_name="sales_data.csv",
        mime="text/csv",
        key="download_sales"
    )

# Tab 4: About & Documentation
with tab4:
    st.header("About the DataGrid Component")
    
    st.markdown("""
    ## What is an Interactive DataGrid?
    
    An interactive DataGrid is a table-like component that allows users to:
    
    - View tabular data in a structured format
    - Edit cell values directly in the interface
    - See a history of changes made to the data
    - Sort and filter data (in more advanced implementations)
    
    This component wraps Highcharts' DataGrid functionality into a reusable Streamlit component, similar to the Sankey diagram implementation provided in the example.
    
    ## Features
    
    - **Interactive**: Edit cell values with double-click
    - **Customizable**: Control which columns are editable
    - **Change Tracking**: Log history of all edits made during the session
    - **Responsive**: Automatically adjusts to container width
    """)
    
    if st.checkbox("Show Installation Instructions"):
        st.markdown("""
        ## Installation
        
        To use this component in your own projects:
        
        ```bash
        pip install streamlit
        pip install pandas numpy jinja2
        ```
        
        Copy the `datagrid_component.py` file to your project directory.
        """)
    
    if st.checkbox("Show Basic Usage"):
        st.markdown("""
        ## Basic Usage
        
        ```python
        import pandas as pd
        import streamlit as st
        from datagrid_component import DataGridComponent
        
        # Load your data
        df = pd.DataFrame({
            'product': ['Apples', 'Pears', 'Plums'],
            'weight': [100, 40, 0.5],
            'price': [1.5, 2.53, 5]
        })
        
        # Create and render DataGrid
        grid = DataGridComponent(
            title="Product Information",
            subtitle="Inventory details"
        )
        
        grid.render(
            df=df,
            height=400,
            editable_columns=['weight', 'price']
        )
        ```
        """)
    
    st.subheader("Customization Options")
    
    if st.checkbox("Show Appearance Options"):
        st.markdown("""
        ### Appearance
        
        - **Title and Subtitle**: Set custom title and subtitle text
        - **Height**: Adjust the height of the grid in pixels
        - **Editable Columns**: Specify which columns users can edit
        
        The component uses Highcharts' DataGrid styling, which automatically adjusts to light or dark mode
        based on the user's system preferences.
        """)
    
    if st.checkbox("Show Data Handling Information"):
        st.markdown("""
        ### Data Handling
        
        The component works with any pandas DataFrame and supports:
        
        - Numeric data (integers, floats)
        - Text data (strings)
        - Date data (as strings)
        - Boolean data
        
        Changes made in the grid are tracked in the UI but are not automatically persisted back to the
        DataFrame. In a real application, you would implement a callback mechanism to update the
        backend data when changes are made.
        
        ### Limitations
        
        - Changes are only tracked within the current session
        - Complex cell content (like HTML or components) is not supported
        - Advanced features like cell validation or conditional formatting would require additional customization
        """)
    
    st.subheader("Technical Implementation")
    
    if st.checkbox("Show Technical Details"):
        st.markdown("""
        ### How It Works
        
        The DataGrid component wraps Highcharts' DataGrid library and integrates it with Streamlit:
        
        1. **HTML Template**: The component uses Jinja2 templates to generate the HTML, CSS, and JavaScript
        2. **Data Conversion**: Pandas DataFrame data is converted to a format suitable for Highcharts
        3. **Event Handling**: JavaScript events track when cells are edited and log the changes
        4. **Streamlit Integration**: The component is rendered using Streamlit's components.html()
        
        ### Extending the Component
        
        To add more functionality:
        
        - Add filtering capabilities by extending the JavaScript
        - Implement data persistence by using Streamlit session state
        - Add data validation rules for specific columns
        - Include cell formatting based on value conditions
        """)
    
    st.info("This component is for demonstration purposes and can be extended for more complex use cases.")
    
    # Credits section
    st.markdown("---")
    st.markdown("""
    ### Credits
    
    - Built with [Streamlit](https://streamlit.io/)
    - Visualization powered by [Highcharts DataGrid](https://www.highcharts.com/products/datagrid/)
    - Inspired by the Sankey diagram component approach
    """)