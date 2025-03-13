#!/bin/bash

# Display HAT Mini Slideshow startup script
# Save this as /home/pi/start_slideshow.sh

# Configuration - you can modify these settings
IMAGE_DIR="/home/pi/slideshow_images"
DELAY=10
TRANSITION="fade"  # none, fade, or slide
RANDOM=true        # true for random order, false for alphabetical
BRIGHTNESS=1.0     # 0.0 to 1.0
SHOW_INFO=true     # true to show image info, false to hide it

# Create image directory if it doesn't exist
mkdir -p "$IMAGE_DIR"

# Create a message to display if there are no images
if [ ! "$(ls -A $IMAGE_DIR)" ]; then
    echo "No images found in slideshow directory."
    echo "Please add some images to $IMAGE_DIR"
fi

# Build the command with appropriate arguments
CMD="python3 /home/pi/photo_slideshow.py"
CMD="$CMD --dir $IMAGE_DIR"
CMD="$CMD --delay $DELAY"
CMD="$CMD --transition $TRANSITION"
CMD="$CMD --brightness $BRIGHTNESS"

# Add optional arguments based on configuration
if [ "$RANDOM" = true ]; then
    CMD="$CMD --random"
else
    CMD="$CMD --no-random"
fi

if [ "$SHOW_INFO" = false ]; then
    CMD="$CMD --hide-info"
fi

# Log the command we're running
echo "Starting slideshow with command:"
echo "$CMD"

# Run the slideshow script
cd /home/pi
$CMD

