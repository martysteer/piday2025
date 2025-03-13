#!/usr/bin/env python3
import argparse
import time
import os
from PIL import Image
from displayhatmini import DisplayHATMini

def parse_arguments():
    parser = argparse.ArgumentParser(description='Display an image on Display HAT Mini')
    parser.add_argument('image', type=str, help='Path to the image file to display')
    orientation_group = parser.add_mutually_exclusive_group()
    orientation_group.add_argument('--portrait', '-p', action='store_true', 
                        help='Display in portrait orientation')
    orientation_group.add_argument('--landscape', '-l', action='store_true', 
                        help='Display in landscape orientation (default)')
    return parser.parse_args()

def resize_image(image, is_portrait=False):
    """Resize image based on orientation while preserving aspect ratio."""
    display_width = DisplayHATMini.WIDTH
    display_height = DisplayHATMini.HEIGHT
    
    if is_portrait:
        # For portrait mode, we'll rotate after resizing
        # Calculate scaling ratios
        width_ratio = display_height / image.width
        height_ratio = display_width / image.height
        ratio = min(width_ratio, height_ratio)
        
        # Resize the image maintaining aspect ratio
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a canvas matching the rotated display dimensions
        result = Image.new("RGB", (display_height, display_width), (0, 0, 0))
        
        # Calculate position to center the image
        x_offset = (display_height - new_width) // 2
        y_offset = (display_width - new_height) // 2
        
        # Paste the resized image centered
        result.paste(resized_image, (x_offset, y_offset))
        
        # Rotate the image for portrait display
        result = result.rotate(90, expand=True)
        
    else:  # landscape mode (default)
        # Calculate scaling ratios
        width_ratio = display_width / image.width
        height_ratio = display_height / image.height
        ratio = min(width_ratio, height_ratio)
        
        # Resize the image maintaining aspect ratio
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a canvas of the display size
        result = Image.new("RGB", (display_width, display_height), (0, 0, 0))
        
        # Calculate position to center the image
        x_offset = (display_width - new_width) // 2
        y_offset = (display_height - new_height) // 2
        
        # Paste the resized image centered
        result.paste(resized_image, (x_offset, y_offset))
    
    return result

def main():
    args = parse_arguments()
    
    # Check if the image file exists
    if not os.path.isfile(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    try:
        # Determine orientation from arguments
        is_portrait = args.portrait
        is_landscape = args.landscape
        
        # Default to landscape if neither specified
        if not is_portrait and not is_landscape:
            is_landscape = True
            
        # Load the image
        image = Image.open(args.image)
        
        # Convert image to RGB mode if it's not already
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Get image dimensions before processing
        print(f"Original image dimensions: {image.width}x{image.height}")
        
        # Determine orientation to use
        orientation = "portrait" if is_portrait else "landscape"
        print(f"Using {orientation} orientation")
        
        # Resize based on selected orientation
        display_image = resize_image(image, is_portrait=is_portrait)
        
        # Initialize the Display HAT Mini with the processed image
        display = DisplayHATMini(display_image)
        
        # Display the image
        display.display()
        
        print(f"Displaying image: {args.image}")
        print("Press Ctrl+C to exit")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()