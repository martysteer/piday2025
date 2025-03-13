#!/usr/bin/env python3
"""
Enhanced Image Gallery for Display HAT Mini

A feature-rich image gallery application for browsing and viewing 
images on a Raspberry Pi with the Display HAT Mini.

Features:
- Browse through all images in a directory
- Automatic slideshow mode with configurable timing
- Image transitions (fade, slide)
- Sort images by name, date, or size
- Transform images (rotate, flip, change orientation)
- Display image information
- Navigate with intuitive button controls
- Settings menu for configuration
"""

import argparse
import time
import os
import sys
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

# Global constants
FADE_STEPS = 10
SLIDE_STEPS = 15
MENU_TIMEOUT = 10  # Seconds before menu auto-closes

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Enhanced Image Gallery for Display HAT Mini')
    
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
    
    parser.add_argument('--slideshow', '-s', action='store_true',
                        help='Start in slideshow mode')
    
    parser.add_argument('--delay', '-d', type=float, default=5.0,
                        help='Slideshow delay in seconds (default: 5.0)')
    
    parser.add_argument('--transition', '-t', choices=['none', 'fade', 'slide'], default='none',
                        help='Transition effect between images (default: none)')
    
    parser.add_argument('--sort', choices=['name', 'date', 'size', 'random'], default='name',
                        help='Image sorting method (default: name)')
    
    return parser.parse_args()

def get_sorted_images(image_files, sort_method):
    """Sort image files based on the specified method."""
    if sort_method == 'name':
        return sorted(image_files)
    elif sort_method == 'date':
        return sorted(image_files, key=lambda x: os.path.getmtime(x))
    elif sort_method == 'size':
        return sorted(image_files, key=lambda x: os.path.getsize(x))
    elif sort_method == 'random':
        files = image_files.copy()
        random.shuffle(files)
        return files
    else:
        return sorted(image_files)  # Default to name

def transition_effect(display, current_image, next_image, effect='none'):
    """Apply transition effect between images."""
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    
    if effect == 'none':
        # Just display the next image
        display.buffer.paste(next_image)
        display.display()
        return
    
    elif effect == 'fade':
        # Apply fade transition
        for step in range(FADE_STEPS + 1):
            alpha = step / FADE_STEPS
            blended = Image.blend(current_image, next_image, alpha)
            display.buffer.paste(blended)
            display.display()
            time.sleep(0.02)  # Short delay between steps
    
    elif effect == 'slide':
        # Apply slide transition (from right to left)
        for step in range(SLIDE_STEPS + 1):
            offset = int((width * (SLIDE_STEPS - step)) / SLIDE_STEPS)
            composite = Image.new("RGB", (width, height))
            composite.paste(current_image, (-offset, 0))
            composite.paste(next_image, (width - offset, 0))
            display.buffer.paste(composite)
            display.display()
            time.sleep(0.02)  # Short delay between steps

def draw_settings_menu(display, options, selected_index, title="Settings Menu"):
    """Draw the settings menu on the display."""
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    
    # Create a new image for the menu
    menu_image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(menu_image)
    
    # Try to load a font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        menu_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except IOError:
        title_font = ImageFont.load_default()
        menu_font = ImageFont.load_default()
    
    # Draw menu title
    draw.rectangle((0, 0, width, 24), fill=(40, 40, 100))
    draw.text((10, 4), title, fill=(255, 255, 255), font=title_font)
    
    # Draw menu options
    option_height = 25
    start_y = 30
    
    for i, (option_name, option_value) in enumerate(options):
        bg_color = (60, 60, 80) if i == selected_index else (20, 20, 40)
        draw.rectangle((0, start_y + i * option_height, width, start_y + (i + 1) * option_height), fill=bg_color)
        
        # Draw option name and value
        draw.text((10, start_y + i * option_height + 5), f"{option_name}:", fill=(255, 255, 255), font=menu_font)
        draw.text((width - 10 - len(str(option_value)) * 7, start_y + i * option_height + 5), 
                  str(option_value), fill=(200, 200, 255), font=menu_font)
    
    # Draw button guide at bottom
    guide_y = height - 30
    draw.rectangle((0, guide_y, width, height), fill=(40, 40, 60))
    draw.text((10, guide_y + 8), "A:↑", fill=(255, 255, 255), font=menu_font)
    draw.text((60, guide_y + 8), "B:↓", fill=(255, 255, 255), font=menu_font) 
    draw.text((110, guide_y + 8), "X:Change", fill=(255, 255, 255), font=menu_font)
    draw.text((210, guide_y + 8), "Y:Exit", fill=(255, 255, 255), font=menu_font)
    
    # Display the menu
    display.buffer.paste(menu_image)
    display.display()

