#!/usr/bin/env python3
"""
PiDay2025 Image Collection

This script provides a simple interface to collect images from participants at the
PiDay2025 exhibition. It assigns a unique ID to each participant, collects
their images, and organizes them in the raw data directory.

Usage:
    python collect_images.py --output-dir data/raw
"""

import os
import time
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime
import typer
from typing import Optional, List, Dict, Any
from tqdm import tqdm
import argparse

app = typer.Typer(help="Collect and organize images from participants.")

def generate_participant_id() -> str:
    """Generate a unique participant ID."""
    # Format: PIDAY_{timestamp}_{random_uuid}
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"PIDAY_{timestamp}_{unique_id}"

def create_participant_directory(base_dir: Path, participant_id: str) -> Path:
    """Create a directory for the participant's images."""
    participant_dir = base_dir / participant_id
    participant_dir.mkdir(exist_ok=True, parents=True)
    return participant_dir

def copy_images_to_participant_dir(
    source_images: List[str], 
    participant_dir: Path,
    rename_files: bool = True
) -> List[Dict[str, Any]]:
    """Copy images to the participant's directory and return metadata."""
    image_metadata = []
    
    for i, img_path in enumerate(tqdm(source_images, desc="Copying images")):
        # Get source file info
        source_path = Path(img_path)
        if not source_path.exists():
            print(f"Warning: Source file {img_path} does not exist, skipping")
            continue
            
        # Generate destination filename (either rename or keep original)
        if rename_files:
            dest_filename = f"{i+1:03d}{source_path.suffix.lower()}"
        else:
            dest_filename = source_path.name
            
        # Copy file
        dest_path = participant_dir / dest_filename
        try:
            shutil.copy2(source_path, dest_path)
            
            # Get file stats
            stats = os.stat(dest_path)
            
            # Add metadata
            metadata = {
                "original_path": str(source_path),
                "stored_path": str(dest_path),
                "filename": dest_filename,
                "size_bytes": stats.st_size,
                "extension": source_path.suffix.lower(),
                "created": stats.st_ctime,
                "modified": stats.st_mtime,
            }
            image_metadata.append(metadata)
            
        except Exception as e:
            print(f"Error copying {source_path} to {dest_path}: {str(e)}")
    
    return image_metadata

