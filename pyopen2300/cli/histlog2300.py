#!/usr/bin/env python3
"""
histlog2300 - Log history data from WS2300
Python equivalent of histlog2300.c
"""

import sys
from datetime import datetime, timedelta
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("histlog2300 - Log history data from WS2300 weather station")
    print("Usage:")
    print("  histlog2300 logfile [config_file]")
    print()
    print("Reads new history records since last log and appends to logfile")


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
            # Read history info from address 0x6B2
            data = ws.read_safe(0x6B2, 20)
            if data is None:
                print("Error: Failed to read history info")
                sys.exit(1)
            
            # Decode history settings
            # Interval (3 nibbles at 0x6B2-0x6B4)
            interval = ((data[1] & 0xF) * 100 + (data[0] >> 4) * 10 + 
                       (data[0] & 0xF)) + 1
            
            # Last record timestamp (BCD at 0x6B8-0x6C1)
            last_minute = (data[3] >> 4) * 10 + (data[3] & 0xF)
            last_hour = (data[4] >> 4) * 10 + (data[4] & 0xF)
            last_day = (data[5] >> 4) * 10 + (data[5] & 0xF)
            last_month = (data[6] >> 4) * 10 + (data[6] & 0xF)
            last_year = 2000 + (data[7] >> 4) * 10 + (data[7] & 0xF)
            
            # Pointer to last record (2 nibbles at 0x6C2-0x6C3)
            last_record = (data[9] & 0xF) * 16 + (data[8] >> 4)
            
            # Number of valid records (2 nibbles at 0x6C4-0x6C5)
            num_records = (data[10] & 0xF) * 16 + (data[9] >> 4)
            
            print(f"History interval: {interval} minutes")
            print(f"Last record: {last_year}-{last_month:02d}-{last_day:02d} "
                  f"{last_hour:02d}:{last_minute:02d}")
            print(f"Last record pointer: 0x{last_record:02X}")
            print(f"Number of records: {num_records}")
            
            # In a full implementation, we would:
            # 1. Read the last timestamp from the log file
            # 2. Calculate how many records to read based on time difference
            # 3. Read and decode those records
            # 4. Append them to the log file
            
            print("\nNote: Full history logging implementation requires:")
            print("  - Reading last log entry timestamp")
            print("  - Calculating records to fetch based on interval")
            print("  - Decoding all record fields (temp, humidity, pressure, etc.)")
            print("  - Appending to log file in proper format")
            print("\nThis is a simplified placeholder implementation.")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

