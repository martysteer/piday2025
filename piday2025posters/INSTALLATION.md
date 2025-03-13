# Setting Up Display HAT Mini Gallery (to Run at Boot)

Follow these step-by-step instructions to have your Display HAT Mini Image Gallery start automatically whenever your Raspberry Pi boots.

## Prerequisites

1. Make sure you have installed the Display HAT Mini Python library:
   ```bash
   sudo pip3 install displayhatmini
   ```

2. Ensure SPI is enabled on your Raspberry Pi:
   ```bash
   sudo raspi-config nonint do_spi 0
   ```

3. Confirm your scripts are in the correct location (~/piday2025posters/)

## Automated Setup Using Systemd

Systemd is the recommended way to start services at boot on modern Raspberry Pi OS.

### 1. Make the startup script executable

```bash
chmod +x ~/piday2025/piday2025posters/startup-script.sh
```

### 2. Create a new systemd service file

```bash
sudo nano /etc/systemd/system/display-hat-gallery.service
```

Add the following content (modify paths if your scripts are in a different location):

```ini
[Unit]
Description=Display HAT Mini Image Gallery
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/piday2025/piday2025posters
ExecStart=/home/pi/piday2025/piday2025posters/startup-script.sh
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### 3. Enable the service to start at boot

```bash
sudo systemctl enable display-hat-gallery.service
```

### 4. Start the service immediately (optional)

```bash
sudo systemctl start display-hat-gallery.service
```

### 5. Check if the service is running correctly

```bash
sudo systemctl status display-hat-gallery.service
```

You should see "active (running)" if everything is working properly.

## Preventing Screen Blanking

To prevent the screen from turning off after a period of inactivity:

1. Edit the LightDM configuration:
   ```bash
   sudo nano /etc/lightdm/lightdm.conf
   ```

2. Find the `[Seat:*]` section and add:
   ```
   xserver-command=X -s 0 dpms
   ```

3. Save and reboot.

For headless systems without X11/LightDM, add these lines to your startup script instead:
```bash
# Disable screen blanking
export DISPLAY=:0
xset s off
xset -dpms
xset s noblank
```

## Testing

1. Run the startup script manually to ensure it works:
   ```bash
   ~/piday2025/piday2025posters/startup-script.sh
   ```

2. Check the log file for any errors:
   ```bash
   cat ~/piday2025/piday2025posters/gallery.log
   ```

3. Reboot your Raspberry Pi to ensure everything starts automatically:
   ```bash
   sudo reboot
   ```

## Troubleshooting

- **Gallery doesn't start**: Check systemd logs with `sudo journalctl -u display-hat-gallery.service`
- **No images displayed**: Verify that ~/piday2025posters/images/ contains valid image files
- **Python errors**: Make sure all required libraries are installed with `pip3 install -r requirements.txt` (if available)
- **Screen turns off**: Double-check the screen blanking prevention steps
