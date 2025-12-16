#!/usr/bin/env python3
"""
bin2300 - Dump memory range in binary format from WS2300 weather station
Python equivalent of bin2300.c
"""

import sys
import argparse
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("bin2300 - Dump memory range in binary format from WS2300 weather station")
    print("Usage:")
    print("  bin2300 filename start_address end_address [config_file]")
    print()
    print("Addresses are in hexadecimal (nibbles)")
    print("Each nibble is saved as one byte in the file (value 00 to 0F)")
    print("Example:")
    print("  bin2300 dump.bin 21C 3A1")


def main():
    """Main function"""
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)
    
    try:
        filename = sys.argv[1]
        start_addr = int(sys.argv[2], 16)
        end_addr = int(sys.argv[3], 16)
        
        config_file = sys.argv[4] if len(sys.argv) > 4 else None
        
        # Ensure even number of nibbles (round up)
        if start_addr % 2 != 0:
            start_addr -= 1
        if end_addr % 2 != 0:
            end_addr += 1
        
        # Convert nibble addresses to byte addresses
        start_byte = start_addr // 2
        end_byte = end_addr // 2
        
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # Open output file in binary mode
            with open(filename, 'wb') as f:
                # Read and dump memory
                addr = start_byte
                while addr <= end_byte:
                    # Read up to 15 bytes at a time
                    bytes_to_read = min(15, end_byte - addr + 1)
                    
                    data = ws.read_safe(addr, bytes_to_read)
                    if data is None:
                        print(f"Error: Failed to read from address 0x{addr:04X}")
                        sys.exit(1)
                    
                    # Write each nibble as a separate byte
                    for byte in data:
                        high_nibble = (byte >> 4) & 0x0F
                        low_nibble = byte & 0x0F
                        f.write(bytes([high_nibble, low_nibble]))
                    
                    addr += bytes_to_read
                
                print(f"Data written to {filename}")
    
    except ValueError as e:
        print(f"Error: Invalid argument - {e}")
        print_usage()
        sys.exit(1)
    except IOError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

