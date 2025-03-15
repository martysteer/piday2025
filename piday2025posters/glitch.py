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
    # Expanded to include more critical bytes
    avoid_indices = [0, 1, 2, 3, 4, 6, 7, 8, 9, 12, 16, 17, 24, 29, 34, 
                    255, 216, 217, 218, 219, 192, 193, 194, 195]
    
    # Generate random index
    index = random.randint(20, 150)  # Reduced range to safer bytes
    
    # Regenerate if in avoid_indices
    while index in avoid_indices:
        index = random.randint(20, 150)
    
    # Return both indices, being more careful with the replacement value
    return index, random.randint(30, 130)

def apply_glitch(img, threshold=0.9):
    """
    Apply glitch effect to a PIL Image
    
    Args:
        img: PIL Image to glitch
        threshold: Threshold value between 0.75 and 0.995
                  Higher values = less glitching
    
    Returns:
        Glitched PIL Image
    """
    # Clamp threshold to a safer range
    threshold = max(0.85, min(0.995, threshold))
    
    # Create a copy of the image to avoid modifying the original
    img_copy = img.copy()
    
    try:
        # Convert image to JPEG bytes
        buffer = io.BytesIO()
        img_copy.save(buffer, format="JPEG", quality=90)
        jpeg_bytes = buffer.getvalue()
        
        # Convert to bytearray for modification
        binary = bytearray(jpeg_bytes)
        
        # Get random indices for glitching
        replace_val, new_val = get_random_indices()
        
        # Count modifications to limit corruption
        mod_count = 0
        max_mods = len(binary) // 50  # Limit modifications to 2% of bytes
        
        # Apply glitch effect with limits
        for i in range(len(binary)):
            if binary[i] == replace_val and random.random() > threshold and mod_count < max_mods:
                binary[i] = new_val
                mod_count += 1
        
        # Convert back to image
        try:
            return Image.open(io.BytesIO(binary))
        except Exception as e:
            print(f"Error reading glitched image: {e}")
            return img_copy
    except Exception as e:
        print(f"Error during glitching: {e}")
        return img_copy

def glitch_transition(display, current_image, next_image, frames=12, threshold_start=0.95, threshold_end=0.85):
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
    
    try:
        # First phase: gradually increasing glitch on current image
        for i in range(frames // 2):
            # Calculate threshold - more careful range
            blend_ratio = i / frames
            threshold = threshold_start - (threshold_start - threshold_end) * (2 * blend_ratio)
            
            # Apply glitch to current image
            glitched = apply_glitch(current, threshold)
            
            # Display the glitched image
            display.buffer.paste(glitched)
            display.display()
            display.process_events()
            
            # Small delay between frames
            time.sleep(0.05)
        
        # Second phase: crossfade to next image without additional glitching
        for i in range(frames // 2, frames):
            # Calculate alpha for crossfade
            alpha = (i - frames // 2) / (frames - frames // 2)
            
            # Start with last glitched current image
            if i == frames // 2:
                glitched_current = apply_glitch(current, threshold_end)
            
            # Simple blend without glitching next_img
            try:
                blended = Image.blend(glitched_current, next_img, alpha)
                
                # Display the blended image
                display.buffer.paste(blended)
                display.display() 
                display.process_events()
                
                # Small delay between frames
                time.sleep(0.05)
            except Exception as e:
                print(f"Error during blend: {e}")
                # If blending fails, jump to next image
                display.buffer.paste(next_img)
                display.display()
                display.process_events()
                break
                
        # IMPORTANT: Add a final frame that's exactly the next image
        # This ensures no artifacts remain from the transition
        time.sleep(0.05)  # Brief pause before final frame
        
        # Create a clean copy of the next image
        clean_next = next_img.copy()  
        
        # Explicitly clear the buffer with a complete redraw
        display.buffer = Image.new("RGB", display.buffer.size, (0, 0, 0))
        display.buffer.paste(clean_next)
        display.display()
        display.process_events()
                
    except Exception as e:
        print(f"Error in glitch transition: {e}")
        # If anything fails, fall back to direct display of next image
        display.buffer = Image.new("RGB", display.buffer.size, (0, 0, 0))
        display.buffer.paste(next_image)
        display.display()
        display.process_events()