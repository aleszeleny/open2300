"""
Unit tests for config module
"""

import pytest
import tempfile
import os
from pyopen2300.config import Config, APRSHost
from pyopen2300.constants import (
    METERS_PER_SECOND, KILOMETERS_PER_HOUR, MILES_PER_HOUR,
    CELSIUS, FAHRENHEIT, MILLIMETERS, INCHES,
    HECTOPASCAL, INCHES_HG
)


class TestAPRSHost:
    """Test APRSHost class"""
    
    def test_creation(self):
        """Test APRSHost creation"""
        host = APRSHost("test.aprs.net", 14580)
        assert host.name == "test.aprs.net"
        assert host.port == 14580


class TestConfig:
    """Test Config class"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.log_level == 1
        assert config.serial_device_name == "/dev/ttyS0"
        assert config.timezone == 0
        assert config.wind_speed_conv_factor == METERS_PER_SECOND
        assert config.temperature_conv == CELSIUS
        assert config.rain_conv_factor == MILLIMETERS
        assert config.pressure_conv_factor == HECTOPASCAL
    
    def test_load_from_file(self, temp_config_file):
        """Test loading configuration from file"""
        config = Config(temp_config_file)
        
        assert config.log_level == 1
        assert config.serial_device_name == "/dev/ttyS0"
        assert config.timezone == 0
        assert config.weather_underground_id == "TESTID"
        assert config.weather_underground_password == "TESTPASS"
    
    def test_wind_speed_units(self):
        """Test wind speed unit conversion"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("WIND_SPEED km/h\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.wind_speed_conv_factor == KILOMETERS_PER_HOUR
        finally:
            os.unlink(temp_path)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("WIND_SPEED MPH\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.wind_speed_conv_factor == MILES_PER_HOUR
        finally:
            os.unlink(temp_path)
    
    def test_temperature_units(self):
        """Test temperature unit configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("TEMPERATURE F\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.temperature_conv == FAHRENHEIT
        finally:
            os.unlink(temp_path)
    
    def test_rain_units(self):
        """Test rain unit configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("RAIN IN\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.rain_conv_factor == INCHES
        finally:
            os.unlink(temp_path)
    
    def test_pressure_units(self):
        """Test pressure unit configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("PRESSURE INHG\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.pressure_conv_factor == INCHES_HG
        finally:
            os.unlink(temp_path)
    
    def test_aprs_hosts(self, temp_config_file):
        """Test APRS host configuration"""
        config = Config(temp_config_file)
        
        assert len(config.aprs_hosts) == 1
        assert config.aprs_hosts[0].name == "rotate.aprs.net"
        assert config.aprs_hosts[0].port == 14580
    
    def test_postgresql_config(self, temp_config_file):
        """Test PostgreSQL configuration"""
        config = Config(temp_config_file)
        
        assert config.pgsql_connect == "hostaddr='127.0.0.1' dbname='test' user='test'"
        assert config.pgsql_table == "weather"
        assert config.pgsql_station == "teststation"
    
    def test_file_not_found(self):
        """Test handling of non-existent config file"""
        with pytest.raises(FileNotFoundError):
            Config("/nonexistent/path/config.conf")
    
    def test_comment_handling(self):
        """Test that comments are properly ignored"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("LOG_LEVEL 2  # Inline comment\n")
            f.write("\n")  # Empty line
            f.write("TIMEZONE 5\n")
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.log_level == 2
            assert config.timezone == 5
        finally:
            os.unlink(temp_path)

