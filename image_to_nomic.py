#!/usr/bin/env python3
"""
Image to Nomic Atlas Embeddings Converter

This script processes a directory of image files and converts them into Nomic Atlas
embeddings in JSONL format, suitable for importing into Nomic Atlas.

Requirements:
    pip install nomic pillow argparse tqdm
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from PIL import Image
from tqdm import tqdm
from nomic import atlas

def setup_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert image files to Nomic Atlas embeddings in JSONL format."
    )
    parser.add_argument(
        "--input_dir", "-i", 
        type=str, 
        required=True,
        help="Directory containing image files"
    )
    parser.add_argument(
        "--output_file", "-o", 
        type=str, 
        default="image_embeddings.jsonl",
        help="Output JSONL file path (default: image_embeddings.jsonl)"
    )
    parser.add_argument(
        "--extensions", "-e", 
        type=str, 
        default=".jpg,.jpeg,.png,.bmp,.gif",
        help="Comma-separated list of image file extensions to process (default: .jpg,.jpeg,.png,.bmp,.gif)"
    )
    parser.add_argument(
        "--batch_size", "-b", 
        type=int, 
        default=16,
        help="Batch size for embedding generation (default: 16)"
    )
    parser.add_argument(
        "--max_files", "-m", 
        type=int, 
        default=None,
        help="Maximum number of files to process (default: process all)"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="nomic-ai/nomic-embed-vision-v1.5",
        help="Nomic embedding model to use (default: nomic-ai/nomic-embed-vision-v1.5)"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default=None,
        help="Device to use (e.g., 'cuda', 'cpu', default: auto-detect)"
    )
    parser.add_argument(
        "--metadata", 
        action="store_true",
        help="Include file metadata in the output"
    )
    return parser.parse_args()

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

def main() -> None:
    """Main function."""
    args = setup_args()
    
    # Process extensions
    extensions = [ext.strip() for ext in args.extensions.split(",")]
    
    # Find image files
    print(f"Searching for images in {args.input_dir}")
    image_files = find_image_files(args.input_dir, extensions, args.max_files)
    print(f"Found {len(image_files)} image files")
    
    if not image_files:
        print("No image files found. Exiting.")
        return
    
    # Process images and generate embeddings
    results = process_images_batch(
        image_files, 
        args.batch_size, 
        args.model,
        args.device,
        args.metadata
    )
    
    # Save results
    save_jsonl(results, args.output_file)
    print(f"Successfully saved {len(results)} embeddings to {args.output_file}")

if __name__ == "__main__":
    main()