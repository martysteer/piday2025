#!/usr/bin/env python3
import os
import time
import random
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from displayhatmini import DisplayHATMini

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Photo Slideshow for Display HAT Mini')
    
    # Image source options
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument('--dir', '-d', 
                        default="/home/pi/slideshow_images",
                        help='Directory containing images (default: /home/pi/slideshow_images)')
    source_group.add_argument('--image', '-i', 
                        help='Display a single image instead of a slideshow')
    
    # Slideshow options
    parser.add_argument('--delay', '-t', type=float, default=10.0,
                        help='Time in seconds between slides (default: 10.0)')
    parser.add_argument('--transition', '-tr', choices=['none', 'fade', 'slide'], default='none',
                        help='Transition effect between slides (default: none)')
    parser.add_argument('--random', '-r', action='store_true',
                        help='Randomize the order of images (default: True)')
    parser.add_argument('--no-random', action='store_true',
                        help='Do not randomize the order of images')
    
    # Display options
    parser.add_argument('--hide-info', action='store_true',
                        help='Hide image information overlay')
    parser.add_argument('--brightness', '-b', type=float, default=1.0,
                        help='Screen brightness level 0.0-1.0 (default: 1.0)')
    parser.add_argument('--extensions', '-e', default='.jpg,.jpeg,.png,.bmp,.gif',
                        help='Comma-separated list of file extensions to include (default: .jpg,.jpeg,.png,.bmp,.gif)')
    
    args = parser.parse_args()
    
    # Process arguments
    if args.no_random:
        args.random = False
        
    # Convert comma-separated extensions to list
    args.extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    return args

# Get arguments
args = parse_args()

# Configuration from arguments
IMAGE_DIR = args.dir
SINGLE_IMAGE = args.image
SLIDE_DELAY = args.delay
EXTENSIONS = args.extensions
SHOW_INFO = not args.hide_info
TRANSITION_MODE_NAME = args.transition
RANDOMIZE = args.random if not args.no_random else False
BRIGHTNESS = max(0.0, min(1.0, args.brightness))  # Clamp between 0 and 1

# Initialize the display
width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT
buffer = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(buffer)

# Try to load a font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
except IOError:
    # Fallback to default font
    font = ImageFont.load_default()

# Initialize display
displayhatmini = DisplayHATMini(buffer)
displayhatmini.set_led(0.05, 0.05, 0.05)  # Dim LED

# Slideshow state variables
running = True
paused = False
current_index = 0
image_list = []
last_change_time = 0
transition_mode = 0  # 0=none, 1=fade, 2=slide
show_info = SHOW_INFO

def get_image_list(directory):
    """Get a list of image files from the specified directory."""
    image_list = []
    try:
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return image_list
            
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and any(filename.lower().endswith(ext) for ext in EXTENSIONS):
                image_list.append(filepath)
    except Exception as e:
        print(f"Error reading directory: {e}")
    
    return image_list

