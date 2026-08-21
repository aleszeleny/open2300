"""Tests for shared reporting data and MQTT behavior."""

from types import SimpleNamespace

from pyopen2300.mqtt import MQTTPublisher
from pyopen2300.reporting import WeatherSnapshot, collect_weather_snapshot


class Timestamp:
    year = 2026
    month = 8
    day = 21
    hour = 12
    minute = 34
    second = 56


class FakeStation:
    def __init__(self):
        self.calls = []

    def _return(self, name, value):
        self.calls.append(name)
        return value

    def temperature_indoor(self, _): return self._return('temperature_indoor', 20.0)
    def temperature_outdoor(self, _): return self._return('temperature_outdoor', 18.0)
    def dewpoint(self, _): return self._return('dewpoint', 10.0)
    def humidity_indoor(self): return self._return('humidity_indoor', 40)
    def humidity_outdoor(self): return self._return('humidity_outdoor', 60)
    def wind_minmax(self, _): return self._return('wind_minmax', (1.0, 4.0, Timestamp(), Timestamp()))
    def ws_time_local(self): return self._return('ws_time_local', Timestamp())
    def ws_time_utc_from_station(self): return self._return('ws_time_utc', Timestamp())
    def wind_all_reset(self, _, flags): return self._return(
        'wind_all_reset', (2.0, 2, [0.0, 22.5, 45.0, 67.5, 90.0, 112.5]))
    def windchill(self, _): return self._return('windchill', 17.0)
    def rain_1h(self, _): return self._return('rain_1h', 0.1)
    def rain_24h(self, _): return self._return('rain_24h', 1.0)
    def rain_total(self, _): return self._return('rain_total', 2.0)
    def rel_pressure(self, _): return self._return('rel_pressure', 1013.0)
    def tendency_forecast(self): return self._return('tendency_forecast', ('Steady', 'Sunny'))


def test_shared_collector_matches_c_order_and_shape():
    config = SimpleNamespace(temperature_conv=0, wind_speed_conv_factor=1.0,
                             rain_conv_factor=1.0, pressure_conv_factor=1.0)
    station = FakeStation()
    snapshot = collect_weather_snapshot(station, config)

    assert station.calls == [
        'temperature_indoor', 'temperature_outdoor', 'dewpoint',
        'humidity_indoor', 'humidity_outdoor', 'wind_minmax',
        'ws_time_local', 'ws_time_utc', 'wind_all_reset', 'windchill',
        'rain_1h', 'rain_24h', 'rain_total', 'rel_pressure',
        'tendency_forecast',
    ]
    assert snapshot.wind_direction == 'NE'
    assert len(snapshot.postgres_values('version')) == 51
    assert snapshot.mqtt_dict()['station_datetime'] == '2026-08-21T12:34:56'


def test_mqtt_topic_uses_optional_station():
    config = SimpleNamespace(mqtt_base_topic='open2300', mqtt_station='',
                             mqtt_host='localhost', mqtt_port=1883,
                             mqtt_username='', mqtt_password='', mqtt_qos=1,
                             mqtt_retain=True, mqtt_ha_discovery=False,
                             mqtt_discovery_prefix='homeassistant')
    assert MQTTPublisher(config).state_topic == 'open2300/'
    config.mqtt_station = 'rpi'
    assert MQTTPublisher(config).state_topic == 'open2300/rpi'


def test_mqtt_measurements_are_rounded_to_schema_precision():
    snapshot = WeatherSnapshot(
        temperature_indoor=20.0, temperature_outdoor=10.0,
        dewpoint=8.839999999999996, humidity_indoor=50, humidity_outdoor=60,
        wind_speed_min=1.04, wind_speed_max=2.06, wind_speed=1.05,
        wind_angle=[0, 1, 2, 3, 4, 5], wind_direction='N', wind_chill=9.94,
        rain_1h=0.04, rain_24h=0.16, rain_total=1.26,
        rel_pressure=1013.04, tendency='Steady', forecast='Sunny',
        station_datetime=Timestamp(),
    )

    data = snapshot.mqtt_dict()
    assert data['dewpoint'] == 8.8
    assert data['rel_pressure'] == 1013.0
