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
from nomic import AtlasDataset

def find_image_files(input_dir):
    """Find all image files in the input directory."""
    image_files = []
    input_path = Path(input_dir)
    
    # Common image extensions
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    # Find all matching files
    for ext in extensions:
        files = [str(f) for f in input_path.glob(f"**/*{ext}")]
        image_files.extend(files)
        print(f"Found {len(files)} files with extension {ext}")
        
        upper_files = [str(f) for f in input_path.glob(f"**/*{ext.upper()}")]
        image_files.extend(upper_files)
        if upper_files:
            print(f"Found {len(upper_files)} files with extension {ext.upper()}")
    
    # Sort for reproducibility
    image_files.sort()
    
    # Print first few and last few files to verify recursion is working
    if image_files:
        print("\nSample of files found:")
        for i, file in enumerate(image_files[:5]):
            print(f"  {i+1}. {file}")
        
        if len(image_files) > 10:
            print("  ...")
            for i, file in enumerate(image_files[-5:]):
                print(f"  {len(image_files)-4+i}. {file}")
    
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
    map_id = None
    map_name = None
    dataset_id = None
    
    if Path(tracking_file).exists():
        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                uploaded = set(data.get('uploaded_files', []))
                map_id = data.get('map_id')
                map_name = data.get('map_name')
                dataset_id = data.get('dataset_id')
                print(f"Found tracking file with {len(uploaded)} already uploaded files")
                
                if map_id:
                    print(f"Existing map ID: {map_id}")
                
                if dataset_id:
                    print(f"Existing dataset ID: {dataset_id}")
                
                # Print first few uploaded files
                if uploaded:
                    print("Sample of already uploaded files:")
                    for i, file in enumerate(list(uploaded)[:5]):
                        print(f"  {i+1}. {file}")
                    if len(uploaded) > 5:
                        print(f"  ... and {len(uploaded) - 5} more")
        except Exception as e:
            print(f"Error reading tracking file: {e}")
    else:
        print(f"No tracking file found at {tracking_file}")
    
    return uploaded, map_id, map_name, dataset_id

def update_tracking_file(tracking_file, uploaded_files, map_id, map_name, dataset_id=None):
    """Update the tracking file with newly uploaded files."""
    data = {
        'map_id': map_id,
        'map_name': map_name,
        'dataset_id': dataset_id,
        'uploaded_files': list(uploaded_files)
    }
    
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated tracking file with {len(uploaded_files)} uploaded files")
    if dataset_id:
        print(f"Dataset ID: {dataset_id}")
    print(f"Map ID: {map_id}")

def prepare_metadata(image_files):
    """Prepare metadata for each image."""
    metadata = []
    image_paths = []
    
    print("\nPreparing metadata for images:")
    for i, filepath in enumerate(image_files):
        path = Path(filepath)
        
        # Get subdirectory as label
        label = path.parent.name
        if label == "images" or label == "":
            label = "unlabeled"
        
        # Generate a unique ID for the file
        file_id = get_file_hash(filepath)
        
        item_metadata = {
            "id": file_id,
            "label": label
        }
        
        metadata.append(item_metadata)
        image_paths.append(filepath)
        
        # Print progress
        if i < 5 or i >= len(image_files) - 5 or i % 20 == 0:
            print(f"  Processing {i+1}/{len(image_files)}: {filepath} → label: '{label}'")
    
    return image_paths, metadata

def get_or_create_atlas_dataset(dataset_id, new_map=False):
    """Get existing dataset or create a new one."""
    try:
        if not new_map:
            # Try to connect to existing dataset
            atlas_dataset = AtlasDataset(dataset_id, unique_id_field="id")
            print(f"Connected to existing dataset: {dataset_id}")
            return atlas_dataset, None
    except Exception as e:
        print(f"Could not connect to dataset {dataset_id}: {e}")
        print("Will create a new dataset.")
    
    # If we're here, we need to create a new dataset
    return None, None

