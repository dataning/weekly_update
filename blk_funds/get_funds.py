from blk_multi_region import read_portfolio_ids, main, parse_excel_to_dataframe, save_to_parquet

# Dictionary mapping regions to portfolio ID files
portfolio_files = {
    # "uk": "portfolio_ids/uk.txt",
    # "americas": "portfolio_ids/americas.txt",
    "au": "portfolio_ids/au.txt"

}

# Process each region
for region, file_path in portfolio_files.items():
    print(f"\nProcessing {region} region with portfolio IDs from {file_path}")
    
    dfs, files = main(
        region=region,
        portfolio_ids_file=file_path,
        output_dir=f"extracted_fund_data"
    )
    
    if dfs is not None:
        print(f"Successfully processed {region} data")
        print(f"Saved files: {files}")
    else:
        print(f"Failed to process {region} data")

# Path to your already downloaded file
file_path = "xls_data/BlackRock-Australia.xls"
file_path = "xls_data/BlackRock-UnitedKingdom.xls"
# Parse the file
au_dfs = parse_excel_to_dataframe(file_path)
uk_dfs = parse_excel_to_dataframe(file_path)


import importlib
import blk_multi_region_extractor  # First import the module
importlib.reload(blk_multi_region_extractor)  # Then reload the module
# Now re-import the functions from the freshly reloaded module
from blk_multi_region_extractor import extract_all_regions, add_custom_region

# Extract data from all predefined regions
extract_all_regions("blackrock_data")

import polars as pl
df = pl.read_parquet("blackrock_data/blackrock_all_regions_20250309.parquet"); df
