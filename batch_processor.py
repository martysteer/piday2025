#!/usr/bin/env python3
"""
PiDay2025 Batch Image Processor

This script monitors a directory for new images, processes them in batches,
and generates Nomic Atlas embeddings. It's designed to run continuously during
the exhibition, processing images as participants submit them.

Usage:
    python batch_processor.py --raw-dir data/raw --output-dir data/embeddings
"""

import os
import time
import json
from pathlib import Path
import typer
from typing import Optional, List
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import from the existing image_to_nomic.py script
from image_to_nomic import (
    find_image_files, 
    process_images_batch, 
    save_jsonl, 
    NomicMode
)

app = typer.Typer(help="Process images in batches for Nomic Atlas embeddings.")

class ImageBatchProcessor(FileSystemEventHandler):
    def __init__(
        self, 
        raw_dir: str, 
        output_dir: str, 
        processed_dir: Optional[str] = None,
        batch_size: int = 16, 
        model_name: str = "nomic-embed-vision-v1.5",
        watch_interval: int = 30,
        nomic_mode: NomicMode = NomicMode.LOCAL
    ):
        self.raw_dir = Path(raw_dir)
        self.output_dir = Path(output_dir)
        self.processed_dir = Path(processed_dir) if processed_dir else None
        self.batch_size = batch_size
        self.model_name = model_name
        self.watch_interval = watch_interval
        self.nomic_mode = nomic_mode
        
        self.pending_images = []
        self.processed_images = set()
        self.last_scan_time = 0
        
        # Create directories if they don't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        if self.processed_dir:
            self.processed_dir.mkdir(exist_ok=True, parents=True)
        
        # Initial scan for existing images
        self._scan_for_new_images()
    
    def on_created(self, event):
        """Called when a file or directory is created in the watched directory."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
            print(f"New image detected: {file_path}")
            self.pending_images.append(file_path)
            self.process_pending_if_needed()
    
    def _scan_for_new_images(self):
        """Scan the raw directory for any new images."""
        current_time = time.time()
        if current_time - self.last_scan_time < self.watch_interval:
            return
            
        self.last_scan_time = current_time
        
        # Find all image files in the raw directory
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        all_images = find_image_files(str(self.raw_dir), extensions)
        
        # Add new images to pending list
        new_images = [img for img in all_images if img not in self.processed_images and img not in self.pending_images]
        if new_images:
            print(f"Found {len(new_images)} new images during directory scan")
            self.pending_images.extend(new_images)
            self.process_pending_if_needed()
    
    def process_pending_if_needed(self):
        """Process pending images if we have enough for a batch."""
        if len(self.pending_images) >= self.batch_size:
            self.process_batch()
        elif self.pending_images and len(self.pending_images) < self.batch_size:
            print(f"Waiting for more images. Current queue: {len(self.pending_images)}/{self.batch_size}")
    
    def process_batch(self, force=False):
        """Process a batch of images and generate embeddings."""
        if not self.pending_images:
            return
        
        # If forcing or we have enough for a full batch
        if force or len(self.pending_images) >= self.batch_size:
            # Get next batch
            batch_size = min(len(self.pending_images), self.batch_size)
            batch = self.pending_images[:batch_size]
            self.pending_images = self.pending_images[batch_size:]
            
            try:
                # Generate a timestamp for this batch
                timestamp = int(time.time())
                output_file = self.output_dir / f"batch_{timestamp}.jsonl"
                
                print(f"Processing batch of {len(batch)} images...")
                
                # Use the existing image_to_nomic functionality
                results = process_images_batch(
                    batch, 
                    batch_size, 
                    self.model_name,
                    include_metadata=True,
                    nomic_mode=self.nomic_mode
                )
                
                # Save results
                save_jsonl(results, str(output_file))
                
                # Move processed images to processed directory if specified
                if self.processed_dir:
                    for img_path in batch:
                        img_file = Path(img_path)
                        dest_path = self.processed_dir / img_file.name
                        try:
                            shutil.move(img_path, dest_path)
                            print(f"Moved {img_path} to {dest_path}")
                        except Exception as e:
                            print(f"Error moving file {img_path}: {str(e)}")
                
                # Update processed images
                self.processed_images.update(batch)
                print(f"Processed batch of {len(batch)} images, saved to {output_file}")
                
            except Exception as e:
                print(f"Error processing batch: {str(e)}")
                # Return the images to pending queue
                self.pending_images = batch + self.pending_images
    
    def run_periodic_tasks(self):
        """Run periodic tasks like scanning for new files and processing small batches."""
        # Scan for new images
        self._scan_for_new_images()
        
        # Process partial batch if it's been waiting too long
        current_time = time.time()
        if self.pending_images and (current_time % 300) < 10:  # Every ~5 minutes
            print("Processing partial batch due to time threshold...")
            self.process_batch(force=True)


@app.command()
def main(
    raw_dir: str = typer.Option("data/raw", "--raw-dir", "-r", help="Directory containing raw images"),
    output_dir: str = typer.Option("data/embeddings", "--output-dir", "-o", help="Directory for embedding output files"),
    processed_dir: Optional[str] = typer.Option(None, "--processed-dir", "-p", help="Directory to move processed images to"),
    batch_size: int = typer.Option(16, "--batch-size", "-b", help="Batch size for processing"),
    model: str = typer.Option("nomic-embed-vision-v1.5", "--model", "-m", help="Nomic embedding model to use"),
    watch_interval: int = typer.Option(30, "--interval", "-i", help="Interval in seconds for directory scans"),
    nomic_mode: NomicMode = typer.Option(NomicMode.LOCAL, "--nomic", help="Nomic mode: 'local' or 'api'")
):
    """
    Process images in batches for the PiDay2025 exhibition.
    
    This script monitors a directory for new images, processes them in batches,
    and generates Nomic Atlas embeddings.
    """
    print(f"Starting batch processor with:")
    print(f"  Raw directory: {raw_dir}")
    print(f"  Output directory: {output_dir}")
    print(f"  Processed directory: {processed_dir}")
    print(f"  Batch size: {batch_size}")
    print(f"  Model: {model}")
    print(f"  Nomic mode: {nomic_mode}")
    
    # Create processor
    processor = ImageBatchProcessor(
        raw_dir=raw_dir,
        output_dir=output_dir,
        processed_dir=processed_dir,
        batch_size=batch_size,
        model_name=model,
        watch_interval=watch_interval,
        nomic_mode=nomic_mode
    )
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(processor, raw_dir, recursive=True)
    observer.start()
    
    try:
        print(f"Watching for images in {raw_dir}")
        while True:
            time.sleep(1)
            processor.run_periodic_tasks()
    except KeyboardInterrupt:
        print("Stopping batch processor...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    app()