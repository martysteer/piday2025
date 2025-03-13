#!/usr/bin/env python3
import argparse
import time
import os
from PIL import Image
from displayhatmini import DisplayHATMini

def parse_arguments():
    parser = argparse.ArgumentParser(description='Display an image on Display HAT Mini with orientation control')
    parser.add_argument('image', type=str, help='Path to the image file to display')
    parser.add_argument('--orientation', '-o', type=str, choices=['landscape', 'portrait'], 
                        default='landscape', help='Display orientation (landscape or portrait)')
    return parser.parse_args()

def resize_with_orientation(image, orientation):
    """
    Resize image based on the specified orientation.
    
    For landscape: image is resized to fit the display's width and height
    For portrait: image is rotated 90 degrees and then resized to fit
    """
    display_width = DisplayHATMini.WIDTH
    display_height = DisplayHATMini.HEIGHT
    
    if orientation == 'portrait':
        # Swap width and height for portrait mode
        target_width = display_height
        target_height = display_width
        
        # Calculate scaling ratios
        width_ratio = target_width / image.width
        height_ratio = target_height / image.height
        ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions while maintaining aspect ratio
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        # Resize the image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a new blank image with the target dimensions
        result = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        
        # Calculate centering position
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        # Paste the resized image onto the blank image
        result.paste(resized_image, (x_offset, y_offset))
        
        # Rotate the image for portrait display
        result = result.rotate(90, expand=True)
        
    else:  # landscape mode
        # Calculate scaling ratios
        width_ratio = display_width / image.width
        height_ratio = display_height / image.height
        ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions while maintaining aspect ratio
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        # Resize the image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a new blank image with the display dimensions
        result = Image.new("RGB", (display_width, display_height), (0, 0, 0))
        
        # Calculate centering position
        x_offset = (display_width - new_width) // 2
        y_offset = (display_height - new_height) // 2
        
        # Paste the resized image onto the blank image
        result.paste(resized_image, (x_offset, y_offset))
    
    return result

def main():
    args = parse_arguments()
    
    # Check if the image file exists
    if not os.path.isfile(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    try:
        # Load the image
        image = Image.open(args.image)
        
        # Convert image to RGB mode if it's not already
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize the image according to the orientation
        print(f"Original image dimensions: {image.width}x{image.height}")
        print(f"Using {args.orientation} orientation")
        
        resized_image = resize_with_orientation(image, args.orientation)
        print(f"Resized image dimensions: {resized_image.width}x{resized_image.height}")
        
        # Initialize the Display HAT Mini
        display = DisplayHATMini(resized_image)
        
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
