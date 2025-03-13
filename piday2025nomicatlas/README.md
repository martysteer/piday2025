# PiDay2025 Image Embeddings

A simple tool to upload images to Nomic Atlas for the PiDay2025 exhibition.

## Setup

```bash
# Set up Python environment
pyenv install 3.10.16
pyenv virtualenv 3.10.16 piday2025
pyenv local piday2025

# Install dependencies
pip install -r requirements.txt

# Authenticate with Nomic
nomic login nk-XXXXXX
```

## Usage

1. **Upload Images**:
   ```bash
   python simple_upload_to_atlas.py --image-dir data/images
   ```

2. **Options**:
   ```
   --image-dir DIR   # Directory with images (default: data/images)
   --map-name NAME   # Atlas map name (default: PiDay2025)
   --batch-size N    # Upload batch size (default: 20)
   --new-map         # Force creation of a new map
   ```

3. **View your map**: After uploading, a URL will be provided to view your Atlas map.

## Notes

- Images are tracked to avoid duplicates
- The script automatically organizes images based on folder structure
- Atlas map/dataset details are saved for future updates