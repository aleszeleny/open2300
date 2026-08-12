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
            
            # Indoor temperature with min/max
            log(config, LOG_MAX, "Reading indoor temperature")
            try:
                ti = ws.temperature_indoor(config.temperature_conv)
                output.append(f"Ti {ti:.1f}")
                
                ti_min, ti_max, time_min, time_max = ws.temperature_indoor_minmax(config.temperature_conv)
                output.append(f"Timin {ti_min:.1f}")
                output.append(f"Timax {ti_max:.1f}")
                output.append(f"TTimin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DTimin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TTimax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DTimax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Indoor temperature: {ti:.1f} (min: {ti_min:.1f}, max: {ti_max:.1f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading indoor temperature: {e}")
                print(f"Warning: Could not read indoor temperature: {e}", file=sys.stderr)
            
            # Outdoor temperature with min/max
            log(config, LOG_MAX, "Reading outdoor temperature")
            try:
                to = ws.temperature_outdoor(config.temperature_conv)
                output.append(f"To {to:.1f}")
                
                to_min, to_max, time_min, time_max = ws.temperature_outdoor_minmax(config.temperature_conv)
                output.append(f"Tomin {to_min:.1f}")
                output.append(f"Tomax {to_max:.1f}")
                output.append(f"TTomin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DTomin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TTomax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DTomax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Outdoor temperature: {to:.1f} (min: {to_min:.1f}, max: {to_max:.1f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading outdoor temperature: {e}")
                print(f"Warning: Could not read outdoor temperature: {e}", file=sys.stderr)
            
            # Dewpoint with min/max
            log(config, LOG_MAX, "Reading dewpoint")
            try:
                dp = ws.dewpoint(config.temperature_conv)
                output.append(f"DP {dp:.1f}")
                
                dp_min, dp_max, time_min, time_max = ws.dewpoint_minmax(config.temperature_conv)
                output.append(f"DPmin {dp_min:.1f}")
                output.append(f"DPmax {dp_max:.1f}")
                output.append(f"TDPmin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DDPmin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TDPmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DDPmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Dewpoint: {dp:.1f} (min: {dp_min:.1f}, max: {dp_max:.1f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading dewpoint: {e}")
                print(f"Warning: Could not read dewpoint: {e}", file=sys.stderr)
            
            # Indoor humidity with min/max
            log(config, LOG_MAX, "Reading indoor humidity")
            try:
                rhi, rhi_min, rhi_max, time_min, time_max = ws.humidity_indoor_all()
                output.append(f"RHi {rhi}")
                output.append(f"RHimin {rhi_min}")
                output.append(f"RHimax {rhi_max}")
                output.append(f"TRHimin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DRHimin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TRHimax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DRHimax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Indoor humidity: {rhi}% (min: {rhi_min}%, max: {rhi_max}%)")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading indoor humidity: {e}")
                print(f"Warning: Could not read indoor humidity: {e}", file=sys.stderr)
            
            # Outdoor humidity with min/max
            log(config, LOG_MAX, "Reading outdoor humidity")
            try:
                rho, rho_min, rho_max, time_min, time_max = ws.humidity_outdoor_all()
                output.append(f"RHo {rho}")
                output.append(f"RHomin {rho_min}")
                output.append(f"RHomax {rho_max}")
                output.append(f"TRHomin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DRHomin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TRHomax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DRHomax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Outdoor humidity: {rho}% (min: {rho_min}%, max: {rho_max}%)")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading outdoor humidity: {e}")
                print(f"Warning: Could not read outdoor humidity: {e}", file=sys.stderr)
            
            # Wind data
            log(config, LOG_MAX, "Reading wind speed and direction")
            try:
                wind_speed, winddir_index, winddir = ws.wind_all(config.wind_speed_conv_factor)
                output.append(f"WS {wind_speed:.1f}")
                
                if winddir_index < len(WIND_DIRECTIONS):
                    wind_dir = WIND_DIRECTIONS[winddir_index]
                    output.append(f"DIRtext {wind_dir}")
                    output.append(f"DIR0 {winddir[0]:.1f}")
                    output.append(f"DIR1 {winddir[1]:.1f}")
                    output.append(f"DIR2 {winddir[2]:.1f}")
                    output.append(f"DIR3 {winddir[3]:.1f}")
                    output.append(f"DIR4 {winddir[4]:.1f}")
                    output.append(f"DIR5 {winddir[5]:.1f}")
                    
                    log(config, LOG_MED, f"Wind: {wind_speed:.1f} from {wind_dir}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading wind data: {e}")
                print(f"Warning: Could not read wind data: {e}", file=sys.stderr)
            
            # Windchill with min/max
            log(config, LOG_MAX, "Reading windchill")
            try:
                wc = ws.windchill(config.temperature_conv)
                output.append(f"WC {wc:.1f}")
                
                wc_min, wc_max, time_min, time_max = ws.windchill_minmax(config.temperature_conv)
                output.append(f"WCmin {wc_min:.1f}")
                output.append(f"WCmax {wc_max:.1f}")
                output.append(f"TWCmin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DWCmin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TWCmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DWCmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Windchill: {wc:.1f} (min: {wc_min:.1f}, max: {wc_max:.1f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading windchill: {e}")
                print(f"Warning: Could not read windchill: {e}", file=sys.stderr)
            
            # Wind speed min/max
            log(config, LOG_MAX, "Reading wind speed min/max")
            try:
                ws_min, ws_max, time_min, time_max = ws.wind_minmax(config.wind_speed_conv_factor)
                output.append(f"WSmin {ws_min:.1f}")
                output.append(f"WSmax {ws_max:.1f}")
                output.append(f"TWSmin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DWSmin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TWSmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DWSmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Wind speed: min {ws_min:.1f}, max {ws_max:.1f}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading wind min/max: {e}")
                print(f"Warning: Could not read wind min/max: {e}", file=sys.stderr)
            
            # Rain 1h
            log(config, LOG_MAX, "Reading rain 1h")
            try:
                r1h, r1h_max, time_max = ws.rain_1h_all(config.rain_conv_factor)
                output.append(f"R1h {r1h:.2f}")
                output.append(f"R1hmax {r1h_max:.2f}")
                output.append(f"TR1hmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DR1hmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Rain 1h: {r1h:.2f} (max: {r1h_max:.2f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading rain 1h: {e}")
                print(f"Warning: Could not read rain 1h: {e}", file=sys.stderr)
            
            # Rain 24h
            log(config, LOG_MAX, "Reading rain 24h")
            try:
                r24h, r24h_max, time_max = ws.rain_24h_all(config.rain_conv_factor)
                output.append(f"R24h {r24h:.2f}")
                output.append(f"R24hmax {r24h_max:.2f}")
                output.append(f"TR24hmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DR24hmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Rain 24h: {r24h:.2f} (max: {r24h_max:.2f})")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading rain 24h: {e}")
                print(f"Warning: Could not read rain 24h: {e}", file=sys.stderr)
            
            # Rain total
            log(config, LOG_MAX, "Reading rain total")
            try:
                rtot, time_since = ws.rain_total_all(config.rain_conv_factor)
                output.append(f"Rtot {rtot:.2f}")
                output.append(f"TRtot {time_since.hour:02d}:{time_since.minute:02d}")
                output.append(f"DRtot {time_since.year:04d}-{time_since.month:02d}-{time_since.day:02d}")
                
                log(config, LOG_MED, f"Rain total: {rtot:.2f}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading rain total: {e}")
                print(f"Warning: Could not read rain total: {e}", file=sys.stderr)
            
            # Pressure with min/max
            log(config, LOG_MAX, "Reading relative pressure")
            try:
                rp = ws.rel_pressure(config.pressure_conv_factor)
                output.append(f"RP {rp:.3f}")
                
                rp_min, rp_max, time_min, time_max = ws.rel_pressure_minmax(config.pressure_conv_factor)
                output.append(f"RPmin {rp_min:.3f}")
                output.append(f"RPmax {rp_max:.3f}")
                output.append(f"TRPmin {time_min.hour:02d}:{time_min.minute:02d}")
                output.append(f"DRPmin {time_min.year:04d}-{time_min.month:02d}-{time_min.day:02d}")
                output.append(f"TRPmax {time_max.hour:02d}:{time_max.minute:02d}")
                output.append(f"DRPmax {time_max.year:04d}-{time_max.month:02d}-{time_max.day:02d}")
                
                log(config, LOG_MED, f"Relative pressure: {rp:.3f} (min: {rp_min:.3f}, max: {rp_max:.3f})")
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
            
            # Weather station local date/time
            log(config, LOG_MAX, "Reading weather station local date/time")
            try:
                ws_local = ws.ws_time_local()
                output.append(f"WSDateLocal {ws_local.year:04d}-{ws_local.month:02d}-{ws_local.day:02d}")
                output.append(f"WSTimeLocal {ws_local.hour:02d}:{ws_local.minute:02d}")
                log(config, LOG_MED, f"Station local time: {ws_local.year:04d}-{ws_local.month:02d}-{ws_local.day:02d} {ws_local.hour:02d}:{ws_local.minute:02d}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading station local time: {e}")
                print(f"Warning: Could not read station local time: {e}", file=sys.stderr)
            
            # Weather station UTC date/time (from station memory)
            log(config, LOG_MAX, "Reading UTC time from station memory")
            try:
                ws_utc = ws.ws_time_utc_from_station()
                output.append(f"WSDateUTC {ws_utc.year:04d}-{ws_utc.month:02d}-{ws_utc.day:02d}")
                output.append(f"WSTimeUTC {ws_utc.hour:02d}:{ws_utc.minute:02d}")
                log(config, LOG_MED, f"Station UTC time: {ws_utc.year:04d}-{ws_utc.month:02d}-{ws_utc.day:02d} {ws_utc.hour:02d}:{ws_utc.minute:02d}")
            except Exception as e:
                log(config, LOG_MIN, f"ERROR reading station UTC time: {e}")
                print(f"Warning: Could not read station UTC time: {e}", file=sys.stderr)
            
            # Station timezone offset and calculated UTC (for verification in verbose mode)
            if config.log_level >= LOG_MAX:
                # Calculate timezone offset from station
                log(config, LOG_MAX, "Calculating timezone offset from station times")
                try:
                    station_tz = ws.ws_timezone_offset_from_station()
                    output.append(f"StationTZ {station_tz:.1f}")
                    log(config, LOG_MAX, f"Station timezone offset: {station_tz:.1f}")
                except Exception as e:
                    log(config, LOG_MAX, f"ERROR calculating station TZ: {e}")
                
                # Calculate UTC from local + config timezone
                log(config, LOG_MAX, "Calculating UTC from local time + config timezone offset")
                try:
                    ws_utc_calc = ws.ws_time_utc_calculated(config.timezone)
                    output.append(f"WSDateUTCCalc {ws_utc_calc.year:04d}-{ws_utc_calc.month:02d}-{ws_utc_calc.day:02d}")
                    output.append(f"WSTimeUTCCalc {ws_utc_calc.hour:02d}:{ws_utc_calc.minute:02d}")
                    output.append(f"ConfigTZ {config.timezone:.1f}")
                    log(config, LOG_MAX, f"Calculated UTC time: {ws_utc_calc.year:04d}-{ws_utc_calc.month:02d}-{ws_utc_calc.day:02d} {ws_utc_calc.hour:02d}:{ws_utc_calc.minute:02d}")
                except Exception as e:
                    log(config, LOG_MAX, f"ERROR calculating UTC time: {e}")
                
                # # Check DCF77 sync status
                # log(config, LOG_MAX, "Checking DCF77 synchronization status")
                # try:
                #     sync_status = ws.ws_dcf77_sync_status(config.timezone)
                #     if sync_status == 1:
                #         sync_str = "Synced"
                #     elif sync_status == 0:
                #         sync_str = "NotSynced"
                #     else:
                #         sync_str = "Unknown"
                #     output.append(f"DCF77Sync {sync_str}")
                #     log(config, LOG_MAX, f"DCF77 sync status: {sync_str}")
                # except Exception as e:
                #     log(config, LOG_MAX, f"ERROR checking DCF77 sync status: {e}")
                
                # Read connection type
                log(config, LOG_MAX, "Reading connection type")
                try:
                    conn_type = ws.ws_connection_type()
                    if conn_type == 0x0:
                        conn_str = "Cable"
                    elif conn_type == 0x3:
                        conn_str = "Lost"
                    elif conn_type == 0xF:
                        conn_str = "Wireless"
                    elif conn_type == -1:
                        conn_str = "Error"
                    else:
                        conn_str = f"Unknown(0x{conn_type:02X})"
                    output.append(f"ConnectionType {conn_str} (0x{conn_type:02X})")
                    log(config, LOG_MAX, f"Connection type: {conn_str}")
                except Exception as e:
                    log(config, LOG_MAX, f"ERROR reading connection type: {e}")
            
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
