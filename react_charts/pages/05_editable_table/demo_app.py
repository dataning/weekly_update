import streamlit as st
import pandas as pd
from simple_editable_grid import SimpleEditableGrid

# Set page configuration
st.set_page_config(page_title="Simple Editable Grid", layout="wide")

# Title and description
st.title("Simple Editable Grid")
st.markdown("This demo shows a simple implementation of an editable data grid using Highcharts DataGrid.")

# Create sample data
def create_product_sample():
    """Create a sample product dataset for demonstration."""
    data = {
        'product': ['Apples', 'Pears', 'Plums', 'Bananas', 'Oranges', 'Grapes'],
        'weight': [100, 40, 0.5, 200, 180, 120],
        'price': [1.5, 2.53, 5, 4.5, 3.2, 8.75],
        'stock': [150, 85, 10, 200, 275, 50],
        'category': ['Fruit', 'Fruit', 'Fruit', 'Fruit', 'Fruit', 'Fruit']
    }
    return pd.DataFrame(data)

# Initialize sample data
if 'products_df' not in st.session_state:
    st.session_state['products_df'] = create_product_sample()

# Create the grid component
grid = SimpleEditableGrid(
    title="Product Inventory", 
    subtitle="Edit weight, price, and stock values (make changes then click Save Changes)"
)

# Render the grid
edited_df = grid.render(
    df=st.session_state['products_df'],
    height=400,
    editable_columns=['weight', 'price', 'stock'],
    key="products_grid"
)

# Update session state
st.session_state['products_df'] = edited_df

# Display current dataframe state
if st.button("Show Current DataFrame State"):
    st.subheader("Current DataFrame State")
    st.dataframe(edited_df, use_container_width=True)
    
    # Add download button
    csv = edited_df.to_csv(index=False)
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name="products_data.csv",
        mime="text/csv"
    )

# Explanation
st.markdown("""
---
### How This Works

This simplified grid component:

1. Uses Highcharts DataGrid for the interactive grid
2. Stores edits in the browser's localStorage
3. Uses GET parameters for passing data back to Python
4. Avoids deprecated Streamlit APIs

Key features:
- Edit values directly in the grid
- View edit history in real-time
- Export to CSV directly from the grid
- Save changes back to the DataFrame

This approach is much simpler than the previous solutions and works more reliably.
""")