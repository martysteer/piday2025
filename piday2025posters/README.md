# Display HAT Mini Tools

A collection of tools and applications for using the Pimoroni Display HAT Mini with Raspberry Pi.

## Installation

1. Install the Display HAT Mini Python library if you haven't already:
   ```bash
   sudo pip3 install displayhatmini
   ```

2. Enable SPI interface on your Raspberry Pi:
   ```bash
   sudo raspi-config nonint do_spi 0
   ```

3. Clone this repository or copy the scripts to your Raspberry Pi.

## Available Tools

### Display Tester (`display-tester.py`)

A simple utility to test your Display HAT Mini by showing a colored rectangle.

**Usage:**
```bash
python3 display-tester.py [--size WIDTHxHEIGHT] [--color HEX_COLOR]
```

**Examples:**
```bash
# Display a full-screen magenta rectangle
python3 display-tester.py --color FF00FF

# Display a smaller green rectangle
python3 display-tester.py --size 160x120 --color 00FF00
```

### Image Viewer (`display-image.py`)

A simple image viewer for displaying a single image with transformation capabilities.

**Usage:**
```bash
python3 display-image.py IMAGE_PATH [options]
```

**Examples:**
```bash
# Display an image
python3 display-image.py images/photo.jpg

# Display in portrait orientation with 80% brightness
python3 display-image.py images/photo.jpg --portrait --brightness 0.8
```

**Button Controls:**
- **A**: Flip image horizontally
- **B**: Rotate image 90° clockwise
- **X**: Toggle info overlay
- **Y**: Clear screen and quit

### Image Gallery (`image-gallery.py`)

A feature-rich image gallery for browsing and viewing multiple images with slideshow capabilities.

**Usage:**
```bash
python3 image-gallery.py [DIRECTORY] [options]
```

**Examples:**
```bash
# Browse images in the current directory
python3 image-gallery.py

# Start a slideshow with fade transitions and 3-second delay
python3 image-gallery.py images/ --slideshow --transition fade --delay 3
```

**Button Controls:**
- **A**: Previous image
- **B**: Next image
- **X** (short press): Toggle slideshow mode
- **X** (long press): Settings menu
- **Y** (short press): Toggle info overlay
- **Y** (long press): Transform menu

**Settings Menu Options:**
- Slideshow Mode: Enable/disable automatic slideshow
- Show Info: Toggle image information overlay
- Orientation: Switch between landscape and portrait
- Transition: Choose between none, fade, or slide transitions
- Slide Direction: Right-to-left or left-to-right
- Sort Method: Sort images by name, date, size, or randomly
- Slide Delay: Time between slides (1-15 seconds)
- Brightness: Display brightness (0.1-1.0)