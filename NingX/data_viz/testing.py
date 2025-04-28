
import polars as pl

def process_data(df):

    # Convert date strings to timestamps
    # Note: Polars handles dates natively and more efficiently
    df = df.with_columns(
        pl.col('Date').str.strptime(pl.Date, format='%Y-%m').alias('date')
    ).with_columns(
        (pl.col('date').cast(pl.Int64) * 1_000).alias('timestamp')
    )
    
    # Create separate dataframes for each type and convert to lists
    def get_type_data(type_name):
        return (df
                .filter(pl.col('Type') == type_name)
                .select(['timestamp', 'Value'])
                .rows())
    
    chart_data = {
        'approve': sorted(get_type_data('approve')),
        'disapprove': sorted(get_type_data('disapprove')),
        'approveVariance': sorted(get_type_data('approve_var')),
        'disapproveVariance': sorted(get_type_data('disapprove_var'))
    }
    
    return chart_data

# Read the CSV file
df = pl.read_csv('data_viz/approval_data.csv')
df = df.with_columns(
    pl.col('Date').str.strptime(pl.Date, format='%Y-%m').alias('date')
).with_columns(
    (pl.col('date').cast(pl.Int64) * 1_000).alias('timestamp')
)
df

# Process and convert to JSON
chart_data = process_data(df)

chart_data
df_single = pl.read_csv('data_viz/approval_data.csv'); df_single
df_multi = pl.read_csv('data_viz/presidential_approval.csv'); df_multi

# Create a new column showing the difference between approval and disapproval with percentage signs
df_with_diff = df_multi.with_columns([
    pl.struct(['approval', 'disapproval'])
    .map_elements(lambda x: 
        f"Approval +{x['approval'] - x['disapproval']}%" 
        if x['approval'] > x['disapproval']
        else f"Disapproval +{x['disapproval'] - x['approval']}%"
    ).alias('change_status')
])

# Sort by year to maintain chronological order
df_with_diff = df_with_diff.sort(['president', 'year_in_term'])

df_with_diff

def process_presidential_data(df):
    # Get unique presidents
    unique_presidents = df.select('president').unique().to_series().to_list()
    
    presidents_data = []
    for president in unique_presidents:
        # Filter data for current president
        president_df = df.filter(pl.col('president') == president)
        
        # Get the first row's years value for this president
        years = president_df.select('years').row(0)[0]
        
        # Get approval and disapproval values in order of year_in_term
        approval_values = president_df.sort('year_in_term').select('approval').to_series().to_list()
        disapproval_values = president_df.sort('year_in_term').select('disapproval').to_series().to_list()
        
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
            'range': range_data
        }
        
        presidents_data.append(president_data)
    
    return presidents_data

# Read and process the data
multi_chart_data = process_presidential_data(df)
multi_chart_data
