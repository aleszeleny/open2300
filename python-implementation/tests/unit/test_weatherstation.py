"""
Unit tests for weatherstation module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pyopen2300.weatherstation import WeatherStation, Timestamp
from pyopen2300.constants import CELSIUS, FAHRENHEIT


class TestTimestamp:
    """Test Timestamp class"""
    
    def test_creation(self):
        """Test Timestamp creation"""
        ts = Timestamp()
        assert ts.minute == 0
        assert ts.hour == 0
        assert ts.day == 0
        assert ts.month == 0
        assert ts.year == 0
    
    def test_to_datetime_valid(self):
        """Test conversion to datetime"""
        ts = Timestamp()
        ts.year = 2025
        ts.month = 12
        ts.day = 16
        ts.hour = 10
        ts.minute = 30
        
        dt = ts.to_datetime()
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 16
    
    def test_to_datetime_invalid(self):
        """Test conversion with invalid date"""
        ts = Timestamp()
        ts.year = 2025
        ts.month = 13  # Invalid month
        ts.day = 32    # Invalid day
        
        dt = ts.to_datetime()
        assert dt is None


class TestWeatherStation:
    """Test WeatherStation protocol functions"""
    
    def test_address_encoder(self):
        """Test address encoding"""
        # Test address 0x346
        encoded = WeatherStation.address_encoder(0x346)
        assert len(encoded) == 4
        assert isinstance(encoded, bytes)
        
        # Verify encoding formula: 0x82 + nibble*4
        # Address 0x346 = nibbles 0, 3, 4, 6
        assert encoded[0] == 0x82 + (0 * 4)  # 0x82
        assert encoded[1] == 0x82 + (3 * 4)  # 0x8E
        assert encoded[2] == 0x82 + (4 * 4)  # 0x92
        assert encoded[3] == 0x82 + (6 * 4)  # 0x9A
    
    def test_data_encoder(self):
        """Test data encoding"""
        data_in = bytes([0x5, 0xA, 0xF])
        encoded = WeatherStation.data_encoder(3, 0x42, data_in)
        
        assert len(encoded) == 3
        assert encoded[0] == 0x42 + (0x5 * 4)
        assert encoded[1] == 0x42 + (0xA * 4)
        assert encoded[2] == 0x42 + (0xF * 4)
    
    def test_numberof_encoder(self):
        """Test number-of-bytes encoding"""
        # Formula: 0xC2 + number * 4
        assert WeatherStation.numberof_encoder(1) == 0xC2 + 4
        assert WeatherStation.numberof_encoder(5) == 0xC2 + 20
        assert WeatherStation.numberof_encoder(15) == 0xFE  # Max capped at 0xFE
        assert WeatherStation.numberof_encoder(20) == 0xFE  # Over max, capped
    
    def test_command_check0123(self):
        """Test command checksum for address bytes"""
        # Formula: sequence * 16 + (command - 0x82) / 4
        assert WeatherStation.command_check0123(0x82, 0) == 0x00
        assert WeatherStation.command_check0123(0x8E, 1) == 0x13
        assert WeatherStation.command_check0123(0x92, 2) == 0x24
    
    def test_command_check4(self):
        """Test command checksum for data request"""
        # Formula: 0x30 + number
        assert WeatherStation.command_check4(5) == 0x35
        assert WeatherStation.command_check4(10) == 0x3A
    
    def test_data_checksum(self):
        """Test data checksum calculation"""
        data = bytes([0x10, 0x20, 0x30])
        checksum = WeatherStation.data_checksum(data, 3)
        assert checksum == (0x10 + 0x20 + 0x30) & 0xFF
        
        # Test overflow handling
        data = bytes([0xFF, 0xFF, 0xFF])
        checksum = WeatherStation.data_checksum(data, 3)
        assert checksum == (0xFF + 0xFF + 0xFF) & 0xFF  # Should wrap


class TestWeatherStationMocked:
    """Test WeatherStation with mocked serial device"""
    
    @patch('pyopen2300.weatherstation.SerialDevice')
    def test_creation(self, mock_serial_class):
        """Test WeatherStation creation"""
        ws = WeatherStation('/dev/ttyS0')
        assert ws.device is not None
        mock_serial_class.assert_called_once_with('/dev/ttyS0')
    
    @patch('pyopen2300.weatherstation.SerialDevice')
    def test_context_manager(self, mock_serial_class):
        """Test context manager usage"""
        with WeatherStation('/dev/ttyS0') as ws:
            assert ws is not None
        
        # Verify close was called
        ws.device.close.assert_called_once()
    
    @patch('pyopen2300.weatherstation.SerialDevice')
    def test_temperature_decoding(self, mock_serial_class):
        """Test temperature value decoding"""
        mock_device = Mock()
        # Simulate reading temperature: 22.5°C encoded as BCD
        # Temperature encoding: ((value + 30) * 100) in BCD
        # 22.5 + 30 = 52.5 -> 5250 in BCD = 0x52, 0x50
        mock_device.read_safe.return_value = bytes([0x50, 0x52])
        
        ws = WeatherStation('/dev/ttyS0')
        ws.device = mock_device
        
        # The actual decoding in temperature_indoor:
        # ((data[1] >> 4) * 10 + (data[1] & 0xF) + 
        #  (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0
        # = (5 * 10 + 2 + 5/10 + 0/100) - 30 = 52.5 - 30 = 22.5
        
        temp = ws.temperature_indoor(CELSIUS)
        assert temp == pytest.approx(22.5)

