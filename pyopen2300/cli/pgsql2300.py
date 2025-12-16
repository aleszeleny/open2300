#!/usr/bin/env python3
"""
pgsql2300 - Log weather data to PostgreSQL database
Python equivalent of pgsql2300.c
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def print_usage():
    """Print usage information"""
    print("pgsql2300 - Log weather data to PostgreSQL database")
    print("Usage:")
    print("  pgsql2300 [config_file]")
    print()
    print("Configure PostgreSQL connection in config file using PGSQL_CONNECT")
    print("Example: PGSQL_CONNECT hostaddr='127.0.0.1' dbname='open2300' user='postgres' password='pass'")


def main():
    """Main function"""
    if not HAS_PSYCOPG2:
        print("Error: psycopg2 module not installed. Install it with: pip install psycopg2-binary")
        sys.exit(1)
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        if not config.pgsql_connect:
            print("Error: PostgreSQL connection string not configured")
            print_usage()
            sys.exit(1)
        
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
            conn = psycopg2.connect(config.pgsql_connect)
            cur = conn.cursor()
            
            # Insert data
            insert_sql = f"""
                INSERT INTO {config.pgsql_table} 
                (timestamp, station, temp_in, temp_out, dewpoint, 
                 humidity_in, humidity_out, wind_speed, wind_direction, pressure)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_sql, (
                timestamp, config.pgsql_station, ti, to, dp,
                rhi, rho, wind_speed, wind_dir, rp
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"Data logged to PostgreSQL at {timestamp}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

