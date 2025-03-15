# displayhatproxy.py
import platform
import os
import sys

# Determine which implementation to use based on platform
if platform.system() == "Darwin":  # macOS
    try:
        # First try to import from the current directory
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


# After importing DisplayHATMini, setup platform-specific processing method
# Call process_events() in your render loop to ensure display updates on all platforms.
if platform.system() == "Darwin":
    # For macOS proxy version
    DisplayHATMini.process_events = lambda self: self.display()
else:
    # For actual hardware, no action needed
    DisplayHATMini.process_events = lambda self: None


# Re-export the DisplayHATMini class
__all__ = ['DisplayHATMini']