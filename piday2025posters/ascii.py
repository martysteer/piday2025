#!/usr/bin/env python3
"""
ASCII transition for Display HAT Mini

This module provides a transition effect that converts images to ASCII art
for use between slides in the image gallery.

Inspired by the 'accurate_conversion' example from p5.asciify.
"""

import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Character set from darkest to lightest (reverse of JavaScript example)
# Using fewer characters for simplicity and better visibility on small display
ASCII_CHARS = '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,"^`\'. '

def get_average_brightness(image_data, x, y, cell_width, cell_height):
    """Calculate average brightness of a rectangular area of pixels."""
    # Extract the rectangular region
    region = image_data[y:y+cell_height, x:x+cell_width]
    
    # Calculate average brightness (0-255)
    if region.size > 0:  # Ensure we don't divide by zero
        return np.mean(region)
    return 0

def image_to_ascii(image, cell_size=8, invert=False):
    """Convert an image to ASCII art."""
    # Resize the image to fit display while maintaining aspect ratio
    width, height = image.size
    image = image.resize((width // cell_size, height // cell_size), Image.LANCZOS)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Get image data as numpy array
    image_data = np.array(image)
    
    # Create a blank image for ASCII output
    ascii_width = width
    ascii_height = height
    ascii_image = Image.new('RGB', (ascii_width, ascii_height), color='black')
    draw = ImageDraw.Draw(ascii_image)
    
    # Try to load a font, fall back to default if necessary
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", cell_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Map pixels to ASCII characters
    char_width = image.width
    char_height = image.height
    
    for y in range(char_height):
        for x in range(char_width):
            # Get pixel brightness
            brightness = image_data[y, x]
            
            # Map brightness to ASCII character index
            if invert:
                char_index = int(brightness * (len(ASCII_CHARS) - 1) / 255)
            else:
                char_index = int((255 - brightness) * (len(ASCII_CHARS) - 1) / 255)
                
            # Get the character
            char = ASCII_CHARS[char_index]
            
            # Calculate position to draw the character
            pos_x = x * cell_size
            pos_y = y * cell_size
            
            # Draw the character
            draw.text((pos_x, pos_y), char, font=font, fill=(255, 255, 255))
    
    return ascii_image

def ascii_transition(display, current_image, next_image, frames=10, invert=False):
    """
    Perform an ASCII art transition between two images.
    
    Args:
        display: DisplayHATMini instance
        current_image: Starting PIL Image
        next_image: Ending PIL Image
        frames: Number of frames in the transition
        invert: Whether to invert the brightness-to-character mapping
    """
    width, height = display.buffer.size
    
    # Create ASCII versions of both images
    current_ascii = image_to_ascii(current_image, cell_size=8, invert=invert)
    next_ascii = image_to_ascii(next_image, cell_size=8, invert=invert)
    
    # Phase 1: Transition from current image to its ASCII representation
    for i in range(frames):
        # Calculate blend ratio
        alpha = i / frames
        
        # Create a blended image
        if i < frames // 2:
            # First half: blend current image with its ASCII version
            blend = Image.blend(current_image, current_ascii, alpha * 2)
        else:
            # Second half: blend ASCII version of current with ASCII version of next
            blend_alpha = (i - frames // 2) / (frames // 2)
            blend = Image.blend(current_ascii, next_ascii, blend_alpha)
        
        # Update the display
        blend = blend.resize((width, height), Image.LANCZOS)
        display.buffer.paste(blend)
        display.display()
        
        # Short delay between frames
        time.sleep(0.05)
    
    # Phase 2: Transition from ASCII representation to next image
    for i in range(frames):
        # Calculate blend ratio
        alpha = i / frames
        
        # Blend ASCII version of next image with actual next image
        blend = Image.blend(next_ascii, next_image, alpha)
        
        # Update the display
        blend = blend.resize((width, height), Image.LANCZOS)
        display.buffer.paste(blend)
        display.display()
        
        # Short delay between frames
        time.sleep(0.05)

# Enhanced version that adds a text overlay effect
def ascii_transition_text_overlay(display, current_image, next_image, frames=15):
    """
    Perform an ASCII art transition with text overlay effect between two images.
    This version keeps both images visible but overlays ASCII characters that
    gradually reveal the next image.
    
    Args:
        display: DisplayHATMini instance
        current_image: Starting PIL Image
        next_image: Ending PIL Image
        frames: Number of frames in the transition
    """
    width, height = display.buffer.size
    
    # Resize images to fit display
    current_image = current_image.resize((width, height), Image.LANCZOS)
    next_image = next_image.resize((width, height), Image.LANCZOS)
    
    # Create text overlay image
    text_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_overlay)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)
    except IOError:
        font = ImageFont.load_default()
    
    # Get grayscale version of next image for character mapping
    next_gray = next_image.convert('L')
    
    # Generate a grid of ASCII characters based on brightness
    cell_size = 8
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            # Get average brightness of cell area in next image
            brightness = 0
            count = 0
            for cy in range(cell_size):
                for cx in range(cell_size):
                    if x+cx < width and y+cy < height:
                        px = next_gray.getpixel((x+cx, y+cy))
                        brightness += px
                        count += 1
            if count > 0:
                avg_brightness = brightness / count
                
                # Map brightness to ASCII character
                char_index = int(avg_brightness * (len(ASCII_CHARS) - 1) / 255)
                char = ASCII_CHARS[char_index]
                
                # Draw the character in white with transparency
                draw.text((x, y), char, font=font, fill=(255, 255, 255, 255))
    
    # Perform transition
    for i in range(frames + 1):
        # Create a new composite image starting with current image
        composite = current_image.copy()
        
        # Calculate transition progress
        progress = i / frames
        
        # Adjust text overlay opacity based on progress
        overlay_with_alpha = text_overlay.copy()
        
        # Apply the text overlay with increasing opacity
        overlay_with_alpha.putalpha(int(255 * progress))
        
        # Blend with next image based on progress
        next_with_alpha = next_image.copy()
        
        # Create the final blended image
        if i <= frames // 2:
            # First half: reveal ASCII characters
            composite.paste(overlay_with_alpha, (0, 0), overlay_with_alpha)
        else:
            # Second half: transition to next image
            blend_factor = (i - frames // 2) / (frames // 2)
            composite = Image.blend(composite, next_image, blend_factor)
        
        # Update display
        display.buffer.paste(composite)
        display.display()
        
        # Short delay between frames
        time.sleep(0.05)
