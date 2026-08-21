#!/usr/bin/env python3
"""Continuous C-compatible PostgreSQL and optional MQTT weather logger."""

import argparse
import logging
import time

from ..config import Config
from ..mqtt import MQTTPublisher
from ..reporting import collect_weather_snapshot
from ..weatherstation import WeatherStation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', help='Configuration file')
    parser.add_argument('-i', '--interval', type=int,
                        help='Interval in seconds; overrides PGSQL_DAEMON_INTERVAL')
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s [%(process)d] %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    logger = logging.getLogger('pgsql2300-daemon')

    config = Config(args.config)
    interval = args.interval if args.interval is not None else config.pgsql_daemon_interval
    if interval < 1:
        parser.error('interval must be at least one second')
    if not config.pgsql_connect and not config.mqtt_host:
        parser.error('configure PGSQL_CONNECT and/or MQTT_HOST')

    postgres = None
    mqtt = None
    station = None
    try:
        if config.pgsql_connect:
            # Keep MQTT-only installations independent of psycopg2.
            from ..db.pgsql_logger import PostgreSQLLogger

            postgres = PostgreSQLLogger(
                config.pgsql_connect, config.pgsql_table,
                config.pgsql_station, auto_reconnect=True)
        if config.mqtt_host:
            mqtt = MQTTPublisher(config, daemon=True)
            mqtt.connect()
        station = WeatherStation(config.serial_device_name)
        logger.info('daemon started; interval=%ss', interval)
        while True:
            try:
                snapshot = collect_weather_snapshot(station, config)
                if postgres:
                    postgres.log_snapshot(snapshot)
                if mqtt:
                    mqtt.publish_snapshot(snapshot)
                logger.info('weather snapshot reported')
            except Exception:
                logger.exception('weather snapshot reporting failed')
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info('stopping daemon')
    finally:
        if station:
            station.close()
        if mqtt:
            mqtt.close()
        if postgres:
            postgres.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
