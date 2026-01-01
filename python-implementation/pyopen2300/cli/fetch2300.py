#!/usr/bin/env python3
"""
fetch2300 - Fetch all current weather data from WS2300
Python equivalent of fetch2300.c
"""

import sys
from datetime import datetime
from ..weatherstation import WeatherStation
from ..config import Config
from ..constants import WIND_DIRECTIONS, LOG_MIN, LOG_MED, LOG_MAX


def log(config, level, message):
    """Print log message if configured log level allows it"""
    if config.log_level >= level:
        print(f"LOG: {message}", file=sys.stderr)


def print_config_summary(config):
    """Print summary of configuration settings"""
    print("=" * 70, file=sys.stderr)
    print("Configuration Summary:", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"Serial Device:        {config.serial_device_name}", file=sys.stderr)
    print(f"Log Level:            {config.log_level}", file=sys.stderr)
    print(f"Timezone:             {config.timezone:+d} hours from UTC", file=sys.stderr)
    
    # Temperature unit
    temp_unit = "Celsius (°C)" if config.temperature_conv == 0 else "Fahrenheit (°F)"
    print(f"Temperature Unit:     {temp_unit}", file=sys.stderr)
    
    # Wind speed unit
    if config.wind_speed_conv_factor == 1.0:
        wind_unit = "m/s (meters per second)"
    elif config.wind_speed_conv_factor == 3.6:
        wind_unit = "km/h (kilometers per hour)"
    elif abs(config.wind_speed_conv_factor - 2.23693629) < 0.001:
        wind_unit = "MPH (miles per hour)"
    else:
        wind_unit = f"custom ({config.wind_speed_conv_factor}x)"
    print(f"Wind Speed Unit:      {wind_unit}", file=sys.stderr)
    
    # Rain unit
    rain_unit = "mm (millimeters)" if config.rain_conv_factor == 1 else "inches"
    print(f"Rain Unit:            {rain_unit}", file=sys.stderr)
    
    # Pressure unit
    if config.pressure_conv_factor == 1.0:
        pressure_unit = "hPa (hectopascals)"
    elif abs(config.pressure_conv_factor - 33.8638864) < 0.001:
        pressure_unit = "inHg (inches of mercury)"
    else:
        pressure_unit = f"custom ({config.pressure_conv_factor}x)"
    print(f"Pressure Unit:        {pressure_unit}", file=sys.stderr)
    
    print("=" * 70, file=sys.stderr)
    print("", file=sys.stderr)


