#!/usr/bin/env python3
"""
Image to Nomic Atlas Embeddings Converter

This script processes a directory of image files and converts them into Nomic Atlas
embeddings in JSONL format, suitable for importing into Nomic Atlas.

Requirements:
    pip install nomic pillow typer tqdm torch
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import typer
from PIL import Image
from tqdm import tqdm
from nomic import atlas
from typing_extensions import Annotated

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
    include_metadata: bool = False
) -> List[Dict[str, Any]]:
    """Process images in batches and generate embeddings."""
    # Determine device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"Using device: {device}")
    
    # Load model
    print(f"Loading embedding model: {model_name}")
    embedder = atlas.EmbeddingModel(model_name=model_name, device=device)
    
    results = []
    total_batches = (len(image_files) + batch_size - 1) // batch_size
    
    for batch_idx in tqdm(range(total_batches), desc="Processing batches"):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(image_files))
        batch_files = image_files[start_idx:end_idx]
        
        # Load images
        loaded_images = []
        valid_files = []
        
        for img_path in batch_files:
            try:
                img = Image.open(img_path).convert("RGB")
                loaded_images.append(img)
                valid_files.append(img_path)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                continue
        
        if not loaded_images:
            continue
        
        # Generate embeddings
        try:
            embeddings = embedder.embed(loaded_images).tolist()
            
            # Create records
            for idx, (file_path, embedding) in enumerate(zip(valid_files, embeddings)):
                record = {
                    "id": str(Path(file_path).stem),
                    "embedding": embedding
                }
                
                if include_metadata:
                    record["metadata"] = get_file_metadata(file_path)
                
                results.append(record)
                
            # Close images
            for img in loaded_images:
                img.close()
                
        except Exception as e:
            print(f"Error generating embeddings for batch {batch_idx}: {e}")
    
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
    model: Annotated[str, typer.Option(help="Nomic embedding model to use")] = "nomic-ai/nomic-embed-vision-v1.5",
    device: Annotated[Optional[str], typer.Option(help="Device to use (e.g., 'cuda', 'cpu')")] = None,
    metadata: Annotated[bool, typer.Option(help="Include file metadata in the output")] = False,
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
        metadata
    )
    
    # Save results
    save_jsonl(results, output_file)
    print(f"Successfully saved {len(results)} embeddings to {output_file}")


if __name__ == "__main__":
    app()