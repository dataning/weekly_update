from dataclasses import dataclass
import polars as pl
import re
from typing import Dict, List
import os
from pathlib import Path

@dataclass
class Form990Processor:
    """Process and manage Form 990 data using Polars DataFrames."""
    
    output_dir: str = "EIN_data"
    
    def __post_init__(self):
        """Initialize the processor by creating output directory."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _clean_field_paths(self, df: pl.DataFrame, col_name: str = 'field_path') -> pl.DataFrame:
        """Clean the field paths in the DataFrame."""
        def clean_path(path: str) -> str | None:
            if not isinstance(path, str):
                return None
            if path.startswith('@'):
                return None
            path = re.sub(r'(\d{4}/)+', r'\1', path)
            path = path.replace('Return/', '').replace('ReturnData/', '')
            path = re.sub(r'^\d{4}/', '', path)
            return path

        cleaned_df = (df
            .with_columns([
                pl.col(col_name)
                .map_elements(clean_path, return_dtype=pl.Utf8)
                .alias(col_name),
                pl.col('group_index')
                .cast(pl.Int64, strict=False)
                .alias('group_index')
            ])
            .filter(pl.col(col_name).is_not_null())
            .filter(~pl.col(col_name).str.starts_with('@'))
            .drop('group_index', 'field_name'))

        cleaned_df = cleaned_df.with_columns(
            pl.col(col_name).str.replace_all('@', '').alias(col_name)
        )

        return cleaned_df.with_columns(
            pl.col(col_name).str.replace_all('/', '_').alias(col_name)
        )

    def _create_form_dataframes(self, df: pl.DataFrame) -> Dict[str, pl.DataFrame]:
        """Split data into separate DataFrames by form type."""
        df = (df
            .with_columns([
                pl.col('field_path').str.split(by='_').list.get(0).alias('form_type'),
                pl.col('field_path').str.split(by='_', inclusive=True).list.slice(1).list.join('_').alias('column_name')
            ])
        )
        
        form_types = df.get_column('form_type').unique().to_list()
        form_dfs = {}
        
        for form_type in form_types:
            form_data = df.filter(pl.col('form_type') == form_type)
            pivoted = (form_data
                .pivot(
                    values='value',
                    index=['EIN', 'year'],
                    on='column_name',
                    aggregate_function='first'
                )
            )
            form_dfs[form_type] = pivoted
            
        return form_dfs

    def _clean_column_names(self, df_dict: Dict[str, pl.DataFrame]) -> Dict[str, pl.DataFrame]:
        """Clean column names in all form DataFrames."""
        pattern_counts = {}
        
        for df in df_dict.values():
            for col in df.columns:
                if '[' in col and ']' in col:
                    base = col[:col.find('[')] + col[col.find(']')+1:]
                    if base not in pattern_counts:
                        pattern_counts[base] = set()
                    idx = col[col.find('[')+1:col.find(']')]
                    if idx.isdigit():
                        pattern_counts[base].add(int(idx))
        
        cleaned_dfs = {}
        for form_type, df in df_dict.items():
            new_names = {}
            
            for col in df.columns:
                new_name = col
                
                if '[' in col and ']' in col:
                    base = col[:col.find('[')] + col[col.find(']')+1:]
                    idx = col[col.find('[')+1:col.find(']')]
                    
                    if idx.isdigit():
                        if base in pattern_counts and len(pattern_counts[base]) == 1 and int(idx) == 1:
                            new_name = base
                
                new_name = new_name.replace('__', '_').rstrip('_')
                new_names[col] = new_name
            
            cleaned_dfs[form_type] = df.rename(new_names)
            
        return cleaned_dfs

    def run(self, ein: str) -> Dict[str, pl.DataFrame]:
        """Run the complete processing pipeline for a given EIN."""
        input_file = f"search_data/{ein}_long.parquet"
        
        # Load and process data
        raw_data = pl.read_parquet(input_file)
        cleaned_data = self._clean_field_paths(raw_data)
        form_dfs = self._create_form_dataframes(cleaned_data)
        final_dfs = self._clean_column_names(form_dfs)
        
        return final_dfs

    def save(self, ein: str, dataframes: Dict[str, pl.DataFrame]) -> None:
        """Save DataFrames to parquet files in EIN-specific subdirectory."""
        # Create EIN-specific subdirectory
        ein_dir = os.path.join(self.output_dir, f"{ein}_irs990")
        Path(ein_dir).mkdir(parents=True, exist_ok=True)
        
        for form_type, df in dataframes.items():
            # Convert form type to lowercase for filename
            form_lower = form_type.lower()
            
            # Special handling for core form
            if form_lower == 'irs990':
                form_lower += 'core'
            
            # Create filename
            filename = f"{ein}_{form_lower}.parquet"
            filepath = os.path.join(ein_dir, filename)
            
            # Save DataFrame
            df.write_parquet(filepath)
            print(f"Saved {form_type} to {filepath}")

    def find_columns(self, dataframes: Dict[str, pl.DataFrame], patterns: List[str]) -> pl.DataFrame:
        """Find which forms contain specific column patterns."""
        columns = []
        schedules = []
        full_column_names = []

        for pattern in patterns:
            matching_columns = {}
            for schedule, df in dataframes.items():
                matches = [col for col in df.columns if pattern in col]
                if matches:
                    for match in matches:
                        if match not in matching_columns:
                            matching_columns[match] = []
                        matching_columns[match].append(schedule)
            
            if matching_columns:
                for col, scheds in matching_columns.items():
                    columns.append(pattern)
                    full_column_names.append(col)
                    schedules.append(", ".join(scheds))
            else:
                columns.append(pattern)
                full_column_names.append("Not Found")
                schedules.append("Not Found")
                print(f"Warning: Pattern '{pattern}' not found in any schedule.")

        return pl.DataFrame({
            "Search Pattern": columns,
            "Matching Column": full_column_names,
            "Schedules": schedules
        })

# Example usage:
# if __name__ == "__main__":
    # Initialize processor
    # processor = Form990Processor()
    
    # Process an EIN
    # ein = "362722198"
    # dict_df = processor.run(ein)
    # dict_df
    # Save results
    # processor.save(ein, dict_df)
    
    # # Example of finding columns
    # columns_to_find = ["EIN", "year", "CYTotalRevenueAmt", "CYContributionsGrantsAmt", "CYInvestmentIncomeAmt",]
    # result = processor.find_columns(dict_df, columns_to_find)
    # print("\nColumn search results:")
    # print(result)