def load_image(image_path):
    """Load and prepare an image for display."""
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGB mode if necessary (for PNG with transparency)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to fit the display while maintaining aspect ratio
        img.thumbnail((width, height))
        
        # Create a blank image with display dimensions
        centered_img = Image.new("RGB", (width, height), (0, 0, 0))
        
        # Paste the resized image in the center
        x_offset = (width - img.width) // 2
        y_offset = (height - img.height) // 2
        centered_img.paste(img, (x_offset, y_offset))
        
        return centered_img
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        # Return an error image
        error_img = Image.new("RGB", (width, height), (0, 0, 0))
        draw_error = ImageDraw.Draw(error_img)
        draw_error.text((10, height//2 - 20), f"Error loading image:", fill=(255, 0, 0), font=font)
        draw_error.text((10, height//2), os.path.basename(image_path), fill=(255, 0, 0), font=font)
        return error_img

def overlay_info(image, filename, index, total):
    """Add image information overlay."""
    if not show_info:
        return image
    
    # Create a copy of the image to avoid modifying the original
    img_with_info = image.copy()
    draw_info = ImageDraw.Draw(img_with_info)
    
    # Create a semi-transparent background for text
    overlay = Image.new('RGBA', (width, 30), (0, 0, 0, 180))
    img_with_info.paste(Image.new('RGB', (width, 30), (0, 0, 0)), (0, height - 30), overlay)
    
    # Add image information
    basename = os.path.basename(filename)
    if len(basename) > 30:  # Truncate if too long
        basename = basename[:27] + "..."
    
    # Format the text based on whether we're in single image mode or slideshow
    if total <= 1:
        info_text = basename
    else:
        info_text = f"{basename} ({index+1}/{total})"
    
    draw_info.text((5, height - 25), info_text, fill=(255, 255, 255), font=font)
    
    return img_with_info

def button_callback(pin):
    global current_index, paused, transition_mode, last_change_time, show_info
    
    # Only handle button presses (not releases)
    if not displayhatmini.read_button(pin):
        return
    
    if pin == displayhatmini.BUTTON_A:  # Previous image
        current_index = (current_index - 1) % len(image_list)
        last_change_time = time.time()
        displayhatmini.set_led(0.8, 0, 0)  # Red flash
        time.sleep(0.1)
        update_display()
        
    elif pin == displayhatmini.BUTTON_B:  # Next image
        current_index = (current_index + 1) % len(image_list)
        last_change_time = time.time()
        displayhatmini.set_led(0, 0.8, 0)  # Green flash
        time.sleep(0.1)
        update_display()
        
    elif pin == displayhatmini.BUTTON_X:  # Pause/resume
        paused = not paused
        if paused:
            displayhatmini.set_led(0.8, 0.8, 0)  # Yellow for paused
        else:
            displayhatmini.set_led(0, 0, 0.8)  # Blue for running
            last_change_time = time.time()
        time.sleep(0.3)  # Longer flash for pause/resume
        
    elif pin == displayhatmini.BUTTON_Y:  # Toggle info/transition
        if paused:
            # When paused, Y toggles info display
            show_info = not show_info
            update_display()
        else:
            # When running, Y cycles through transitions
            transition_mode = (transition_mode + 1) % 3
        displayhatmini.set_led(0.8, 0, 0.8)  # Purple flash
        time.sleep(0.1)
    
    # Reset LED after a short time
    displayhatmini.set_led(0.05, 0.05, 0.05)  # Back to dim white

def update_display():
    """Update the display with the current image."""
    if not image_list:
        return
        
    image = load_image(image_list[current_index])
    image_with_info = overlay_info(image, image_list[current_index], current_index, len(image_list))
    buffer.paste(image_with_info)
    displayhatmini.display()

def display_message(message, subtext=""):
    """Display a message on the screen."""
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    
    # Draw the main message
    text_width, text_height = draw.textsize(message, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2 - 10)
    draw.text(position, message, fill=(255, 255, 255), font=font)
    
    # Draw the subtext if provided
    if subtext:
        subtext_width, subtext_height = draw.textsize(subtext, font=font)
        position = ((width - subtext_width) // 2, (height - subtext_height) // 2 + 10)
        draw.text(position, subtext, fill=(200, 200, 200), font=font)
    
    displayhatmini.display()

def main():
    global current_index, last_change_time, image_list, running, transition_mode
    
    # Set transition mode based on command line argument
    if TRANSITION_MODE_NAME == 'fade':
        transition_mode = 1
    elif TRANSITION_MODE_NAME == 'slide':
        transition_mode = 2
    else:  # 'none'
        transition_mode = 0
    
    # Set display brightness
    displayhatmini.set_backlight(BRIGHTNESS)
    
    # Handle single image mode
    if SINGLE_IMAGE:
        print(f"Displaying single image: {SINGLE_IMAGE}")
        display_message("Loading image...", os.path.basename(SINGLE_IMAGE))
        
        if not os.path.exists(SINGLE_IMAGE):
            message = "Image not found!"
            print(message)
            display_message(message, SINGLE_IMAGE)
            time.sleep(5)
            running = False
            return
            
        # Show the single image
        image = load_image(SINGLE_IMAGE)
        if SHOW_INFO:
            image = overlay_info(image, SINGLE_IMAGE, 0, 1)
        buffer.paste(image)
        displayhatmini.display()
        
        # Keep showing the single image until interrupted
        while running:
            time.sleep(0.1)
            
    # Handle slideshow mode
    else:
        print("Starting slideshow...")
        display_message("Starting slideshow", "Loading images...")
        
        print(f"Looking for images in: {IMAGE_DIR}")
        
        # Get list of images
        image_list = get_image_list(IMAGE_DIR)
        
        if not image_list:
            message = "No images found!"
            print(message)
            display_message(message, IMAGE_DIR)
            time.sleep(5)
            running = False
            return
        
        print(f"Found {len(image_list)} images")
        display_message(f"Found {len(image_list)} images", "Starting slideshow...")
        time.sleep(1)
        
        # Randomize the images if requested
        if RANDOMIZE:
            print("Randomizing image order")
            random.shuffle(image_list)
        
        # Start with the first image
        update_display()
        last_change_time = time.time()
        
        # Main loop
        while running:
            current_time = time.time()
            
            # Update the display if needed
            if not paused and (current_time - last_change_time > SLIDE_DELAY):
                # Time to show next image
                current_index = (current_index + 1) % len(image_list)
                
                # Load the next image
                next_image = load_image(image_list[current_index])
                next_image_with_info = overlay_info(next_image, image_list[current_index], 
                                                current_index, len(image_list))
                current_image = buffer.copy()
                
                # Apply transition effect
                if transition_mode == 1:  # Fade
                    # Simple fade (not true alpha blend but a rough approximation)
                    for alpha in range(0, 11, 2):
                        alpha = alpha / 10.0
                        blended = Image.blend(current_image, next_image_with_info, alpha)
                        buffer.paste(blended)
                        displayhatmini.display()
                        time.sleep(0.05)
                elif transition_mode == 2:  # Slide
                    # Slide from right
                    for i in range(0, width + 1, 20):
                        # Create composite image
                        temp = Image.new("RGB", (width, height))
                        temp.paste(current_image, (-i, 0))
                        temp.paste(next_image_with_info, (width - i, 0))
                        buffer.paste(temp)
                        displayhatmini.display()
                        time.sleep(0.01)
                else:  # No transition
                    buffer.paste(next_image_with_info)
                    displayhatmini.display()
                
                last_change_time = current_time
            
            # Small delay to prevent CPU hogging
            time.sleep(0.1)

if __name__ == "__main__":
    try:
        # Print configuration info
        print(f"Display HAT Mini Photo Viewer")
        print(f"-----------------------------")
        if SINGLE_IMAGE:
            print(f"Mode: Single image")
            print(f"Image: {SINGLE_IMAGE}")
        else:
            print(f"Mode: Slideshow")
            print(f"Directory: {IMAGE_DIR}")
            print(f"Delay: {SLIDE_DELAY} seconds")
            print(f"Transition: {TRANSITION_MODE_NAME}")
            print(f"Randomized: {RANDOMIZE}")
        print(f"Show info overlay: {SHOW_INFO}")
        print(f"Brightness: {BRIGHTNESS}")
        print(f"File extensions: {', '.join(EXTENSIONS)}")
        print(f"-----------------------------")
        
        # Register button callback
        displayhatmini.on_button_pressed(button_callback)
        main()
    except KeyboardInterrupt:
        print("Slideshow terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        display_message("An error occurred", str(e))
        time.sleep(5)
    finally:
        # Clean up
        displayhatmini.set_led(0, 0, 0)
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        displayhatmini.display()
