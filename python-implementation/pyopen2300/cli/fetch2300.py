#!/usr/bin/env python3
"""
fetch2300 - Fetch all current weather data from WS2300
Python equivalent of fetch2300.c
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WIND_DIRECTIONS


def main():
    """Main function"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            output = []
            
            # Get current date/time
            now = datetime.now()
            output.append(f"Date {now.strftime('%Y-%b-%d')}")
            output.append(f"Time {now.strftime('%H:%M:%S')}")
            
            # Indoor temperature
            try:
                ti = ws.temperature_indoor(config.temperature_conv)
                output.append(f"Ti {ti:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read indoor temperature: {e}", file=sys.stderr)
            
            # Outdoor temperature
            try:
                to = ws.temperature_outdoor(config.temperature_conv)
                output.append(f"To {to:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read outdoor temperature: {e}", file=sys.stderr)
            
            # Dewpoint
            try:
                dp = ws.dewpoint(config.temperature_conv)
                output.append(f"DP {dp:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read dewpoint: {e}", file=sys.stderr)
            
            # Indoor humidity
            try:
                rhi = ws.humidity_indoor()
                output.append(f"RHi {rhi}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read indoor humidity: {e}", file=sys.stderr)
            
            # Outdoor humidity
            try:
                rho = ws.humidity_outdoor()
                output.append(f"RHo {rho}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read outdoor humidity: {e}", file=sys.stderr)
            
            # Wind data (simplified - full implementation would include all wind functions)
            try:
                # Read wind speed from address 0x527
                data = ws.read_safe(0x527, 3)
                if data:
                    wind_speed = ((data[2] >> 4) * 100 + (data[2] & 0xF) * 10 +
                                 (data[1] >> 4) + (data[1] & 0xF) / 10.0)
                    wind_speed = wind_speed * config.wind_speed_conv_factor / 10.0
                    output.append(f"WS {wind_speed:.1f}")
                    
                    # Wind direction (simplified)
                    dir_index = data[0] & 0x0F
                    if dir_index < len(WIND_DIRECTIONS):
                        output.append(f"DIRtext {WIND_DIRECTIONS[dir_index]}")
            except Exception as e:
                print(f"Warning: Could not read wind data: {e}", file=sys.stderr)
            
            # Pressure
            try:
                rp = ws.rel_pressure(config.pressure_conv_factor)
                output.append(f"RP {rp:.3f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                print(f"Warning: Could not read pressure: {e}", file=sys.stderr)
            
            # Tendency and forecast
            try:
                tendency, forecast = ws.tendency_forecast()
                output.append(f"Tendency {tendency}")
                output.append(f"Forecast {forecast}")
            except Exception as e:
                print(f"Warning: Could not read tendency/forecast: {e}", file=sys.stderr)
            
            # Rain data (simplified - would need full implementation)
            # Note: Rain functions require more complex calculations
            output.append("# Rain data functions not yet fully implemented")
            
            # Print all output
            for line in output:
                print(line)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

