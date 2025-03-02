#!/usr/bin/env python3
"""
Image to Nomic Atlas Embeddings Converter

This script processes a directory of image files and converts them into Nomic Atlas
embeddings in JSONL format, suitable for importing into Nomic Atlas.

Requirements:
    pip install "nomic[local]" pillow typer tqdm torch
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

import torch
import typer
from PIL import Image
from tqdm import tqdm
from nomic import embed
import numpy as np
from typing_extensions import Annotated

class NomicMode(str, Enum):
    """Nomic embedding mode options"""
    LOCAL = "local"
    API = "api"

app = typer.Typer(help="Convert image files to Nomic Atlas embeddings in JSONL format.")


def find_image_files(input_dir: str, extensions: List[str], max_files: Optional[int] = None) -> List[str]:
    """Find all image files with the specified extensions in the input directory."""
    image_files = []
    input_path = Path(input_dir)
    
    for ext in extensions:
        files = list(input_path.glob(f"**/*{ext}"))
        image_files.extend([str(f) for f in files])
    
    # Sort for reproducibility
    image_files.sort()
    
    if max_files is not None:
        image_files = image_files[:max_files]
    
    return image_files


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


def process_images_batch(
    image_files: List[str], 
    batch_size: int, 
    model_name: str,
    device: Optional[str] = None,
    include_metadata: bool = False,
    nomic_mode: NomicMode = NomicMode.LOCAL,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """Process images in batches and generate embeddings."""
    # Determine device
    if device is None and nomic_mode == NomicMode.LOCAL:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if nomic_mode == NomicMode.LOCAL:
        print(f"Using device: {device} with local embedding")
    elif nomic_mode == NomicMode.API:
        print("Using Nomic API for embedding")
    
    results = []
    total_batches = (len(image_files) + batch_size - 1) // batch_size
    
    for batch_idx in tqdm(range(total_batches), desc="Processing batches"):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(image_files))
        batch_files = image_files[start_idx:end_idx]
        
        # In dry run mode, just create dummy embeddings
        if dry_run:
            print(f"Dry run: Creating dummy embeddings for batch {batch_idx+1}/{total_batches}")
            for file_path in batch_files:
                record = {
                    "id": str(Path(file_path).stem),
                    "embedding": [0.0] * 512  # Common embedding size
                }
                
                if include_metadata:
                    record["metadata"] = get_file_metadata(file_path)
                
                results.append(record)
            continue
            
        # Generate embeddings using nomic.embed.image
        try:
            # Configure kwargs based on mode
            kwargs = {"model": model_name}
            if nomic_mode == NomicMode.LOCAL:
                kwargs["device"] = device
            
            output = embed.image(
                images=batch_files,
                **kwargs
            )
            
            embeddings = np.array(output['embeddings']).tolist()
            
            # Create records
            for idx, (file_path, embedding) in enumerate(zip(batch_files, embeddings)):
                record = {
                    "id": str(Path(file_path).stem),
                    "embedding": embedding
                }
                
                if include_metadata:
                    record["metadata"] = get_file_metadata(file_path)
                
                results.append(record)
                
        except Exception as e:
            print(f"Error generating embeddings for batch {batch_idx+1}/{total_batches}: {str(e)}")
    
    return results


def save_jsonl(records: List[Dict[str, Any]], output_file: str) -> None:
    """Save records to JSONL format."""
    with open(output_file, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')


@app.command()
def main(
    input_dir: Annotated[str, typer.Option("--input-dir", "-i", help="Directory containing image files")],
    output_file: Annotated[str, typer.Option("--output-file", "-o", help="Output JSONL file path")] = "image_embeddings.jsonl",
    extensions: Annotated[str, typer.Option("--extensions", "-e", help="Comma-separated list of image file extensions to process")] = ".jpg,.jpeg,.png,.bmp,.gif",
    batch_size: Annotated[int, typer.Option("--batch-size", "-b", help="Batch size for embedding generation")] = 16,
    max_files: Annotated[Optional[int], typer.Option("--max-files", "-m", help="Maximum number of files to process")] = None,
    model: Annotated[str, typer.Option(help="Nomic embedding model to use")] = "nomic-embed-vision-v1.5",
    device: Annotated[Optional[str], typer.Option(help="Device to use (e.g., 'cuda', 'cpu')")] = None,
    metadata: Annotated[bool, typer.Option(help="Include file metadata in the output")] = False,
    nomic_mode: Annotated[NomicMode, typer.Option("--nomic", help="Nomic mode: 'local' or 'api'")] = NomicMode.LOCAL,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Run without calling Nomic API")] = False,
) -> None:
    """
    Convert image files to Nomic Atlas embeddings in JSONL format.
    
    This tool processes all images in the specified directory and creates embeddings
    using the Nomic Atlas API, saving the results in JSONL format.
    """
    # Process extensions
    extension_list = [ext.strip() for ext in extensions.split(",")]
    
    # Find image files
    print(f"Searching for images in {input_dir}")
    image_files = find_image_files(input_dir, extension_list, max_files)
    print(f"Found {len(image_files)} image files")
    
    if not image_files:
        print("No image files found. Exiting.")
        return
    
    # Process images and generate embeddings
    results = process_images_batch(
        image_files, 
        batch_size, 
        model,
        device,
        metadata,
        nomic_mode,
        dry_run
    )
    
    # Save results
    save_jsonl(results, output_file)
    print(f"Successfully saved {len(results)} embeddings to {output_file}")


if __name__ == "__main__":
    app()