# Display HAT Mini Photo Viewer

A versatile photo viewer and slideshow application for the Raspberry Pi Display HAT Mini.

## Installation

1. Save the script as `/home/pi/photo_slideshow.py`
2. Make it executable:
   ```bash
   chmod +x /home/pi/photo_slideshow.py
   ```

## Basic Usage

Run a simple slideshow from the default directory:
```bash
python3 photo_slideshow.py
```

Display a single image:
```bash
python3 photo_slideshow.py --image /path/to/image.jpg
```

Customize slideshow parameters:
```bash
python3 photo_slideshow.py --dir /path/to/photos --delay 5 --transition fade --random
```

## Command Line Arguments

### Image Source Options

| Option | Description |
|--------|-------------|
| `--dir`, `-d` | Directory containing images (default: /home/pi/slideshow_images) |
| `--image`, `-i` | Display a single image instead of a slideshow |

### Slideshow Options

| Option | Description |
|--------|-------------|
| `--delay`, `-t` | Time in seconds between slides (default: 10.0) |
| `--transition`, `-tr` | Transition effect between slides: none, fade, or slide (default: none) |
| `--random`, `-r` | Randomize the order of images (default: sorted by filename) |
| `--no-random` | Do not randomize the order of images |

### Display Options

| Option | Description |
|--------|-------------|
| `--hide-info` | Hide image information overlay |
| `--brightness`, `-b` | Screen brightness level 0.0-1.0 (default: 1.0) |
| `--extensions`, `-e` | Comma-separated list of file extensions to include (default: .jpg,.jpeg,.png,.bmp,.gif) |

## Example Commands

Show all JPG and PNG images from a USB drive with a 5-second delay:
```bash
python3 photo_slideshow.py --dir /media/usb --delay 5 --extensions .jpg,.png
```

Display a slideshow with fade transitions at 80% brightness:
```bash
python3 photo_slideshow.py --dir ~/Pictures --transition fade --brightness 0.8
```

Display a single image in full screen:
```bash
python3 photo_slideshow.py --image ~/Pictures/family.jpg
```

## Button Controls

The Display HAT Mini buttons provide the following controls:

| Button | Function |
|--------|----------|
| A | Previous image |
| B | Next image |
| X | Pause/resume slideshow |
| Y | In slideshow mode: cycle through transition effects<br>In paused mode: toggle image info display |

## Setting Up Autostart

1. Save the startup script as `/home/pi/start_slideshow.sh`
2. Make it executable:
   ```bash
   chmod +x /home/pi/start_slideshow.sh
   ```
3. Edit the script to customize your slideshow settings
4. Create a systemd service to run at startup:
   ```bash
   sudo nano /etc/systemd/system/slideshow.service
   ```
   With the content:
   ```
   [Unit]
   Description=Display HAT Mini Photo Slideshow
   After=multi-user.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi
   ExecStart=/home/pi/start_slideshow.sh
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
5. Enable and start the service:
   ```bash
   sudo systemctl enable slideshow.service
   sudo systemctl start slideshow.service
   ```

## Troubleshooting

- **No images appear**: Check that the image directory exists and contains supported image files
- **Screen turns off**: Disable screen blanking by editing `/etc/lightdm/lightdm.conf` and adding `xserver-command=X -s 0 dpms` to the `[Seat:*]` section
- **Slideshow doesn't start on boot**: Check the systemd service status with `sudo systemctl status slideshow.service`
