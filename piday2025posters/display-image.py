#!/usr/bin/env python3
import argparse
import time
import os
from PIL import Image
from displayhatmini import DisplayHATMini

def parse_arguments():
    parser = argparse.ArgumentParser(description='Display an image on Display HAT Mini')
    parser.add_argument('image', type=str, help='Path to the image file to display')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Check if the image file exists
    if not os.path.isfile(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    try:
        # Load the image
        image = Image.open(args.image)
        
        # Resize the image to fit the display if needed
        if image.width != DisplayHATMini.WIDTH or image.height != DisplayHATMini.HEIGHT:
            print(f"Resizing image from {image.width}x{image.height} to {DisplayHATMini.WIDTH}x{DisplayHATMini.HEIGHT}")
            image = image.resize((DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), Image.Resampling.LANCZOS)
        
        # Convert image to RGB mode if it's not already
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Initialize the Display HAT Mini
        display = DisplayHATMini(image)
        
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