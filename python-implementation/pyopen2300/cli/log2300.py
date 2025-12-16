#!/usr/bin/env python3
"""
log2300 - Log current weather data to file
Python equivalent of log2300.c
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("log2300 - Log current weather data to file")
    print("Usage:")
    print("  log2300 logfile [config_file]")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    logfile = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # Get current timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Read data
            ti = ws.temperature_indoor(config.temperature_conv)
            to = ws.temperature_outdoor(config.temperature_conv)
            dp = ws.dewpoint(config.temperature_conv)
            rhi = ws.humidity_indoor()
            rho = ws.humidity_outdoor()
            
            # Read wind speed (simplified)
            data = ws.read_safe(0x527, 3)
            if data:
                wind_speed = ((data[2] >> 4) * 100 + (data[2] & 0xF) * 10 +
                             (data[1] >> 4) + (data[1] & 0xF) / 10.0)
                wind_speed = wind_speed * config.wind_speed_conv_factor / 10.0
                wind_dir = (data[0] & 0x0F) * 22.5  # degrees
            else:
                wind_speed = 0.0
                wind_dir = 0.0
            
            rp = ws.rel_pressure(config.pressure_conv_factor)
            
            # Create log line
            log_line = (f"{timestamp} {ti:.1f} {to:.1f} {dp:.1f} {rhi} {rho} "
                       f"{wind_speed:.1f} {wind_dir:.1f} {rp:.3f}\n")
            
            # Append to log file
            with open(logfile, 'a') as f:
                f.write(log_line)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

