#!/usr/bin/env python3
import argparse
import time
import os
from PIL import Image, ImageOps
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
        original_image = Image.open(args.image)
        
        # Convert image to RGB mode if it's not already
        if original_image.mode != "RGB":
            original_image = original_image.convert("RGB")
        
        # Initial resize according to orientation
        print(f"Original image dimensions: {original_image.width}x{original_image.height}")
        print(f"Using {args.orientation} orientation")
        
        # Keep track of image transformations
        is_flipped = False
        rotation = 0
        current_orientation = args.orientation
        
        # Create buffer for the display
        buffer = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0))
        
        # Initialize the Display HAT Mini
        display = DisplayHATMini(buffer)
        
        # Function to update the display with current image state
        def update_display():
            # Apply transformations
            img = original_image.copy()
            
            # Apply rotation
            if rotation != 0:
                img = img.rotate(rotation, expand=True)
            
            # Apply flip
            if is_flipped:
                img = ImageOps.mirror(img)
            
            # Resize with orientation
            resized_img = resize_with_orientation(img, current_orientation)
            
            # Update the buffer
            buffer.paste(resized_img)
            
            # Update the display
            display.display()
            
            # Print the current state
            print(f"Image state: rotation={rotation}°, flipped={is_flipped}, orientation={current_orientation}")
        
        # Button callback function
        def button_callback(pin):
            nonlocal is_flipped, rotation, current_orientation
            
            # Only handle button presses (not releases)
            if not display.read_button(pin):
                return
            
            if pin == display.BUTTON_A:
                print("Button A pressed: Flipping image")
                is_flipped = not is_flipped
                update_display()
                
            elif pin == display.BUTTON_B:
                print("Button B pressed: Resetting transformations")
                is_flipped = False
                rotation = 0
                update_display()
                
            elif pin == display.BUTTON_X:
                print("Button X pressed: Rotating 90 degrees clockwise")
                rotation = (rotation + 90) % 360
                update_display()
                
            elif pin == display.BUTTON_Y:
                print("Button Y pressed: Toggling orientation")
                current_orientation = 'portrait' if current_orientation == 'landscape' else 'landscape'
                update_display()
        
        # Register button handler
        display.on_button_pressed(button_callback)
        
        # Set LED to indicate the program is running
        display.set_led(0.1, 0.1, 0.1)
        
        # Initial display update
        update_display()
        
        print(f"Displaying image: {args.image}")
        print("Button controls:")
        print("  A: Flip image horizontally")
        print("  B: Reset all transformations")
        print("  X: Rotate image 90° clockwise")
        print("  Y: Toggle between landscape/portrait orientation")
        print("Press Ctrl+C to exit")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            # Turn off LED before exiting
            display.set_led(0, 0, 0)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
