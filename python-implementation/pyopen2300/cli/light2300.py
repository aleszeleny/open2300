#!/usr/bin/env python3
"""
light2300 - Control LCD backlight of WS2300 weather station
Python equivalent of light2300.c
"""

import sys
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WRITENIB


def print_usage():
    """Print usage information"""
    print("light2300 - Control LCD backlight of WS2300 weather station")
    print("Usage:")
    print("  light2300 on [config_file]   - Turn backlight on")
    print("  light2300 off [config_file]  - Turn backlight off")


def light(ws: WeatherStation, control: int):
    """
    Control LCD backlight
    
    Args:
        ws: WeatherStation instance
        control: 1 for on, 0 for off
    """
    # Address for backlight control
    address = 0x016
    
    # Write control value
    data = bytes([control])
    result = ws.write_safe(address, 1, WRITENIB, data)
    
    if result != 1:
        raise IOError("Failed to control backlight")


def main():
    """Main function"""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command not in ['on', 'off']:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            if command == 'on':
                light(ws, 1)
                print("Backlight turned on")
            else:
                light(ws, 0)
                print("Backlight turned off")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

