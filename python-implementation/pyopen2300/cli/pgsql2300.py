#!/usr/bin/env python3
"""
pgsql2300 - Log weather data to PostgreSQL database
Python equivalent of pgsql2300.c

Uses prepared statements and autocommit mode for efficient logging.
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config

try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class PostgreSQLLogger:
    """
    PostgreSQL logger with prepared statements and autocommit mode
    """
    
    def __init__(self, connection_string: str, table_name: str, station_name: str):
        """
        Initialize PostgreSQL logger
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to insert into
            station_name: Name of this weather station
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.station_name = station_name
        self.conn = None
        self.cursor = None
        self.prepared_statement_name = "insert_weather_data"
        
    def connect(self):
        """Connect to database and prepare statement"""
        try:
            # Connect with autocommit mode enabled
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            
            self.cursor = self.conn.cursor()
            
            # Prepare the INSERT statement
            # Note: psycopg2 doesn't have native PREPARE STATEMENT support like PostgreSQL,
            # but using parameterized queries achieves similar benefits (query plan caching)
            self.insert_query = sql.SQL("""
                INSERT INTO {} 
                (timestamp, station, temp_in, temp_out, dewpoint, 
                 humidity_in, humidity_out, wind_speed, wind_direction, pressure)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(sql.Identifier(self.table_name))
            
            # PostgreSQL will cache the query plan after first execution
            
        except Exception as e:
            raise IOError(f"Failed to connect to PostgreSQL: {e}")
    
    def log_data(self, timestamp, temp_in, temp_out, dewpoint,
                 humidity_in, humidity_out, wind_speed, wind_direction, pressure):
        """
        Log weather data using prepared statement
        
        Args:
            timestamp: Datetime of measurement
            temp_in: Indoor temperature
            temp_out: Outdoor temperature
            dewpoint: Dewpoint temperature
            humidity_in: Indoor humidity (%)
            humidity_out: Outdoor humidity (%)
            wind_speed: Wind speed
            wind_direction: Wind direction (degrees)
            pressure: Atmospheric pressure
        """
        if not self.cursor:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        try:
            # Execute with parameters
            # With autocommit enabled, this commits immediately
            self.cursor.execute(self.insert_query, (
                timestamp,
                self.station_name,
                temp_in,
                temp_out,
                dewpoint,
                humidity_in,
                humidity_out,
                wind_speed,
                wind_direction,
                pressure
            ))
            
        except Exception as e:
            raise IOError(f"Failed to insert data: {e}")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


def print_usage():
    """Print usage information"""
    print("pgsql2300 - Log weather data to PostgreSQL database")
    print("Usage:")
    print("  pgsql2300 [config_file]")
    print()
    print("Configure PostgreSQL connection in config file using PGSQL_CONNECT")
    print("Example: PGSQL_CONNECT hostaddr='127.0.0.1' dbname='open2300' user='postgres' password='pass'")
    print()
    print("Features:")
    print("  - Uses autocommit mode for immediate writes")
    print("  - Parameterized queries for query plan caching")
    print("  - Efficient for repeated logging operations")


def main():
    """Main function"""
    if not HAS_PSYCOPG2:
        print("Error: psycopg2 module not installed.")
        print("Install it with: pip install psycopg2-binary (x86/x64)")
        print("           or: pip install psycopg2 (Raspberry Pi/ARM)")
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
            
            # Read data from weather station
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
            
            # Log to database using prepared statement and autocommit
            with PostgreSQLLogger(config.pgsql_connect, 
                                 config.pgsql_table, 
                                 config.pgsql_station) as db:
                
                db.log_data(
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
            
            print(f"Data logged to PostgreSQL at {timestamp}")
            if config.log_level >= 2:
                print(f"  Temperature: {to:.1f}° (out), {ti:.1f}° (in)")
                print(f"  Humidity: {rho}% (out), {rhi}% (in)")
                print(f"  Pressure: {rp:.1f}")
                print(f"  Wind: {wind_speed:.1f} at {wind_dir:.0f}°")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
