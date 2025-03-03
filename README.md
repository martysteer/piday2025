# PiDay2025 Image Collection & Embedding Project

## Project Overview
This project creates a pipeline to collect and process user-submitted images during the PiDay2025 exhibition. The system will:

1. Collect images from approximately 40 participants
2. Process images in batches as participants leave
3. Generate embeddings using Nomic Atlas
4. Upload the embeddings to Nomic Atlas for visualization
5. Provide a real-time incremental processing system

## Setup Instructions

### Environment Setup

1. **Clone the Repository**
   ```bash
   git clone <your-github-repo-url>
   cd piday2025
   ```

2. **Set Up Python Environment**
   ```bash
   # Using pyenv (recommended)
   pyenv install 3.10.16
   pyenv virtualenv 3.10.16 piday2025
   pyenv local piday2025
   
   # Trust certificates for package installs
   pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Authenticate with Nomic Atlas**
   ```bash
   nomic login nk-lQO-NJQXEPXmXyNc1p97qloFUhtBHSI-j9SwFOUQZC0
   ```

### Project Structure

Create the following directory structure:
```
piday2025/
├── image_to_nomic.py        # Existing script for embedding generation
├── requirements.txt         # Dependency list
├── .python-version          # Python version file
├── collect_images.py        # New script for image collection (to be created)
├── batch_processor.py       # New script for batch processing (to be created)
├── atlas_uploader.py        # New script for Atlas uploading (to be created)
├── data/
│   ├── raw/                 # Directory for collected raw images
│   ├── processed/           # Directory for processed image data
│   └── embeddings/          # Directory for generated embeddings
└── ui/                      # Simple UI for image collection (optional)
```

## Implementation Plan

### 1. Image Collection System

Create a simple image collection system that:
- Assigns a unique ID to each participant
- Collects a set of images from each participant
- Stores metadata (timestamp, participant info, etc.)
- Organizes images in the `data/raw/` directory

#### Key Features:
- Create subdirectories for each participant
- Generate a manifest file with participant metadata
- Implement simple validation to ensure image quality

### 2. Batch Processing System

Modify the existing `image_to_nomic.py` script or create a new `batch_processor.py` that:
- Watches the `data/raw/` directory for new images
- Processes images in batches as they accumulate
- Generates embeddings using Nomic's API
- Saves embeddings to the `data/embeddings/` directory

#### Implementation Details:
```python
# Example batch_processor.py structure
import os
import time
import json
from pathlib import Path
import typer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from image_to_nomic import process_images_batch, find_image_files, save_jsonl

