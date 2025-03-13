# Setting Up Display HAT Mini Gallery (to Run at Boot)

This guide provides step-by-step instructions to set up your Display HAT Mini Image Gallery to start automatically whenever your Raspberry Pi boots.

## Prerequisites

1. Install the Display HAT Mini Python library:
   ```bash
   sudo pip3 install displayhatmini
   ```

2. Enable SPI on your Raspberry Pi:
   ```bash
   sudo raspi-config nonint do_spi 0
   ```

3. Ensure your scripts are in the correct location (~/piday2025/piday2025posters/)

## Setup Using Systemd

### 1. Make the startup script executable

```bash
chmod +x ~/piday2025/piday2025posters/startup-script.sh
```

### 2. Create a systemd service file

```bash
sudo nano /etc/systemd/system/display-hat-gallery.service
```

Add the following content:

```ini
[Unit]
Description=Display HAT Mini Image Gallery
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/piday2025/piday2025posters
ExecStart=/home/pi/piday2025/piday2025posters/startup-script.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### 3. Add user to required groups

Ensure your pi user has the necessary permissions:

```bash
sudo usermod -a -G gpio,spi,i2c,video pi
```

### 4. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable display-hat-gallery.service
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

## Troubleshooting

If your service isn't starting properly, try these steps:

1. Check the service logs:
   ```bash
   sudo journalctl -u display-hat-gallery.service
   ```

2. Verify the gallery log file:
   ```bash
   cat ~/piday2025/piday2025posters/gallery.log
   ```

3. Test the startup script manually:
   ```bash
   ~/piday2025/piday2025posters/startup-script.sh
   ```

4. If your system is using X11 and the service needs display access, edit the service:
   ```bash
   sudo systemctl edit display-hat-gallery.service
   ```
   
   Add between the comments:
   ```ini
   [Service]
   Environment="DISPLAY=:0"
   Environment="XAUTHORITY=/home/pi/.Xauthority"
   ```

5. Check SPI is enabled:
   ```bash
   sudo raspi-config nonint get_spi
   ```
   (Should return 0 for enabled)

6. Reboot your Raspberry Pi after making changes:
   ```bash
   sudo reboot
   ```