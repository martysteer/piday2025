#!/usr/bin/env python3
"""
PiDay2025 Atlas Uploader

This script uploads embedding JSONL files to Nomic Atlas.

Usage:
    python upload_to_atlas.py --embeddings-dir data/embeddings

Requirements:
    pip install nomic typer
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import typer
import numpy as np
from nomic import atlas

# Define the app
app = typer.Typer(help="Upload embeddings to Nomic Atlas.")

def find_jsonl_files(embeddings_dir: str) -> List[str]:
    """Find all JSONL files in the embeddings directory."""
    embeddings_path = Path(embeddings_dir)
    jsonl_files = [str(f) for f in embeddings_path.glob("**/*.jsonl")]
    jsonl_files.sort()  # Sort for consistent ordering
    return jsonl_files

def load_atlas_info(embeddings_dir: str) -> Dict[str, Any]:
    """Load Atlas map information if it exists."""
    info_file = Path(embeddings_dir) / "atlas_info.json"
    info = {}
    
    if info_file.exists():
        try:
            with open(info_file, 'r') as f:
                info = json.load(f)
                print(f"Loaded existing Atlas map ID: {info.get('map_id')}")
        except Exception as e:
            print(f"Error loading Atlas info file: {str(e)}")
    
    return info

def save_atlas_info(embeddings_dir: str, map_id: str, map_name: str) -> None:
    """Save Atlas map information for future reference."""
    info_file = Path(embeddings_dir) / "atlas_info.json"
    
    try:
        with open(info_file, 'w') as f:
            json.dump({
                'map_id': map_id,
                'map_name': map_name,
                'last_update': time.time()
            }, f, indent=2)
        print(f"Saved Atlas map info to {info_file}")
    except Exception as e:
        print(f"Error saving Atlas info file: {str(e)}")

def load_embeddings_from_file(filepath: str) -> tuple:
    """Load embeddings and data from a JSONL file with flat structure."""
    embeddings = []
    data = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                record = json.loads(line)
                
                # Extract the embedding
                if 'embedding' in record:
                    embeddings.append(record['embedding'])
                    
                    # Create a data record with all fields except the embedding
                    item_data = {k: v for k, v in record.items() if k != 'embedding'}
                    data.append(item_data)
                else:
                    print(f"Warning: Record missing embedding field in {filepath}")
        
        return embeddings, data
    
    except Exception as e:
        print(f"Error loading embeddings from {filepath}: {str(e)}")
        return [], []

@app.command()
def main(
    embeddings_dir: str = typer.Option("data/embeddings", "--embeddings-dir", "-e", help="Directory containing embedding JSONL files"),
    map_id: Optional[str] = typer.Option(None, "--map-id", "-m", help="Existing Atlas map ID (will create new if not provided)"),
    map_name: str = typer.Option("PiDay2025", "--map-name", "-n", help="Name for the Atlas map"),
    map_description: str = typer.Option("PiDay2025 Exhibition Images", "--map-description", "-d", help="Description for the Atlas map"),
    new_map: bool = typer.Option(False, "--new-map", help="Force creation of a new map, even if map ID exists"),
):
    """
    Upload embeddings to Nomic Atlas for the PiDay2025 exhibition.
    
    This script takes embedding JSONL files and uploads them to Nomic Atlas,
    creating a new map or updating an existing one.
    """
    # Create directory if it doesn't exist
    Path(embeddings_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all JSONL files
    print(f"Looking for JSONL files in {embeddings_dir}")
    jsonl_files = find_jsonl_files(embeddings_dir)
    print(f"Found {len(jsonl_files)} JSONL files")
    
    if not jsonl_files:
        print("No embedding files found. Exiting.")
        return
    
    # Load Atlas info if not creating a new map
    if not new_map and map_id is None:
        atlas_info = load_atlas_info(embeddings_dir)
        map_id = atlas_info.get('map_id')
    
    # Process all JSONL files
    total_embeddings = 0
    all_embeddings = []
    all_data = []
    
    for file_path in jsonl_files:
        print(f"Loading embeddings from {file_path}")
        embeddings, data = load_embeddings_from_file(file_path)
        
        if embeddings and data:
            all_embeddings.extend(embeddings)
            all_data.extend(data)
            total_embeddings += len(embeddings)
            print(f"Loaded {len(embeddings)} embeddings")
        else:
            print(f"No valid embeddings found in {file_path}")
    
    if not all_embeddings:
        print("No valid embeddings found in any files. Exiting.")
        return
    
    print(f"Uploading {total_embeddings} embeddings to Atlas...")
    
    # Convert embeddings to numpy array
    np_embeddings = np.array(all_embeddings)
    print(f"Embeddings array shape: {np_embeddings.shape}")
    
    try:
        # Create or update Atlas map
        if new_map or map_id is None:
            # Create new map
            print(f"Creating new Atlas map: {map_name}")
            result = atlas.map_data(
                embeddings=np_embeddings,
                data=all_data,
                identifier=map_name,
                description=map_description
            )
            map_id = result.id
            print(f"Created new Atlas map with ID: {map_id}")
        else:
            # Update existing map
            print(f"Updating existing Atlas map: {map_id}")
            result = atlas.map_data(
                embeddings=np_embeddings,
                data=all_data,
                identifier=map_id,
                rebuild=True  # Rebuild to ensure consistent visualization
            )
            print(f"Updated Atlas map {map_id} with {total_embeddings} embeddings")
        
        # Save map info for future reference
        save_atlas_info(embeddings_dir, map_id, map_name)
        
        print(f"Successfully uploaded {total_embeddings} embeddings to Atlas map: {map_id}")
        print(f"You can view the map at: https://atlas.nomic.ai/map/{map_id}")
    
    except Exception as e:
        print(f"Error uploading to Atlas: {str(e)}")

if __name__ == "__main__":
    app()