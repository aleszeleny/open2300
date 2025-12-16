#!/usr/bin/env python3
"""
sqlitelog2300 - Log weather data to SQLite database
Python equivalent of sqlitelog2300.c
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("sqlitelog2300 - Log weather data to SQLite database")
    print("Usage:")
    print("  sqlitelog2300 database_file [config_file]")
    print()
    print("If database doesn't exist, it will be created with required table")


def create_table(conn):
    """Create weather table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            temp_in REAL,
            temp_out REAL,
            dewpoint REAL,
            humidity_in INTEGER,
            humidity_out INTEGER,
            wind_speed REAL,
            wind_direction REAL,
            pressure REAL
        )
    """)
    conn.commit()


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    db_file = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # Get current timestamp
            timestamp = datetime.now()
            
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
            
            # Connect to database
            conn = sqlite3.connect(db_file)
            
            # Create table if needed
            create_table(conn)
            
            # Insert data
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather 
                (timestamp, temp_in, temp_out, dewpoint, humidity_in, humidity_out,
                 wind_speed, wind_direction, pressure)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, ti, to, dp, rhi, rho, wind_speed, wind_dir, rp))
            
            conn.commit()
            conn.close()
            
            print(f"Data logged to SQLite database at {timestamp}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

