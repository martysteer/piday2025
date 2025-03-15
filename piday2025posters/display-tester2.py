#!/usr/bin/env python3
import argparse
import time
from PIL import Image, ImageDraw

try:
    # from displayhatmini import DisplayHATMini  ## orginal
    from displayhatproxy import DisplayHATMini   ## proxy wrapper
except ImportError:
    print("Error: Could not import DisplayHATMini. Make sure displayhatproxy.py is in the same directory.")
    exit(1)


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
            display.process_events()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()