#!/usr/bin/env python3
import argparse
import time
import os
from PIL import Image, ImageDraw, ImageFont
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

def display_button_name(display, button_name):
    """Display the button name in the center of the screen."""
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    
    # Create a blank image with black background
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if necessary
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except IOError:
        font = ImageFont.load_default()
    
    # Get text size for centering
    # For older PIL versions that don't have textbbox
    try:
        _, _, text_width, text_height = draw.textbbox((0, 0), button_name, font=font)
        text_width -= 0  # Adjust for textbbox offset
        text_height -= 0  # Adjust for textbbox offset
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(button_name, font=font)
    
    # Calculate position to center the text
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # Draw the text
    draw.text((text_x, text_y), button_name, font=font, fill=(255, 255, 255))
    
    # Update the display
    display.buffer = image
    display.display()

def button_callback(pin, display):
    """Handle button press events."""
    # Only handle button presses (not releases)
    if not display.read_button(pin):
        return
    
    # Determine which button was pressed
    if pin == display.BUTTON_A:
        display_button_name(display, "Button A")
    elif pin == display.BUTTON_B:
        display_button_name(display, "Button B")
    elif pin == display.BUTTON_X:
        display_button_name(display, "Button X")
    elif pin == display.BUTTON_Y:
        display_button_name(display, "Button Y")

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
        
        # Set up button handling without callbacks (manually polling)
        print("Button callbacks failed, using manual polling instead")
        
        # Display the image
        display.display()
        
        print(f"Displaying image: {args.image}")
        print("Press buttons A, B, X, or Y to display button names")
        print("Press Ctrl+C to exit")
        
        try:
            # Previous button states
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
                    display_button_name(display, "Button A")
                    print("Button A pressed")
                if curr_b and not prev_b:
                    display_button_name(display, "Button B")
                    print("Button B pressed")
                if curr_x and not prev_x:
                    display_button_name(display, "Button X")
                    print("Button X pressed")
                if curr_y and not prev_y:
                    display_button_name(display, "Button Y")
                    print("Button Y pressed")
                
                # Update previous states
                prev_a = curr_a
                prev_b = curr_b
                prev_x = curr_x
                prev_y = curr_y
                
                # Short delay to prevent CPU hogging
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()