# PyOpen2300 - Python Implementation

This is a Python reimplementation of the open2300 weather station tools for controlling and reading data from WS-2300 weather stations.

## About

PyOpen2300 is a complete Python port of the original C-based open2300 project (version 1.11). It provides the same functionality for communicating with WS-2300 weather stations through a serial interface.

**Original C Implementation:**
- Copyright 2003-2006, Kenneth Lavrsen
- Licensed under GNU General Public License version 2.0

**Python Reimplementation:**
- 2025
- Same GPL v2.0 license

## Features

- Full serial communication protocol implementation for WS-2300
- Multiple command-line tools for weather data access
- Support for PostgreSQL and SQLite databases (MySQL support removed)
- Weather Underground upload support
- XML export functionality
- Configuration file support

## Installation

### Prerequisites

- Python 3.6 or higher
- Serial port access (usually `/dev/ttyS0` or `/dev/ttyUSB0` on Linux)

**For Raspberry Pi users:** See `INSTALL-RASPBERRY-PI.md` or `README-RASPBERRY-PI.txt` for RPi-specific instructions.

### Install from source

For a Linux system using systemd, the Makefile installs the Python package,
virtual environment, configuration, and timer under `/opt/open2300`:

```bash
cd python-implementation
make install          # Debian/Ubuntu/x86 systems
make install-rpi      # Raspberry Pi OS
sudo make enable
```

The installer creates or reuses the `weather` system user and adds it to
`dialout` for serial-port access. Edit `/opt/open2300/open2300.conf` before
enabling the timer. The installed units are `open2300-python.service` and
`open2300-python.timer`; the timer runs every minute.

**On x86/x64 systems (Linux, macOS, Windows):**
```bash
cd open2300

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

**On Raspberry Pi (including RPi2):**
```bash
cd open2300

# Install dependencies (use RPi-specific requirements)
pip3 install -r requirements-rpi.txt

# Install the package
pip3 install -e .
```

See `INSTALL-RASPBERRY-PI.md` for detailed Raspberry Pi setup.

### Serial Port Access

On Linux, you need read/write access to the serial device:

```bash
# Give access to serial port (example for /dev/ttyS0)
sudo chmod 666 /dev/ttyS0

# Or add your user to the dialout group
sudo usermod -a -G dialout $USER
# (logout and login again for this to take effect)
```

## Configuration

Copy the example configuration file:

```bash
cp python-implementation/open2300-dist.conf open2300.conf
```

Edit `open2300.conf` to set your serial device and preferences:

```ini
SERIAL_DEVICE /dev/ttyS0
TIMEZONE 0
WIND_SPEED m/s
TEMPERATURE C
RAIN mm
PRESSURE hPa
```

The tools will search for the config file in these locations (in order):
1. Path specified as command-line argument
2. `./open2300.conf` (current directory)
3. `/usr/local/etc/open2300.conf`
4. `/etc/open2300.conf`

## Available Tools

### Basic Tools

- **open2300** - Low-level read/write operations
  ```bash
  open2300 346 r 2          # Read 2 bytes from address 0x346
  open2300 23B w 0123       # Write nibbles to address 0x23B
  ```

- **dump2300** - Dump memory range to file
  ```bash
  dump2300 dump.txt 21C 3A1
  ```

- **bin2300** - Dump memory in binary format
  ```bash
  bin2300 dump.bin 21C 3A1
  ```

- **light2300** - Control LCD backlight
  ```bash
  light2300 on
  light2300 off
  ```

### Data Reading Tools

- **fetch2300** - Fetch all current weather data
  ```bash
  fetch2300 [config_file]
  ```

- **log2300** - Log current data to file
  ```bash
  log2300 weather.log [config_file]
  ```

- **xml2300** - Export data to XML
  ```bash
  xml2300 weather.xml [config_file]
  ```

### Upload Tools

- **wu2300** - Upload to Weather Underground
  ```bash
  # Configure Weather Underground ID and password in config file first
  wu2300 [config_file]
  ```

### Database Tools

- **pgsql2300** - Log to PostgreSQL database
  ```bash
  # Configure PGSQL_CONNECT in config file first
  pgsql2300 [config_file]
  ```

- **mqtt2300** - Publish one retained JSON weather snapshot to MQTT
  ```bash
  mqtt2300 [config_file]
  ```

- **pgsql2300-daemon** - Continuously report to PostgreSQL and optional MQTT
  ```bash
  pgsql2300-daemon --config open2300.conf
  ```

- **sqlitelog2300** - Log to SQLite database
  ```bash
  sqlitelog2300 weather.db [config_file]
  ```

## Database Setup

### PostgreSQL

1. Install psycopg2: `pip install psycopg2-binary`
2. Create database and table using `pgsql2300.sql`
3. Configure connection in `open2300.conf`:
   ```ini
   PGSQL_CONNECT hostaddr='127.0.0.1' dbname='open2300' user='postgres' password='pass'
   PGSQL_TABLE weather
   PGSQL_STATION mystation
   ```

MQTT reporting is enabled by setting `MQTT_HOST`. The default state topic is
`open2300/<MQTT_STATION>`, and Home Assistant discovery is enabled with
`MQTT_HA_DISCOVERY true`. The daemon adds retained availability and LWT;
one-shot commands publish state/discovery only.

### SQLite

SQLite support is built into Python. The table is created automatically:

```bash
sqlitelog2300 weather.db
```

## Differences from C Implementation

- **Removed MySQL support** - Use PostgreSQL or SQLite instead
- **Python-native implementations** - Uses Python libraries (pyserial, psycopg2, etc.)
- **Simplified installation** - No compilation required
- **Same functionality** - All core features are preserved

## Scheduled Logging

Use cron to schedule regular data logging:

```bash
# Edit crontab
crontab -e

# Add entries (example: log every 5 minutes)
*/5 * * * * /usr/local/bin/log2300 /var/log/weather.log
*/15 * * * * /usr/local/bin/wu2300
```

## Troubleshooting

### Cannot open serial device

- Check that the device exists: `ls -l /dev/ttyS0`
- Check permissions: `sudo chmod 666 /dev/ttyS0`
- Try adding user to dialout group: `sudo usermod -a -G dialout $USER`

### Could not reset weather station

- Check cable connection
- Verify correct serial port in config
- Try different USB port if using USB-to-serial adapter
- Some weather stations need a power cycle

### Import errors

```bash
# Install required packages
pip install -r requirements.txt

# For PostgreSQL support
pip install psycopg2-binary
```

## Development

The package structure:

```
pyopen2300/
  __init__.py         # Package initialization
  constants.py        # Constants and definitions
  config.py           # Configuration management
  serial_comm.py      # Serial communication layer
  weatherstation.py   # Weather station protocol
  cli/                # Command-line tools
    __init__.py
    open2300.py
    fetch2300.py
    log2300.py
    wu2300.py
    ... (other tools)
```

## License

GNU General Public License version 2.0 or later

See the COPYING file for details.

## Credits

- **Kenneth Lavrsen** - Original C implementation (2003-2006)
- **Contributors** - See the original open2300 documentation for all contributors to the C version

## References

- Original open2300 project: See README and INSTALL files
- WS-2300 memory map: See memory_map_2300.txt
- Protocol documentation: See api.txt

## Support

For issues specific to the Python implementation, check the code comments and compare with the original C implementation.

For weather station hardware issues, refer to the original open2300 documentation.
