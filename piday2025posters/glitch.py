#!/usr/bin/env python3
"""
Glitch transition effect for Display HAT Mini
Translates the JavaScript glitch effect from https://codepen.io/ara_node/pen/Bambjr
"""

import random
import io
import time
from PIL import Image

def get_random_indices():
    """
    Generate random indices for glitching, avoiding certain values
    that might completely break the image.
    """
    # These are indices to avoid, similar to the ng array in JS
    avoid_indices = [1, 2, 3, 4, 6, 7, 8, 9, 12, 16, 17, 24, 29, 34]
    
    # Generate random index
    index = random.randint(0, 99)
    
    # Regenerate if in avoid_indices
    while index in avoid_indices:
        index = random.randint(0, 99)
    
    return index, random.randint(0, 99)

def apply_glitch(img, threshold=0.8):
    """
    Apply glitch effect to a PIL Image
    
    Args:
        img: PIL Image to glitch
        threshold: Threshold value between 0.75 and 0.995
                  Higher values = less glitching
    
    Returns:
        Glitched PIL Image
    """
    # Clamp threshold
    threshold = max(0.75, min(0.995, threshold))
    
    # Convert image to JPEG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    jpeg_bytes = buffer.getvalue()
    
    # Convert to bytearray for modification
    binary = bytearray(jpeg_bytes)
    
    # Get random indices for glitching
    replace_val, new_val = get_random_indices()
    
    # Apply glitch effect
    for i in range(len(binary)):
        if binary[i] == replace_val and random.random() > threshold:
            binary[i] = new_val
    
    # Convert back to image
    try:
        return Image.open(io.BytesIO(binary))
    except Exception:
        # If the image is too corrupted, return original
        return img

def glitch_transition(display, current_image, next_image, frames=15, threshold_start=0.95, threshold_end=0.75):
    """
    Perform a glitch transition between two images
    
    Args:
        display: DisplayHATMini instance
        current_image: Starting PIL Image
        next_image: Ending PIL Image
        frames: Number of frames in the transition
        threshold_start: Starting threshold (less glitchy)
        threshold_end: Ending threshold (more glitchy)
    """
    # Create copies to avoid modifying originals
    current = current_image.copy()
    next_img = next_image.copy()
    
    # Blend from current to next image with increasing glitch
    for i in range(frames):
        # Calculate blend ratio and threshold
        blend_ratio = i / frames
        threshold = threshold_start - (threshold_start - threshold_end) * min(1, 2 * blend_ratio)
        
        # Blend images
        if blend_ratio < 0.5:
            # First half: glitch the current image more and more
            blended = current.copy()
            blended = apply_glitch(blended, threshold)
        else:
            # Second half: start transitioning to next image with less glitching
            alpha = (blend_ratio - 0.5) * 2  # 0 to 1 in second half
            blended = Image.blend(
                apply_glitch(current, threshold), 
                apply_glitch(next_img, threshold_start - (blend_ratio - 0.5)), 
                alpha
            )
        
        # Display the glitched image
        display.buffer.paste(blended)
        display.display()
        display.process_events()  # Ensure display updates on all platforms
        
        # Small delay between frames
        time.sleep(0.05)
