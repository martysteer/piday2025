# PiDay2025 Image Embedding Pipeline

A simplified pipeline for processing images and generating Nomic Atlas embeddings for the PiDay2025 exhibition.

## Overview

This project provides two main scripts:

1. `process_images.py` - Converts images to embeddings
2. `upload_to_atlas.py` - Uploads embeddings to Nomic Atlas

The workflow is simple:
- Place your images in the `data/images` directory
- Run the processing script to generate embeddings
- Run the upload script to create or update an Atlas map

## Setup

### Environment Setup

```bash
# Using pyenv (recommended)
pyenv install 3.10.16
pyenv virtualenv 3.10.16 piday2025
pyenv local piday2025

# Install dependencies
pip install -r requirements.txt

# Authenticate with Nomic Atlas
nomic login nk-lQO-NJQXEPXmXyNc1p97qloFUhtBHSI-j9SwFOUQZC0
```

### Directory Structure

```
piday2025/
├── process_images.py      # Script to process images into embeddings
├── upload_to_atlas.py     # Script to upload embeddings to Atlas
├── requirements.txt       # Dependencies
├── .python-version        # Python version for pyenv
└── data/
    ├── images/            # Raw images go here
    └── embeddings/        # Generated embeddings stored here
```

## Usage

### 1. Process Images

```bash
# Process all new images in the images directory
python process_images.py

# Specify custom directories
python process_images.py --image-dir path/to/images --output-dir path/to/embeddings

# Process in smaller batches (e.g., 8 images at a time)
python process_images.py --batch-size 8

# Use the Nomic API instead of local processing
python process_images.py --use-api

# Force reprocessing of all images
python process_images.py --force
```

### 2. Upload to Atlas

```bash
# Upload embeddings to a new Atlas map
python upload_to_atlas.py

# Update an existing Atlas map
python upload_to_atlas.py --map-id your-map-id

# Create a new map with a custom name
python upload_to_atlas.py --map-name "My PiDay Images" --new-map
```

## Exhibition Workflow

1. **Before the Exhibition**:
   - Set up the environment
   - Test the pipeline with sample images

2. **During the Exhibition**:
   - Collect participant images in the `data/images` directory
   - Run `process_images.py` after collecting each batch of images
   - Run `upload_to_atlas.py` to update the Atlas map

3. **After the Exhibition**:
   - Process any remaining images
   - Make a final upload to Atlas

## Notes

- The scripts will automatically create the necessary directories
- Only new images are processed, making it safe to run the processing script multiple times
- The Atlas map ID is saved in `data/embeddings/atlas_info.json` for future updates
- Local processing is used by default (faster with GPU), but API processing is available
- The Atlas URL will be displayed after uploading