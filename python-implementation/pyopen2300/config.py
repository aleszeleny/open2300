"""
Configuration management for pyopen2300
"""

import os
from typing import List, Tuple, Optional
from .constants import (
    DEFAULT_SERIAL_DEVICE,
    METERS_PER_SECOND,
    KILOMETERS_PER_HOUR,
    MILES_PER_HOUR,
    CELSIUS,
    FAHRENHEIT,
    MILLIMETERS,
    INCHES,
    HECTOPASCAL,
    MILLIBARS,
    INCHES_HG,
    LOG_MIN
)


class APRSHost:
    """APRS host configuration"""
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port


class Config:
    """Configuration for open2300 tools"""
    
    # Default search paths for config file
    DEFAULT_PATHS = [
        './open2300.conf',
        '/usr/local/etc/open2300.conf',
        '/etc/open2300.conf'
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with default values"""
        # Logging
        self.log_level = LOG_MIN
        
        # Serial device
        self.serial_device_name = DEFAULT_SERIAL_DEVICE
        
        # Timezone
        self.timezone = 0
        
        # Unit conversion factors
        self.wind_speed_conv_factor = METERS_PER_SECOND
        self.temperature_conv = CELSIUS
        self.rain_conv_factor = MILLIMETERS
        self.pressure_conv_factor = HECTOPASCAL
        
        # Citizen Weather (CWOP/APRS)
        self.citizen_weather_id = "CW0000"
        self.citizen_weather_passcode = "-1"
        self.citizen_weather_latitude = "5540.12N"
        self.citizen_weather_longitude = "01224.60E"
        self.aprs_hosts: List[APRSHost] = []
        
        # Weather Underground
        self.weather_underground_id = "WUID"
        self.weather_underground_password = "WUPASSWORD"
        
        # PostgreSQL (MySQL support removed as requested)
        self.pgsql_connect = ""
        self.pgsql_table = "weather"
        self.pgsql_station = "open2300"
        self.pgsql_daemon_interval = 300  # Default: 5 minutes (in seconds)
        
        # Load configuration from file
        if config_path:
            self.load_from_file(config_path)
        else:
            # Search default paths
            for path in self.DEFAULT_PATHS:
                if os.path.exists(path):
                    self.load_from_file(path)
                    break
    
    def load_from_file(self, config_path: str):
        """Load configuration from file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse configuration line
                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue
                
                key, value = parts[0], parts[1]
                
                # Remove inline comments
                if '#' in value:
                    value = value.split('#')[0].strip()
                
                self._set_config_value(key, value)
    
    def _set_config_value(self, key: str, value: str):
        """Set a configuration value based on key"""
        
        if key == "LOG_LEVEL":
            self.log_level = int(value)
        
        elif key == "SERIAL_DEVICE":
            self.serial_device_name = value
        
        elif key == "TIMEZONE":
            self.timezone = int(value)
        
        elif key == "WIND_SPEED":
            if value == "m/s":
                self.wind_speed_conv_factor = METERS_PER_SECOND
            elif value == "km/h":
                self.wind_speed_conv_factor = KILOMETERS_PER_HOUR
            elif value == "MPH":
                self.wind_speed_conv_factor = MILES_PER_HOUR
        
        elif key == "TEMPERATURE":
            if value == "C":
                self.temperature_conv = CELSIUS
            elif value == "F":
                self.temperature_conv = FAHRENHEIT
        
        elif key == "RAIN":
            if value == "mm":
                self.rain_conv_factor = MILLIMETERS
            elif value == "IN":
                self.rain_conv_factor = INCHES
        
        elif key == "PRESSURE":
            if value == "hPa" or value == "mb":
                self.pressure_conv_factor = HECTOPASCAL
            elif value == "INHG":
                self.pressure_conv_factor = INCHES_HG
        
        elif key == "CITIZEN_WEATHER_ID":
            self.citizen_weather_id = value
        
        elif key == "CITIZEN_WEATHER_PASSCODE":
            self.citizen_weather_passcode = value
        
        elif key == "CITIZEN_WEATHER_LATITUDE":
            self.citizen_weather_latitude = value
        
        elif key == "CITIZEN_WEATHER_LONGITUDE":
            self.citizen_weather_longitude = value
        
        elif key == "APRS_SERVER":
            # Format: "hostname port"
            parts = value.split()
            if len(parts) >= 2:
                host = APRSHost(parts[0], int(parts[1]))
                self.aprs_hosts.append(host)
        
        elif key == "WEATHER_UNDERGROUND_ID":
            self.weather_underground_id = value
        
        elif key == "WEATHER_UNDERGROUND_PASSWORD":
            self.weather_underground_password = value
        
        elif key == "PGSQL_CONNECT":
            self.pgsql_connect = value
        
        elif key == "PGSQL_TABLE":
            self.pgsql_table = value
        
        elif key == "PGSQL_STATION":
            self.pgsql_station = value
        
        elif key == "PGSQL_DAEMON_INTERVAL":
            try:
                self.pgsql_daemon_interval = int(value)
                if self.pgsql_daemon_interval < 1:
                    self.pgsql_daemon_interval = 300  # Minimum 1 second, default to 5 min if invalid
            except ValueError:
                self.pgsql_daemon_interval = 300  # Default if invalid value

