#!/usr/bin/env python3
"""Read one WS-2300 snapshot and publish it to MQTT."""

import sys

from ..config import Config
from ..mqtt import MQTTPublisher
from ..reporting import collect_weather_snapshot
from ..weatherstation import WeatherStation


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        config = Config(config_file)
        if not config.mqtt_host:
            print('Error: MQTT_HOST is not configured', file=sys.stderr)
            return 1
        with WeatherStation(config.serial_device_name) as station:
            snapshot = collect_weather_snapshot(station, config)
        publisher = MQTTPublisher(config)
        try:
            publisher.publish_snapshot(snapshot)
        finally:
            publisher.close()
        return 0
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
