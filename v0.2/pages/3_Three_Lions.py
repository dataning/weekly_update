import streamlit as st
import pandas as pd
from engine.nonprofit_builder import Form990Processor
from engine.nonprofit_prepare import Multi_IRS990_Forms
from components.text_display import display_multi_column_content, format_profile_content
from components.compare_compensation import display_multi_compensation_analysis

# Define default EINs
DEFAULT_EINS = ["237172306", "362722198", "042111203"]

def get_ein_data(ein):
    """
    Retrieve data for a single EIN
    """
    try:
        long_processor = Form990Processor()
        abc_df = long_processor.run(ein)
        forms = Multi_IRS990_Forms(ein, abc_df)
        
        data = {
            'profile': forms.get_profile().to_pandas(),
            'revenue_expense': forms.get_revenue_expense().to_pandas(),
            'endowment': forms.get_endowment().to_pandas(),
            'invested': forms.get_invested().to_pandas(),
            'other_securities': forms.get_investment_other_securities().to_pandas(),
            'people': forms.get_people().to_pandas(),
            'compensation': forms.get_compensation_data().to_pandas(),
            'contractor': forms.get_contractors().to_pandas()
        }
        
        for df_name in data:
            if not data[df_name].empty:
                data[df_name]['EIN'] = ein
            
        return data
    except Exception as e:
        st.error(f"Error processing EIN {ein}: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state with default values"""
    if 'selected_eins' not in st.session_state:
        st.session_state.selected_eins = {
            'ein1': DEFAULT_EINS[0],
            'ein2': DEFAULT_EINS[1],
            'ein3': DEFAULT_EINS[2]
        }
    
    if 'ein_data' not in st.session_state:
        st.session_state.ein_data = {}
        # Pre-load data for default EINs
        for ein in DEFAULT_EINS:
            if ein not in st.session_state.ein_data:
                st.session_state.ein_data[ein] = get_ein_data(ein)

def main():
    st.set_page_config(layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    # Input for EINs with default values
    ein_input = st.text_input(
        "Enter EINs (comma-separated)", 
        value=", ".join(DEFAULT_EINS),
        key="ein_input"
    )
    
    ein_list = [ein.strip() for ein in ein_input.split(',')]
    
    # Get organization names first
    def get_org_name(ein_data):
        if ein_data and 'profile' in ein_data and not ein_data['profile'].empty:
            df = ein_data['profile']
            if 'DoingBusinessAsName_BusinessNameLine1Txt' in df.columns:
                dba_name = df['DoingBusinessAsName_BusinessNameLine1Txt'].iloc[0]
                if pd.notna(dba_name):
                    return dba_name
            if 'Filer_BusinessName_BusinessNameLine1Txt' in df.columns:
                filer_name = df['Filer_BusinessName_BusinessNameLine1Txt'].iloc[0]
                if pd.notna(filer_name):
                    return filer_name
        return "Organization Name Not Available"

    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    # Column 1
    with col1:
        org_name = get_org_name(st.session_state.ein_data.get(st.session_state.selected_eins['ein1']))
        st.markdown(f"### {org_name}")
        ein1 = st.selectbox(
            "Select EIN 1",
            options=ein_list,
            key='ein1_select',
            index=ein_list.index(st.session_state.selected_eins['ein1']) if st.session_state.selected_eins['ein1'] in ein_list else 0
        )
        
        if ein1 != st.session_state.selected_eins['ein1']:
            st.session_state.selected_eins['ein1'] = ein1
            st.session_state.ein_data[ein1] = get_ein_data(ein1)
    
    # Column 2
    with col2:
        org_name = get_org_name(st.session_state.ein_data.get(st.session_state.selected_eins['ein2']))
        st.markdown(f"### {org_name}")
        ein2 = st.selectbox(
            "Select EIN 2",
            options=ein_list,
            key='ein2_select',
            index=ein_list.index(st.session_state.selected_eins['ein2']) if st.session_state.selected_eins['ein2'] in ein_list else 0
        )
        
        if ein2 != st.session_state.selected_eins['ein2']:
            st.session_state.selected_eins['ein2'] = ein2
            st.session_state.ein_data[ein2] = get_ein_data(ein2)
    
    # Column 3
    with col3:
        org_name = get_org_name(st.session_state.ein_data.get(st.session_state.selected_eins['ein3']))
        st.markdown(f"### {org_name}")
        ein3 = st.selectbox(
            "Select EIN 3",
            options=ein_list,
            key='ein3_select',
            index=ein_list.index(st.session_state.selected_eins['ein3']) if st.session_state.selected_eins['ein3'] in ein_list else 0
        )
        
        if ein3 != st.session_state.selected_eins['ein3']:
            st.session_state.selected_eins['ein3'] = ein3
            st.session_state.ein_data[ein3] = get_ein_data(ein3)

    # Create separate profile dataframes
    profile_df1 = (st.session_state.ein_data.get(ein1, {}) or {}).get('profile', pd.DataFrame())
    profile_df2 = (st.session_state.ein_data.get(ein2, {}) or {}).get('profile', pd.DataFrame())
    profile_df3 = (st.session_state.ein_data.get(ein3, {}) or {}).get('profile', pd.DataFrame())

    # Styles definition
    column_styles = [
        {
            'border_color': "#e51ec7",  # Pink
            'bg_color': "#fdf2ff",
            'padding': "25px",
            'border_width': "6px"
        },
        {
            'border_color': "#391ee5",  # Blue
            'bg_color': "#f2f4ff",
            'padding': "25px",
            'border_width': "6px"
        },
        {
            'border_color': "#1ee5df",  # Cyan
            'bg_color': "#f2fffd",
            'padding': "25px",
            'border_width': "6px"
        }
    ]

    # Display profile data exploration
    st.header("Profile")
    
    # Format content for each profile
    profile_contents = [
        format_profile_content(profile_df1, ein1),
        format_profile_content(profile_df2, ein2),
        format_profile_content(profile_df3, ein3)
    ]
    
    # Display all profiles in columns with custom styles
    display_multi_column_content(profile_contents, column_styles)
    
    # Option to view full dataframes
    if st.checkbox("View full profile data"):
        tabs = st.tabs(["Profile 1", "Profile 2", "Profile 3"])
        for tab, df in zip(tabs, [profile_df1, profile_df2, profile_df3]):
            with tab:
                if not df.empty:
                    st.dataframe(df)

    # In your main application
    display_multi_compensation_analysis(st.session_state.ein_data, [ein1, ein2, ein3])

if __name__ == "__main__":
    main()