def create_new_atlas_map(map_name, batch_images, batch_metadata, dataset_id=None):
    """Create a new Atlas map and dataset."""
    print(f"Creating new Atlas map: {map_name}")
    
    # Create new map with first batch
    atlas_map = atlas.map_data(
        blobs=batch_images,
        data=batch_metadata,
        identifier=map_name,
        description=f"{map_name} Exhibition Images",
        id_field="id"  # Use 'id' as the ID field
    )
    
    map_id = atlas_map.id
    
    # Get dataset ID from map
    if hasattr(atlas_map, 'project_id'):
        dataset_id = atlas_map.project_id
    elif hasattr(atlas_map, 'dataset_id'):
        dataset_id = atlas_map.dataset_id
    
    # Use default if we still don't have one
    if not dataset_id:
        dataset_id = "martysteer/piday2025"
        print(f"Using default dataset ID: {dataset_id}")
    
    # Initialize dataset for future batches
    atlas_dataset = AtlasDataset(dataset_id, unique_id_field="id")
    
    print(f"Created new Atlas map with ID: {map_id}")
    print(f"Dataset ID: {dataset_id}")
    
    return atlas_dataset, map_id, dataset_id

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Upload images directly to Nomic Atlas")
    parser.add_argument("--image-dir", "-i", default="data/images", help="Directory containing image files")
    parser.add_argument("--track-file", "-t", default="data/atlas_tracking.json", help="File to track uploaded images")
    parser.add_argument("--map-name", "-n", default="PiDay2025", help="Name for the Atlas map")
    parser.add_argument("--batch-size", "-b", type=int, default=20, help="Number of images to upload in each batch")
    parser.add_argument("--new-map", action="store_true", help="Force creation of a new map")
    parser.add_argument("--dataset-id", "-d", default="martysteer/piday2025", help="Specify dataset ID directly (username/dataset_name)")
    args = parser.parse_args()
    
    print("\n=== PiDay2025 Direct Image Upload ===")
    print(f"Image directory: {args.image_dir}")
    print(f"Tracking file: {args.track_file}")
    print(f"Map name: {args.map_name}")
    print(f"Batch size: {args.batch_size}")
    print(f"Force new map: {args.new_map}")
    print(f"Dataset ID: {args.dataset_id}")
    
    # Create directories if they don't exist
    Path(args.image_dir).mkdir(parents=True, exist_ok=True)
    Path(args.track_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    print(f"\nSearching for images in {args.image_dir}")
    all_image_files = find_image_files(args.image_dir)
    print(f"Found {len(all_image_files)} total image files")
    
    if not all_image_files:
        print("No image files found. Exiting.")
        return
    
    # Get already uploaded files and map info
    uploaded_files, existing_map_id, existing_map_name, existing_dataset_id = get_uploaded_files(args.track_file)
    
    # Use dataset ID with simple priority: command line arg > tracking file > default
    dataset_id = args.dataset_id
    if dataset_id != "martysteer/piday2025" or existing_dataset_id is None:
        print(f"Using dataset ID from command line: {dataset_id}")
    elif existing_dataset_id:
        dataset_id = existing_dataset_id
        print(f"Using dataset ID from tracking file: {dataset_id}")
    
    # Use existing map name if available and not specified
    if existing_map_name and args.map_name == "PiDay2025":
        args.map_name = existing_map_name
        print(f"Using existing map name: {args.map_name}")
    
    # Filter out already uploaded files
    new_image_files = [f for f in all_image_files if f not in uploaded_files]
    print(f"\nFound {len(new_image_files)} new files to upload")
    
    if not new_image_files:
        print("No new files to upload. Exiting.")
        return
    
    # Get map ID from tracking file if not creating a new map
    map_id = None
    if not args.new_map:
        map_id = existing_map_id
        if map_id:
            print(f"Using existing map ID: {map_id}")
        if dataset_id:
            print(f"Using existing dataset ID: {dataset_id}")
        if not map_id and not dataset_id:
            print("No existing map/dataset IDs found. Will create a new map.")
    
    # Prepare metadata for all images
    image_paths, metadata = prepare_metadata(new_image_files)
    
    # Process in batches
    batch_size = args.batch_size
    
    print(f"Uploading {len(image_paths)} images in batches of {batch_size}")
    
    # Print directory structure information
    print("\nDirectory structure summary:")
    labels = {}
    for meta in metadata:
        label = meta["label"]
        if label in labels:
            labels[label] += 1
        else:
            labels[label] = 1
    
    for label, count in labels.items():
        print(f"  {label}: {count} images")
    
    # Initialize dataset object if we have a dataset ID
    atlas_dataset = None
    first_batch = True
    
    # Try to connect to existing dataset
    if not args.new_map and dataset_id:
        atlas_dataset, _ = get_or_create_atlas_dataset(dataset_id)
    
    # Process batches    
    for i in range(0, len(image_paths), batch_size):
        batch_end = min(i + batch_size, len(image_paths))
        batch_images = image_paths[i:batch_end]
        batch_metadata = metadata[i:batch_end]
        
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(image_paths) + batch_size - 1) // batch_size} ({len(batch_images)} images)")
        print("First few images in this batch:")
        for j, img in enumerate(batch_images[:min(3, len(batch_images))]):
            print(f"  {j+1}. {img}")
        
        try:
            # Create a new map with the first batch if needed
            if first_batch and (args.new_map or atlas_dataset is None):
                atlas_dataset, map_id, dataset_id = create_new_atlas_map(
                    args.map_name, 
                    batch_images, 
                    batch_metadata,
                    dataset_id
                )
                first_batch = False
            else:
                # Add to existing dataset
                print(f"Adding batch to existing Atlas dataset: {dataset_id}")
                atlas_dataset.add_data(
                    blobs=batch_images,
                    data=batch_metadata
                )
                print(f"Successfully added batch to dataset")
            
            # Mark files as uploaded
            uploaded_files.update(batch_images)
            update_tracking_file(args.track_file, uploaded_files, map_id, args.map_name, dataset_id)
            print(f"Successfully uploaded batch {i//batch_size + 1}")
            
        except Exception as e:
            print(f"Error uploading batch: {str(e)}")
            # Print more details about the error
            import traceback
            print(traceback.format_exc())
            break
    
    # After all batches, create or update the Atlas map visualization
    if atlas_dataset is not None:
        print("\nUpdating the Atlas map visualization...")
        try:
            # Create/update the map visualization
            index_params = {
                "topic_model": {"build_topic_model": False},
                "embedding_model": "nomic-embed-vision-v1.5",
            }
            
            # If we have a map ID, use it, otherwise let Nomic create a new one
            if map_id:
                index_params["name"] = map_id
            
            atlas_map = atlas_dataset.create_index(**index_params)
            
            # Update map_id if it was newly created
            if map_id is None and atlas_map is not None:
                map_id = atlas_map.id
                update_tracking_file(args.track_file, uploaded_files, map_id, args.map_name, dataset_id)
                
            print(f"Successfully updated Atlas map visualization with ID: {map_id}")
        except Exception as e:
            print(f"Warning: Could not update map visualization: {e}")
            import traceback
            print(traceback.format_exc())
    
    if map_id:
        print(f"\nSuccessfully uploaded images to Atlas map: {map_id}")
        print(f"You can view the map at: https://atlas.nomic.ai/map/{map_id}")
        if dataset_id:
            print(f"Dataset ID: {dataset_id}")
            print(f"Dataset URL: https://atlas.nomic.ai/data/{dataset_id}")

if __name__ == "__main__":
    main()