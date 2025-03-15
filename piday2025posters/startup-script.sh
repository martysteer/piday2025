#!/bin/bash

# Display HAT Mini Image Gallery startup script
# Save this as /home/pi/piday2025/piday2025posters/startup-script.sh

# Path to the script directory - adjust if needed
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
IMAGE_DIR="${SCRIPT_DIR}/images"

# Configuration - align with image-gallery.py options
DELAY=3.0                 # Time in seconds between slides
TRANSITION="glitch"       # none, fade, or slide
SORT="name"               # name, date, size, random
ORIENTATION="portrait"    # landscape or portrait
SHOW_INFO=false           # true to show image info, false to hide it

# Log file for debugging
LOG_FILE="${SCRIPT_DIR}/gallery.log"

# Create image directory if it doesn't exist
mkdir -p "$IMAGE_DIR"

# Log startup information
echo "$(date): Starting Display HAT Mini Gallery" > "$LOG_FILE"
echo "Image directory: $IMAGE_DIR" >> "$LOG_FILE"
echo "Number of images: $(ls -1 "$IMAGE_DIR" | wc -l)" >> "$LOG_FILE"

# Create a message to display if there are no images
if [ ! "$(ls -A $IMAGE_DIR)" ]; then
    echo "No images found in gallery directory." >> "$LOG_FILE"
    echo "Please add some images to $IMAGE_DIR"
fi

# Build the command with appropriate arguments
CMD="python3 ${SCRIPT_DIR}/image-gallery.py"
CMD="$CMD '$IMAGE_DIR'"
CMD="$CMD --delay $DELAY"
CMD="$CMD --transition $TRANSITION"
CMD="$CMD --sort $SORT"
CMD="$CMD --slideshow"  # Start in slideshow mode

# Add options based on configuration
if [ "$ORIENTATION" == "portrait" ]; then
    CMD="$CMD --portrait"
else
    CMD="$CMD --landscape"
fi

if [ "$SHOW_INFO" == false ]; then
    CMD="$CMD --no-info"
fi

# Log the command we're running
echo "Command: $CMD" >> "$LOG_FILE"

# Run the image gallery script
cd "$SCRIPT_DIR"
eval "$CMD" >> "$LOG_FILE" 2>&1
