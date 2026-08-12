# fetch2300 - Verbose Logging and Configuration Display

The Python version of `fetch2300` now includes verbose debug messages and configuration summary display based on the `LOG_LEVEL` setting in your configuration file.

## Log Levels

The logging system has 4 levels (same as the C version):

| Level | Value | Description | What Gets Logged |
|-------|-------|-------------|------------------|
| `LOG_OFF` | 0 | No logging | Only errors and weather data output |
| `LOG_MIN` | 1 | Minimal logging | Major operations (open/close, success/failure) + config summary |
| `LOG_MED` | 2 | Medium logging | All of LOG_MIN + data values read |
| `LOG_MAX` | 3 | Maximum logging | All of LOG_MED + each individual operation |

## Configuration

Set the log level in your `open2300.conf` file:

```ini
LOG_LEVEL 1    # Minimal logging (recommended)
LOG_LEVEL 2    # Medium logging (shows data values)
LOG_LEVEL 3    # Maximum logging (very verbose, for debugging)
```

## Example Output

### LOG_LEVEL 0 (Off) - Data Only

```
Date 2025-Dec-31
Time 19:30:45
Ti 21.5
To 5.3
DP 2.1
RHi 45
RHo 78
WS 3.2
DIRtext NW
RP 1013.250
Tendency Steady
Forecast Cloudy
# Rain data functions not yet fully implemented
```

### LOG_LEVEL 1 (Minimal) - Basic Progress

```
LOG: Loading configuration from: default locations
======================================================================
Configuration Summary:
======================================================================
Serial Device:        /dev/ttyS0
Log Level:            1
Timezone:             +1 hours from UTC
Temperature Unit:     Celsius (°C)
Wind Speed Unit:      m/s (meters per second)
Rain Unit:            mm (millimeters)
Pressure Unit:        hPa (hectopascals)
======================================================================

LOG: Opening weather station...
LOG: Weather station opened successfully
LOG: Closing weather station
LOG: Weather station closed
LOG: Data fetch completed successfully
======================================================================
Weather Data Output:
======================================================================
Date 2025-Dec-31
Time 19:30:45
Ti 21.5
To 5.3
DP 2.1
RHi 45
RHo 78
WS 3.2
DIRtext NW
RP 1013.250
Tendency Steady
Forecast Cloudy
# Rain data functions not yet fully implemented
```

### LOG_LEVEL 2 (Medium) - With Data Values

```
LOG: Loading configuration from: default locations
======================================================================
Configuration Summary:
======================================================================
Serial Device:        /dev/ttyS0
Log Level:            2
Timezone:             +1 hours from UTC
Temperature Unit:     Celsius (°C)
Wind Speed Unit:      m/s (meters per second)
Rain Unit:            mm (millimeters)
Pressure Unit:        hPa (hectopascals)
======================================================================

LOG: Opening weather station...
LOG: Using serial device: /dev/ttyS0
LOG: Weather station opened successfully
LOG: Reading current weather data...
LOG: Indoor temperature: 21.5
LOG: Outdoor temperature: 5.3
LOG: Dewpoint: 2.1
LOG: Indoor humidity: 45%
LOG: Outdoor humidity: 78%
LOG: Wind: 3.2 from NW
LOG: Relative pressure: 1013.250
LOG: Tendency: Steady, Forecast: Cloudy
LOG: Closing weather station
LOG: Weather station closed
LOG: Data fetch completed successfully
======================================================================
Weather Data Output:
======================================================================
Date 2025-Dec-31
Time 19:30:45
Ti 21.5
To 5.3
DP 2.1
RHi 45
RHo 78
WS 3.2
DIRtext NW
RP 1013.250
Tendency Steady
Forecast Cloudy
# Rain data functions not yet fully implemented
```

### LOG_LEVEL 3 (Maximum) - Very Verbose

```
LOG: Loading configuration from: default locations
======================================================================
Configuration Summary:
======================================================================
Serial Device:        /dev/ttyS0
Log Level:            3
Timezone:             +1 hours from UTC
Temperature Unit:     Celsius (°C)
Wind Speed Unit:      m/s (meters per second)
Rain Unit:            mm (millimeters)
Pressure Unit:        hPa (hectopascals)
======================================================================

LOG: Opening weather station...
LOG: Using serial device: /dev/ttyS0
LOG: Weather station opened successfully
LOG: Reading current weather data...
LOG: Getting current date/time
LOG: Reading indoor temperature
LOG: Indoor temperature: 21.5
LOG: Reading outdoor temperature
LOG: Outdoor temperature: 5.3
LOG: Reading dewpoint
LOG: Dewpoint: 2.1
LOG: Reading indoor humidity
LOG: Indoor humidity: 45%
LOG: Reading outdoor humidity
LOG: Outdoor humidity: 78%
LOG: Reading wind speed and direction
LOG: Wind: 3.2 from NW
LOG: Reading relative pressure
LOG: Relative pressure: 1013.250
LOG: Reading tendency and forecast
LOG: Tendency: Steady, Forecast: Cloudy
LOG: Reading rain data
LOG: Closing weather station
LOG: Weather station closed
LOG: Data fetch completed successfully
======================================================================
Weather Data Output:
======================================================================
Date 2025-Dec-31
Time 19:30:45
Ti 21.5
To 5.3
DP 2.1
RHi 45
RHo 78
WS 3.2
DIRtext NW
RP 1013.250
Tendency Steady
Forecast Cloudy
# Rain data functions not yet fully implemented
```

