import pandas as pd
import numpy as np
from markitdown import MarkItDown
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
import json
import re
import time
import random
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from enum import Enum

class ProcessingStatus(Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    FAILED = "failed"
    INVALID_DATA = "invalid_data"

@dataclass
class ProcessingResult:
    """Stores the result of processing a single EIN"""
    ein: str
    status: ProcessingStatus
    error_message: Optional[str] = None
    data: Optional[Dict] = None
    timestamp: str = datetime.now().isoformat()

class ProcessingMetrics:
    """Tracks processing metrics and statistics"""
    def __init__(self):
        self.total_processed: int = 0
        self.successful: Set[str] = set()
        self.empty_responses: Set[str] = set()
        self.failed: Dict[str, str] = {}  # EIN -> error message
        self.invalid_data: Set[str] = set()
        
    def add_result(self, result: ProcessingResult):
        """Update metrics based on processing result"""
        self.total_processed += 1
        
        if result.status == ProcessingStatus.SUCCESS:
            self.successful.add(result.ein)
        elif result.status == ProcessingStatus.EMPTY:
            self.empty_responses.add(result.ein)
        elif result.status == ProcessingStatus.FAILED:
            self.failed[result.ein] = result.error_message
        elif result.status == ProcessingStatus.INVALID_DATA:
            self.invalid_data.add(result.ein)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for serialization"""
        return {
            'total_processed': self.total_processed,
            'successful_count': len(self.successful),
            'empty_count': len(self.empty_responses),
            'failed_count': len(self.failed),
            'invalid_count': len(self.invalid_data),
            'successful_eins': sorted(list(self.successful)),
            'empty_eins': sorted(list(self.empty_responses)),
            'failed_eins': {ein: msg for ein, msg in sorted(self.failed.items())},
            'invalid_eins': sorted(list(self.invalid_data))
        }

    def from_dict(self, data: Dict):
        """Load metrics from dictionary"""
        self.total_processed = data['total_processed']
        self.successful = set(data['successful_eins'])
        self.empty_responses = set(data['empty_eins'])
        self.failed = data['failed_eins']
        self.invalid_data = set(data['invalid_eins'])

class RateLimiter:
    """Rate limiter to control request frequency"""
    def __init__(self, min_delay=1, max_delay=2):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()

@retry(stop=stop_after_attempt(3), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_nonprofit_with_retry(ein: str, rate_limiter) -> ProcessingResult:
    """Analyze a single nonprofit with improved error handling and status tracking"""
    try:
        rate_limiter.wait()
        
        md = MarkItDown()
        url = f"https://givefreely.com/charity-directory/nonprofit/ein-{ein}/"
        result = md.convert(url)
        markdown_text = result.text_content
        
        # Check for empty or invalid response
        if not markdown_text or markdown_text.isspace():
            return ProcessingResult(ein=ein, status=ProcessingStatus.EMPTY)
        
        parsed_data = {}
        
        # Parse Organization Info
        org_info = {
            'ein': ein,
            'name': re.search(r'# (.+?)\n', markdown_text).group(1) if re.search(r'# (.+?)\n', markdown_text) else None
        }
        
        # If we couldn't parse basic org info, consider it invalid
        if not org_info['name']:
            return ProcessingResult(
                ein=ein,
                status=ProcessingStatus.INVALID_DATA,
                error_message="Could not parse organization name"
            )
        
        # Extract location and 501(c)(3) status
        header_info = re.search(r'EIN: \d+ ✦ ([^✦]+) ✦ (Designated as a 501\(c\)\(3\))', markdown_text)
        if header_info:
            org_info['location'] = header_info.group(1).strip()
            org_info['tax_status'] = header_info.group(2).strip()
        
        # Extract organizational details
        org_fields = {
            'principal_officer': r'Principal Officer\n\n(.*?)\n',
            'address': r'Main Address\n\n(.*?)\n',
            'ntee_code': r'Code:(.*?)(?=\n|\r|$)',
            'founding_year': r'Founding Year\n\n(\d+)',
            'website': r'Website\n\n\[(.*?)\]',
            'phone': r'Phone\n\n(\(\d+\)\s*\d+[-\d]*)'
        }
        
        for field, pattern in org_fields.items():
            match = re.search(pattern, markdown_text, re.DOTALL)
            if match:
                org_info[field] = match.group(1).strip()
        
        parsed_data['organization_info'] = pd.DataFrame([org_info])
        
        # Parse Financial Info
        financial_info = {}
        
        # Extract revenue and metrics
        financial_metrics = {
            'executive_compensation': r'Executive Compensation:\s*\$?([\d,]+)',
            'professional_fundraising_fees': r'Professional Fundraising Fees:\s*\$?([\d,]+)',
            'other_salaries_wages': r'Other Salaries and Wages:\s*\$?([\d,]+)',
            'investment_income': r'Investment Income:\s*\*\*\$?([\d,]+)\*\*',
            'program_service_revenue': r'Program Service Revenue:\s*\*\*\$?([\d,]+)\*\*',
            'gross_receipts': r'Gross Receipts:\s*\*\*\$?([\d,]+)\*\*',
            'total_assets': r'Total Assets:\s*\*\*\$?([\d,]+)\*\*',
            'total_liabilities': r'Total Liabilities:\s*\*\*\$?([\d,]+)\*\*',
            'net_assets': r'Net Assets:\s*\*\*\$?([\d,]+)\*\*'
        }
        
        revenue_match = re.search(r'revenue in (\d{4}) was \$?([\d,]+)', markdown_text)
        if revenue_match:
            financial_info['fiscal_year'] = int(revenue_match.group(1))
            financial_info['total_revenue'] = int(revenue_match.group(2).replace(',', ''))
        
        for metric, pattern in financial_metrics.items():
            match = re.search(pattern, markdown_text)
            if match:
                financial_info[metric] = int(match.group(1).replace(',', ''))
        
        parsed_data['financials'] = pd.DataFrame([financial_info])
        
        # Parse Compensations
        compensation_pattern = r'([A-Za-z\s\.]+?)\s*\(([^)]+)\)\n\n\*\s*Compensation:\s*\$?([\d,]+)\n\*\s*Related:\s*\$?([\d,]+)\n\*\s*Other:\s*\$?([\d,]+)'
        
        compensations = []
        for match in re.finditer(compensation_pattern, markdown_text):
            name, title, comp, related, other = match.groups()
            
            name = re.sub(r'\d+', '', name).strip()
            
            comp = int(comp.replace(',', '')) if comp else 0
            related = int(related.replace(',', '')) if related else 0
            other = int(other.replace(',', '')) if other else 0
            
            is_trustee = any(word.lower() in title.lower() 
                           for word in ['director', 'trustee', 'board', 'chair'])
            
            compensations.append({
                'name': name,
                'title': title.strip(),
                'is_trustee': is_trustee,
                'compensation': comp,
                'related_compensation': related,
                'other_compensation': other,
                'total_compensation': comp + related + other
            })
        
        if compensations:
            parsed_data['compensations'] = pd.DataFrame(compensations)
        
        # Validate parsed data
        if not parsed_data or all(df.empty for df in parsed_data.values() if isinstance(df, pd.DataFrame)):
            return ProcessingResult(
                ein=ein,
                status=ProcessingStatus.EMPTY,
                error_message="No data found in parsed response"
            )
        
        return ProcessingResult(
            ein=ein,
            status=ProcessingStatus.SUCCESS,
            data=parsed_data
        )
    
    except Exception as e:
        return ProcessingResult(
            ein=ein,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )

class NonprofitBatchProcessor:
    """Enhanced batch processor with better tracking and reporting"""
    def __init__(self, output_dir='nonprofit_data', min_delay=1, max_delay=2):
        self.output_dir = Path(output_dir)
        self.batch_dir = self.output_dir / 'batches'
        self.final_dir = self.output_dir / 'final'
        self.metrics_dir = self.output_dir / 'metrics'
        self.state_file = self.output_dir / 'processing_state.json'
        
        # Create directories
        for directory in [self.output_dir, self.batch_dir, 
                         self.final_dir, self.metrics_dir]:
            directory.mkdir(exist_ok=True)
        
        self.combined_data = {}
        self.rate_limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay)
        self.metrics = ProcessingMetrics()
    
    def process_in_batches(self, ein_list: List[str], batch_size=20, resume=True):
        """Process EINs in batches with enhanced tracking"""
        state = self._load_state() if resume else None
        
        if state and resume:
            print(f"Resuming from previous state. Last processed: {state['timestamp']}")
            completed_batches = state['completed_batches']
            self.metrics = self._load_metrics()
        else:
            completed_batches = []
            self.metrics = ProcessingMetrics()
        
        total_batches = len(ein_list) // batch_size + (1 if len(ein_list) % batch_size else 0)
        
        for i in range(0, len(ein_list), batch_size):
            batch_num = i // batch_size
            
            if batch_num in completed_batches:
                print(f"Batch {batch_num}/{total_batches} already processed, skipping...")
                continue
            
            print(f"\nProcessing batch {batch_num}/{total_batches}...")
            batch_eins = ein_list[i:i + batch_size]
            
            batch_data, batch_metrics = self._process_batch(batch_eins)
            
            # Update metrics
            for result in batch_metrics:
                self.metrics.add_result(result)
            
            # Save batch data and update state
            self._save_batch(batch_data, batch_num)
            self._save_metrics(batch_num)
            completed_batches.append(batch_num)
            self._save_state(ein_list, batch_size, completed_batches)
            
            # Print batch summary
            self._print_batch_summary(batch_num, batch_metrics)
            
            delay = random.uniform(3, 5)
            print(f"Waiting {delay:.2f} seconds before next batch...")
            time.sleep(delay)
        
        print("\nProcessing complete. Combining all batches...")
        self._combine_all_batches()
        self._save_final_report()
        return self.combined_data, self.metrics
    
    def _process_batch(self, batch_eins):
        """Process a batch of EINs with detailed result tracking"""
        batch_data = {
            'organization_info': [],
            'financials': [],
            'compensations': []
        }
        batch_metrics = []
        
        for ein in tqdm(batch_eins):
            result = analyze_nonprofit_with_retry(ein, self.rate_limiter)
            batch_metrics.append(result)
            
            if result.status == ProcessingStatus.SUCCESS and result.data:
                for key in batch_data.keys():
                    if key in result.data:
                        if isinstance(result.data[key], pd.DataFrame):
                            result.data[key]['ein'] = ein
                            batch_data[key].append(result.data[key])
            
            time.sleep(random.uniform(0.2, 0.5))
        
        # Combine batch data
        for key in batch_data.keys():
            if batch_data[key]:
                batch_data[key] = pd.concat(batch_data[key], ignore_index=True)
        
        return batch_data, batch_metrics
    
    def _save_batch(self, batch_data, batch_num):
        """Save batch data to parquet files"""
        batch_path = self.batch_dir / f'batch_{batch_num}'
        batch_path.mkdir(exist_ok=True)
        
        for key, df in batch_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_parquet(batch_path / f'{key}.parquet')
    
    def _load_metrics(self):
        """Load metrics from the most recent batch"""
        metrics = ProcessingMetrics()
        metrics_files = sorted(self.metrics_dir.glob('metrics_batch_*.json'))
        if metrics_files:
            latest_metrics = metrics_files[-1]
            with open(latest_metrics, 'r') as f:
                metrics_data = json.load(f)
                metrics.from_dict(metrics_data)
        return metrics
    
    def _save_metrics(self, batch_num):
        """Save current metrics to file"""
        metrics_file = self.metrics_dir / f'metrics_batch_{batch_num}.json'
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics.to_dict(), f, indent=2)
    
    def _save_state(self, ein_list: List[str], batch_size: int, completed_batches: List[int]):
        """Save processing state"""
        state = {
            'ein_list': ein_list,
            'batch_size': batch_size,
            'completed_batches': completed_batches,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load processing state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return None
    
    def _combine_all_batches(self):
        """Combine all batches into final datasets"""
        all_data = {
            'organization_info': [],
            'financials': [],
            'compensations': []
        }
        
        for batch_dir in sorted(self.batch_dir.glob('batch_*')):
            for file_path in batch_dir.glob('*.parquet'):
                key = file_path.stem
                df = pd.read_parquet(file_path)
                all_data[key].append(df)
        
        for key in all_data.keys():
            if all_data[key]:
                combined_df = pd.concat(all_data[key], ignore_index=True)
                combined_df.to_parquet(self.final_dir / f'{key}_combined.parquet')
                self.combined_data[key] = combined_df
    
    def _save_final_report(self):
        """Generate and save final processing report"""
        report = {
            'processing_summary': self.metrics.to_dict(),
            'timestamp': datetime.now().isoformat(),
            'final_dataset_stats': {
                key: {
                    'rows': len(df),
                    'columns': list(df.columns)
                } for key, df in self.combined_data.items()
            }
        }
        
        report_file = self.final_dir / 'processing_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nFinal report saved to {report_file}")
    
    def _print_batch_summary(self, batch_num, batch_metrics):
        """Print summary of batch processing results"""
        status_counts = {status: 0 for status in ProcessingStatus}
        for result in batch_metrics:
            status_counts[result.status] += 1
        
        print(f"\nBatch {batch_num} Summary:")
        for status, count in status_counts.items():
            if count > 0:
                print(f"- {status.value}: {count}")
    
    def load_combined_data(self):
        """Load final combined datasets"""
        for file_path in self.final_dir.glob('*_combined.parquet'):
            key = file_path.stem.replace('_combined', '')
            self.combined_data[key] = pd.read_parquet(file_path)
        return self.combined_data
    
    def get_processing_summary(self):
        """Get a detailed summary of the processing results"""
        summary = self.metrics.to_dict()
        summary['data_stats'] = {
            key: {
                'rows': len(df),
                'columns': list(df.columns)
            } for key, df in self.combined_data.items()
        }
        return summary

# Load the EIN list
ein_list = pd.read_parquet('global_data/nonprofit_wide_20250102.parquet')['ein'].unique().tolist()
print(f"Total EINs to process: {len(ein_list)}")

# Initialize the processor
processor = NonprofitBatchProcessor(
    output_dir='nonprofit_data',
    min_delay=1,
    max_delay=2
)

# Process the EINs
data, metrics = processor.process_in_batches(
    ein_list,
    batch_size=50,
    resume=True  # Will resume from last checkpoint if available
)

# Combine with existing data
df = processor.load_combined_data()
df['organization_info']

# Save updated combined files
for key in data:
    if isinstance(data[key], pd.DataFrame) and not data[key].empty:
        output_path = f'givefreely_{key}.parquet'
        data[key].to_parquet(output_path)
        print(f"Saved {output_path}")


# Get processing summary
summary = processor.get_processing_summary()

# Print final statistics
print("\nProcessing Complete!")
print(f"Total processed: {summary['total_processed']}")
print(f"Successful: {summary['successful_count']}")
print(f"Empty responses: {summary['empty_count']}")
print(f"Failed requests: {summary['failed_count']}")
print(f"Invalid data: {summary['invalid_count']}")

# Example: Analyze failed requests
if summary['failed_count'] > 0:
    print("\nFailed EINs and their errors:")
    for ein, error in summary['failed_eins'].items():
        print(f"EIN {ein}: {error}")

# Example: Get success rate
success_rate = (summary['successful_count'] / summary['total_processed']) * 100
print(f"\nSuccess rate: {success_rate:.2f}%")

# Example: Look at the data we collected
for key, stats in summary['data_stats'].items():
    print(f"\n{key} dataset:")
    print(f"- Rows: {stats['rows']}")
    print(f"- Columns: {stats['columns']}")


# ---------------------------------------------------------------------------- #
#                                   Refilling                                  #
# ---------------------------------------------------------------------------- #

def process_nonprofit_data_complete(
    main_parquet_path: str,
    new_parquet_path: str,
    ntee_dict_path: str,
    output_path: Optional[str] = None
) -> pl.DataFrame:
    """
    Process nonprofit data by combining parquet files and standardizing NTEE codes.
    
    Args:
        main_parquet_path (str): Path to the main nonprofit data parquet file
        new_parquet_path (str): Path to the new organization info parquet file
        ntee_dict_path (str): Path to NTEE dictionary parquet file
        output_path (str, optional): Path to save the processed DataFrame. If None, won't save.
    
    Returns:
        pl.DataFrame: Processed DataFrame with joined data and standardized NTEE codes
    """
    def standardize_ntee_code(code: str) -> str:
        """Standardizes NTEE codes by removing trailing zero if applicable"""
        return (code[:-1] if isinstance(code, str) and 
                len(code) > 3 and code[-1] == '0' else code)
    
    # Step 1: Initial data loading and joining
    print("\nPhase 1: Initial Data Processing")
    print("--------------------------------")
    print("Loading data...")
    main_df = pl.read_parquet(main_parquet_path)
    new_df = pl.read_parquet(new_parquet_path)
    
    print("Joining dataframes...")
    df_joined = main_df.join(
        new_df,
        left_on="ein",
        right_on="ein",
        how="left"
    )
    
    # Split NTEE code into code and description
    print("Processing NTEE codes...")
    df_joined = df_joined.with_columns([
        pl.col('ntee_code_right')
        .str.split_exact(' - ', 1)
        .struct.rename_fields(['ntee_code_short', 'ntee_word'])
    ]).unnest('ntee_code_right')
    
    # Count nulls before filling
    nulls_before = df_joined.filter(pl.col('ntee_code').is_null()).height
    
    # Fill null NTEE codes
    df_joined = df_joined.with_columns([
        pl.col('ntee_code').fill_null(pl.col('ntee_code_short'))
    ])
    
    # Count nulls after filling
    nulls_after = df_joined.filter(pl.col('ntee_code').is_null()).height
    
    print(f"\nInitial Processing Summary:")
    print(f"Total rows: {df_joined.height}")
    print(f"NTEE codes filled: {nulls_before - nulls_after}")
    print(f"Remaining null NTEE codes: {nulls_after}")
    
    # Step 2: NTEE code standardization and dictionary joining
    print("\nPhase 2: NTEE Code Standardization")
    print("----------------------------------")
    print("Loading NTEE dictionary...")
    ntee_dict_df = pl.read_parquet(ntee_dict_path)
    
    # Standardize NTEE codes in both dataframes
    print("Standardizing NTEE codes...")
    df_joined_std = df_joined.with_columns(
        pl.col('ntee_code')
        .map_elements(standardize_ntee_code, return_dtype=pl.Utf8)
        .alias('ntee_code_std')
    )
    
    ntee_dict_with_std = ntee_dict_df.with_columns(
        pl.col('NTEE Code')
        .map_elements(standardize_ntee_code, return_dtype=pl.Utf8)
        .alias('ntee_code_std')
    )
    
    # Join with NTEE dictionary
    print("Joining with NTEE dictionary...")
    result = (df_joined_std
        .join(
            ntee_dict_with_std.select(['ntee_code_std', 'Description', 'Definition']),
            on='ntee_code_std',
            how='left'
        )
        .drop('ntee_code_std')
    )
    
    # Fill missing descriptions with ntee_word
    result = result.with_columns([
        pl.col('Description').fill_null(pl.col('ntee_word'))
    ])
    
    print(f"\nFinal Processing Summary:")
    print(f"Total organizations: {result.height}")
    print(f"Organizations with NTEE descriptions: {result.filter(pl.col('Description').is_not_null()).height}")
    print(f"Missing NTEE descriptions: {result.filter(pl.col('Description').is_null()).height}")
    
    # Save if output path provided
    if output_path:
        print(f"\nSaving processed data to {output_path}")
        result.write_parquet(output_path)
    
    return result

# Example usage:
if __name__ == "__main__":
    final_df = process_nonprofit_data_complete(
        main_parquet_path='global_data/nonprofit_wide_20250102.parquet',
        new_parquet_path='givefreely_organization_info.parquet',
        ntee_dict_path='app_data/ntee_dictionary.parquet',
        output_path='app_data/nonprofit_wide_20250107.parquet'
    )

    