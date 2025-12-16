#!/usr/bin/env python3
"""
dump2300 - Dump memory range from WS2300 weather station
Python equivalent of dump2300.c
"""

import sys
import argparse
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("dump2300 - Dump memory range from WS2300 weather station")
    print("Usage:")
    print("  dump2300 filename start_address end_address [config_file]")
    print()
    print("Addresses are in hexadecimal (nibbles)")
    print("Example:")
    print("  dump2300 dump.txt 21C 3A1")


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
            # Open output file (use /dev/null to skip file output)
            write_file = filename != "/dev/null"
            if write_file:
                f = open(filename, 'w')
            
            # Read and dump memory
            addr = start_byte
            while addr <= end_byte:
                # Read up to 15 bytes at a time
                bytes_to_read = min(15, end_byte - addr + 1)
                
                data = ws.read_safe(addr, bytes_to_read)
                if data is None:
                    print(f"Error: Failed to read from address 0x{addr:04X}")
                    if write_file:
                        f.close()
                    sys.exit(1)
                
                # Print and write data
                for i, byte in enumerate(data):
                    nibble_addr = (addr + i) * 2
                    high_nibble = (byte >> 4) & 0x0F
                    low_nibble = byte & 0x0F
                    
                    line = f"{nibble_addr:04X}: {high_nibble:X}{low_nibble:X}\n"
                    print(line, end='')
                    if write_file:
                        f.write(line)
                
                addr += bytes_to_read
            
            if write_file:
                f.close()
                print(f"\nData written to {filename}")
    
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

