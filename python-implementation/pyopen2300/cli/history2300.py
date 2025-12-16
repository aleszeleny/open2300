#!/usr/bin/env python3
"""
history2300 - Read history records from WS2300
Python equivalent of history2300.c
"""

import sys
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("history2300 - Read history records from WS2300")
    print("Usage:")
    print("  history2300 filename start_record end_record [config_file]")
    print()
    print("Records are numbered in hexadecimal (00 to AE)")
    print("Example:")
    print("  history2300 history.txt 00 10")


def main():
    """Main function"""
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)
    
    try:
        filename = sys.argv[1]
        start_record = int(sys.argv[2], 16)
        end_record = int(sys.argv[3], 16)
        config_file = sys.argv[4] if len(sys.argv) > 4 else None
        
        if start_record > 0xAE or end_record > 0xAE:
            print("Error: Record numbers must be between 00 and AE (hex)")
            sys.exit(1)
        
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # First read history info
            data = ws.read_safe(0x6B2, 10)
            if data is None:
                print("Error: Failed to read history info")
                sys.exit(1)
            
            # Open output file
            write_file = filename != "/dev/null"
            if write_file:
                f = open(filename, 'w')
            
            # Each record is 19 nibbles = 10 bytes (last nibble unused)
            # First record starts at address 0x6C6
            
            for record_num in range(start_record, end_record + 1):
                # Calculate address
                address = 0x6C6 + record_num * 19
                
                # Read 10 bytes
                record_data = ws.read_safe(address // 2, 10)
                if record_data is None:
                    print(f"Warning: Failed to read record {record_num:02X}")
                    continue
                
                # Decode record (simplified - full decoding would extract all fields)
                line = f"Record {record_num:02X}: "
                for byte in record_data:
                    line += f"{byte:02X} "
                line += "\n"
                
                print(line, end='')
                if write_file:
                    f.write(line)
            
            if write_file:
                f.close()
                print(f"\nHistory data written to {filename}")
    
    except ValueError as e:
        print(f"Error: Invalid argument - {e}")
        print_usage()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

