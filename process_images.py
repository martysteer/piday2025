#!/usr/bin/env python3
"""
PiDay2025 Image Processor

This script processes image files and converts them into Nomic Atlas
embeddings in JSONL format, suitable for importing into Nomic Atlas.

Usage:
    python process_images.py --image-dir data/images --output-dir data/embeddings

Requirements:
    pip install "nomic[local]" pillow typer tqdm torch
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

import torch
import typer
from PIL import Image
from tqdm import tqdm
from nomic import embed
import numpy as np

# Define the app
app = typer.Typer(help="Convert image files to Nomic Atlas embeddings in JSONL format.")

def find_image_files(input_dir: str) -> List[str]:
    """Find all image files in the input directory."""
    image_files = []
    input_path = Path(input_dir)
    
    # Common image extensions
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    # Find all matching files
    for ext in extensions:
        image_files.extend([str(f) for f in input_path.glob(f"**/*{ext}")])
        image_files.extend([str(f) for f in input_path.glob(f"**/*{ext.upper()}")])
    
    # Sort for reproducibility
    image_files.sort()
    return image_files

def get_processed_files(output_dir: str) -> Set[str]:
    """Get a set of files that have already been processed."""
    output_path = Path(output_dir)
    processed = set()
    
    # Create the directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check all JSONL files in the output directory
    for jsonl_file in output_path.glob("*.jsonl"):
        try:
            with open(jsonl_file, 'r') as f:
                for line in f:
                    record = json.loads(line)
                    if 'metadata' in record and 'filepath' in record['metadata']:
                        processed.add(record['metadata']['filepath'])
        except Exception as e:
            print(f"Error reading {jsonl_file}: {e}")
    
    return processed

def get_file_metadata(filepath: str) -> Dict[str, Any]:
    """Extract basic metadata from the file."""
    stats = os.stat(filepath)
    file = Path(filepath)
    
    return {
        "filename": file.name,
        "filepath": str(file),
        "extension": file.suffix.lower(),
        "size_bytes": stats.st_size,
        "created": stats.st_ctime,
        "modified": stats.st_mtime,
    }

def process_images(
    image_files: List[str], 
    batch_size: int, 
    output_file: str,
    model_name: str,
    use_api: bool = False,
    include_metadata: bool = True,
) -> int:
    """Process images and generate embeddings."""
    # Determine device for local processing
    device = "cuda" if torch.cuda.is_available() and not use_api else "cpu"
    mode = "api" if use_api else "local"
    print(f"Processing using {mode} mode" + (f" on {device}" if mode == "local" else ""))
    
    # Process in batches
    total_processed = 0
    batch_num = 0
    
    for batch_start in range(0, len(image_files), batch_size):
        batch_num += 1
        batch_end = min(batch_start + batch_size, len(image_files))
        batch_files = image_files[batch_start:batch_end]
        
        print(f"Processing batch {batch_num}/{(len(image_files) + batch_size - 1) // batch_size} ({len(batch_files)} images)")
        
        try:
            # Configure kwargs based on mode
            kwargs = {"model": model_name
                    #   "task_type": "search_document"
                     }
            
            if use_api:
                # API mode
                output = embed.image(images=batch_files, **kwargs)
            else:
                # Local mode
                kwargs["inference_mode"] = 'local'
                output = embed.image(images=batch_files, **kwargs)
            
            embeddings = np.array(output['embeddings']).tolist()
            
            # Create records
            records = []
            for idx, (file_path, embedding) in enumerate(zip(batch_files, embeddings)):
                record = {
                    "id": str(Path(file_path).stem),
                    "embedding": embedding
                }
                
                if include_metadata:
                    record["metadata"] = get_file_metadata(file_path)
                
                records.append(record)
            
            # Append to output file
            with open(output_file, 'a') as f:
                for record in records:
                    f.write(json.dumps(record) + '\n')
            
            total_processed += len(batch_files)
            
        except Exception as e:
            print(f"Error processing batch {batch_num}: {str(e)}")
    
    return total_processed

@app.command()
def main(
    image_dir: str = typer.Option("data/images", "--image-dir", "-i", help="Directory containing image files"),
    output_dir: str = typer.Option("data/embeddings", "--output-dir", "-o", help="Output directory for JSONL files"),
    batch_size: int = typer.Option(16, "--batch-size", "-b", help="Batch size for embedding generation"),
    model: str = typer.Option("nomic-embed-vision-v1.5", "--model", "-m", help="Nomic embedding model to use"),
    use_api: bool = typer.Option(False, "--use-api", help="Use Nomic API instead of local processing"),
    force_reprocess: bool = typer.Option(False, "--force", "-f", help="Force reprocessing of all files"),
):
    """
    Convert image files to Nomic Atlas embeddings in JSONL format.
    
    This script processes images in the specified directory and creates embeddings,
    saving the results in JSONL format in the output directory.
    """
    # Create directories if they don't exist
    image_path = Path(image_dir)
    output_path = Path(output_dir)
    
    if not image_path.exists():
        print(f"Creating image directory: {image_path}")
        image_path.mkdir(parents=True, exist_ok=True)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    print(f"Searching for images in {image_dir}")
    all_image_files = find_image_files(image_dir)
    print(f"Found {len(all_image_files)} image files")
    
    if not all_image_files:
        print("No image files found. Exiting.")
        return
    
    # Get already processed files
    processed_files = set() if force_reprocess else get_processed_files(output_dir)
    print(f"Found {len(processed_files)} already processed files")
    
    # Filter out already processed files
    new_image_files = [f for f in all_image_files if f not in processed_files]
    print(f"Found {len(new_image_files)} new files to process")
    
    if not new_image_files:
        print("No new files to process. Exiting.")
        return
    
    # Create output file with timestamp
    timestamp = int(time.time())
    output_file = output_path / f"embeddings_{timestamp}.jsonl"
    
    # Process images
    processed_count = process_images(
        new_image_files, 
        batch_size, 
        str(output_file),
        model,
        use_api,
        include_metadata=True
    )
    
    print(f"Successfully processed {processed_count} images")
    print(f"Embeddings saved to {output_file}")

if __name__ == "__main__":
    app()