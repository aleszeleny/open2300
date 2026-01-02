#!/usr/bin/env python3
"""
Example: Long-running PostgreSQL logger daemon with PREPARED STATEMENTS

This example shows how to use PostgreSQL prepared statements for continuous
weather data logging with optimal performance.

Features:
- PostgreSQL PREPARED STATEMENTS (optimal performance)
- Single database connection (no reconnect overhead)
- Autocommit mode (immediate writes)
- Automatic reconnection on connection loss
- Efficient for frequent logging (minimizes query parsing overhead)
"""

import sys
import time
import argparse
from datetime import datetime

# Add parent directory to path if running from examples directory
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyopen2300.weatherstation import WeatherStation
from pyopen2300.config import Config
from pyopen2300.constants import WIND_DIRECTIONS

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class PersistentPostgreSQLLogger:
    """
    Persistent PostgreSQL logger using PREPARED STATEMENTS
    for optimal performance in long-running daemons.
    """
    
    def __init__(self, connection_string: str, table_name: str, 
                 station_name: str = None, auto_reconnect: bool = True):
        """
        Initialize persistent logger with prepared statement
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Table name for weather data
            station_name: Station identifier (optional)
            auto_reconnect: Automatically reconnect on connection loss
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.station_name = station_name
        self.auto_reconnect = auto_reconnect
        self.conn = None
        self.cursor = None
        self.prepared_statement_name = "insert_weather_data"
        self.connect()
    
    def connect(self):
        """Connect to database and prepare statement"""
        try:
            # Connect with autocommit mode
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            
            # PREPARE the INSERT statement on the server
            # This is parsed and planned once, then reused for all executions
            prepare_sql = f"""
                PREPARE {self.prepared_statement_name} (
                    real, real, real, int, int, real, real, text, real,
                    real, real, real, real, text, text
                ) AS
                INSERT INTO {self.table_name} (
                      temperature_indoor
                    , temperature_outdoor
                    , dewpoint
                    , humidity_indoor
                    , humidity_outdoor
                    , wind_speed
                    , wind_angle
                    , wind_direction
                    , wind_chill
                    , rain_1h
                    , rain_24h
                    , rain_total
                    , rel_pressure
                    , tendency
                    , forecast
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """
            
            self.cursor.execute(prepare_sql)
            print(f"Prepared statement '{self.prepared_statement_name}' created on server")
            
        except Exception as e:
            raise IOError(f"Failed to connect to PostgreSQL: {e}")
    
    def log_data(self, temperature_indoor, temperature_outdoor, dewpoint,
                 humidity_indoor, humidity_outdoor, wind_speed,
                 wind_angle, wind_direction, wind_chill,
                 rain_1h, rain_24h, rain_total,
                 rel_pressure, tendency, forecast):
        """
        Log complete weather data using PREPARED STATEMENT
        
        All 15 measurements matching pgsql2300 implementation.
        Uses EXECUTE with the prepared statement for optimal performance.
        """
        if not self.cursor or self.conn.closed:
            if self.auto_reconnect:
                print("Connection lost, reconnecting...")
                self.connect()
            else:
                raise RuntimeError("Not connected to database")
        
        try:
            # EXECUTE the prepared statement with parameters
            # This is much faster than re-parsing the query each time
            self.cursor.execute(
                f"EXECUTE {self.prepared_statement_name} (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    temperature_indoor, temperature_outdoor, dewpoint,
                    humidity_indoor, humidity_outdoor, wind_speed,
                    wind_angle, wind_direction, wind_chill,
                    rain_1h, rain_24h, rain_total,
                    rel_pressure, tendency, forecast
                )
            )
        except psycopg2.errors.UndefinedPreparedStatement:
            # Prepared statement doesn't exist (maybe after reconnect)
            # Recreate it and retry
            print("Prepared statement not found, recreating...")
            self.connect()
            self.cursor.execute(
                f"EXECUTE {self.prepared_statement_name} (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    temperature_indoor, temperature_outdoor, dewpoint,
                    humidity_indoor, humidity_outdoor, wind_speed,
                    wind_angle, wind_direction, wind_chill,
                    rain_1h, rain_24h, rain_total,
                    rel_pressure, tendency, forecast
                )
            )
        except Exception as e:
            if self.auto_reconnect and "connection" in str(e).lower():
                print(f"Connection error: {e}, reconnecting...")
                self.connect()
                # Retry once after reconnection
                self.cursor.execute(
                    f"EXECUTE {self.prepared_statement_name} (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        temperature_indoor, temperature_outdoor, dewpoint,
                        humidity_indoor, humidity_outdoor, wind_speed,
                        wind_angle, wind_direction, wind_chill,
                        rain_1h, rain_24h, rain_total,
                        rel_pressure, tendency, forecast
                    )
                )
            else:
                raise
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            try:
                # Deallocate prepared statement
                self.cursor.execute(f"DEALLOCATE {self.prepared_statement_name}")
            except:
                pass  # Ignore errors if statement doesn't exist
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Main daemon loop - logs all 15 weather measurements using PREPARED STATEMENTS"""
    
    if not HAS_PSYCOPG2:
        print("Error: psycopg2 module not installed.", file=sys.stderr)
        print("Install it with: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='PostgreSQL weather data logger daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use interval from config file (default: 300 seconds)
  %(prog)s -i 60              # Log every 60 seconds
  %(prog)s --interval 600     # Log every 10 minutes
  
Configuration:
  Set PGSQL_DAEMON_INTERVAL in open2300.conf to set default interval (in seconds).
  Command-line parameter overrides config file value.
        """
    )
    parser.add_argument(
        '-i', '--interval',
        type=int,
        metavar='SECONDS',
        help='Logging interval in seconds (overrides config file)'
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        metavar='FILE',
        help='Path to configuration file (default: search standard locations)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    
    if not config.pgsql_connect:
        print("Error: PostgreSQL not configured in open2300.conf")
        print("Add PGSQL_CONNECT to your config file")
        sys.exit(1)
    
    # Determine logging interval (command-line overrides config)
    if args.interval is not None:
        interval = args.interval
        if interval < 1:
            print("Error: Interval must be at least 1 second", file=sys.stderr)
            sys.exit(1)
        print(f"Using command-line interval: {interval} seconds")
    else:
        interval = config.pgsql_daemon_interval
        print(f"Using config file interval: {interval} seconds (from PGSQL_DAEMON_INTERVAL)")
    
    # Create persistent logger with PREPARED STATEMENT
    logger = PersistentPostgreSQLLogger(
        connection_string=config.pgsql_connect,
        table_name=config.pgsql_table,
        station_name=getattr(config, 'pgsql_station', None),
        auto_reconnect=True  # Automatically reconnect on connection loss
    )
    
    print(f"PostgreSQL logger started - logging to table '{config.pgsql_table}'")
    print("Using PREPARED STATEMENTS for optimal performance")
    print(f"Logging ALL 15 weather measurements every {interval} seconds ({interval/60:.1f} minutes)")
    print("Fields: temp, dewpoint, humidity, wind (speed/dir/chill), rain (1h/24h/total), pressure, forecast")
    print("Press Ctrl+C to stop.")
    print()
    
    # Open weather station once
    ws = WeatherStation(config.serial_device_name)
    
    try:
        iteration = 0
        while True:
            iteration += 1
            try:
                # Get timestamp
                timestamp = datetime.now()
                
                # READ ALL WEATHER DATA (matching pgsql2300.py)
                
                # Temperature
                temperature_indoor = ws.temperature_indoor(config.temperature_conv)
                temperature_outdoor = ws.temperature_outdoor(config.temperature_conv)
                dewpoint = ws.dewpoint(config.temperature_conv)
                
                # Humidity
                humidity_indoor = ws.humidity_indoor()
                humidity_outdoor = ws.humidity_outdoor()
                
                # Wind (all data)
                wind_speed, winddir_index, winddir_degrees = ws.wind_all(config.wind_speed_conv_factor)
                wind_angle = winddir_degrees[0]  # Current direction in degrees
                wind_direction = WIND_DIRECTIONS[winddir_index] if winddir_index < len(WIND_DIRECTIONS) else "N"
                
                # Windchill
                wind_chill = ws.windchill(config.temperature_conv)
                
                # Rain
                rain_1h, _, _ = ws.rain_1h_all(config.rain_conv_factor)
                rain_24h, _, _ = ws.rain_24h_all(config.rain_conv_factor)
                rain_total, _ = ws.rain_total_all(config.rain_conv_factor)
                
                # Pressure and forecast
                rel_pressure = ws.rel_pressure(config.pressure_conv_factor)
                tendency, forecast = ws.tendency_forecast()
                
                # Log all 15 fields using PREPARED STATEMENT
                logger.log_data(
                    temperature_indoor=temperature_indoor,
                    temperature_outdoor=temperature_outdoor,
                    dewpoint=dewpoint,
                    humidity_indoor=humidity_indoor,
                    humidity_outdoor=humidity_outdoor,
                    wind_speed=wind_speed,
                    wind_angle=wind_angle,
                    wind_direction=wind_direction,
                    wind_chill=wind_chill,
                    rain_1h=rain_1h,
                    rain_24h=rain_24h,
                    rain_total=rain_total,
                    rel_pressure=rel_pressure,
                    tendency=tendency,
                    forecast=forecast
                )
                
                # Print summary
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] #{iteration:04d} "
                      f"Temp: {temperature_outdoor:.1f}° | "
                      f"Humidity: {humidity_outdoor}% | "
                      f"Wind: {wind_speed:.1f} {wind_direction} | "
                      f"Rain 1h: {rain_1h:.1f} | "
                      f"Pressure: {rel_pressure:.1f} {tendency} | "
                      f"Forecast: {forecast}")
                
            except Exception as e:
                print(f"Error reading/logging data: {e}")
                import traceback
                traceback.print_exc()
                # Continue anyway - will retry on next iteration
            
            # Wait for configured interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nStopping logger...")
    finally:
        # Clean up
        logger.close()
        ws.close()
        print("Logger stopped.")


if __name__ == '__main__':
    main()
