from dataclasses import dataclass, field
from typing import Dict, Optional
import pandas as pd
import requests
import logging
import json
from pathlib import Path
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Config:
    episode_slug: str = field(default="")
    base_url: str = field(default="https://deepcast.fm/api/fm/transcripts/episode/")
    anonymous_id: str = field(default="308b4683-3dc6-4d3d-a34a-65cb1828fa6b")
    
    @property
    def url(self) -> str:
        return f"{self.base_url}{self.episode_slug}"
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "X-Anonymous-ID": self.anonymous_id,
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Alt-Used": "deepcast.fm",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cookie": f"anonymousid={self.anonymous_id}",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Referer": f"https://deepcast.fm/episode/{self.episode_slug}"
        }

class TranscriptProcessor:
    def __init__(self, raw_folder: Path, processed_folder: Path):
        """
        Initialize TranscriptProcessor with specific output folders
        
        Args:
            raw_folder: Path for raw transcript JSON files
            processed_folder: Path for processed transcript files
        """
        self.df = pd.DataFrame()
        self.config = Config()
        self.raw_folder = raw_folder
        self.processed_folder = processed_folder
    
    def get_data(self, episode_slug: str) -> pd.DataFrame:
        """
        Fetch and process transcript data for given episode slug.
        """
        try:
            self.config = Config(episode_slug=episode_slug)
            
            # Save raw response first
            raw_file = self.raw_folder / f"{episode_slug}.json"
            if not raw_file.exists():  # Only fetch if raw file doesn't exist
                response = requests.get(self.config.url, headers=self.config.headers, timeout=10)
                response.raise_for_status()
                
                # Save raw response
                raw_file.write_text(response.text)
                logger.info(f"Saved raw transcript to: {raw_file}")
            else:
                logger.info(f"Using existing raw transcript from: {raw_file}")
            
            # Process transcript from raw file
            data = json.loads(raw_file.read_text())
            rows = []
            for segment in data:
                speaker = segment.get('speaker', '')
                for para in segment.get('paragraphs', []):
                    rows.append({
                        'speaker': speaker,
                        'text': para.get('text', ''),
                        'start': para.get('start', 0),
                        'end': para.get('end', 0),
                        'timestamp': datetime.fromtimestamp(para.get('start', 0) / 1000).strftime('%H:%M:%S')
                    })
            
            self.df = pd.DataFrame(rows).sort_values('start').reset_index(drop=True)
            
            # Save processed files
            self._save_files(episode_slug)
            
            logger.info(f"Successfully processed transcript for episode: {episode_slug}")
            return self.df
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            return pd.DataFrame()
    
    def _save_files(self, episode_slug: str) -> None:
        """Save transcript to parquet and txt files in processed folder."""
        if self.df.empty:
            return
            
        # Use episode slug for filename
        base_name = episode_slug
        
        # Save parquet
        parquet_path = self.processed_folder / f"{base_name}.parquet"
        self.df.to_parquet(parquet_path, compression='snappy')
        
        # Save consolidated text with spacing between speakers
        txt_path = self.processed_folder / f"{base_name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            current_speaker = None
            current_text = []
            
            for _, row in self.df.iterrows():
                if row['speaker'] != current_speaker:
                    if current_speaker and current_text:
                        f.write(f"{current_speaker}: {' '.join(current_text)}\n\n")  # Added extra newline
                    current_speaker = row['speaker']
                    current_text = [row['text']]
                else:
                    current_text.append(row['text'])
            
            # Write the last speaker's text
            if current_speaker and current_text:
                f.write(f"{current_speaker}: {' '.join(current_text)}\n")  # Last line doesn't need extra newline
        
        logger.info(f"Saved processed files:")
        logger.info(f"- Parquet: {parquet_path}")
        logger.info(f"- Text: {txt_path}")