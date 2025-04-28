
import polars as pl
import json

def process_presidential_data(df):
    # Get unique presidents
    unique_presidents = df.select('president').unique().to_series().to_list()
    presidents_data = []
    
    for president in unique_presidents:
        # Filter data for current president
        president_df = df.filter(pl.col('president') == president)
        
        # Get the first row's years value for this president
        years = president_df.select('years').row(0)[0]
        
        # Get values in order of year_in_term
        sorted_df = president_df.sort('year_in_term')
        approval_values = sorted_df.select('approval').to_series().to_list()
        disapproval_values = sorted_df.select('disapproval').to_series().to_list()
        change_status_values = sorted_df.select('change_status').to_series().to_list()
        
        # Create range data for the area between lines
        range_data = [[apr, dis] for apr, dis in zip(approval_values, disapproval_values)]
        
        # Create clean ID from president name
        clean_id = president.lower().replace(' ', '').replace('.', '')
        
        president_data = {
            'id': clean_id,
            'name': president,
            'years': years,
            'approval': approval_values,
            'disapproval': disapproval_values,
            'range': range_data,
            'change_status': change_status_values
        }
        presidents_data.append(president_data)
    
    return presidents_data

# Read and process the data
df = pl.read_csv('pages/02_multiple_charts/presidential_approval.csv')

df_with_diff = df.with_columns([
    pl.struct(['approval', 'disapproval'])
    .map_elements(
        lambda x: 
            f"Approval +{x['approval'] - x['disapproval']}%" 
            if x['approval'] > x['disapproval']
            else f"Disapproval +{x['disapproval'] - x['approval']}%",
        return_dtype=pl.Utf8  # Specify return type as string
    ).alias('change_status')
])

df_with_diff = df_with_diff.sort(['president', 'year_in_term'])
df_with_diff.write_parquet('presidential_approval.parquet')
chart_data = process_presidential_data(df_with_diff)
chart_data.write_ndjson('presidential_chart_data.ndjson')
with open('presidential_chart_data.json', 'w') as f:
    json.dump(chart_data, f, indent=2)