def change_setting_value(setting_type, current_value, direction=1):
    """Change a setting value based on its type."""
    if setting_type == "bool":
        return not current_value
    elif setting_type == "orientation":
        return "landscape" if current_value == "portrait" else "portrait"
    elif setting_type == "transition":
        transitions = ["none", "fade", "slide"]
        current_index = transitions.index(current_value)
        new_index = (current_index + direction) % len(transitions)
        return transitions[new_index]
    elif setting_type == "sort":
        sort_methods = ["name", "date", "size", "random"]
        current_index = sort_methods.index(current_value)
        new_index = (current_index + direction) % len(sort_methods)
        return sort_methods[new_index]
    elif setting_type == "float":
        # For slideshow delay, increase/decrease by 0.5
        new_value = current_value + (0.5 * direction)
        return max(1.0, min(15.0, new_value))  # Clamp between 1 and 15 seconds
    elif setting_type == "brightness":
        # For brightness, increase/decrease by 0.1
        new_value = current_value + (0.1 * direction)
        return max(0.1, min(1.0, new_value))  # Clamp between 0.1 and 1.0
    else:
        return current_value

def settings_menu(display, current_settings):
    """Display and handle the settings menu."""
    # Define menu options with their types
    options = [
        ("Slideshow Mode", "bool"),
        ("Show Info", "bool"),
        ("Orientation", "orientation"),
        ("Transition", "transition"),
        ("Sort Method", "sort"),
        ("Slide Delay", "float"),
        ("Brightness", "brightness")
    ]
    
    # Map settings to options
    values = [
        current_settings["slideshow_mode"],
        current_settings["show_info"],
        current_settings["orientation"],
        current_settings["transition"],
        current_settings["sort_method"],
        current_settings["slide_delay"],
        current_settings["brightness"]
    ]
    
    # Menu state
    selected_index = 0
    menu_active = True
    menu_start_time = time.time()
    
    # Display the initial menu
    display_options = [(options[i][0], values[i]) for i in range(len(options))]
    draw_settings_menu(display, display_options, selected_index)
    
    # Track previous button states
    prev_a = False
    prev_b = False
    prev_x = False
    prev_y = False
    
    while menu_active:
        # Check for menu timeout
        if time.time() - menu_start_time > MENU_TIMEOUT:
            print("Menu timed out")
            menu_active = False
            break
        
        # Read current button states
        curr_a = display.read_button(display.BUTTON_A)
        curr_b = display.read_button(display.BUTTON_B)
        curr_x = display.read_button(display.BUTTON_X)
        curr_y = display.read_button(display.BUTTON_Y)
        
        # Menu navigation and selection
        if curr_a and not prev_a:
            # Move selection up
            selected_index = (selected_index - 1) % len(options)
            menu_start_time = time.time()  # Reset timeout
            display.set_led(0.5, 0, 0)  # Red flash
        
        elif curr_b and not prev_b:
            # Move selection down
            selected_index = (selected_index + 1) % len(options)
            menu_start_time = time.time()  # Reset timeout
            display.set_led(0, 0.5, 0)  # Green flash
        
        elif curr_x and not prev_x:
            # Change the selected option
            option_type = options[selected_index][1]
            values[selected_index] = change_setting_value(option_type, values[selected_index])
            menu_start_time = time.time()  # Reset timeout
            display.set_led(0, 0, 0.5)  # Blue flash
        
        elif curr_y and not prev_y:
            # Exit menu
            menu_active = False
            display.set_led(0.5, 0, 0.5)  # Purple flash
        
        # Update display if buttons were pressed
        if (curr_a and not prev_a) or (curr_b and not prev_b) or (curr_x and not prev_x):
            display_options = [(options[i][0], values[i]) for i in range(len(options))]
            draw_settings_menu(display, display_options, selected_index)
        
        # Update previous button states
        prev_a = curr_a
        prev_b = curr_b
        prev_x = curr_x
        prev_y = curr_y
        
        # Reset LED
        if not (curr_a or curr_b or curr_x or curr_y):
            display.set_led(0.1, 0.1, 0.1)
        
        # Small delay to prevent CPU hogging
        time.sleep(0.1)
    
    # Update settings with new values
    current_settings["slideshow_mode"] = values[0]
    current_settings["show_info"] = values[1]
    current_settings["orientation"] = values[2]
    current_settings["transition"] = values[3]
    current_settings["sort_method"] = values[4]
    current_settings["slide_delay"] = values[5]
    current_settings["brightness"] = values[6]
    
    # Apply brightness immediately
    display.set_backlight(current_settings["brightness"])
    
    return current_settings

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
    brightness = max(0.1, min(1.0, args.brightness))  # Clamp between 0.1 and 1.0
    display.set_backlight(brightness)
    
    # Set a subtle LED indicator
    display.set_led(0.1, 0.1, 0.1)
    
    # Initialize app settings
    settings = {
        "slideshow_mode": args.slideshow,
        "show_info": args.show_info,
        "orientation": "portrait" if args.portrait else "landscape",
        "transition": args.transition,
        "sort_method": args.sort,
        "slide_delay": args.delay,
        "brightness": brightness
    }
    
    # Sort the image files
    image_files = get_sorted_images(image_files, settings["sort_method"])
    
    # Initialize state variables
    current_index = 0
    is_portrait = args.portrait
    is_landscape = args.landscape
    
    # Default to landscape if neither specified
    if not is_portrait and not is_landscape:
        is_landscape = True
        is_portrait = False
    
    # Transform settings
    rotation_angle = 0
    horizontal_flip = False
    last_slideshow_time = time.time()
    
    # Display loading message
    display_info_message(display, "Loading Gallery", f"{len(image_files)} images found")
    time.sleep(1)
    
    # Function to update the current display
    def update_display(transition_name=None):
        nonlocal current_index
        
        # Load the current image
        current_image = load_image(image_files[current_index])
        if current_image is None:
            display_info_message(display, "Error", f"Could not load {os.path.basename(image_files[current_index])}")
            time.sleep(1)
            return None
        
        # Process the image with current settings
        is_portrait = settings["orientation"] == "portrait"
        processed_image = process_image(
            current_image, 
            is_portrait=is_portrait, 
            rotation=rotation_angle, 
            flip_horizontal=horizontal_flip
        )
        
        # Add info overlay if enabled
        if settings["show_info"]:
            processed_image = overlay_info(
                processed_image, 
                image_files[current_index], 
                current_index, 
                len(image_files),
                is_portrait=is_portrait
            )
        
        return processed_image
    
    # Initial display update
    current_image = update_display()
    if current_image is not None:
        buffer.paste(current_image)
        display.display()
    
    # Show instructions
    print("\nButton controls:")
    print("  A: Previous image")
    print("  B: Next image")
    print("  X (short press): Toggle slideshow mode")
    print("  X (long press): Settings menu")
    print("  Y (short press): Toggle info overlay")
    print("  Y (long press): Transform menu")
    print("\nPress Ctrl+C to exit")
    
    # Main loop with manual button polling
    try:
        # Track previous button states to detect transitions
        prev_a = False
        prev_b = False
        prev_x = False
        prev_y = False
        x_press_time = 0
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
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                    
                elif curr_b and not prev_b:
                    # Toggle orientation
                    settings["orientation"] = "portrait" if settings["orientation"] == "landscape" else "landscape"
                    print(f"Switching to {settings['orientation']} orientation")
                    display.set_led(0, 1, 0)  # Green flash
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                    
                elif curr_x and not prev_x:
                    # Rotate 90° clockwise
                    rotation_angle = (rotation_angle + 90) % 360
                    print(f"Rotating to {rotation_angle}°")
                    display.set_led(0, 0, 1)  # Blue flash
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                    
                elif curr_y and not prev_y:
                    # Exit transform menu
                    in_transform_menu = False
                    print("Exiting transform menu")
                    display_info_message(display, "Exiting Transform Menu")
                    time.sleep(0.5)
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
            
            # Normal gallery navigation mode
            else:
                if curr_a and not prev_a:
                    # Previous image
                    old_image = buffer.copy()
                    current_index = (current_index - 1) % len(image_files)
                    print(f"Showing previous image: {image_files[current_index]}")
                    display.set_led(1, 0, 0)  # Red flash
                    
                    new_image = update_display()
                    if new_image:
                        if settings["transition"] != "none":
                            transition_effect(display, old_image, new_image, settings["transition"])
                        else:
                            buffer.paste(new_image)
                            display.display()
                    
                elif curr_b and not prev_b:
                    # Next image
                    old_image = buffer.copy()
                    current_index = (current_index + 1) % len(image_files)
                    print(f"Showing next image: {image_files[current_index]}")
                    display.set_led(0, 1, 0)  # Green flash
                    
                    new_image = update_display()
                    if new_image:
                        if settings["transition"] != "none":
                            transition_effect(display, old_image, new_image, settings["transition"])
                        else:
                            buffer.paste(new_image)
                            display.display()
                
                # Check for long press on X button (Settings menu)
                if curr_x and not x_press_time:
                    x_press_time = time.time()
                    display.set_led(0, 0.5, 0.5)  # Cyan for press indication
                
                elif curr_x and x_press_time and time.time() - x_press_time > 1.0:
                    # Long press detected (>1 second)
                    x_press_time = 0
                    print("Opening settings menu")
                    display.set_led(0, 1, 1)  # Bright cyan
                    
                    # Open settings menu
                    settings = settings_menu(display, settings)
                    
                    # Re-sort images if sort method changed
                    image_files = get_sorted_images(image_files, settings["sort_method"])
                    
                    # Update display after settings change
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                
                elif not curr_x and x_press_time:
                    # Short press (released before long press threshold)
                    if time.time() - x_press_time < 1.0:
                        # Toggle slideshow mode
                        settings["slideshow_mode"] = not settings["slideshow_mode"]
                        print(f"Slideshow mode: {settings['slideshow_mode']}")
                        
                        if settings["slideshow_mode"]:
                            display_info_message(display, "Slideshow Mode", "ON")
                        else:
                            display_info_message(display, "Slideshow Mode", "OFF")
                        
                        time.sleep(0.5)
                        
                        # Restore the display
                        new_image = update_display()
                        if new_image:
                            buffer.paste(new_image)
                            display.display()
                    
                    x_press_time = 0
                    display.set_led(0.1, 0.1, 0.1)  # Reset to subtle indicator
                
                # Check for short press on Y button (Info toggle)
                if curr_y and not prev_y:
                    settings["show_info"] = not settings["show_info"]
                    print(f"Image info overlay: {settings['show_info']}")
                    display.set_led(0.5, 0.5, 0)  # Yellow flash
                    
                    # Update display after toggle
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                
                # Check for long press on Y button (Transform menu)
                if curr_y and not y_press_time:
                    y_press_time = time.time()
                
                elif curr_y and y_press_time and time.time() - y_press_time > 1.0:
                    # Long press detected (>1 second)
                    in_transform_menu = True
                    y_press_time = 0
                    display.set_led(1, 1, 0)  # Bright yellow
                    display_info_message(display, "Transform Menu",
                                        "A: Flip | B: Orientation | X: Rotate | Y: Exit")
                    time.sleep(1.5)
                    
                    # Restore the display
                    new_image = update_display()
                    if new_image:
                        buffer.paste(new_image)
                        display.display()
                    
                elif not curr_y and y_press_time:
                    # Button released before long press threshold
                    y_press_time = 0
                
                # Handle slideshow mode
                if settings["slideshow_mode"] and time.time() - last_slideshow_time > settings["slide_delay"]:
                    # Time to advance to next image
                    old_image = buffer.copy()
                    current_index = (current_index + 1) % len(image_files)
                    print(f"Slideshow: {image_files[current_index]}")
                    
                    new_image = update_display()
                    if new_image:
                        if settings["transition"] != "none":
                            transition_effect(display, old_image, new_image, settings["transition"])
                        else:
                            buffer.paste(new_image)
                            display.display()
                    
                    last_slideshow_time = time.time()
            
            # Update previous button states
            prev_a = curr_a
            prev_b = curr_b
            prev_x = curr_x
            prev_y = curr_y
            
            # Reset LED to subtle indicator after actions (if not in a menu)
            if not in_transform_menu and not curr_x and not curr_y:
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