def save_participant_metadata(
    participant_dir: Path, 
    participant_id: str,
    image_metadata: List[Dict[str, Any]],
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """Save participant metadata to a JSON file."""
    metadata_file = participant_dir / "metadata.json"
    
    metadata = {
        "participant_id": participant_id,
        "timestamp": datetime.now().isoformat(),
        "image_count": len(image_metadata),
        "images": image_metadata,
    }
    
    # Add any additional info provided
    if additional_info:
        metadata.update(additional_info)
    
    # Save to file
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved metadata to {metadata_file}")

def validate_images(file_paths: List[str]) -> List[str]:
    """Validate image files and return only valid ones."""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    valid_images = []
    
    for path in file_paths:
        file_path = Path(path)
        
        # Check if file exists
        if not file_path.exists():
            print(f"Warning: File {path} does not exist, skipping")
            continue
            
        # Check if it's a file (not directory)
        if not file_path.is_file():
            print(f"Warning: {path} is not a file, skipping")
            continue
            
        # Check extension
        if file_path.suffix.lower() not in valid_extensions:
            print(f"Warning: {path} is not a supported image format, skipping")
            continue
            
        # File seems valid
        valid_images.append(path)
    
    return valid_images

@app.command()
def interactive(
    output_dir: str = typer.Option("data/raw", "--output-dir", "-o", help="Directory to store collected images"),
):
    """
    Run in interactive mode to collect images from multiple participants.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    print("=== PiDay2025 Image Collection Tool ===")
    print(f"Images will be stored in: {output_path}")
    print()
    
    while True:
        print("\n--- New Participant ---")
        
        # Generate participant ID
        participant_id = generate_participant_id()
        print(f"Assigned ID: {participant_id}")
        
        # Create participant directory
        participant_dir = create_participant_directory(output_path, participant_id)
        print(f"Created directory: {participant_dir}")
        
        # Ask for image source
        print("\nHow would you like to provide images?")
        print("1. Specify a directory")
        print("2. List individual image files")
        choice = input("Choose an option (1/2): ").strip()
        
        image_paths = []
        if choice == "1":
            source_dir = input("Enter source directory path: ").strip()
            source_path = Path(source_dir)
            
            if not source_path.exists() or not source_path.is_dir():
                print("Error: Invalid directory path")
                continue
                
            # Find all image files in the directory
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            for ext in extensions:
                image_paths.extend([str(f) for f in source_path.glob(f"**/*{ext}")])
                image_paths.extend([str(f) for f in source_path.glob(f"**/*{ext.upper()}")])
                
            print(f"Found {len(image_paths)} image files in {source_dir}")
            
        elif choice == "2":
            print("Enter image file paths (one per line, empty line to finish):")
            while True:
                path = input("> ").strip()
                if not path:
                    break
                image_paths.append(path)
        else:
            print("Invalid choice. Please try again.")
            continue
        
        # Validate images
        valid_images = validate_images(image_paths)
        if not valid_images:
            print("No valid images found. Please try again.")
            continue
            
        print(f"Validated {len(valid_images)} images")
        
        # Gather additional info
        print("\nAdditional information (optional):")
        name = input("Participant name (or leave blank): ").strip()
        email = input("Participant email (or leave blank): ").strip()
        notes = input("Any notes (or leave blank): ").strip()
        
        additional_info = {}
        if name:
            additional_info["name"] = name
        if email:
            additional_info["email"] = email
        if notes:
            additional_info["notes"] = notes
        
        # Process images
        print("\nProcessing images...")
        rename = typer.confirm("Rename files sequentially? (recommended)", default=True)
        image_metadata = copy_images_to_participant_dir(valid_images, participant_dir, rename_files=rename)
        
        # Save metadata
        save_participant_metadata(participant_dir, participant_id, image_metadata, additional_info)
        
        print(f"\nSuccessfully processed {len(image_metadata)} images for participant {participant_id}")
        
        # Ask to continue with another participant
        if not typer.confirm("Process another participant?", default=True):
            print("Image collection complete. Exiting.")
            break

@app.command()
def batch(
    source_dir: str = typer.Option(..., "--source-dir", "-s", help="Source directory containing images"),
    output_dir: str = typer.Option("data/raw", "--output-dir", "-o", help="Directory to store collected images"),
    participant_id: Optional[str] = typer.Option(None, "--id", help="Custom participant ID (generated if not provided)"),
    rename: bool = typer.Option(True, "--rename/--no-rename", help="Rename files sequentially"),
):
    """
    Process a batch of images for a single participant.
    """
    # Setup directories
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Generate or use provided participant ID
    if not participant_id:
        participant_id = generate_participant_id()
    
    print(f"Processing images for participant: {participant_id}")
    
    # Create participant directory
    participant_dir = create_participant_directory(output_path, participant_id)
    
    # Find images in source directory
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: Source directory {source_dir} does not exist or is not a directory")
        return
    
    # Find all image files in the directory
    image_paths = []
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    for ext in extensions:
        image_paths.extend([str(f) for f in source_path.glob(f"**/*{ext}")])
        image_paths.extend([str(f) for f in source_path.glob(f"**/*{ext.upper()}")])
    
    # Validate images
    valid_images = validate_images(image_paths)
    if not valid_images:
        print("No valid images found.")
        return
    
    print(f"Found {len(valid_images)} valid images")
    
    # Process images
    image_metadata = copy_images_to_participant_dir(valid_images, participant_dir, rename_files=rename)
    
    # Save metadata
    save_participant_metadata(participant_dir, participant_id, image_metadata)
    
    print(f"Successfully processed {len(image_metadata)} images for participant {participant_id}")

if __name__ == "__main__":
    app()