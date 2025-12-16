#!/usr/bin/env python3
"""
dumpconfig2300 - Display current configuration
Python equivalent of dumpconfig2300.c
"""

import sys
from ..config import Config


def main():
    """Main function"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        print("PyOpen2300 Configuration")
        print("=" * 50)
        print()
        
        print(f"Serial Device:              {config.serial_device_name}")
        print(f"Timezone:                   {config.timezone} hours from UTC")
        print(f"Log Level:                  {config.log_level}")
        print()
        
        # Units
        wind_unit = "m/s"
        if config.wind_speed_conv_factor == 3.6:
            wind_unit = "km/h"
        elif config.wind_speed_conv_factor == 2.23693629:
            wind_unit = "MPH"
        
        temp_unit = "Celsius" if config.temperature_conv == 0 else "Fahrenheit"
        rain_unit = "mm" if config.rain_conv_factor == 1 else "inches"
        
        pressure_unit = "hPa"
        if config.pressure_conv_factor == 33.8638864:
            pressure_unit = "inHg"
        
        print(f"Wind Speed Unit:            {wind_unit}")
        print(f"Temperature Unit:           {temp_unit}")
        print(f"Rain Unit:                  {rain_unit}")
        print(f"Pressure Unit:              {pressure_unit}")
        print()
        
        # Weather Underground
        print("Weather Underground:")
        print(f"  ID:                       {config.weather_underground_id}")
        print(f"  Password:                 {'*' * len(config.weather_underground_password)}")
        print()
        
        # Citizen Weather
        print("Citizen Weather (CWOP):")
        print(f"  ID:                       {config.citizen_weather_id}")
        print(f"  Latitude:                 {config.citizen_weather_latitude}")
        print(f"  Longitude:                {config.citizen_weather_longitude}")
        print(f"  APRS Hosts:               {len(config.aprs_hosts)}")
        for i, host in enumerate(config.aprs_hosts):
            print(f"    {i+1}. {host.name}:{host.port}")
        print()
        
        # Database
        print("PostgreSQL:")
        if config.pgsql_connect:
            print(f"  Connect String:           {config.pgsql_connect}")
            print(f"  Table:                    {config.pgsql_table}")
            print(f"  Station:                  {config.pgsql_station}")
        else:
            print("  Not configured")
        print()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

