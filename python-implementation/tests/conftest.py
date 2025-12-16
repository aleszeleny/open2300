"""
Pytest configuration and fixtures
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file"""
    content = """
# Test configuration
LOG_LEVEL 1
SERIAL_DEVICE /dev/ttyS0
TIMEZONE 0
WIND_SPEED m/s
TEMPERATURE C
RAIN mm
PRESSURE hPa

CITIZEN_WEATHER_ID CW0000
CITIZEN_WEATHER_PASSCODE -1
CITIZEN_WEATHER_LATITUDE 5540.12N
CITIZEN_WEATHER_LONGITUDE 01224.60E

APRS_SERVER rotate.aprs.net 14580

WEATHER_UNDERGROUND_ID TESTID
WEATHER_UNDERGROUND_PASSWORD TESTPASS

PGSQL_CONNECT hostaddr='127.0.0.1' dbname='test' user='test'
PGSQL_TABLE weather
PGSQL_STATION teststation
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_serial():
    """Mock serial device"""
    mock = MagicMock()
    mock.read.return_value = b'\x02'
    mock.write.return_value = 1
    mock.is_open = True
    return mock


@pytest.fixture
def mock_weather_data():
    """Sample weather data for testing"""
    return {
        'temperature_indoor': 22.5,
        'temperature_outdoor': 18.3,
        'humidity_indoor': 45,
        'humidity_outdoor': 65,
        'pressure': 1013.25,
        'wind_speed': 5.2,
        'wind_direction': 180.0,
        'dewpoint': 12.5
    }

