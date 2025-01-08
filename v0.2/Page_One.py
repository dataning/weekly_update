import streamlit as st
import os
from pathlib import Path
import pandas as pd
import polars as pl
from engine.nonprofit_builder import Form990Processor
from engine.nonprofit_prepare import Multi_IRS990_Forms
from components.profile_component import display_profile
from components.revenue_expense import display_financial_analysis
from components.endowment_funds_component import display_endowment_analysis
from components.investment_portfolio import display_portfolio_analysis
from components.investments_other_securities import display_investment_categories
from components.employee import display_compensation_analysis
from components.people import display_employee_metrics
from components.contractor import display_contractor_analysis


# Set page to wide mode - this must be the first Streamlit command
st.set_page_config(layout="wide")

@st.cache_data
def get_ein_list_from_files():
    search_dir = Path('search_data')
    
    if not search_dir.exists():
        st.error("Directory 'search_data' not found!")
        return []
    
    ein_files = list(search_dir.glob('*_long.parquet'))
    ein_list = [f.name.split('_')[0] for f in ein_files]
    ein_list.sort()
    
    return ein_list

@st.cache_data
def get_big_data():
   return pl.read_parquet('app_data/nonprofit_wide_20250107.parquet')
df_big = get_big_data()

# Initialize session states
if 'layout_type' not in st.session_state:
    st.session_state.layout_type = "Tabbed View"

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Overview"

# Get the cached list of EINs
available_eins = get_ein_list_from_files()

if not available_eins:
    st.error("No EIN files found in search_data directory!")
else:
    # Sidebar setup
    with st.sidebar:
        st.title("Navigation")
        
        # EIN Selection
        selected_ein = st.selectbox(
            "Select Organization EIN",
            options=available_eins,
            index=0
        )

        # Layout Switch
        st.session_state.layout_type = st.radio(
            "Select Layout:",
            ["Scrolling View", "Tabbed View"],
            key="layout_switch"
        )
        
        # Navigation (only show if tabbed view is selected)
        if st.session_state.layout_type == "Tabbed View":
            st.session_state.current_page = st.radio(
                "Go to",
                ["Overview", "Endowment Funds", "Investment", "People", "Contractors", "Revenue & Expense"],
                key="page_selector"
            )

    # Process the selected EIN
    EIN = selected_ein
    long_processor = Form990Processor()
    abc_df = long_processor.run(EIN)
    forms = Multi_IRS990_Forms(EIN, abc_df)
    selected_ein = int(selected_ein)  # Convert to integer
    filtered_df = df_big.filter(pl.col("ein") == selected_ein).to_pandas()

    # Get the dataframes
    profile_df = forms.get_profile().to_pandas()
    revenue_expense_df = forms.get_revenue_expense().to_pandas()
    endowment_df = forms.get_endowment().to_pandas()
    invested_df = forms.get_invested().to_pandas()
    other_securities_df = forms.get_investment_other_securities().to_pandas()
    people_df = forms.get_people().to_pandas()
    compensation_df = forms.get_compensation_data().to_pandas()
    contractor_df = forms.get_contractors().to_pandas()

    # Display based on layout type
    if st.session_state.layout_type == "Scrolling View":
        # Scrolling View - show all sections
        display_profile(profile_df, filtered_df)
        
        st.header("Endowment Funds")
        display_endowment_analysis(endowment_df)
        st.divider()
        
        st.header("Asset Allocation - Declared")
        display_portfolio_analysis(invested_df)
        st.divider()
        
        st.header("Asset Allocation - Private")
        display_investment_categories(other_securities_df)
        st.divider()
        
        st.header("Compensation")
        display_compensation_analysis(compensation_df)
        display_employee_metrics(people_df)
        st.divider()
        
        st.header("Contractors")
        display_contractor_analysis(contractor_df)
        st.divider()
        
        st.header("Revenue & Expense")
        display_financial_analysis(revenue_expense_df)
        
    else:
        # Tabbed View - show selected section
        if st.session_state.current_page == "Overview":
            display_profile(profile_df, filtered_df)
        elif st.session_state.current_page == "Endowment Funds":
            st.header("Endowment Funds")
            display_endowment_analysis(endowment_df)
        elif st.session_state.current_page == "Investment":
            st.header("Asset Allocation - Declared")
            display_portfolio_analysis(invested_df)
            st.divider()
            
            st.header("Asset Allocation - Private")
            display_investment_categories(other_securities_df)
        elif st.session_state.current_page == "People":
            st.header("Compensation")
            display_compensation_analysis(compensation_df)
            display_employee_metrics(people_df)
        elif st.session_state.current_page == "Contractors":
            st.header("Contractors")
            display_contractor_analysis(contractor_df)
        elif st.session_state.current_page == "Revenue & Expense":
            st.header("Revenue & Expense")
            display_financial_analysis(revenue_expense_df)