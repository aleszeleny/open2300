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
            
            # Weather station date/time
            try:
                ws_timestamp = ws.ws_time()
                station_time = SubElement(root, 'station_datetime')
                date_elem = SubElement(station_time, 'date')
                date_elem.text = f"{ws_timestamp.year:04d}-{ws_timestamp.month:02d}-{ws_timestamp.day:02d}"
                time_elem = SubElement(station_time, 'time')
                time_elem.text = f"{ws_timestamp.hour:02d}:{ws_timestamp.minute:02d}"
            except:
                pass
            
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

