#!/usr/bin/env python3
"""
xml2300 - Export weather data to XML
Python equivalent of xml2300.c
"""

import sys
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from ..weatherstation import WeatherStation
from ..config import Config


def print_usage():
    """Print usage information"""
    print("xml2300 - Export weather data to XML")
    print("Usage:")
    print("  xml2300 xmlfile [config_file]")


def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    xmlfile = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load configuration
        config = Config(config_file)
        
        # Open weather station
        with WeatherStation(config.serial_device_name) as ws:
            # Create XML structure
            root = Element('weatherstation')
            root.set('type', 'WS2300')
            root.set('version', '1.11')
            
            # Timestamp
            timestamp = SubElement(root, 'timestamp')
            timestamp.text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Temperature
            temp = SubElement(root, 'temperature')
            try:
                ti = ws.temperature_indoor(config.temperature_conv)
                indoor = SubElement(temp, 'indoor')
                indoor.text = f"{ti:.1f}"
                indoor.set('unit', 'C' if config.temperature_conv == 0 else 'F')
            except:
                pass
            
            try:
                to = ws.temperature_outdoor(config.temperature_conv)
                outdoor = SubElement(temp, 'outdoor')
                outdoor.text = f"{to:.1f}"
                outdoor.set('unit', 'C' if config.temperature_conv == 0 else 'F')
            except:
                pass
            
            try:
                dp = ws.dewpoint(config.temperature_conv)
                dewpoint = SubElement(temp, 'dewpoint')
                dewpoint.text = f"{dp:.1f}"
                dewpoint.set('unit', 'C' if config.temperature_conv == 0 else 'F')
            except:
                pass
            
            # Humidity
            humidity = SubElement(root, 'humidity')
            try:
                rhi = ws.humidity_indoor()
                indoor_hum = SubElement(humidity, 'indoor')
                indoor_hum.text = str(rhi)
                indoor_hum.set('unit', '%')
            except:
                pass
            
            try:
                rho = ws.humidity_outdoor()
                outdoor_hum = SubElement(humidity, 'outdoor')
                outdoor_hum.text = str(rho)
                outdoor_hum.set('unit', '%')
            except:
                pass
            
            # Pressure
            try:
                rp = ws.rel_pressure(config.pressure_conv_factor)
                pressure = SubElement(root, 'pressure')
                pressure.text = f"{rp:.3f}"
                pressure.set('unit', 'hPa')
            except:
                pass
            
            # Forecast
            try:
                tendency, forecast = ws.tendency_forecast()
                fc = SubElement(root, 'forecast')
                tend = SubElement(fc, 'tendency')
                tend.text = tendency
                pred = SubElement(fc, 'prediction')
                pred.text = forecast
            except:
                pass
            
            # Weather station local date/time
            try:
                ws_local = ws.ws_time_local()
                station_local = SubElement(root, 'station_datetime_local')
                date_elem = SubElement(station_local, 'date')
                date_elem.text = f"{ws_local.year:04d}-{ws_local.month:02d}-{ws_local.day:02d}"
                time_elem = SubElement(station_local, 'time')
                time_elem.text = f"{ws_local.hour:02d}:{ws_local.minute:02d}"
            except:
                pass
            
            # Weather station UTC date/time (from station memory)
            try:
                ws_utc = ws.ws_time_utc_from_station()
                station_utc = SubElement(root, 'station_datetime_utc')
                date_elem = SubElement(station_utc, 'date')
                date_elem.text = f"{ws_utc.year:04d}-{ws_utc.month:02d}-{ws_utc.day:02d}"
                time_elem = SubElement(station_utc, 'time')
                time_elem.text = f"{ws_utc.hour:02d}:{ws_utc.minute:02d}"
            except:
                pass
            
            # Connection Type
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
                conn_elem = SubElement(root, 'connection_type')
                conn_elem.text = conn_str
            except Exception as e:
                print(f"Warning: Could not read connection type: {e}", file=sys.stderr)
            
            # Write to file
            xml_string = prettify_xml(root)
            with open(xmlfile, 'w') as f:
                f.write(xml_string)
            
            print(f"Weather data written to {xmlfile}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

