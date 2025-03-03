#!/bin/bash
# PiDay2025 Pipeline Runner
# This script starts all three components of the PiDay2025 image processing pipeline

# Create required directories
mkdir -p data/raw data/embeddings data/processed

# Start each component in its own terminal window
# Adjust these commands based on your operating system
echo "Starting the PiDay2025 pipeline..."

# On macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  # Start collection tool
  osascript -e 'tell app "Terminal" to do script "cd $(pwd) && python collect_images.py"' 
  
  # Start batch processor
  osascript -e 'tell app "Terminal" to do script "cd $(pwd) && python batch_processor.py --raw-dir data/raw --output-dir data/embeddings --processed-dir data/processed"'
  
  # Start Atlas uploader
  osascript -e 'tell app "Terminal" to do script "cd $(pwd) && python atlas_uploader.py --embeddings-dir data/embeddings"'
  
# On Linux with gnome-terminal
elif [[ "$OSTYPE" == "linux-gnu"* ]] && command -v gnome-terminal &> /dev/null; then
  gnome-terminal -- bash -c "python collect_images.py; exec bash"
  gnome-terminal -- bash -c "python batch_processor.py --raw-dir data/raw --output-dir data/embeddings --processed-dir data/processed; exec bash"
  gnome-terminal -- bash -c "python atlas_uploader.py --embeddings-dir data/embeddings; exec bash"

# On Windows (using start command)
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  start cmd /k "python collect_images.py"
  start cmd /k "python batch_processor.py --raw-dir data/raw --output-dir data/embeddings --processed-dir data/processed"
  start cmd /k "python atlas_uploader.py --embeddings-dir data/embeddings"

# Generic approach (background processes)
else
  echo "Could not detect terminal type, running scripts in background..."
  python collect_images.py &
  python batch_processor.py --raw-dir data/raw --output-dir data/embeddings --processed-dir data/processed &
  python atlas_uploader.py --embeddings-dir data/embeddings &
  echo "Pipeline components started in background. Use 'ps' to check processes."
fi

echo "PiDay2025 pipeline started successfully."
echo "- Image collection: data/raw"
echo "- Processed embeddings: data/embeddings"
echo "- Processed images: data/processed"