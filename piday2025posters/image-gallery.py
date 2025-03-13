#!/usr/bin/env python3
"""
Image Gallery for Display HAT Mini

A feature-rich image gallery application for browsing and viewing 
images on a Raspberry Pi with the Display HAT Mini.

Features:
- Browse through all images in a directory
- Transform images (rotate, flip, change orientation)
- Display image information
- Navigate with intuitive button controls
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
    find_images, 
    overlay_info, 
    clear_display
)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Image Gallery for Display HAT Mini')
    
    parser.add_argument('directory', type=str, nargs='?', default='.',
                        help='Directory containing images to display (default: current directory)')
    
    parser.add_argument('--extensions', '-e', type=str, default='.jpg,.jpeg,.png,.bmp,.gif',
                        help='Comma-separated list of file extensions to include (default: .jpg,.jpeg,.png,.bmp,.gif)')
    
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
    """Main function for the image gallery application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Extract file extensions
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    # Find all images in the specified directory
    image_files = find_images(args.directory, extensions)
    
    if not image_files:
        print(f"No images found in directory: {args.directory}")
        print(f"Supported extensions: {', '.join(extensions)}")
        return
    
    print(f"Found {len(image_files)} images in {args.directory}")
    
    # Initialize display with a blank image
    buffer = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0))
    display = DisplayHATMini(buffer)
    
    # Set display brightness
    brightness = max(0.0, min(1.0, args.brightness))  # Clamp between 0 and 1
    display.set_backlight(brightness)
    
    # Set a subtle LED indicator
    display.set_led(0.1, 0.1, 0.1)
    
    # Initialize state variables
    current_index = 0
    is_portrait = args.portrait
    is_landscape = args.landscape
    
    # Default to landscape if neither specified
    if not is_portrait and not is_landscape:
        is_landscape = True
        is_portrait = False
    
    # Transform settings
    orientation_mode = "portrait" if is_portrait else "landscape"
    rotation_angle = 0
    horizontal_flip = False
    show_info = args.show_info
    
    # Display loading message
    display_info_message(display, "Loading Gallery", f"{len(image_files)} images found")
    time.sleep(1)
    
    # Load and display the first image
    current_image = load_image(image_files[current_index])
    if current_image is None:
        display_info_message(display, "Error", f"Could not load {os.path.basename(image_files[current_index])}")
        time.sleep(2)
        return
    
    # Function to update the current display
    def update_display():
        nonlocal current_image
        
        # Load the current image
        current_image = load_image(image_files[current_index])
        if current_image is None:
            display_info_message(display, "Error", f"Could not load {os.path.basename(image_files[current_index])}")
            time.sleep(1)
            return
        
        # Process the image with current settings
        processed_image = process_image(
            current_image, 
            is_portrait=is_portrait, 
            rotation=rotation_angle, 
            flip_horizontal=horizontal_flip
        )
        
        # Add info overlay if enabled
        if show_info:
            processed_image = overlay_info(
                processed_image, 
                image_files[current_index], 
                current_index, 
                len(image_files),
                is_portrait=is_portrait
            )
        
        # Update the display
        buffer.paste(processed_image)
        display.display()
    
    # Initial display update
    update_display()
    
    # Show instructions
    print("\nButton controls:")
    print("  A: Previous image")
    print("  B: Next image")
    print("  X: Toggle information overlay")
    print("  Y: Hold to access transform menu")
    print("\nPress Ctrl+C to exit")
    
    # Main loop with manual button polling
    try:
        # Track previous button states to detect transitions
        prev_a = False
        prev_b = False
        prev_x = False
        prev_y = False
        y_press_time = 0
        in_transform_menu = False
        
        while True:
            # Read current button states
            curr_a = display.read_button(display.BUTTON_A)
            curr_b = display.read_button(display.BUTTON_B)
            curr_x = display.read_button(display.BUTTON_X)
            curr_y = display.read_button(display.BUTTON_Y)
            
            # Transform menu mode
            if in_transform_menu:
                if curr_a and not prev_a:
                    # Flip horizontally
                    horizontal_flip = not horizontal_flip
                    print(f"Flipping image horizontally: {horizontal_flip}")
                    display.set_led(1, 0, 0)  # Red flash
                    update_display()
                    
                elif curr_b and not prev_b:
                    # Toggle orientation
                    is_portrait = not is_portrait
                    orientation_mode = "portrait" if is_portrait else "landscape"
                    print(f"Switching to {orientation_mode} orientation")
                    display.set_led(0, 1, 0)  # Green flash
                    update_display()
                    
                elif curr_x and not prev_x:
                    # Rotate 90° clockwise
                    rotation_angle = (rotation_angle + 90) % 360
                    print(f"Rotating to {rotation_angle}°")
                    display.set_led(0, 0, 1)  # Blue flash
                    update_display()
                    
                elif curr_y and not prev_y:
                    # Exit transform menu
                    in_transform_menu = False
                    print("Exiting transform menu")
                    display_info_message(display, "Exiting Transform Menu")
                    time.sleep(0.5)
                    update_display()
            
            # Normal gallery navigation mode
            else:
                if curr_a and not prev_a:
                    # Previous image
                    current_index = (current_index - 1) % len(image_files)
                    print(f"Showing previous image: {image_files[current_index]}")
                    display.set_led(1, 0, 0)  # Red flash
                    update_display()
                    
                elif curr_b and not prev_b:
                    # Next image
                    current_index = (current_index + 1) % len(image_files)
                    print(f"Showing next image: {image_files[current_index]}")
                    display.set_led(0, 1, 0)  # Green flash
                    update_display()
                    
                elif curr_x and not prev_x:
                    # Toggle info overlay
                    show_info = not show_info
                    print(f"Image info overlay: {show_info}")
                    display.set_led(0, 0, 1)  # Blue flash
                    update_display()
                
                # Check for long press on Y button
                if curr_y and not y_press_time:
                    y_press_time = time.time()
                    display.set_led(0.5, 0.5, 0)  # Yellow for press indication
                
                elif curr_y and y_press_time and time.time() - y_press_time > 1.0:
                    # Long press detected (>1 second)
                    in_transform_menu = True
                    y_press_time = 0
                    display.set_led(1, 1, 0)  # Bright yellow
                    display_info_message(display, "Transform Menu",
                                        "A: Flip | B: Orientation | X: Rotate | Y: Exit")
                    time.sleep(1.5)
                    
                elif not curr_y and y_press_time:
                    # Button released before long press threshold
                    y_press_time = 0
                    display.set_led(0.1, 0.1, 0.1)  # Reset to subtle indicator
            
            # Update previous button states
            prev_a = curr_a
            prev_b = curr_b
            prev_x = curr_x
            prev_y = curr_y
            
            # Reset LED to subtle indicator after actions
            if not curr_y or not y_press_time:
                display.set_led(0.1, 0.1, 0.1)
            
            # Short delay to prevent CPU hogging
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        
    finally:
        # Clean up
        clear_display(display)

if __name__ == "__main__":
    main()
