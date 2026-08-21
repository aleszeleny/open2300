#!/usr/bin/env python3
"""
pgsql2300 - Log weather data to PostgreSQL database
Python equivalent of pgsql2300.c

Reads all weather measurements and logs them to PostgreSQL database.
Matches the C implementation exactly.
"""

import inspect
import os
import sys
from datetime import datetime
from .. import __version__
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import LOG_MIN, LOG_MED, LOG_MAX
from ..reporting import collect_weather_snapshot
from ..sql_identifier import table_identifier
from ..mqtt import MQTTPublisher

try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


PGSQL2300_VERSION = f"pgsql2300.py {__version__}"


def log_message(config, level: int, message: str):
    """Write a C-compatible diagnostic message when the level is enabled."""
    if config.log_level < level:
        return

    caller = inspect.currentframe().f_back
    source_file = os.path.basename(caller.f_code.co_filename)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"{timestamp} [{os.getpid()}]\t[{source_file}:{caller.f_lineno}]\t{message}",
        file=sys.stderr,
        flush=True,
    )


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
                 humidity_indoor, humidity_outdoor,
                 wind_speed_min, wind_speed_max,
                 wind_speed_min_datetime, wind_speed_max_datetime,
                 ws_datetime_local, ws_datetime_utc,
                 wind_speed, wind_angle, wind_direction, wind_chill,
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
            wind_speed_min: Wind speed minimum (read before reset)
            wind_speed_max: Wind speed maximum (read before reset)
            wind_speed_min_datetime: Timestamp of wind speed minimum
            wind_speed_max_datetime: Timestamp of wind speed maximum
            ws_datetime_local: Weather station local time (Timestamp)
            ws_datetime_utc: Weather station UTC time (Timestamp)
            wind_speed: Current wind speed
            wind_angle: List of 6 wind directions in degrees (current + previous 5)
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
                      rec_datetime
                    , temperature_indoor
                    , temperature_outdoor
                    , dewpoint
                    , humidity_indoor
                    , humidity_outdoor
                    , wind_speed_min
                    , wind_speed_max
                    , wind_speed_min_datetime
                    , wind_speed_max_datetime
                    , station_datetime
                    , ws_datetime_local
                    , ws_datetime_utc
                    , wind_speed
                    , wind_angle_current
                    , wind_angle_previous_1
                    , wind_angle_previous_2
                    , wind_angle_previous_3
                    , wind_angle_previous_4
                    , wind_angle_previous_5
                    , wind_direction
                    , wind_chill
                    , rain_1h
                    , rain_24h
                    , rain_total
                    , rel_pressure
                    , tendency
                    , forecast
                    , pgsql2300_version
                ) VALUES (
                      now()
                    , %s, %s, %s, %s, %s, %s, %s
                    , make_timestamp(%s, %s, %s, %s, %s, 0)
                    , make_timestamp(%s, %s, %s, %s, %s, 0)
                    , make_timestamp(%s, %s, %s, %s, %s, %s)
                    , make_timestamp(%s, %s, %s, %s, %s, %s)
                    , make_timestamp(%s, %s, %s, %s, %s, %s)
                    , %s, %s, %s, %s, %s, %s, %s, %s, %s
                    , %s, %s, %s, %s, %s, %s, %s
                )
            """).format(table_identifier(self.table_name))

            # station_datetime mirrors ws_datetime_utc, matching pgsql2300.c
            self.cursor.execute(insert_query, (
                temperature_indoor,
                temperature_outdoor,
                dewpoint,
                humidity_indoor,
                humidity_outdoor,
                wind_speed_min,
                wind_speed_max,
                wind_speed_min_datetime.year, wind_speed_min_datetime.month,
                wind_speed_min_datetime.day, wind_speed_min_datetime.hour,
                wind_speed_min_datetime.minute,
                wind_speed_max_datetime.year, wind_speed_max_datetime.month,
                wind_speed_max_datetime.day, wind_speed_max_datetime.hour,
                wind_speed_max_datetime.minute,
                ws_datetime_utc.year, ws_datetime_utc.month, ws_datetime_utc.day,
                ws_datetime_utc.hour, ws_datetime_utc.minute, ws_datetime_utc.second,
                ws_datetime_local.year, ws_datetime_local.month, ws_datetime_local.day,
                ws_datetime_local.hour, ws_datetime_local.minute, ws_datetime_local.second,
                ws_datetime_utc.year, ws_datetime_utc.month, ws_datetime_utc.day,
                ws_datetime_utc.hour, ws_datetime_utc.minute, ws_datetime_utc.second,
                wind_speed,
                wind_angle[0], wind_angle[1], wind_angle[2],
                wind_angle[3], wind_angle[4], wind_angle[5],
                wind_direction, wind_chill,
                rain_1h, rain_24h, rain_total,
                rel_pressure, tendency, forecast, PGSQL2300_VERSION
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

    def log_snapshot(self, snapshot):
        """Log a shared weather snapshot using the C-compatible insert."""
        self.log_data(
            temperature_indoor=snapshot.temperature_indoor,
            temperature_outdoor=snapshot.temperature_outdoor,
            dewpoint=snapshot.dewpoint,
            humidity_indoor=snapshot.humidity_indoor,
            humidity_outdoor=snapshot.humidity_outdoor,
            wind_speed_min=snapshot.wind_speed_min,
            wind_speed_max=snapshot.wind_speed_max,
            wind_speed_min_datetime=snapshot.wind_speed_min_datetime,
            wind_speed_max_datetime=snapshot.wind_speed_max_datetime,
            ws_datetime_local=snapshot.ws_datetime_local,
            ws_datetime_utc=snapshot.ws_datetime_utc,
            wind_speed=snapshot.wind_speed,
            wind_angle=snapshot.wind_angle,
            wind_direction=snapshot.wind_direction,
            wind_chill=snapshot.wind_chill,
            rain_1h=snapshot.rain_1h,
            rain_24h=snapshot.rain_24h,
            rain_total=snapshot.rain_total,
            rel_pressure=snapshot.rel_pressure,
            tendency=snapshot.tendency,
            forecast=snapshot.forecast,
        )

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
    print("  - Wind speed min/max (read before reset), speed, direction, and windchill")
    print("  - Station local time and UTC time")
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
        log_message(config, LOG_MIN, f"Starting pgsql2300 version {PGSQL2300_VERSION}")
        log_message(config, LOG_MED, "Reading data from weather station.")
        log_message(config, LOG_MAX, f"Opening weather station on {config.serial_device_name}")
        with WeatherStation(config.serial_device_name) as ws:
            log_message(config, LOG_MAX, "Reading weather data...")
            snapshot = collect_weather_snapshot(
                ws, config, log=lambda message: log_message(config, LOG_MAX, message))
            log_message(config, LOG_MAX, "CLOSING THE WEATHER STATION.")

        # Log to database
        log_message(config, LOG_MED, "Connecting to PostgreSQL database.")
        with PostgreSQLLogger(config.pgsql_connect,
                             config.pgsql_table,
                             getattr(config, 'pgsql_station', None)) as db:

            db.log_snapshot(snapshot)

        if config.mqtt_host:
            log_message(config, LOG_MED, "Connecting to MQTT broker.")
            mqtt_publisher = MQTTPublisher(config)
            try:
                mqtt_publisher.publish_snapshot(snapshot)
            finally:
                mqtt_publisher.close()

        log_message(config, LOG_MIN, "Data successfully reported.")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
