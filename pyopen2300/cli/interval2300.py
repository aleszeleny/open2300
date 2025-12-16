#!/usr/bin/env python3
"""
interval2300 - Read/set history logging interval
Python equivalent of interval2300.c
"""

import sys
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WRITENIB


def print_usage():
    """Print usage information"""
    print("interval2300 - Read or set history logging interval")
    print("Usage:")
    print("  interval2300 0 0 [config_file]              - Read current interval")
    print("  interval2300 interval next [config_file]    - Set interval")
    print()
    print("  interval: Minutes between history records (0 to read only)")
    print("  next: Minutes until next record")


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    try:
        interval = int(sys.argv[1])
        next_record = int(sys.argv[2])
        config_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # History settings are at address 0x6B2
            # Read current settings
            data = ws.read_safe(0x6B2, 10)
            if data is None:
                print("Error: Failed to read history settings")
                sys.exit(1)
            
            # Decode current interval (binary, 3 nibbles)
            current_interval = ((data[1] & 0xF) * 100 + (data[0] >> 4) * 10 + 
                              (data[0] & 0xF)) + 1
            
            # Decode countdown
            countdown = ((data[3] & 0xF) * 100 + (data[2] >> 4) * 10 + 
                        (data[2] & 0xF)) + 1
            
            print(f"Current interval: {current_interval} minutes")
            print(f"Minutes until next record: {countdown}")
            
            if interval == 0:
                # Read only mode
                print("\nRead-only mode (interval=0), no changes made")
            else:
                # Set new interval
                print(f"\nSetting new interval: {interval} minutes")
                print(f"Setting countdown: {next_record} minutes")
                
                # Encode new interval (subtract 1, as per protocol)
                interval_val = interval - 1
                next_val = next_record - 1
                
                # Write interval (3 nibbles)
                interval_nibbles = bytearray([
                    interval_val & 0xF,
                    (interval_val >> 4) & 0xF,
                    (interval_val >> 8) & 0xF
                ])
                
                result = ws.write_safe(0x6B2, 3, WRITENIB, bytes(interval_nibbles))
                if result != 3:
                    print("Error: Failed to write interval")
                    sys.exit(1)
                
                # Write countdown (3 nibbles)
                next_nibbles = bytearray([
                    next_val & 0xF,
                    (next_val >> 4) & 0xF,
                    (next_val >> 8) & 0xF
                ])
                
                result = ws.write_safe(0x6B5, 3, WRITENIB, bytes(next_nibbles))
                if result != 3:
                    print("Error: Failed to write countdown")
                    sys.exit(1)
                
                print("Interval settings updated successfully")
    
    except ValueError as e:
        print(f"Error: Invalid argument - {e}")
        print_usage()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

