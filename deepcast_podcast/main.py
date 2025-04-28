import os
from pathlib import Path
import logging
from typing import Optional, Dict
import pandas as pd
import argparse
from urllib.parse import urlparse

# Import the custom modules
from jina_processor import get_content_from_jina
from transcript_processor import TranscriptProcessor

class PodcastDataProcessor:
    def __init__(self, base_dir: str = "podcast_data", episode_id: str = None):
        """
        Initialize the podcast processor with a base directory for all outputs.
        
        Args:
            base_dir: Base directory for all podcast data
            episode_id: Episode ID for creating subdirectory
        """
        self.base_dir = Path(base_dir)
        
        # Create episode-specific subdirectory if episode_id is provided
        if episode_id:
            self.episode_dir = self.base_dir / episode_id
        else:
            self.episode_dir = self.base_dir
            
        self.summary_dir = self.episode_dir / "summaries"
        self.transcript_dir = self.episode_dir / "transcripts"
        self.raw_transcript_dir = self.transcript_dir / "raw_transcript"
        self.processed_transcript_dir = self.transcript_dir / "processed_transcript"
        
        # Create all necessary directories
        for directory in [self.summary_dir, self.transcript_dir, 
                         self.raw_transcript_dir, self.processed_transcript_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize transcript processor with correct paths
        self.transcript_processor = TranscriptProcessor(
            raw_folder=self.raw_transcript_dir,
            processed_folder=self.processed_transcript_dir
        )
    
    @staticmethod
    def extract_episode_id(input_str: str) -> str:
        """Extract episode ID from either a full URL or direct episode ID string."""
        parsed = urlparse(input_str)
        if parsed.scheme and parsed.netloc:
            path_parts = parsed.path.split('/')
            episode_id = path_parts[-1] if path_parts[-1] else path_parts[-2]
        else:
            episode_id = input_str
        return episode_id

    def save_summary_data(self, dfs: Dict[str, pd.DataFrame], episode_id: str) -> None:
        """Save summary DataFrames to parquet files."""
        if dfs:
            for name, df in dfs.items():
                if isinstance(df, pd.DataFrame):
                    filename = f"{name}.parquet"  # Simplified filename since we're in episode-specific directory
                    filepath = self.summary_dir / filename
                    df.to_parquet(filepath)
                    self.logger.info(f"Saved {name} data to: {filepath}")

    def process_episode(self, episode_input: str) -> Dict[str, Optional[pd.DataFrame]]:
        """Process a single episode, getting both summary and transcript data."""
        # Extract episode ID
        episode_id = self.extract_episode_id(episode_input)
        self.logger.info(f"Processing episode ID: {episode_id}")
        
        # Construct full URL if needed
        if not episode_input.startswith('http'):
            episode_url = f"https://deepcast.fm/episode/{episode_id}"
        else:
            episode_url = episode_input
        
        results = {
            'summary_dfs': None,
            'transcript_df': None,
            'episode_id': episode_id
        }
        
        try:
            # Get summary data from Jina
            self.logger.info("Fetching summary data from Jina...")
            summary_dfs = get_content_from_jina(episode_url)
            if summary_dfs:
                results['summary_dfs'] = summary_dfs
                self.logger.info("Successfully retrieved summary data")
                # Save summary data
                self.save_summary_data(summary_dfs, episode_id)
            
            # Get transcript data
            self.logger.info("Fetching transcript data...")
            transcript_df = self.transcript_processor.get_data(episode_id)
            if not transcript_df.empty:
                results['transcript_df'] = transcript_df
                self.logger.info("Successfully retrieved transcript data")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing episode: {e}")
            return results

def main():
    parser = argparse.ArgumentParser(description='Process DeepCast podcast episodes')
    parser.add_argument('episode', help='Episode URL or ID to process')
    parser.add_argument('--output-dir', default='podcast_data',
                      help='Base directory for output files (default: podcast_data)')
    args = parser.parse_args()
    
    # Extract episode_id for directory creation
    episode_id = PodcastDataProcessor.extract_episode_id(args.episode)
    
    # Initialize processor with episode-specific directory
    processor = PodcastDataProcessor(base_dir=args.output_dir, episode_id=episode_id)
    
    # Process episode
    results = processor.process_episode(args.episode)
    
    # Print results summary
    print(f"\nProcessing results for episode ID: {results['episode_id']}")
    
    if results['summary_dfs']:
        print("\nSummary Data Statistics:")
        for key, df in results['summary_dfs'].items():
            if isinstance(df, pd.DataFrame):
                print(f"{key}: {len(df)} rows")
    
    if results['transcript_df'] is not None:
        print("\nTranscript Statistics:")
        df = results['transcript_df']
        print(f"Total segments: {len(df)}")
        print(f"Unique speakers: {df['speaker'].unique()}")
        print(f"Time range: {df['timestamp'].iloc[0]} - {df['timestamp'].iloc[-1]}")

if __name__ == "__main__":
    main()