"""Shared weather collection and reporting data for database and MQTT sinks."""

import json


class WeatherSnapshot:
    """One complete C-compatible weather-station reading."""

    def __init__(self, **values):
        self.__dict__.update(values)

    def postgres_values(self, version):
        """Return values in the same order as pgsql2300.c."""
        min_time = self.wind_speed_min_datetime
        max_time = self.wind_speed_max_datetime
        station_time = self.ws_datetime_utc
        local_time = self.ws_datetime_local
        utc_time = self.ws_datetime_utc

        return (
            self.temperature_indoor, self.temperature_outdoor, self.dewpoint,
            self.humidity_indoor, self.humidity_outdoor,
            self.wind_speed_min, self.wind_speed_max,
            min_time.year, min_time.month, min_time.day, min_time.hour, min_time.minute,
            max_time.year, max_time.month, max_time.day, max_time.hour, max_time.minute,
            station_time.year, station_time.month, station_time.day,
            station_time.hour, station_time.minute, station_time.second,
            local_time.year, local_time.month, local_time.day,
            local_time.hour, local_time.minute, local_time.second,
            utc_time.year, utc_time.month, utc_time.day,
            utc_time.hour, utc_time.minute, utc_time.second,
            self.wind_speed,
            self.wind_angle[0], self.wind_angle[1], self.wind_angle[2],
            self.wind_angle[3], self.wind_angle[4], self.wind_angle[5],
            self.wind_direction, self.wind_chill,
            self.rain_1h, self.rain_24h, self.rain_total,
            self.rel_pressure, self.tendency, self.forecast, version,
        )

    def mqtt_dict(self):
        """Return the retained MQTT state without debug-only timestamps."""
        data = {
            'temperature_indoor': self._measurement(self.temperature_indoor),
            'temperature_outdoor': self._measurement(self.temperature_outdoor),
            'dewpoint': self._measurement(self.dewpoint),
            'humidity_indoor': self.humidity_indoor,
            'humidity_outdoor': self.humidity_outdoor,
            'wind_speed_min': self._measurement(self.wind_speed_min),
            'wind_speed_max': self._measurement(self.wind_speed_max),
            'wind_speed': self._measurement(self.wind_speed),
            'wind_angle_current': self.wind_angle[0],
            'wind_angle_previous_1': self.wind_angle[1],
            'wind_angle_previous_2': self.wind_angle[2],
            'wind_angle_previous_3': self.wind_angle[3],
            'wind_angle_previous_4': self.wind_angle[4],
            'wind_angle_previous_5': self.wind_angle[5],
            'wind_direction': self.wind_direction,
            'wind_chill': self._measurement(self.wind_chill),
            'rain_1h': self._measurement(self.rain_1h),
            'rain_24h': self._measurement(self.rain_24h),
            'rain_total': self._measurement(self.rain_total),
            'rel_pressure': self._measurement(self.rel_pressure),
            'tendency': self.tendency,
            'forecast': self.forecast,
            'station_datetime': self._timestamp_string(self.station_datetime),
        }
        return data

    def mqtt_payload(self):
        return json.dumps(self.mqtt_dict(), separators=(',', ':'), sort_keys=True)

    @staticmethod
    def _measurement(value):
        """Match the one-decimal precision used by the PostgreSQL schema."""
        return round(value, 1)

    @staticmethod
    def _timestamp_string(timestamp):
        return (
            f'{timestamp.year:04d}-{timestamp.month:02d}-{timestamp.day:02d}T'
            f'{timestamp.hour:02d}:{timestamp.minute:02d}:{timestamp.second:02d}'
        )


def collect_weather_snapshot(ws, config, log=None):
    """Read the complete weather dataset using the C implementation's order."""
    def announce(message):
        if log:
            log(message)

    announce('READ TEMPERATURE INDOOR.')
    temperature_indoor = ws.temperature_indoor(config.temperature_conv)
    announce('READ TEMPERATURE OUTDOOR.')
    temperature_outdoor = ws.temperature_outdoor(config.temperature_conv)
    announce('READ DEWPOINT.')
    dewpoint = ws.dewpoint(config.temperature_conv)
    announce('READ RELATIVE HUMIDITY INDOOR.')
    humidity_indoor = ws.humidity_indoor()
    announce('READ RELATIVE HUMIDITY OUTDOOR.')
    humidity_outdoor = ws.humidity_outdoor()
    announce('READ WIND SPEED MIN AND MAX.')
    wind_speed_min, wind_speed_max, wind_speed_min_datetime, wind_speed_max_datetime = \
        ws.wind_minmax(config.wind_speed_conv_factor)
    announce('READ STATION LOCAL TIME.')
    ws_datetime_local = ws.ws_time_local()
    announce('READ STATION UTC TIME.')
    ws_datetime_utc = ws.ws_time_utc_from_station()
    announce('READ WIND SPEED AND DIRECTION, RESET MIN/MAX.')
    wind_speed, winddir_index, wind_angle = ws.wind_all_reset(
        config.wind_speed_conv_factor, 0x01 | 0x02)
    directions = (
        'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
    )
    wind_direction = directions[winddir_index] if winddir_index < len(directions) else 'N'
    announce('READ WINDCHILL.')
    wind_chill = ws.windchill(config.temperature_conv)
    announce('READ RAIN 1H.')
    rain_1h = ws.rain_1h(config.rain_conv_factor)
    announce('READ RAIN 24H.')
    rain_24h = ws.rain_24h(config.rain_conv_factor)
    announce('READ RAIN TOTAL.')
    rain_total = ws.rain_total(config.rain_conv_factor)
    announce('READ RELATIVE PRESSURE.')
    rel_pressure = ws.rel_pressure(config.pressure_conv_factor)
    announce('READ TENDENCY AND FORECAST.')
    tendency, forecast = ws.tendency_forecast()

    return WeatherSnapshot(
        temperature_indoor=temperature_indoor,
        temperature_outdoor=temperature_outdoor,
        dewpoint=dewpoint,
        humidity_indoor=humidity_indoor,
        humidity_outdoor=humidity_outdoor,
        wind_speed_min=wind_speed_min,
        wind_speed_max=wind_speed_max,
        wind_speed_min_datetime=wind_speed_min_datetime,
        wind_speed_max_datetime=wind_speed_max_datetime,
        ws_datetime_local=ws_datetime_local,
        ws_datetime_utc=ws_datetime_utc,
        station_datetime=ws_datetime_utc,
        wind_speed=wind_speed,
        wind_angle=wind_angle,
        wind_direction=wind_direction,
        wind_chill=wind_chill,
        rain_1h=rain_1h,
        rain_24h=rain_24h,
        rain_total=rain_total,
        rel_pressure=rel_pressure,
        tendency=tendency,
        forecast=forecast,
    )
