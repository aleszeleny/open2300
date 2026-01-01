#!/usr/bin/env python3
"""
pgsql2300 - Log weather data to PostgreSQL database
Python equivalent of pgsql2300.c

Reads all weather measurements and logs them to PostgreSQL database.
Matches the C implementation exactly.
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WIND_DIRECTIONS

try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class PostgreSQLLogger:
    """
    PostgreSQL logger matching C implementation
    """
    
    def __init__(self, connection_string: str, table_name: str, station_name: str = None):
        """
        Initialize PostgreSQL logger
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to insert into
            station_name: Name of this weather station (optional)
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.station_name = station_name
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            
        except Exception as e:
            raise IOError(f"Failed to connect to PostgreSQL: {e}")
    
    def log_data(self, temperature_indoor, temperature_outdoor, dewpoint,
                 humidity_indoor, humidity_outdoor, wind_speed,
                 wind_angle, wind_direction, wind_chill,
                 rain_1h, rain_24h, rain_total,
                 rel_pressure, tendency, forecast):
        """
        Log weather data to database
        
        Args match the C implementation exactly:
            temperature_indoor: Indoor temperature
            temperature_outdoor: Outdoor temperature
            dewpoint: Dewpoint temperature
            humidity_indoor: Indoor humidity (%)
            humidity_outdoor: Outdoor humidity (%)
            wind_speed: Wind speed
            wind_angle: Wind direction (degrees)
            wind_direction: Wind direction (text: N, NNE, etc.)
            wind_chill: Windchill temperature
            rain_1h: Rain in last hour
            rain_24h: Rain in last 24 hours
            rain_total: Total rain since reset
            rel_pressure: Relative atmospheric pressure
            tendency: Pressure tendency (Steady/Rising/Falling)
            forecast: Weather forecast (Rainy/Cloudy/Sunny)
        """
        if not self.cursor:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        try:
            # Build INSERT query matching C version structure
            insert_query = sql.SQL("""
                INSERT INTO {} (
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
                ) VALUES (
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """).format(sql.Identifier(self.table_name))
            
            # Execute with parameters
            self.cursor.execute(insert_query, (
                temperature_indoor,
                temperature_outdoor,
                dewpoint,
                humidity_indoor,
                humidity_outdoor,
                wind_speed,
                wind_angle,
                wind_direction,
                wind_chill,
                rain_1h,
                rain_24h,
                rain_total,
                rel_pressure,
                tendency,
                forecast
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
    print("Data logged (matching C version):")
    print("  - Indoor/Outdoor temperature and dewpoint")
    print("  - Indoor/Outdoor humidity")
    print("  - Wind speed, direction, and windchill")
    print("  - Rain (1h, 24h, total)")
    print("  - Relative pressure, tendency, and forecast")


def main():
    """Main function - matches C version pgsql2300.c"""
    if not HAS_PSYCOPG2:
        print("Error: psycopg2 module not installed.", file=sys.stderr)
        print("Install it with: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        if not config.pgsql_connect:
            print("Error: PostgreSQL connection string not configured", file=sys.stderr)
            print_usage()
            sys.exit(1)
        
        # Open weather station
        print(f"LOG: Opening weather station on {config.serial_device_name}", file=sys.stderr)
        with WeatherStation(config.serial_device_name) as ws:
            print("LOG: Reading weather data...", file=sys.stderr)
            
            # READ TEMPERATURE INDOOR
            print("LOG: READ TEMPERATURE INDOOR", file=sys.stderr)
            temperature_indoor = ws.temperature_indoor(config.temperature_conv)
            
            # READ TEMPERATURE OUTDOOR
            print("LOG: READ TEMPERATURE OUTDOOR", file=sys.stderr)
            temperature_outdoor = ws.temperature_outdoor(config.temperature_conv)
            
            # READ DEWPOINT
            print("LOG: READ DEWPOINT", file=sys.stderr)
            dewpoint = ws.dewpoint(config.temperature_conv)
            
            # READ RELATIVE HUMIDITY INDOOR
            print("LOG: READ RELATIVE HUMIDITY INDOOR", file=sys.stderr)
            humidity_indoor = ws.humidity_indoor()
            
            # READ RELATIVE HUMIDITY OUTDOOR
            print("LOG: READ RELATIVE HUMIDITY OUTDOOR", file=sys.stderr)
            humidity_outdoor = ws.humidity_outdoor()
            
            # READ WIND SPEED AND DIRECTION AND WINDCHILL
            print("LOG: READ WIND SPEED AND DIRECTION", file=sys.stderr)
            wind_speed, winddir_index, winddir_degrees = ws.wind_all(config.wind_speed_conv_factor)
            wind_angle = winddir_degrees[0]  # Current direction in degrees
            wind_direction = WIND_DIRECTIONS[winddir_index] if winddir_index < len(WIND_DIRECTIONS) else "N"
            
            # READ WINDCHILL
            print("LOG: READ WINDCHILL", file=sys.stderr)
            wind_chill = ws.windchill(config.temperature_conv)
            
            # READ RAIN 1H
            print("LOG: READ RAIN 1H", file=sys.stderr)
            rain_1h, _, _ = ws.rain_1h_all(config.rain_conv_factor)
            
            # READ RAIN 24H
            print("LOG: READ RAIN 24H", file=sys.stderr)
            rain_24h, _, _ = ws.rain_24h_all(config.rain_conv_factor)
            
            # READ RAIN TOTAL
            print("LOG: READ RAIN TOTAL", file=sys.stderr)
            rain_total, _ = ws.rain_total_all(config.rain_conv_factor)
            
            # READ RELATIVE PRESSURE
            print("LOG: READ RELATIVE PRESSURE", file=sys.stderr)
            rel_pressure = ws.rel_pressure(config.pressure_conv_factor)
            
            # READ TENDENCY AND FORECAST
            print("LOG: READ TENDENCY AND FORECAST", file=sys.stderr)
            tendency, forecast = ws.tendency_forecast()
            
            print("LOG: Closing weather station", file=sys.stderr)
        
        # Build SQL query as C version does (for display/debug)
        sql_query = f"""INSERT INTO {config.pgsql_table} (
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
) VALUES (
     {temperature_indoor:.1f}
   , {temperature_outdoor:.1f}
   , {dewpoint:.1f}
   , {humidity_indoor}
   , {humidity_outdoor}
   , {wind_speed:.1f}
   , {wind_angle:.1f}
   , '{wind_direction}'
   , {wind_chill:.1f}
   , {rain_1h:.1f}
   , {rain_24h:.1f}
   , {rain_total:.1f}
   , {rel_pressure:.1f}
   , '{tendency}'
   , '{forecast}'
)
"""
        
        # Print SQL query like C version does
        print(sql_query)
        
        # Log to database
        print("LOG: Connecting to PostgreSQL database", file=sys.stderr)
        with PostgreSQLLogger(config.pgsql_connect, 
                             config.pgsql_table, 
                             getattr(config, 'pgsql_station', None)) as db:
            
            db.log_data(
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
        
        print("LOG: Data successfully logged to PostgreSQL", file=sys.stderr)
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