class ImageBatchProcessor(FileSystemEventHandler):
    def __init__(self, raw_dir, output_dir, batch_size=16, model_name="nomic-embed-vision-v1.5"):
        self.raw_dir = Path(raw_dir)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.model_name = model_name
        self.pending_images = []
        self.processed_images = set()
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def on_created(self, event):
        if event.is_directory:
            return
        if any(event.src_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            self.pending_images.append(event.src_path)
            self.process_pending_if_needed()
    
    def process_pending_if_needed(self):
        if len(self.pending_images) >= self.batch_size:
            self.process_batch()
    
    def process_batch(self):
        # Get next batch
        batch = self.pending_images[:self.batch_size]
        self.pending_images = self.pending_images[self.batch_size:]
        
        # Process images
        timestamp = int(time.time())
        output_file = self.output_dir / f"batch_{timestamp}.jsonl"
        
        # Use the existing image_to_nomic functionality
        results = process_images_batch(
            batch, 
            self.batch_size, 
            self.model_name,
            include_metadata=True
        )
        
        # Save results
        save_jsonl(results, str(output_file))
        
        # Update processed images
        self.processed_images.update(batch)
        print(f"Processed batch of {len(batch)} images, saved to {output_file}")

def main():
    # Set up directories
    raw_dir = "data/raw"
    output_dir = "data/embeddings"
    
    # Create processor
    processor = ImageBatchProcessor(raw_dir, output_dir)
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(processor, raw_dir, recursive=True)
    observer.start()
    
    try:
        print(f"Watching for images in {raw_dir}")
        while True:
            time.sleep(1)
            # Periodically process any remaining images even if batch size not reached
            if processor.pending_images and (time.time() % 60) < 1:
                processor.process_batch()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

### 3. Atlas Uploading System

Create an `atlas_uploader.py` script that:
- Watches the `data/embeddings/` directory for new JSONL files
- Uploads embeddings to Nomic Atlas
- Updates a single Nomic Atlas map incrementally
- Provides status updates on the upload process

#### Implementation Details:
```python
# Example atlas_uploader.py structure
import os
import time
import json
from pathlib import Path
import typer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from nomic import atlas

class AtlasUploader(FileSystemEventHandler):
    def __init__(self, embeddings_dir, map_id=None, map_name="PiDay2025"):
        self.embeddings_dir = Path(embeddings_dir)
        self.map_id = map_id
        self.map_name = map_name
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.jsonl'):
            self.upload_file(event.src_path)
    
    def upload_file(self, filepath):
        if filepath in self.processed_files:
            return
            
        print(f"Uploading {filepath} to Atlas...")
        
        # Load embeddings from JSONL
        embeddings = []
        data = []
        with open(filepath, 'r') as f:
            for line in f:
                record = json.loads(line)
                embeddings.append(record['embedding'])
                
                # Extract metadata for data field
                metadata = record.get('metadata', {})
                data.append({
                    'id': record['id'],
                    'filename': metadata.get('filename', ''),
                    'filepath': metadata.get('filepath', ''),
                    'created': metadata.get('created', ''),
                })
        
        try:
            # Create or update Atlas map
            if self.map_id is None:
                # First upload - create new map
                result = atlas.map_data(
                    embeddings=embeddings,
                    data=data,
                    name=self.map_name,
                    description="PiDay2025 Exhibition Images"
                )
                self.map_id = result.id
                print(f"Created new Atlas map with ID: {self.map_id}")
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
            print(f"Error uploading to Atlas: {str(e)}")

def main():
    # Set up directories
    embeddings_dir = "data/embeddings"
    
    # Create uploader (pass map_id if resuming an existing map)
    uploader = AtlasUploader(embeddings_dir)
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(uploader, embeddings_dir)
    observer.start()
    
    try:
        print(f"Watching for embedding files in {embeddings_dir}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

## Event Workflow

1. **Before the Exhibition**
   - Set up all systems and test the complete pipeline
   - Create a test Atlas map to ensure everything works
   - Prepare the image collection interface
   - Set up backup systems for reliability

2. **During the Exhibition**
   - For each participant:
     - Assign a unique ID
     - Collect images (camera setup or upload station)
     - Store images in `data/raw/{participant_id}/`
   - The batch processor will automatically:
     - Detect new images
     - Process them in batches
     - Generate embeddings
   - The Atlas uploader will automatically:
     - Detect new embedding files
     - Upload them to Nomic Atlas
     - Update the exhibition map

3. **After Each Batch of Participants**
   - Verify that images were processed correctly
   - Check that embeddings were uploaded to Atlas
   - Show participants their images on the Atlas map

4. **After the Exhibition**
   - Process any remaining images
   - Finalize the Atlas map
   - Generate a final report of all processed images

## Additional Considerations

### Performance Optimization
- Adjust batch sizes based on available hardware
- Use GPU acceleration if available
- Consider distributed processing for larger events

### Error Handling
- Implement robust error handling and recovery
- Set up logging for all operations
- Create backup procedures for critical failures

### User Experience
- Develop a simple UI for participants to see their images on the map
- Consider creating a QR code that participants can scan to view the map
- Add real-time status displays showing processing progress

### Security and Privacy
- Implement proper data handling practices
- Consider adding consent forms for image collection
- Sanitize filenames and metadata

## Technical Requirements

- Python 3.10 or newer
- Nomic API access
- Sufficient storage for raw and processed images
- Internet connection for API calls
- Optional: GPU for faster processing

## Command Reference

```bash
# Start the image collection system
python collect_images.py

# Start the batch processor (watches raw directory)
python batch_processor.py

# Start the Atlas uploader (watches embeddings directory)
python atlas_uploader.py

# Process a specific directory manually
python image_to_nomic.py --input-dir data/raw/specific_batch --output-file data/embeddings/manual_batch.jsonl
```

By running these three scripts simultaneously, you'll have a complete pipeline that:
1. Collects images from participants
2. Processes them in batches
3. Generates embeddings
4. Uploads them to Nomic Atlas

This system will handle the ~40 participants incrementally throughout your event.