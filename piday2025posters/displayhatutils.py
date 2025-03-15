#!/usr/bin/env python3
"""
Utility module for Display HAT Mini applications.
Contains common functions used across multiple Display HAT Mini applications
and proxy implementation for cross-platform support.
"""

import os
import glob
import time
import platform
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

# First, determine which DisplayHATMini implementation to use based on platform
if platform.system() == "Darwin":  # macOS
    try:
        # Import the proxy implementation
        from proxydisplayhatmini import DisplayHATMini
        print("Using proxy DisplayHATMini implementation for macOS")
    except ImportError:
        raise ImportError("Error: proxydisplayhatmini.py not found in the current directory or PYTHONPATH.")
else:  # Raspberry Pi or other Linux system
    try:
        from displayhatmini import DisplayHATMini
        print("Using actual DisplayHATMini implementation")
    except ImportError:
        raise ImportError("Error: Display HAT Mini library not found. Please install it with: sudo pip3 install displayhatmini")

# Add platform-specific processing method to DisplayHATMini
if platform.system() == "Darwin":
    # For macOS proxy version
    DisplayHATMini.process_events = lambda self: self.display()
else:
    # For actual hardware, no action needed
    DisplayHATMini.process_events = lambda self: None

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
    """
    Display a message in the center of the screen.
    
    Args:
        display: DisplayHATMini instance
        message: Main message to display
        submessage: Optional secondary message to display below the main message
    """
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
    
    # Update the display - paste to the buffer instead of replacing it
    display.buffer.paste(image)
    display.display()

def load_image(image_path):
    """
    Load an image file with error handling.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        PIL Image object or None if loading failed
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Convert image to RGB mode if it's not already
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        return image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def find_images(directory, extensions=None):
    """
    Find all image files in the specified directory.
    
    Args:
        directory: Path to the directory containing images
        extensions: List of file extensions to include (e.g., ['.jpg', '.png'])
                   If None, all common image extensions are used
    
    Returns:
        List of image file paths
    """
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    
    image_files = []
    
    # Make sure directory exists
    if not os.path.isdir(directory):
        print(f"Directory not found: {directory}")
        return image_files
    
    # Find all files with the specified extensions
    for ext in extensions:
        pattern = os.path.join(directory, f'*{ext.lower()}')
        image_files.extend(glob.glob(pattern))
        
        # Also check for uppercase extensions
        pattern = os.path.join(directory, f'*{ext.upper()}')
        image_files.extend(glob.glob(pattern))
    
    # Sort the files alphabetically
    image_files.sort()
    
    return image_files

def overlay_info(image, filename, index=0, total=1, is_portrait=False):
    """
    Add image information overlay to the bottom of the image.
    
    Args:
        image: PIL Image to add overlay to
        filename: Path of the image file
        index: Current image index (0-based)
        total: Total number of images
        is_portrait: Whether the image is in portrait orientation
    
    Returns:
        PIL Image with information overlay
    """
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    
    # Make a copy of the image to avoid modifying the original
    img_with_info = image.copy()
    draw = ImageDraw.Draw(img_with_info)
    
    # Try to load a font, fall back to default if necessary
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except IOError:
        font = ImageFont.load_default()
    
    # Get the basename of the file
    basename = os.path.basename(filename)
    if len(basename) > 25:  # Truncate if too long
        basename = basename[:22] + "..."
    
    # Format the info text
    info_text = f"{basename} ({index+1}/{total})"
    
    # Create a semi-transparent overlay for the text background
    overlay_height = 20
    if is_portrait:
        # Adjust for portrait orientation
        img_with_info.paste(
            Image.new('RGB', (height, overlay_height), (0, 0, 0)),
            (0, width - overlay_height)
        )
        # Draw the text
        draw.text((5, width - overlay_height + 3), info_text, fill=(255, 255, 255), font=font)
    else:
        # Add overlay at the bottom of the image
        img_with_info.paste(
            Image.new('RGB', (width, overlay_height), (0, 0, 0)),
            (0, height - overlay_height)
        )
        # Draw the text
        draw.text((5, height - overlay_height + 3), info_text, fill=(255, 255, 255), font=font)
    
    return img_with_info

def clear_display(display):
    """
    Clear the display with a black screen.
    
    Args:
        display: DisplayHATMini instance
    """
    black_screen = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), (0, 0, 0))
    display.buffer.paste(black_screen)
    display.display()
    display.set_led(0, 0, 0)  # Turn off LED
    display.set_backlight(0)  # Turn off backlight completely
