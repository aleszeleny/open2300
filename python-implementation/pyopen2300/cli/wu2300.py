#!/usr/bin/env python3
"""
wu2300 - Upload weather data to Weather Underground
Python equivalent of wu2300.c
"""

import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WEATHER_UNDERGROUND_BASEURL, WEATHER_UNDERGROUND_PATH, WEATHER_UNDERGROUND_SOFTWARETYPE


def print_usage():
    """Print usage information"""
    print("wu2300 - Upload weather data to Weather Underground")
    print("Usage:")
    print("  wu2300 [config_file]")
    print()
    print("Configure Weather Underground ID and password in config file")


def main():
    """Main function"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Check Weather Underground credentials
        if config.weather_underground_id == "WUID" or config.weather_underground_password == "WUPASSWORD":
            print("Error: Please configure Weather Underground ID and password in config file")
            sys.exit(1)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # Get timestamp in UTC
            now = datetime.now(timezone.utc)
            datestamp = now.strftime('%Y-%m-%d+%H:%M:%S')
            
            # Read weather data - WU requires specific units
            # Temperature in Fahrenheit
            ti_f = ws.temperature_indoor(1)  # 1 = Fahrenheit
            to_f = ws.temperature_outdoor(1)
            dp_f = ws.dewpoint(1)
            
            # Humidity in %
            rhi = ws.humidity_indoor()
            rho = ws.humidity_outdoor()
            
            # Pressure in inches Hg
            rp_inhg = ws.rel_pressure(33.8638864)  # Convert to inHg
            
            # Wind speed in MPH
            data = ws.read_safe(0x527, 3)
            if data:
                wind_speed_mph = ((data[2] >> 4) * 100 + (data[2] & 0xF) * 10 +
                                 (data[1] >> 4) + (data[1] & 0xF) / 10.0)
                wind_speed_mph = wind_speed_mph * 2.23693629 / 10.0  # Convert to MPH
                wind_dir = (data[0] & 0x0F) * 22.5  # degrees
            else:
                wind_speed_mph = 0.0
                wind_dir = 0
            
            # Build query parameters
            params = {
                'ID': config.weather_underground_id,
                'PASSWORD': config.weather_underground_password,
                'dateutc': datestamp,
                'tempf': f"{to_f:.1f}",
                'humidity': str(rho),
                'dewptf': f"{dp_f:.1f}",
                'baromin': f"{rp_inhg:.3f}",
                'windspeedmph': f"{wind_speed_mph:.1f}",
                'winddir': str(int(wind_dir)),
                'indoortempf': f"{ti_f:.1f}",
                'indoorhumidity': str(rhi),
                'softwaretype': WEATHER_UNDERGROUND_SOFTWARETYPE,
                'action': 'updateraw'
            }
            
            # Build URL
            query_string = urllib.parse.urlencode(params)
            url = f"https://{WEATHER_UNDERGROUND_BASEURL}{WEATHER_UNDERGROUND_PATH}?{query_string}"
            
            # Send request
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    result = response.read().decode('utf-8')
                    if 'success' in result.lower():
                        print("Successfully uploaded data to Weather Underground")
                    else:
                        print(f"Upload completed with response: {result}")
            except urllib.error.URLError as e:
                print(f"Error uploading to Weather Underground: {e}")
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