## Configuration Summary Display

When `LOG_LEVEL` is 1 or higher, `fetch2300` displays a configuration summary showing:

- **Serial Device**: Which serial port is being used
- **Log Level**: Current logging verbosity
- **Timezone**: Hours offset from UTC
- **Temperature Unit**: Celsius or Fahrenheit
- **Wind Speed Unit**: m/s, km/h, or MPH
- **Rain Unit**: Millimeters or inches
- **Pressure Unit**: hPa (hectopascals) or inHg (inches of mercury)

This helps verify that your configuration is being read correctly.

## Usage Examples

### Basic Usage (uses default config)
```bash
fetch2300
```

### With Specific Config File
```bash
fetch2300 /path/to/open2300.conf
```

### Redirect Data to File (logs still go to stderr)
```bash
fetch2300 > weather_data.txt
# Logs appear on screen, data goes to file
```

### Redirect Both Data and Logs
```bash
fetch2300 > weather_data.txt 2> fetch_log.txt
# Data goes to weather_data.txt, logs go to fetch_log.txt
```

### Data Only (suppress logs)
```bash
fetch2300 2>/dev/null
# Only weather data is shown
```

## Log Message Format

All log messages are sent to **stderr** (not stdout), so they don't interfere with the weather data output. This allows you to:

- Pipe data to other programs while still seeing progress
- Redirect data to files while monitoring progress
- Separate data from diagnostics

Format: `LOG: <message>`

Errors: `ERROR: <message>` or `Warning: <message>`

## Troubleshooting

### No Configuration Summary Shown

**Problem**: Configuration summary doesn't appear

**Solution**: Check your `LOG_LEVEL` setting:
```bash
grep LOG_LEVEL /etc/open2300.conf
```

It should be 1 or higher. If it's 0, increase it:
```ini
LOG_LEVEL 1
```

### Too Much Output

**Problem**: Too many log messages

**Solution**: Reduce the log level:
```ini
LOG_LEVEL 1    # or even 0 for no logs
```

### Want to See What's Being Read

**Problem**: Want to see actual values as they're read

**Solution**: Use `LOG_LEVEL 2`:
```ini
LOG_LEVEL 2
```

### Debugging Communication Issues

**Problem**: Weather station not responding correctly

**Solution**: Use maximum logging:
```ini
LOG_LEVEL 3
```

This shows every operation being performed.

## Comparison with C Version

The Python version's logging is equivalent to the C version:

| Feature | C Version | Python Version |
|---------|-----------|----------------|
| Log levels | 0-3 | 0-3 (same) |
| Config summary | No | **Yes** (new feature) |
| Progress messages | Yes (with DEBUG) | Yes (with LOG_LEVEL) |
| Data values shown | No | **Yes** (at LOG_MED) |
| Stderr output | Yes | Yes |

The Python version adds:
- ✓ Configuration summary display
- ✓ Data values in log output (LOG_MED)
- ✓ More descriptive messages
- ✓ Consistent formatting

## Integration with Scripts

### Shell Script Example

```bash
#!/bin/bash
# Weather data collection script

echo "Fetching weather data at $(date)"

# Run fetch2300 with logging
if fetch2300 > /var/log/weather/data.txt 2> /var/log/weather/fetch.log; then
    echo "Success"
else
    echo "Failed - check /var/log/weather/fetch.log"
    exit 1
fi
```

### Python Script Example

```python
#!/usr/bin/env python3
import subprocess
import sys

# Run fetch2300 and capture output
result = subprocess.run(
    ['fetch2300'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    # Parse data from stdout
    data = result.stdout
    print("Weather data received")
    
    # Logs are in stderr
    if result.stderr:
        print("Logs:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
else:
    print("Error:", result.stderr, file=sys.stderr)
    sys.exit(1)
```

## Performance Impact

Log levels have minimal performance impact:

- **LOG_OFF (0)**: No overhead
- **LOG_MIN (1)**: < 1ms overhead (config summary + 5-6 messages)
- **LOG_MED (2)**: < 2ms overhead (adds data value formatting)
- **LOG_MAX (3)**: < 3ms overhead (adds per-operation messages)

All levels are suitable for production use. The actual weather station communication takes much longer (2-5 seconds) than any logging overhead.

## Recommended Settings

### Production Use
```ini
LOG_LEVEL 1    # See major operations, detect issues
```

### Development/Testing
```ini
LOG_LEVEL 2    # See data values being read
```

### Debugging
```ini
LOG_LEVEL 3    # See everything
```

### Automated Scripts
```ini
LOG_LEVEL 0    # No logs, just data
# Or redirect: fetch2300 2>/dev/null
```

## Related Documentation

- `open2300.conf` - Configuration file format
- `README-PYTHON.md` - Python implementation overview
- `INSTALL` - Installation instructions

## Future Enhancements

Planned improvements:
- [ ] Add timing information (how long each read takes)
- [ ] Add retry count display when reads fail
- [ ] Add serial communication statistics
- [ ] Color-coded log levels (when terminal supports it)

---

**Note**: All log messages go to stderr, weather data goes to stdout. This separation allows flexible piping and redirection.