def main():
    """Main function"""
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load configuration
        log_msg = f"Loading configuration from: {config_file if config_file else 'default locations'}"
        print(f"LOG: {log_msg}", file=sys.stderr)
        
        config = Config(config_file)
        
        # Print configuration summary if logging enabled
        if config.log_level >= LOG_MIN:
            print_config_summary(config)
        
        log(config, LOG_MIN, "Opening weather station...")
        log(config, LOG_MED, f"Using serial device: {config.serial_device_name}")
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            log(config, LOG_MIN, "Weather station opened successfully")
            log(config, LOG_MED, "Reading current weather data...")
            output = []
            
            # Get current date/time
            log(config, LOG_MAX, "Getting current date/time")
            now = datetime.now()
            output.append(f"Date {now.strftime('%Y-%b-%d')}")
            output.append(f"Time {now.strftime('%H:%M:%S')}")
            
            # Indoor temperature
            log(config, LOG_MAX, "Reading indoor temperature")
            try:
                ti = ws.temperature_indoor(config.temperature_conv)
                output.append(f"Ti {ti:.1f}")
                log(config, LOG_MED, f"Indoor temperature: {ti:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading indoor temperature: {e}")
                print(f"Warning: Could not read indoor temperature: {e}", file=sys.stderr)
            
            # Outdoor temperature
            log(config, LOG_MAX, "Reading outdoor temperature")
            try:
                to = ws.temperature_outdoor(config.temperature_conv)
                output.append(f"To {to:.1f}")
                log(config, LOG_MED, f"Outdoor temperature: {to:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading outdoor temperature: {e}")
                print(f"Warning: Could not read outdoor temperature: {e}", file=sys.stderr)
            
            # Dewpoint
            log(config, LOG_MAX, "Reading dewpoint")
            try:
                dp = ws.dewpoint(config.temperature_conv)
                output.append(f"DP {dp:.1f}")
                log(config, LOG_MED, f"Dewpoint: {dp:.1f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading dewpoint: {e}")
                print(f"Warning: Could not read dewpoint: {e}", file=sys.stderr)
            
            # Indoor humidity
            log(config, LOG_MAX, "Reading indoor humidity")
            try:
                rhi = ws.humidity_indoor()
                output.append(f"RHi {rhi}")
                log(config, LOG_MED, f"Indoor humidity: {rhi}%")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading indoor humidity: {e}")
                print(f"Warning: Could not read indoor humidity: {e}", file=sys.stderr)
            
            # Outdoor humidity
            log(config, LOG_MAX, "Reading outdoor humidity")
            try:
                rho = ws.humidity_outdoor()
                output.append(f"RHo {rho}")
                log(config, LOG_MED, f"Outdoor humidity: {rho}%")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading outdoor humidity: {e}")
                print(f"Warning: Could not read outdoor humidity: {e}", file=sys.stderr)
            
            # Wind data
            # Reading 6 bytes gives us current + last 5 wind directions
            log(config, LOG_MAX, "Reading wind speed and direction")
            try:
                # Read wind speed and direction from address 0x527 (6 bytes total)
                # data[0] = overflow flag (should be 0x00 for valid data)
                # data[1] = low byte of wind speed
                # data[2] = high nibble: current direction, low nibble: high bits of wind speed
                # data[3-5] = last 5 wind directions (2 per byte, nibbles)
                data = ws.read_safe(0x527, 6)
                if data:
                    # Check for invalid wind data (from C code logic)
                    if (data[0] != 0x00 or 
                        (data[1] == 0xFF and ((data[2] & 0xF) == 0 or (data[2] & 0xF) == 1))):
                        log(config, LOG_MED, "Invalid wind data received, skipping")
                    else:
                        # Wind direction is in upper 4 bits of data[2]
                        dir_index = (data[2] >> 4) & 0x0F
                        
                        # Wind speed is 12-bit value: lower 4 bits of data[2] + all of data[1]
                        # Formula: ((data[2] & 0xF) << 8) + data[1]) / 10.0
                        wind_speed_raw = (((data[2] & 0x0F) << 8) + data[1]) / 10.0
                        wind_speed = wind_speed_raw * config.wind_speed_conv_factor
                        
                        output.append(f"WS {wind_speed:.1f}")
                        
                        if dir_index < len(WIND_DIRECTIONS):
                            wind_dir = WIND_DIRECTIONS[dir_index]
                            output.append(f"DIRtext {wind_dir}")
                            
                            # Debug: show all 6 direction values
                            if config.log_level >= 3:  # LOG_MAX
                                dir_degrees = [
                                    (data[2] >> 4) * 22.5,  # Current
                                    (data[3] & 0xF) * 22.5, # -1
                                    (data[3] >> 4) * 22.5,  # -2
                                    (data[4] & 0xF) * 22.5, # -3
                                    (data[4] >> 4) * 22.5,  # -4
                                    (data[5] & 0xF) * 22.5  # -5
                                ]
                                log(config, LOG_MAX, f"Wind directions (current to -5): {dir_degrees}")
                            
                            log(config, LOG_MED, f"Wind: {wind_speed:.1f} from {wind_dir} (index {dir_index})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading wind data: {e}")
                print(f"Warning: Could not read wind data: {e}", file=sys.stderr)
            
            # Pressure
            log(config, LOG_MAX, "Reading relative pressure")
            try:
                rp = ws.rel_pressure(config.pressure_conv_factor)
                output.append(f"RP {rp:.3f}")
                log(config, LOG_MED, f"Relative pressure: {rp:.3f}")
                # Note: Min/max functions would be added here
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading pressure: {e}")
                print(f"Warning: Could not read pressure: {e}", file=sys.stderr)
            
            # Tendency and forecast
            log(config, LOG_MAX, "Reading tendency and forecast")
            try:
                tendency, forecast = ws.tendency_forecast()
                output.append(f"Tendency {tendency}")
                output.append(f"Forecast {forecast}")
                log(config, LOG_MED, f"Tendency: {tendency}, Forecast: {forecast}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading tendency/forecast: {e}")
                print(f"Warning: Could not read tendency/forecast: {e}", file=sys.stderr)
            
            # Rain data (simplified - would need full implementation)
            log(config, LOG_MAX, "Reading rain data")
            # Note: Rain functions require more complex calculations
            output.append("# Rain data functions not yet fully implemented")
            
            log(config, LOG_MIN, "Closing weather station")
            
        log(config, LOG_MIN, "Weather station closed")
        log(config, LOG_MIN, "Data fetch completed successfully")
        
        # Print separator before data output if logging enabled
        if config.log_level >= LOG_MIN:
            print("=" * 70, file=sys.stderr)
            print("Weather Data Output:", file=sys.stderr)
            print("=" * 70, file=sys.stderr)
        
        # Print all output
        for line in output:
            print(line)
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

