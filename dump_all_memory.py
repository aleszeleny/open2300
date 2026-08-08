#!/usr/bin/env python3
"""
Dump entire WS2300 memory for comparison
Usage: python3 dump_all_memory.py [output_file] [config_file]
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyopen2300.weatherstation import WeatherStation
from pyopen2300.config import Config


def main():
    """Dump entire WS2300 memory"""
    
    # Get output filename
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"ws2300_memory_dump_{timestamp}.txt"
    
    # Get config file (optional)
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Dumping entire WS2300 memory to: {output_file}")
    print("This may take a few minutes...")
    print("")
    
    # Load configuration
    try:
        config = Config(config_file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Open weather station
    try:
        ws = WeatherStation(config.serial_device_name)
    except Exception as e:
        print(f"Error opening weather station: {e}")
        sys.exit(1)
    
    # Dump entire memory range (0x0000 to 0x1FFF bytes = 0x0000 to 0x3FFE nibbles)
    start_addr = 0x0000
    end_addr = 0x1FFF
    
    try:
        with open(output_file, 'w') as f:
            # Write header
            f.write(f"# WS2300 Memory Dump\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Address range: 0x{start_addr:04X} to 0x{end_addr:04X}\n")
            f.write(f"# Format: Address (nibbles) | Byte Address | Data (hex)\n")
            f.write(f"#\n")
            f.write(f"# To compare two dumps:\n")
            f.write(f"#   diff -u dump1.txt dump2.txt\n")
            f.write(f"#   or: vimdiff dump1.txt dump2.txt\n")
            f.write(f"#\n\n")
            
            addr = start_addr
            total_bytes = 0
            
            while addr <= end_addr:
                # Read up to 15 bytes at a time
                bytes_to_read = min(15, end_addr - addr + 1)
                
                try:
                    data = ws.read_safe(addr, bytes_to_read)
                    if data is None:
                        print(f"Error: Failed to read from address 0x{addr:04X}")
                        break
                    
                    # Write data
                    for i, byte in enumerate(data):
                        byte_addr = addr + i
                        nibble_addr = byte_addr * 2
                        
                        # Format: Address (nibbles) | Byte Address | Data (hex)
                        line = f"{nibble_addr:04X}|{byte_addr:04X} {byte:02X}\n"
                        f.write(line)
                        total_bytes += 1
                    
                    # Progress indicator
                    if addr % 0x100 == 0:
                        print(f"Progress: 0x{addr:04X} / 0x{end_addr:04X} ({addr*100//(end_addr+1)}%)", end='\r')
                    
                    addr += bytes_to_read
                    
                except Exception as e:
                    print(f"\nError reading address 0x{addr:04X}: {e}")
                    break
        
        print(f"\n\nMemory dump complete!")
        print(f"File: {output_file}")
        print(f"Total bytes: {total_bytes}")
        print(f"File size: {os.path.getsize(output_file)} bytes")
        print("")
        print("To compare two dumps:")
        print("  diff -u dump1.txt dump2.txt")
        print("  or:")
        print("  vimdiff dump1.txt dump2.txt")
        
    except Exception as e:
        print(f"Error writing to file: {e}")
        sys.exit(1)
    finally:
        ws.close()


if __name__ == '__main__':
    main()

