#!/usr/bin/env python3
"""
PiDay2025 Direct Image Upload Script

This script directly uploads images to Nomic Atlas without the intermediate embedding step.
It tracks which images have already been uploaded to avoid duplicates.

Usage:
    python simple_upload_to_atlas.py --image-dir data/images

Requirements:
    pip install nomic
"""

import os
import json
import hashlib
from pathlib import Path
import argparse

from nomic import atlas

def find_image_files(input_dir):
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

def get_file_hash(filepath):
    """Generate a hash for the file to use as an ID."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)  # Read in 64k chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def get_uploaded_files(tracking_file):
    """Get the list of files that have already been uploaded."""
    uploaded = set()
    
    if Path(tracking_file).exists():
        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                uploaded = set(data.get('uploaded_files', []))
                print(f"Found {len(uploaded)} already uploaded files")
        except Exception as e:
            print(f"Error reading tracking file: {e}")
    
    return uploaded

def update_tracking_file(tracking_file, uploaded_files, map_id, map_name):
    """Update the tracking file with newly uploaded files."""
    data = {
        'map_id': map_id,
        'map_name': map_name,
        'uploaded_files': list(uploaded_files)
    }
    
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated tracking file with {len(uploaded_files)} uploaded files")

def prepare_metadata(image_files):
    """Prepare metadata for each image."""
    metadata = []
    image_paths = []
    
    for filepath in image_files:
        path = Path(filepath)
        
        # Get subdirectory as label
        label = path.parent.name
        if label == "images" or label == "":
            label = "unlabeled"
        
        # Generate a unique ID for the file
        file_id = get_file_hash(filepath)
        
        metadata.append({
            "id": file_id,
            "filename": path.name,
            "filepath": str(path),
            "label": label
        })
        
        image_paths.append(filepath)
    
    return image_paths, metadata

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Upload images directly to Nomic Atlas")
    parser.add_argument("--image-dir", "-i", default="data/images", help="Directory containing image files")
    parser.add_argument("--track-file", "-t", default="data/atlas_tracking.json", help="File to track uploaded images")
    parser.add_argument("--map-name", "-n", default="PiDay2025", help="Name for the Atlas map")
    parser.add_argument("--batch-size", "-b", type=int, default=100, help="Number of images to upload in each batch")
    parser.add_argument("--new-map", action="store_true", help="Force creation of a new map")
    args = parser.parse_args()
    
    # Create directories if they don't exist
    Path(args.image_dir).mkdir(parents=True, exist_ok=True)
    Path(args.track_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    print(f"Searching for images in {args.image_dir}")
    all_image_files = find_image_files(args.image_dir)
    print(f"Found {len(all_image_files)} image files")
    
    if not all_image_files:
        print("No image files found. Exiting.")
        return
    
    # Get already uploaded files
    uploaded_files = get_uploaded_files(args.track_file)
    
    # Filter out already uploaded files
    new_image_files = [f for f in all_image_files if f not in uploaded_files]
    print(f"Found {len(new_image_files)} new files to upload")
    
    if not new_image_files:
        print("No new files to upload. Exiting.")
        return
    
    # Get map ID from tracking file if not creating a new map
    map_id = None
    if not args.new_map:
        try:
            with open(args.track_file, 'r') as f:
                data = json.load(f)
                map_id = data.get('map_id')
                if map_id:
                    print(f"Using existing map: {map_id}")
        except:
            pass
    
    # Prepare metadata for all images
    image_paths, metadata = prepare_metadata(new_image_files)
    
    # Process in batches
    atlas_map = None
    batch_size = args.batch_size
    
    print(f"Uploading {len(image_paths)} images in batches of {batch_size}")
    
    for i in range(0, len(image_paths), batch_size):
        batch_end = min(i + batch_size, len(image_paths))
        batch_images = image_paths[i:batch_end]
        batch_metadata = metadata[i:batch_end]
        
        print(f"Processing batch {i//batch_size + 1}/{(len(image_paths) + batch_size - 1) // batch_size} ({len(batch_images)} images)")
        
        try:
            if map_id is None or args.new_map:
                # Create new map with first batch
                print(f"Creating new Atlas map: {args.map_name}")
                atlas_map = atlas.map_data(
                    blobs=batch_images,
                    data=batch_metadata,
                    identifier=args.map_name,
                    description=f"{args.map_name} Exhibition Images"
                )
                map_id = atlas_map.id
                args.new_map = False  # Set to False so we update this map for subsequent batches
                print(f"Created new Atlas map with ID: {map_id}")
            else:
                # Update existing map
                print(f"Adding to existing Atlas map: {map_id}")
                atlas_dataset = atlas.AtlasDataset(map_id)
                atlas_dataset.add_data(
                    blobs=batch_images,
                    data=batch_metadata
                )
                print(f"Added batch to Atlas map {map_id}")
            
            # Mark files as uploaded
            uploaded_files.update(batch_images)
            update_tracking_file(args.track_file, uploaded_files, map_id, args.map_name)
            
        except Exception as e:
            print(f"Error uploading batch: {str(e)}")
            break
    
    if map_id:
        print(f"Successfully uploaded images to Atlas map: {map_id}")
        print(f"You can view the map at: https://atlas.nomic.ai/map/{map_id}")

if __name__ == "__main__":
    main()