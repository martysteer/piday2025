#!/usr/bin/env python3
"""
Proxy implementation of DisplayHATMini for macOS
Simulates the DisplayHATMini hardware using pygame for display
"""

import pygame
import sys
from PIL import Image, ImageEnhance

class ST7789:
    """Mock ST7789 class to maintain API compatibility"""
    def __init__(self, port, cs, dc, backlight, width, height, rotation, spi_speed_hz):
        self.width = width
        self.height = height
        self.rotation = rotation
        self.backlight = backlight
    
    def display(self, image):
        # This is handled by DisplayHATMini in our proxy version
        pass
    
    def set_window(self):
        # Not needed in our implementation
        pass
    
    def data(self, data):
        # Not needed in our implementation
        pass
    
    def set_backlight(self, value):
        # Just a stub for API compatibility
        pass

class DisplayHATMini:
    # Match constants from original
    WIDTH = 320
    HEIGHT = 240
    
    # Button constants
    BUTTON_A = 5
    BUTTON_B = 6
    BUTTON_X = 16
    BUTTON_Y = 24
    
    # LED constants
    LED_R = 17
    LED_G = 27
    LED_B = 22
    
    # Other constants for API compatibility
    SPI_PORT = 0
    SPI_CS = 1
    SPI_DC = 9
    BACKLIGHT = 13
    
    def __init__(self, buffer, backlight_pwm=False):
        """Initialize proxy Display HAT Mini emulator"""
        self.buffer = buffer  # This should be a PIL Image
        self.backlight_brightness = 1.0
        self.led_r = 0
        self.led_g = 0
        self.led_b = 0
        self.button_states = {
            self.BUTTON_A: False,
            self.BUTTON_B: False,
            self.BUTTON_X: False,
            self.BUTTON_Y: False
        }
        self.button_callback = None
        
        # Initialize only the pygame modules we need (avoiding audio)
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Display HAT Mini Emulator")
        
        # Create the ST7789 object to maintain API compatibility
        self.st7789 = ST7789(
            port=self.SPI_PORT,
            cs=self.SPI_CS,
            dc=self.SPI_DC,
            backlight=None if backlight_pwm else self.BACKLIGHT,
            width=self.WIDTH,
            height=self.HEIGHT,
            rotation=180,
            spi_speed_hz=60 * 1000 * 1000
        )
        
        # Display initial state
        if self.buffer:
            self.display()
        
        # Show help text on startup
        font = pygame.font.SysFont(None, 18)
        help_text = font.render("Use AB/XY or Arrow keys to simulate buttons", True, (255, 255, 255))
        help_rect = help_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 15))
        self.screen.blit(help_text, help_rect)
        pygame.display.flip()
        
        # Mark that we need to redraw the screen on the next display call
        self.needs_redraw = True
    
    def __del__(self):
        """Clean up pygame on exit"""
        try:
            pygame.display.quit()
            pygame.font.quit()
            pygame.quit()
        except:
            pass
    
    def set_led(self, r=0, g=0, b=0):
        """Set LED color (shown as a colored square in corner)"""
        if r < 0.0 or r > 1.0:
            raise ValueError("r must be in the range 0.0 to 1.0")
        elif g < 0.0 or g > 1.0:
            raise ValueError("g must be in the range 0.0 to 1.0")
        elif b < 0.0 or b > 1.0:
            raise ValueError("b must be in the range 0.0 to 1.0")
        else:
            self.led_r = r
            self.led_g = g
            self.led_b = b
            
            # Draw LED indicator
            led_rect = pygame.Rect(self.WIDTH - 30, 10, 20, 20)
            pygame.draw.rect(
                self.screen, 
                (int(r*255), int(g*255), int(b*255)), 
                led_rect
            )
            pygame.display.update(led_rect)
    
    def set_backlight(self, value):
        """Set backlight brightness (we'll adjust image brightness)"""
        self.backlight_brightness = max(0.0, min(1.0, value))
        self.needs_redraw = True
    
    def on_button_pressed(self, callback):
        """Register callback for button events"""
        self.button_callback = callback
    
    def read_button(self, pin):
        """Read current state of a button"""
        # Process any pending events
        self._process_events()
        return self.button_states.get(pin, False)
    
    def display(self):
        """Update the display with current buffer"""
        # Process any pending events
        self._process_events()
        
        # Make sure we have a buffer
        if not self.buffer:
            return
        
        # Apply backlight effect if needed
        display_image = self.buffer
        if self.backlight_brightness < 1.0 and self.needs_redraw:
            # Create a darker version to simulate backlight
            enhancer = ImageEnhance.Brightness(self.buffer)
            display_image = enhancer.enhance(self.backlight_brightness)
        
        # Convert to pygame surface and display
        mode = display_image.mode
        size = display_image.size
        data = display_image.tobytes()
        surface = pygame.image.fromstring(data, size, mode)
        self.screen.blit(surface, (0, 0))
        
        # Draw button state indicators
        self._draw_button_indicators()
        
        # Draw LED indicator
        led_rect = pygame.Rect(self.WIDTH - 30, 10, 20, 20)
        pygame.draw.rect(
            self.screen, 
            (int(self.led_r*255), int(self.led_g*255), int(self.led_b*255)), 
            led_rect
        )
        
        # Show help text
        font = pygame.font.SysFont(None, 18)
        help_text = font.render("Use WASD or Arrow keys to simulate buttons", True, (255, 255, 255))
        help_rect = help_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 15))
        self.screen.blit(help_text, help_rect)
        
        # Update the display
        pygame.display.flip()
        self.needs_redraw = False
    
    def _draw_button_indicators(self):
        """Draw button state indicators at the top of the screen"""
        buttons = [
            ("A", self.BUTTON_A, 60),
            ("B", self.BUTTON_B, 100),
            ("X", self.BUTTON_X, 140),
            ("Y", self.BUTTON_Y, 180)
        ]
        
        for label, button, x_pos in buttons:
            pressed = self.button_states.get(button, False)
            color = (255, 0, 0) if pressed else (64, 64, 64)
            
            # Draw button
            btn_rect = pygame.Rect(x_pos, 10, 20, 20)
            pygame.draw.rect(self.screen, color, btn_rect)
            
            # Draw label
            font = pygame.font.SysFont(None, 20)
            text = font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, text_rect)
    
    def _process_events(self):
        """Process pygame events for button presses"""
        # Key mapping: Use WASD or arrow keys for A,B,X,Y buttons
        key_map = {
            pygame.K_a: self.BUTTON_A,
            pygame.K_b: self.BUTTON_B,
            pygame.K_x: self.BUTTON_X,
            pygame.K_y: self.BUTTON_Y,
            pygame.K_UP: self.BUTTON_A,
            pygame.K_LEFT: self.BUTTON_B,
            pygame.K_DOWN: self.BUTTON_X,
            pygame.K_RIGHT: self.BUTTON_Y
        }
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in key_map:
                    button = key_map[event.key]
                    # Update button state
                    self.button_states[button] = True
                    # Call callback if registered
                    if self.button_callback:
                        self.button_callback(button)
            elif event.type == pygame.KEYUP:
                if event.key in key_map:
                    button = key_map[event.key]
                    # Update button state
                    self.button_states[button] = False
                    # Call callback if registered
                    if self.button_callback:
                        self.button_callback(button)