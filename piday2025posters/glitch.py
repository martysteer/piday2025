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
    import random
    
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
    import random
    import io
    from PIL import Image
    
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


def glitch_transition(display, current_image, next_image, frames=8, threshold_start=0.92, threshold_end=0.82):
    """
    Perform a direct glitch transition between two images without crossfade.
    The transition increases glitch intensity and then directly shows the next image.
    
    Args:
        display: DisplayHATMini instance
        current_image: Starting PIL Image
        next_image: Ending PIL Image
        frames: Number of frames in the transition
        threshold_start: Starting threshold (less glitchy)
        threshold_end: Ending threshold (more glitchy)
    """
    # Create new copies to avoid modifying originals
    current = current_image.copy()
    
    # Get display dimensions
    width, height = display.buffer.size
    
    try:
        # Phase 1: gradually increase glitch on current image
        for i in range(frames):
            # Calculate threshold - gradually increase glitch intensity
            blend_ratio = i / frames
            threshold = threshold_start - (threshold_start - threshold_end) * blend_ratio
            
            # Create a fresh buffer for this frame
            frame_buffer = Image.new("RGB", (width, height), (0, 0, 0))
            
            # Apply glitch to current image with increasing intensity
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
            time.sleep(0.04)
        
        # Phase 2: Directly show next image (no fade)
        final_buffer = Image.new("RGB", (width, height), (0, 0, 0))
        final_buffer.paste(next_image)
        
        # Update the display with the next image
        display.buffer.paste(final_buffer)
        display.display()
        display.process_events()
        
        # Clean up
        del final_buffer
                
    except Exception as e:
        print(f"Error in glitch transition: {e}")
        # If anything fails, fall back to direct display of next image
        clean_buffer = Image.new("RGB", (width, height), (0, 0, 0))
        clean_buffer.paste(next_image)
        display.buffer.paste(clean_buffer)
        display.display()
        display.process_events()


