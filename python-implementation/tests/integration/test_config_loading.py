"""
Integration tests for configuration loading
"""

import pytest
import os
import tempfile
from pyopen2300.config import Config


class TestConfigIntegration:
    """Test configuration loading in realistic scenarios"""
    
    def test_full_config_loading(self, temp_config_file):
        """Test loading a complete configuration file"""
        config = Config(temp_config_file)
        
        # Verify all sections loaded correctly
        assert config.log_level > 0
        assert config.serial_device_name
        assert config.timezone is not None
        assert config.wind_speed_conv_factor > 0
        assert config.temperature_conv in [0, 1]
        assert config.rain_conv_factor > 0
        assert config.pressure_conv_factor > 0
        
        # Verify Weather Underground config
        assert config.weather_underground_id
        assert config.weather_underground_password
        
        # Verify APRS config
        assert len(config.aprs_hosts) > 0
        
        # Verify PostgreSQL config
        assert config.pgsql_connect
        assert config.pgsql_table
        assert config.pgsql_station
    
    def test_config_with_multiple_aprs_servers(self):
        """Test configuration with multiple APRS servers"""
        config_content = """
APRS_SERVER first.aprs.net 14580
APRS_SERVER second.aprs.net 14580
APRS_SERVER third.aprs.net 14580
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert len(config.aprs_hosts) == 3
            assert config.aprs_hosts[0].name == "first.aprs.net"
            assert config.aprs_hosts[1].name == "second.aprs.net"
            assert config.aprs_hosts[2].name == "third.aprs.net"
        finally:
            os.unlink(temp_path)
    
    def test_config_search_paths(self):
        """Test default configuration file search paths"""
        # Create config in current directory
        config_content = "LOG_LEVEL 3\nSERIAL_DEVICE /dev/test\n"
        
        # Test that it searches current directory
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.conf',
            dir='.',
            delete=False,
            prefix='open2300'
        ) as f:
            f.write(config_content)
            temp_path = f.name
        
        try:
            # This should not find the file without explicit path
            config = Config()
            # Will use defaults since file name doesn't match
            assert config.log_level == 1  # Default
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

