"""
Unit tests for constants module
"""

import pytest
from pyopen2300 import constants


class TestConstants:
    """Test constants module"""
    
    def test_protocol_constants(self):
        """Test protocol-related constants"""
        assert constants.MAXRETRIES == 50
        assert constants.WRITENIB == 0x42
        assert constants.SETBIT == 0x12
        assert constants.UNSETBIT == 0x32
    
    def test_unit_conversions(self):
        """Test unit conversion factors"""
        assert constants.METERS_PER_SECOND == 1.0
        assert constants.KILOMETERS_PER_HOUR == 3.6
        assert constants.MILES_PER_HOUR == pytest.approx(2.23693629)
        
        assert constants.MILLIMETERS == 1
        assert constants.INCHES == 25.4
        
        assert constants.HECTOPASCAL == 1.0
        assert constants.INCHES_HG == pytest.approx(33.8638864)
    
    def test_temperature_units(self):
        """Test temperature unit constants"""
        assert constants.CELSIUS == 0
        assert constants.FAHRENHEIT == 1
    
    def test_logging_levels(self):
        """Test logging level constants"""
        assert constants.LOG_OFF == 0
        assert constants.LOG_MIN == 1
        assert constants.LOG_MED == 2
        assert constants.LOG_MAX == 3
    
    def test_wind_directions(self):
        """Test wind direction array"""
        assert len(constants.WIND_DIRECTIONS) == 16
        assert constants.WIND_DIRECTIONS[0] == "N"
        assert constants.WIND_DIRECTIONS[4] == "E"
        assert constants.WIND_DIRECTIONS[8] == "S"
        assert constants.WIND_DIRECTIONS[12] == "W"
    
    def test_weather_underground_settings(self):
        """Test Weather Underground constants"""
        assert constants.WEATHER_UNDERGROUND_BASEURL == "weatherstation.wunderground.com"
        assert constants.WEATHER_UNDERGROUND_PATH == "/weatherstation/updateweatherstation.php"
        assert constants.WEATHER_UNDERGROUND_SOFTWARETYPE == "pyopen2300"

