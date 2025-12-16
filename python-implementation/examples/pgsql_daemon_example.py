#!/usr/bin/env python3
"""
Example: Long-running PostgreSQL logger daemon

This example shows how to use the PersistentPostgreSQLLogger
for continuous weather data logging with a single database connection.

Features:
- Single database connection (no reconnect overhead)
- Autocommit mode (immediate writes)
- Automatic reconnection on connection loss
- Efficient for frequent logging
"""

import sys
import time
from datetime import datetime

# Add parent directory to path if running from examples directory
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyopen2300.weatherstation import WeatherStation
from pyopen2300.config import Config
from pyopen2300.db.pgsql_logger import PersistentPostgreSQLLogger


def main():
    """Main daemon loop"""
    
    # Load configuration
    config = Config()
    
    if not config.pgsql_connect:
        print("Error: PostgreSQL not configured in open2300.conf")
        sys.exit(1)
    
    # Create persistent logger (connects once at startup)
    logger = PersistentPostgreSQLLogger(
        connection_string=config.pgsql_connect,
        table_name=config.pgsql_table,
        station_name=config.pgsql_station,
        auto_reconnect=True  # Automatically reconnect on connection loss
    )
    
    print(f"PostgreSQL logger started - logging to table '{config.pgsql_table}'")
    print("Logging every 5 minutes. Press Ctrl+C to stop.")
    
    # Open weather station
    ws = WeatherStation(config.serial_device_name)
    
    try:
        while True:
            try:
                # Get timestamp
                timestamp = datetime.now()
                
                # Read weather data
                ti = ws.temperature_indoor(config.temperature_conv)
                to = ws.temperature_outdoor(config.temperature_conv)
                dp = ws.dewpoint(config.temperature_conv)
                rhi = ws.humidity_indoor()
                rho = ws.humidity_outdoor()
                
                # Read wind speed
                data = ws.read_safe(0x527, 3)
                if data:
                    wind_speed = ((data[2] >> 4) * 100 + (data[2] & 0xF) * 10 +
                                 (data[1] >> 4) + (data[1] & 0xF) / 10.0)
                    wind_speed = wind_speed * config.wind_speed_conv_factor / 10.0
                    wind_dir = (data[0] & 0x0F) * 22.5
                else:
                    wind_speed = 0.0
                    wind_dir = 0.0
                
                rp = ws.rel_pressure(config.pressure_conv_factor)
                
                # Log to database (uses prepared statement + autocommit)
                logger.log_data(
                    timestamp=timestamp,
                    temp_in=ti,
                    temp_out=to,
                    dewpoint=dp,
                    humidity_in=rhi,
                    humidity_out=rho,
                    wind_speed=wind_speed,
                    wind_direction=wind_dir,
                    pressure=rp
                )
                
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Temp: {to:.1f}° | Humidity: {rho}% | Pressure: {rp:.1f}")
                
            except Exception as e:
                print(f"Error reading/logging data: {e}")
                # Continue anyway - will retry on next iteration
            
            # Wait 5 minutes
            time.sleep(300)
            
    except KeyboardInterrupt:
        print("\nStopping logger...")
    finally:
        # Clean up
        logger.close()
        ws.close()
        print("Logger stopped.")


if __name__ == '__main__':
    main()

