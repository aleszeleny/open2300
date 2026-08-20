"""MQTT reporting and Home Assistant discovery for WS-2300 data."""

import json
import socket


class MQTTUnavailableError(RuntimeError):
    pass


class MQTTPublisher:
    """Publish retained weather state, optionally with daemon availability."""

    def __init__(self, config, daemon=False):
        self.config = config
        self.daemon = daemon
        self.client = None
        self.state_topic = self._state_topic()
        self.availability_topic = self.state_topic + '/availability'
        self._discovery_published = False

    def _load_client(self):
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise MQTTUnavailableError(
                'MQTT support requires paho-mqtt; install pyopen2300[mqtt]'
            ) from exc
        return mqtt

    def _state_topic(self):
        base = self.config.mqtt_base_topic.rstrip('/')
        if self.config.mqtt_station:
            return f'{base}/{self.config.mqtt_station}'
        return base + '/'

    def connect(self):
        mqtt = self._load_client()
        client_id = f'open2300-{self.config.mqtt_station or socket.gethostname()}'
        try:
            client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                                 client_id=client_id)
        except (AttributeError, TypeError):
            client = mqtt.Client(client_id=client_id)
        if self.config.mqtt_username:
            client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
        if self.daemon:
            client.will_set(self.availability_topic, payload='offline',
                            qos=self.config.mqtt_qos, retain=True)
        client.connect(self.config.mqtt_host, self.config.mqtt_port, keepalive=60)
        client.loop_start()
        self.client = client
        if self.daemon:
            self._publish(self.availability_topic, 'online', retain=True)

    def publish_snapshot(self, snapshot):
        if self.client is None:
            self.connect()
        self._publish(self.state_topic, snapshot.mqtt_payload(),
                      retain=self.config.mqtt_retain)
        if self.config.mqtt_ha_discovery and not self._discovery_published:
            self._publish_discovery()
            self._discovery_published = True

    def _publish(self, topic, payload, retain=None):
        if retain is None:
            retain = self.config.mqtt_retain
        info = self.client.publish(topic, payload, qos=self.config.mqtt_qos,
                                   retain=retain)
        info.wait_for_publish()
        if info.rc != 0:
            raise IOError(f'MQTT publish failed for {topic}: rc={info.rc}')

    def _publish_discovery(self):
        device_id = f'open2300_{self.config.mqtt_station or "station"}'
        device = {
            'identifiers': [device_id],
            'name': self.config.mqtt_station or 'Open2300',
            'manufacturer': 'Open2300',
            'model': 'WS2300',
        }
        for field in _DISCOVERY_FIELDS:
            payload = {
                'name': f'Open2300 {field.replace("_", " ")}',
                'unique_id': f'{device_id}_{field}',
                'state_topic': self.state_topic,
                'value_template': f'{{{{ value_json.{field} }}}}',
                'device': device,
            }
            unit, device_class = _field_metadata(field, self.config)
            if unit:
                payload['unit_of_measurement'] = unit
            if device_class:
                payload['device_class'] = device_class
            if field not in ('wind_direction', 'tendency', 'forecast'):
                payload['state_class'] = 'measurement'
            if self.daemon:
                payload.update({
                    'availability_topic': self.availability_topic,
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                })
            topic = (f'{self.config.mqtt_discovery_prefix.rstrip("/")}/sensor/'
                     f'{device_id}/{field}/config')
            self._publish(topic, json.dumps(payload, separators=(',', ':')), retain=True)

    def close(self):
        if self.client is None:
            return
        if self.daemon:
            self._publish(self.availability_topic, 'offline', retain=True)
        self.client.loop_stop()
        self.client.disconnect()
        self.client = None


_DISCOVERY_FIELDS = (
    'temperature_indoor', 'temperature_outdoor', 'dewpoint',
    'humidity_indoor', 'humidity_outdoor', 'wind_speed_min', 'wind_speed_max',
    'wind_speed', 'wind_angle_current', 'wind_angle_previous_1',
    'wind_angle_previous_2', 'wind_angle_previous_3', 'wind_angle_previous_4',
    'wind_angle_previous_5', 'wind_direction', 'wind_chill', 'rain_1h',
    'rain_24h', 'rain_total', 'rel_pressure', 'tendency', 'forecast',
)


def _field_metadata(field, config):
    if field in ('temperature_indoor', 'temperature_outdoor', 'dewpoint', 'wind_chill'):
        return ('°F' if config.temperature_conv else '°C', 'temperature')
    if field in ('humidity_indoor', 'humidity_outdoor'):
        return ('%', 'humidity')
    if field == 'rel_pressure':
        return ('inHg' if config.pressure_conv_factor != 1.0 else 'hPa',
                'atmospheric_pressure')
    if field.startswith('rain_') or field == 'rain_total':
        return ('in' if config.rain_conv_factor != 1.0 else 'mm', 'precipitation')
    if field.startswith('wind_angle'):
        return ('°', None)
    if field.startswith('wind_speed') or field == 'wind_speed':
        if config.wind_speed_conv_factor == 3.6:
            return ('km/h', None)
        if config.wind_speed_conv_factor != 1.0:
            return ('mph', None)
        return ('m/s', None)
    return (None, None)
