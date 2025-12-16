# PyOpen2300 - Python Implementation

This directory contains a complete Python reimplementation of the open2300 weather station tools.

## Quick Start

```bash
cd python-implementation

# Install dependencies
pip install -r requirements.txt          # For x86/x64
# OR
pip3 install -r requirements-rpi.txt     # For Raspberry Pi

# Install the package
pip install -e .

# Configure
cp ../open2300-dist.conf open2300.conf
nano open2300.conf  # Edit serial device

# Test
dumpconfig2300
fetch2300
```

## Documentation

- **README-PYTHON.md** - Complete user guide
- **PYTHON-INSTALL.txt** - Quick installation guide
- **PYTHON-PORT-SUMMARY.md** - Technical implementation details
- **PYTHON-REIMPLEMENTATION-COMPLETE.txt** - Project summary

### Raspberry Pi Support

- **INSTALL-RASPBERRY-PI.md** - Complete RPi installation guide
- **README-RASPBERRY-PI.txt** - Quick reference
- **RASPBERRY-PI-SUPPORT.md** - Technical details and benchmarks
- **RASPBERRY-PI-README-FIRST.txt** - Start here for RPi

### PostgreSQL

- **POSTGRESQL-PREPARED-STATEMENTS.md** - Prepared statements guide
- **POSTGRESQL-UPGRADE-SUMMARY.txt** - PostgreSQL upgrade details

## Structure

```
python-implementation/
├── pyopen2300/              Python package
│   ├── __init__.py
│   ├── constants.py
│   ├── config.py
│   ├── serial_comm.py
│   ├── weatherstation.py
│   ├── cli/                 Command-line tools
│   │   ├── open2300.py
│   │   ├── fetch2300.py
│   │   ├── log2300.py
│   │   └── ... (15 tools)
│   └── db/                  Database support
│       └── pgsql_logger.py
│
├── examples/                Example scripts
│   └── pgsql_daemon_example.py
│
├── setup.py                 Package setup
├── requirements.txt         Dependencies (x86/x64)
├── requirements-rpi.txt     Dependencies (Raspberry Pi)
└── [Documentation files]
```

## Features

- ✅ Complete WS-2300 serial protocol implementation
- ✅ All command-line tools from C version
- ✅ PostgreSQL and SQLite database support
- ✅ Weather Underground upload
- ✅ Raspberry Pi support (including RPi2)
- ✅ Prepared statements with autocommit mode
- ✅ Easy installation via pip

## Available Commands

After installation, these commands are available:

**Basic operations:**
- `open2300` - Low-level read/write
- `dump2300` - Memory dump
- `bin2300` - Binary dump
- `dumpconfig2300` - Show configuration

**Data reading:**
- `fetch2300` - Fetch all data
- `log2300` - Log to file
- `xml2300` - XML export

**Network services:**
- `wu2300` - Weather Underground upload

**Database:**
- `pgsql2300` - PostgreSQL logging
- `sqlitelog2300` - SQLite logging

**Station control:**
- `light2300` - LCD backlight
- `interval2300` - History interval
- `minmax2300` - Reset min/max

**History:**
- `history2300` - Read history
- `histlog2300` - Log history

## Requirements

- Python 3.6 or higher
- pyserial (for serial communication)
- psycopg2 (optional, for PostgreSQL)

## Platform Support

- ✅ Linux (x86/x64)
- ✅ Raspberry Pi (all models, including RPi2)
- ✅ macOS
- ✅ Windows (with serial drivers)

## License

GNU General Public License version 2.0 or later

Original C implementation: Kenneth Lavrsen (2003-2006)
Python port: 2025

## Related

The original C implementation is in the parent directory.
Both implementations can coexist and share the same `open2300.conf` file.

