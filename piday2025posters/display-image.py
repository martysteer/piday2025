#!/usr/bin/env python3
import argparse
import time
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
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

def process_image(image, is_portrait=False, rotation=0, flip_horizontal=False):
    """
    Process image based on current transformation settings.
    
    Args:
        image: The original PIL Image
        is_portrait: Whether to display in portrait orientation
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        flip_horizontal: Whether to flip the image horizontally
        
    Returns:
        Processed PIL Image ready for display
    """
    # Make a copy of the image to avoid modifying the original
    img = image.copy()
    
    # Apply horizontal flip if needed
    if flip_horizontal:
        img = ImageOps.mirror(img)
    
    # Apply rotation if needed
    if rotation != 0:
        img = img.rotate(rotation, expand=True)
    
    # Resize based on orientation
    display_width = DisplayHATMini.WIDTH
    display_height = DisplayHATMini.HEIGHT
    
    if is_portrait:
        # For portrait mode, we'll rotate after resizing
        # Calculate scaling ratios
        width_ratio = display_height / img.width
        height_ratio = display_width / img.height
        ratio = min(width_ratio, height_ratio)
        
        # Resize the image maintaining aspect ratio
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        resized_image = img.resize((new_width, new_height), Image.LANCZOS)
        
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
        width_ratio = display_width / img.width
        height_ratio = display_height / img.height
        ratio = min(width_ratio, height_ratio)
        
        # Resize the image maintaining aspect ratio
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        resized_image = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Create a canvas of the display size
        result = Image.new("RGB", (display_width, display_height), (0, 0, 0))
        
        # Calculate position to center the image
        x_offset = (display_width - new_width) // 2
        y_offset = (display_height - new_height) // 2
        
        # Paste the resized image centered
        result.paste(resized_image, (x_offset, y_offset))
    
    return result

def display_info_message(display, message, submessage=""):
    """Display a message in the center of the screen."""
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    
    # Create a blank image with black background
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if necessary
    try:
        main_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except IOError:
        main_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    
    # Get text size for centering
    try:
        # For newer PIL versions
        _, _, text_width, text_height = draw.textbbox((0, 0), message, font=main_font)
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(message, font=main_font)
    
    # Calculate position to center the text
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 - 15 if submessage else (height - text_height) // 2
    
    # Draw the main message
    draw.text((text_x, text_y), message, font=main_font, fill=(255, 255, 255))
    
    # Draw submessage if provided
    if submessage:
        try:
            # For newer PIL versions
            _, _, subtext_width, subtext_height = draw.textbbox((0, 0), submessage, font=sub_font)
        except AttributeError:
            # Fallback for older PIL versions
            subtext_width, subtext_height = draw.textsize(submessage, font=sub_font)
        
        subtext_x = (width - subtext_width) // 2
        subtext_y = text_y + text_height + 10
        
        draw.text((subtext_x, subtext_y), submessage, font=sub_font, fill=(200, 200, 200))
    
    # Update the display
    display.buffer = image
    display.display()

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
            is_portrait = False
            
        # Load the image
        original_image = Image.open(args.image)
        
        # Convert image to RGB mode if it's not already
        if original_image.mode != "RGB":
            original_image = original_image.convert("RGB")
            
        # Get image dimensions before processing
        print(f"Original image dimensions: {original_image.width}x{original_image.height}")
        
        # Initialize transformation state
        orientation_mode = "portrait" if is_portrait else "landscape"
        rotation_angle = 0
        horizontal_flip = False
        
        # Initialize display with a blank image
        buffer = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0))
        display = DisplayHATMini(buffer)
        
        # Set a subtle LED indicator
        display.set_led(0.1, 0.1, 0.1)
        
        # Process image with initial settings
        processed_image = process_image(
            original_image, 
            is_portrait=is_portrait, 
            rotation=rotation_angle, 
            flip_horizontal=horizontal_flip
        )
        
        # Display the initial image
        buffer.paste(processed_image)
        display.display()
        
        # Show initial status
        print(f"Displaying image: {args.image}")
        print(f"Initial settings: orientation={orientation_mode}, rotation={rotation_angle}°, flipped={horizontal_flip}")
        print("\nButton controls:")
        print("  A: Flip image horizontally")
        print("  B: Toggle between portrait/landscape orientation")
        print("  X: Rotate image 90° clockwise")
        print("  Y: Clear the screen and quit")
        print("\nPress Ctrl+C to exit")
        
        # Define button callback for interactive control
        def button_handler(pin):
            nonlocal orientation_mode, rotation_angle, horizontal_flip, is_portrait
            
            # Only handle button presses (not releases)
            if not display.read_button(pin):
                return
                
            if pin == display.BUTTON_A:
                # A: Flip image horizontally
                horizontal_flip = not horizontal_flip
                print(f"Flipping image horizontally: {horizontal_flip}")
                display.set_led(1, 0, 0)  # Red flash
                
            elif pin == display.BUTTON_B:
                # B: Toggle orientation
                is_portrait = not is_portrait
                orientation_mode = "portrait" if is_portrait else "landscape"
                print(f"Switching to {orientation_mode} orientation")
                display.set_led(0, 1, 0)  # Green flash
                
            elif pin == display.BUTTON_X:
                # X: Rotate 90° clockwise
                rotation_angle = (rotation_angle + 90) % 360
                print(f"Rotating to {rotation_angle}°")
                display.set_led(0, 0, 1)  # Blue flash
                
            elif pin == display.BUTTON_Y:
                # Y: Clear screen and quit
                print("Clearing screen and exiting...")
                display.set_led(1, 1, 1)  # White flash
                
                # Clear the screen
                buffer.paste(Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0)))
                display.display()
                
                # Turn off LED
                display.set_led(0, 0, 0)
                
                # Exit program
                time.sleep(0.5)  # Brief delay to see the flash
                sys.exit(0)
            
            # Process and display the updated image
            processed_image = process_image(
                original_image, 
                is_portrait=is_portrait, 
                rotation=rotation_angle, 
                flip_horizontal=horizontal_flip
            )
            
            buffer.paste(processed_image)
            display.display()
            
            # Reset LED to subtle indicator after a brief flash
            time.sleep(0.1)
            display.set_led(0.1, 0.1, 0.1)
        
        # Instead of using callbacks which might fail with the "Failed to add edge detection" error,
        # we'll manually poll the button states in the main loop
        print("Using manual button polling instead of edge detection")
        
        # Main loop to keep the program running
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
                    button_handler(display.BUTTON_A)
                if curr_b and not prev_b:
                    button_handler(display.BUTTON_B)
                if curr_x and not prev_x:
                    button_handler(display.BUTTON_X)
                if curr_y and not prev_y:
                    button_handler(display.BUTTON_Y)
                
                # Update previous button states
                prev_a = curr_a
                prev_b = curr_b
                prev_x = curr_x
                prev_y = curr_y
                
                # Short delay to prevent CPU hogging
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            display.set_led(0, 0, 0)  # Turn off LED
            
            # Clear the screen on exit
            buffer.paste(Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0)))
            display.display()
            
    except Exception as e:
        print(f"Error: {e}")
        
        # Try to display error message on the screen if display is initialized
        try:
            if 'display' in locals():
                display_info_message(display, "Error", str(e))
                display.set_led(1, 0, 0)  # Red LED to indicate error
                time.sleep(5)  # Show error for 5 seconds
                display.set_led(0, 0, 0)  # Turn off LED
        except:
            pass

if __name__ == "__main__":
    main()