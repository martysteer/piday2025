#!/usr/bin/env python3
"""
PiDay2025 Atlas Uploader

This script monitors the embeddings directory for new JSONL files and uploads them
to Nomic Atlas. It's designed to run continuously during the exhibition,
incrementally updating the Atlas map as new embeddings are generated.

Usage:
    python atlas_uploader.py --embeddings-dir data/embeddings
"""

import os
import time
import json
from pathlib import Path
import typer
from typing import Optional, List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from nomic import atlas

app = typer.Typer(help="Upload embeddings to Nomic Atlas.")

class AtlasUploader(FileSystemEventHandler):
    def __init__(
        self, 
        embeddings_dir: str, 
        map_id: Optional[str] = None, 
        map_name: str = "PiDay2025",
        map_description: str = "PiDay2025 Exhibition Images",
        watch_interval: int = 60
    ):
        self.embeddings_dir = Path(embeddings_dir)
        self.map_id = map_id
        self.map_name = map_name
        self.map_description = map_description
        self.watch_interval = watch_interval
        
        self.processed_files = set()
        self.pending_files = []
        self.last_scan_time = 0
        
        # Create info file to store map ID
        self.info_file = self.embeddings_dir / "atlas_info.json"
        self._load_map_info()
        
        # Initial scan for existing embeddings
        self._scan_for_new_files()
    
    def _load_map_info(self):
        """Load Atlas map information if it exists."""
        if self.info_file.exists():
            try:
                with open(self.info_file, 'r') as f:
                    info = json.load(f)
                    if self.map_id is None:  # Don't override if specified in constructor
                        self.map_id = info.get('map_id')
                    print(f"Loaded existing Atlas map ID: {self.map_id}")
            except Exception as e:
                print(f"Error loading Atlas info file: {str(e)}")
    
    def _save_map_info(self):
        """Save Atlas map information for resuming later."""
        if self.map_id:
            try:
                with open(self.info_file, 'w') as f:
                    json.dump({
                        'map_id': self.map_id,
                        'map_name': self.map_name,
                        'last_update': time.time()
                    }, f)
            except Exception as e:
                print(f"Error saving Atlas info file: {str(e)}")
    
    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith('.jsonl') and Path(file_path).name != "atlas_info.json":
            print(f"New embeddings file detected: {file_path}")
            self.pending_files.append(file_path)
            self.process_pending()
    
    def _scan_for_new_files(self):
        """Scan the embeddings directory for any new JSONL files."""
        current_time = time.time()
        if current_time - self.last_scan_time < self.watch_interval:
            return
            
        self.last_scan_time = current_time
        
        # Find all JSONL files
        all_files = list(self.embeddings_dir.glob("**/*.jsonl"))
        all_files = [str(f) for f in all_files]
        
        # Add new files to pending list
        new_files = [f for f in all_files if f not in self.processed_files and f not in self.pending_files]
        if new_files:
            print(f"Found {len(new_files)} new embedding files during directory scan")
            self.pending_files.extend(new_files)
            self.process_pending()
    
    def process_pending(self):
        """Process any pending embedding files."""
        if not self.pending_files:
            return
            
        # Process one file at a time to avoid rate limiting
        file_path = self.pending_files.pop(0)
        self.upload_file(file_path)
    
    def upload_file(self, filepath: str):
        """Upload a JSONL file to Nomic Atlas."""
        if filepath in self.processed_files:
            return
            
        print(f"Uploading {filepath} to Atlas...")
        
        try:
            # Load embeddings from JSONL
            embeddings = []
            data = []
            
            with open(filepath, 'r') as f:
                for line in f:
                    record = json.loads(line)
                    embeddings.append(record['embedding'])
                    
                    # Extract metadata for data field
                    metadata = record.get('metadata', {})
                    item_data = {
                        'id': record['id'],
                    }
                    
                    # Add metadata if available
                    if metadata:
                        item_data.update({
                            'filename': metadata.get('filename', ''),
                            'filepath': metadata.get('filepath', ''),
                            'created': metadata.get('created', ''),
                            'size_bytes': metadata.get('size_bytes', 0),
                            'extension': metadata.get('extension', ''),
                        })
                    
                    data.append(item_data)
            
            # Check if we have data to upload
            if not embeddings or not data:
                print(f"No valid embeddings found in {filepath}, skipping")
                self.processed_files.add(filepath)
                return
                
            print(f"Uploading {len(embeddings)} embeddings to Atlas...")
            
            # Create or update Atlas map
            if self.map_id is None:
                # First upload - create new map
                result = atlas.map_data(
                    embeddings=embeddings,
                    data=data,
                    name=self.map_name,
                    description=self.map_description
                )
                self.map_id = result.id
                print(f"Created new Atlas map with ID: {self.map_id}")
                self._save_map_info()
            else:
                # Subsequent uploads - update existing map
                result = atlas.map_data(
                    embeddings=embeddings,
                    data=data,
                    id=self.map_id,
                    rebuild=False  # Don't rebuild the entire map
                )
                print(f"Updated Atlas map {self.map_id} with {len(embeddings)} new embeddings")
            
            # Mark as processed
            self.processed_files.add(filepath)
            
        except Exception as e:
            print(f"Error uploading {filepath} to Atlas: {str(e)}")
            # Put back in pending queue for retry
            self.pending_files.append(filepath)
    
    def run_periodic_tasks(self):
        """Run periodic tasks like scanning for new files."""
        # Scan for new files
        self._scan_for_new_files()
        
        # Save map info occasionally
        if self.map_id and (time.time() % 300) < 10:  # Every ~5 minutes
            self._save_map_info()


@app.command()
def main(
    embeddings_dir: str = typer.Option("data/embeddings", "--embeddings-dir", "-e", help="Directory containing embedding JSONL files"),
    map_id: Optional[str] = typer.Option(None, "--map-id", "-m", help="Existing Atlas map ID (will create new if not provided)"),
    map_name: str = typer.Option("PiDay2025", "--map-name", "-n", help="Name for the Atlas map"),
    map_description: str = typer.Option("PiDay2025 Exhibition Images", "--map-description", "-d", help="Description for the Atlas map"),
    watch_interval: int = typer.Option(60, "--interval", "-i", help="Interval in seconds for directory scans")
):
    """
    Upload embeddings to Nomic Atlas for the PiDay2025 exhibition.
    
    This script monitors a directory for new embedding files and uploads them
    to Nomic Atlas, building an incremental map of exhibition images.
    """
    print(f"Starting Atlas uploader with:")
    print(f"  Embeddings directory: {embeddings_dir}")
    print(f"  Map ID: {map_id or 'New map will be created'}")
    print(f"  Map name: {map_name}")
    
    # Create uploader
    uploader = AtlasUploader(
        embeddings_dir=embeddings_dir,
        map_id=map_id,
        map_name=map_name,
        map_description=map_description,
        watch_interval=watch_interval
    )
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(uploader, embeddings_dir, recursive=True)
    observer.start()
    
    try:
        print(f"Watching for embedding files in {embeddings_dir}")
        while True:
            time.sleep(1)
            uploader.run_periodic_tasks()
    except KeyboardInterrupt:
        print("Stopping Atlas uploader...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    app()