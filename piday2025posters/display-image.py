#!/usr/bin/env python3
"""
Display Image for Display HAT Mini

A simple image viewer application that displays a single image
on a Raspberry Pi with the Display HAT Mini, with options to
transform the image (rotate, flip, change orientation).
"""

import argparse
import time
import os
import sys
from PIL import Image
from displayhatmini import DisplayHATMini

# Import the shared utility functions
from display_hat_utils import (
    process_image, 
    display_info_message, 
    load_image, 
    overlay_info, 
    clear_display
)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Display an image on Display HAT Mini')
    
    parser.add_argument('image', type=str, help='Path to the image file to display')
    
    orientation_group = parser.add_mutually_exclusive_group()
    orientation_group.add_argument('--portrait', '-p', action='store_true', 
                        help='Display in portrait orientation')
    orientation_group.add_argument('--landscape', '-l', action='store_true', 
                        help='Display in landscape orientation (default)')
    
    parser.add_argument('--show-info', '-i', action='store_true', default=True,
                        help='Show image information overlay (default)')
    parser.add_argument('--no-info', action='store_false', dest='show_info',
                        help='Hide image information overlay')
    
    parser.add_argument('--brightness', '-b', type=float, default=1.0,
                        help='Screen brightness level 0.0-1.0 (default: 1.0)')
    
    return parser.parse_args()

def main():
    """Main function for the image display application."""
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
            is_portrait = False
            
        # Initialize display with a blank image
        buffer = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0))
        display = DisplayHATMini(buffer)
        
        # Set display brightness
        brightness = max(0.0, min(1.0, args.brightness))  # Clamp between 0 and 1
        display.set_backlight(brightness)
        
        # Set a subtle LED indicator
        display.set_led(0.1, 0.1, 0.1)
        
        # Initialize transformation state
        orientation_mode = "portrait" if is_portrait else "landscape"
        rotation_angle = 0
        horizontal_flip = False
        show_info = args.show_info
        
        # Display loading message
        display_info_message(display, "Loading Image", os.path.basename(args.image))
        time.sleep(0.5)  # Brief delay to ensure message is visible
        
        # Load the image
        original_image = load_image(args.image)
        if original_image is None:
            display_info_message(display, "Error", f"Could not load {os.path.basename(args.image)}")
            time.sleep(2)
            return
            
        # Get image dimensions before processing
        print(f"Original image dimensions: {original_image.width}x{original_image.height}")
        
        # Function to update the displayed image with current settings
        def update_display():
            # Process image with current settings
            processed_image = process_image(
                original_image, 
                is_portrait=is_portrait, 
                rotation=rotation_angle, 
                flip_horizontal=horizontal_flip
            )
            
            # Add info overlay if enabled
            if show_info:
                processed_image = overlay_info(
                    processed_image, 
                    args.image, 
                    0, 
                    1,
                    is_portrait=is_portrait
                )
            
            # Update the display
            buffer.paste(processed_image)
            display.display()
        
        # Display the initial image
        update_display()
        
        # Show initial status
        print(f"Displaying image: {args.image}")
        print(f"Initial settings: orientation={orientation_mode}, rotation={rotation_angle}°, flipped={horizontal_flip}")
        print("\nButton controls:")
        print("  A: Flip image horizontally")
        print("  B: Toggle between portrait/landscape orientation")
        print("  X: Rotate image 90° clockwise")
        print("  Y: Toggle info overlay")
        print("\nPress Ctrl+C to exit")
        
        # Main loop with manual button polling
        try:
            # Track previous button states to detect transitions
            prev_a = False
            prev_b = False
            prev_x = False
            prev_y = False
            
            while True:
                # Read current button states
                curr_a = display.read_button(display.BUTTON_A)
                curr_b = display.read_button(display.BUTTON_B)
                curr_x = display.read_button(display.BUTTON_X)
                curr_y = display.read_button(display.BUTTON_Y)
                
                # Check for button presses (transitions from not pressed to pressed)
                if curr_a and not prev_a:
                    # A: Flip image horizontally
                    horizontal_flip = not horizontal_flip
                    print(f"Flipping image horizontally: {horizontal_flip}")
                    display.set_led(1, 0, 0)  # Red flash
                    update_display()
                    
                if curr_b and not prev_b:
                    # B: Toggle orientation
                    is_portrait = not is_portrait
                    orientation_mode = "portrait" if is_portrait else "landscape"
                    print(f"Switching to {orientation_mode} orientation")
                    display.set_led(0, 1, 0)  # Green flash
                    update_display()
                    
                if curr_x and not prev_x:
                    # X: Rotate 90° clockwise
                    rotation_angle = (rotation_angle + 90) % 360
                    print(f"Rotating to {rotation_angle}°")
                    display.set_led(0, 0, 1)  # Blue flash
                    update_display()
                    
                if curr_y and not prev_y:
                    # Y: Toggle info overlay
                    show_info = not show_info
                    print(f"Info overlay: {show_info}")
                    display.set_led(1, 0, 1)  # Purple flash
                    update_display()
                
                # Update previous button states
                prev_a = curr_a
                prev_b = curr_b
                prev_x = curr_x
                prev_y = curr_y
                
                # Reset LED to subtle indicator after flash
                if not (curr_a or curr_b or curr_x or curr_y):
                    display.set_led(0.1, 0.1, 0.1)
                
                # Short delay to prevent CPU hogging
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            
    except Exception as e:
        print(f"Error: {e}")
        
        # Try to display error message on the screen if display is initialized
        try:
            if 'display' in locals():
                display_info_message(display, "Error", str(e))
                display.set_led(1, 0, 0)  # Red LED to indicate error
                time.sleep(5)  # Show error for 5 seconds
        except:
            pass
            
    finally:
        # Clean up if display was initialized
        if 'display' in locals():
            clear_display(display)

if __name__ == "__main__":
    main()