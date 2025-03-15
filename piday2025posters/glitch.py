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
    Generate safer random indices for glitching, avoiding critical JPEG header bytes
    """
    # These are indices to avoid, expanded to include more critical bytes
    avoid_indices = [0, 1, 2, 3, 4, 6, 7, 8, 9, 12, 16, 17, 24, 29, 34, 
                    255, 216, 217, 218, 219, 192, 193, 194, 195]
    
    # Generate random index
    index = random.randint(50, 150)  # Reduced range to safer bytes
    
    # Regenerate if in avoid_indices
    while index in avoid_indices:
        index = random.randint(50, 150)
    
    # Return both indices, being more careful with the replacement value
    return index, random.randint(50, 130)

def apply_glitch(img, threshold=0.9):
    """
    Apply glitch effect to a PIL Image with improved safety checks
    
    Args:
        img: PIL Image to glitch
        threshold: Threshold value between 0.85 and 0.995
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
        img_copy.save(buffer, format="JPEG", quality=92)
        jpeg_bytes = buffer.getvalue()
        
        # Convert to bytearray for modification
        binary = bytearray(jpeg_bytes)
        
        # Get random indices for glitching
        replace_val, new_val = get_random_indices()
        
        # Count modifications to limit corruption
        mod_count = 0
        max_mods = len(binary) // 200  # Limit modifications to 0.5% of bytes for safety
        
        # Apply glitch effect with limits
        for i in range(len(binary)):
            # Skip the first 500 bytes to avoid JPEG header corruption
            if i < 500:
                continue
                
            if binary[i] == replace_val and random.random() > threshold and mod_count < max_mods:
                binary[i] = new_val
                mod_count += 1
        
        # Convert back to image
        try:
            glitched_img = Image.open(io.BytesIO(binary))
            # Convert to RGB to ensure consistency
            if glitched_img.mode != "RGB":
                glitched_img = glitched_img.convert("RGB")
            return glitched_img
        except Exception as e:
            print(f"Error reading glitched image: {e}")
            return img_copy
    except Exception as e:
        print(f"Error during glitching: {e}")
        return img_copy

def glitch_transition(display, current_image, next_image, frames=12, threshold_start=0.95, threshold_end=0.85):
    """
    Perform a glitch transition between two images with improved buffer management
    to prevent flashing of previous images.
    
    Args:
        display: DisplayHATMini instance
        current_image: Starting PIL Image
        next_image: Ending PIL Image
        frames: Number of frames in the transition
        threshold_start: Starting threshold (less glitchy)
        threshold_end: Ending threshold (more glitchy)
    """
    # Create new copies to avoid modifying originals
    # This prevents any cross-contamination from previous transitions
    current = current_image.copy()
    next_img = next_image.copy()
    
    # Get display dimensions
    width, height = display.buffer.size
    
    try:
        # First phase: gradually increasing glitch on current image
        for i in range(frames // 2):
            # Calculate threshold
            blend_ratio = i / (frames // 2)
            threshold = threshold_start - (threshold_start - threshold_end) * blend_ratio
            
            # Create a fresh buffer for this frame
            frame_buffer = Image.new("RGB", (width, height), (0, 0, 0))
            
            # Apply glitch to current image
            glitched = apply_glitch(current, threshold)
            
            # Paste the glitched image into the fresh buffer
            frame_buffer.paste(glitched)
            
            # Update the display with this frame
            display.buffer.paste(frame_buffer)
            display.display()
            display.process_events()
            
            # Clean up to prevent memory leaks
            del glitched
            del frame_buffer
            
            # Small delay between frames
            time.sleep(0.05)
        
        # Get one final glitched version of the current image
        final_glitched = apply_glitch(current, threshold_end)
        
        # Second phase: crossfade from glitched current image to clean next image
        for i in range(frames // 2 + 1):
            # Calculate alpha for crossfade
            alpha = i / (frames // 2)
            
            # Create a fresh buffer for this frame
            frame_buffer = Image.new("RGB", (width, height), (0, 0, 0))
            
            # Blend the images
            blended = Image.blend(final_glitched, next_img, alpha)
            
            # Paste the blended image into the fresh buffer
            frame_buffer.paste(blended)
            
            # Update the display with this frame
            display.buffer.paste(frame_buffer)
            display.display()
            display.process_events()
            
            # Clean up to prevent memory leaks
            del blended
            del frame_buffer
            
            # Small delay between frames
            time.sleep(0.05)
        
        # IMPORTANT: Ensure final frame is exactly the next image with no artifacts
        # Create a fresh buffer for the final frame
        final_buffer = Image.new("RGB", (width, height), (0, 0, 0))
        final_buffer.paste(next_img)
        
        # Update the display with the final image
        display.buffer.paste(final_buffer)
        display.display()
        display.process_events()
        
        # Clean up
        del final_buffer
        del final_glitched
                
    except Exception as e:
        print(f"Error in glitch transition: {e}")
        # If anything fails, fall back to direct display of next image
        clean_buffer = Image.new("RGB", (width, height), (0, 0, 0))
        clean_buffer.paste(next_image)
        display.buffer.paste(clean_buffer)
        display.display()
        display.process_events()