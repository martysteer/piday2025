#!/usr/bin/env python3
import argparse
import time
import platform
import os
from PIL import Image, ImageDraw

def parse_arguments():
    parser = argparse.ArgumentParser(description='Display a colored square on Display HAT Mini')
    parser.add_argument('--size', type=str, default='320x240',
                        help='Size of the square in WxH format (default: 320x240)')
    parser.add_argument('--color', type=str, default='FF52DA',
                        help='Color of the square in hex format (default: FF52DA)')
    return parser.parse_args()

def hex_to_rgb(hex_color):
    # Remove the '#' if it exists
    hex_color = hex_color.lstrip('#')
    
    # Convert the hex color to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def main():
    args = parse_arguments()
    
    # Import the appropriate display HAT library based on platform
    if platform.system() == "Darwin":  # macOS
        # Check if proxydisplayhatmini is available
        try:
            from proxydisplayhatmini import DisplayHATMini
            print("Using proxy DisplayHATMini implementation for macOS")
        except ImportError:
            print("Error: proxydisplayhatmini.py not found in current directory.")
            print("Please make sure the file is in the same directory as this script.")
            return
    else:  # Raspberry Pi or other Linux system
        try:
            from displayhatmini import DisplayHATMini
        except ImportError:
            print("Error: Display HAT Mini library not found. Please install it with:")
            print("sudo pip3 install displayhatmini")
            return
    
    # Parse the size argument
    try:
        width, height = map(int, args.size.split('x'))
    except ValueError:
        print("Error: Size should be in the format WxH (e.g., 320x240)")
        return
    
    # Parse the color argument
    try:
        color = hex_to_rgb(args.color)
    except ValueError:
        print("Error: Color should be a valid hex color code (e.g., FF52DA)")
        return
    
    # Create a buffer for the display
    buffer = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT))
    draw = ImageDraw.Draw(buffer)
    
    # Initialize the Display HAT Mini
    display = DisplayHATMini(buffer)
    
    # Set a subtle LED indicator
    display.set_led(0.1, 0.1, 0.1)
    
    # Calculate the position to center the square
    x_offset = (DisplayHATMini.WIDTH - width) // 2
    y_offset = (DisplayHATMini.HEIGHT - height) // 2
    
    # Draw the square
    draw.rectangle(
        (x_offset, y_offset, x_offset + width, y_offset + height),
        fill=color
    )
    
    # Display the image
    display.display()
    
    print(f"Displaying a {width}x{height} square with color #{args.color}")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            # For macOS version, we need to regularly call display() to process events
            if platform.system() == "Darwin":
                display.display()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
