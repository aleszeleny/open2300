#!/usr/bin/env python3
"""
open2300 - Low-level read/write tool for WS2300 weather station
Python equivalent of open2300.c
"""

import sys
import argparse
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WRITENIB, SETBIT, UNSETBIT


def print_usage():
    """Print usage information"""
    print("open2300 - Low-level read/write tool for WS2300")
    print("Usage:")
    print("  Read bytes:    open2300 address_hex r number_of_bytes [config_file]")
    print("  Write nibbles: open2300 address_hex w text_hex_string [config_file]")
    print("  Set bits:      open2300 address_hex s bit_number [config_file]")
    print("  Unset bits:    open2300 address_hex c bit_number [config_file]")
    print()
    print("Examples:")
    print("  open2300 346 r 2          # Read 2 bytes from address 0x346")
    print("  open2300 23B w 0123       # Write nibbles 0,1,2,3 to address 0x23B")
    print("  open2300 100 s 2          # Set bit 2 at address 0x100")
    print("  open2300 100 c 2          # Clear bit 2 at address 0x100")


def main():
    """Main function"""
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)
    
    # Parse arguments
    try:
        address = int(sys.argv[1], 16)
        operation = sys.argv[2].lower()
        
        config_file = sys.argv[-1] if len(sys.argv) > 4 and not sys.argv[-1].isdigit() else None
        
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            if operation == 'r':
                # Read bytes
                num_bytes = int(sys.argv[3])
                if num_bytes < 1 or num_bytes > 15:
                    print("Error: Number of bytes must be between 1 and 15")
                    sys.exit(1)
                
                data = ws.read_safe(address, num_bytes)
                if data is None:
                    print("Error: Failed to read from weather station")
                    sys.exit(1)
                
                # Print as hex
                print(f"Address 0x{address:04X}:")
                for i, byte in enumerate(data):
                    print(f"  [{i}] 0x{byte:02X} ({byte})")
            
            elif operation == 'w':
                # Write nibbles
                hex_string = sys.argv[3]
                writedata = bytearray()
                
                for char in hex_string:
                    try:
                        writedata.append(int(char, 16))
                    except ValueError:
                        print(f"Error: Invalid hex character '{char}'")
                        sys.exit(1)
                
                result = ws.write_safe(address, len(writedata), WRITENIB, bytes(writedata))
                if result != len(writedata):
                    print("Error: Failed to write to weather station")
                    sys.exit(1)
                
                print(f"Successfully wrote {len(writedata)} nibbles to address 0x{address:04X}")
            
            elif operation == 's':
                # Set bit
                bit_number = int(sys.argv[3])
                if bit_number < 0 or bit_number > 3:
                    print("Error: Bit number must be between 0 and 3")
                    sys.exit(1)
                
                result = ws.write_safe(address, 1, SETBIT, bytes([bit_number]))
                if result != 1:
                    print("Error: Failed to set bit")
                    sys.exit(1)
                
                print(f"Successfully set bit {bit_number} at address 0x{address:04X}")
            
            elif operation == 'c':
                # Unset bit
                bit_number = int(sys.argv[3])
                if bit_number < 0 or bit_number > 3:
                    print("Error: Bit number must be between 0 and 3")
                    sys.exit(1)
                
                result = ws.write_safe(address, 1, UNSETBIT, bytes([bit_number]))
                if result != 1:
                    print("Error: Failed to unset bit")
                    sys.exit(1)
                
                print(f"Successfully unset bit {bit_number} at address 0x{address:04X}")
            
            else:
                print(f"Error: Unknown operation '{operation}'")
                print_usage()
                sys.exit(1)
    
    except ValueError as e:
        print(f"Error: Invalid argument - {e}")
        print_usage()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

