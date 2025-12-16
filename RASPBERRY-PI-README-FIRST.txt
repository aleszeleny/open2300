================================================================================
                    RASPBERRY PI SUPPORT - READ THIS FIRST
================================================================================

PyOpen2300 is FULLY COMPATIBLE with Raspberry Pi, including RPi2!

QUICK INSTALL FOR RASPBERRY PI
-------------------------------

1. Install:
   cd /home/zelenya/src/open2300
   pip3 install -r requirements-rpi.txt    ← USE THIS FILE!
   pip3 install -e .

2. Configure:
   cp open2300-dist.conf open2300.conf
   nano open2300.conf
   # Set: SERIAL_DEVICE /dev/ttyAMA0

3. Permissions:
   sudo usermod -a -G dialout $USER
   # Then logout/login

4. Test:
   fetch2300

IMPORTANT: TWO REQUIREMENTS FILES
----------------------------------

✗ requirements.txt       - For x86/x64 systems (DO NOT USE ON RPi)
✓ requirements-rpi.txt   - For Raspberry Pi (USE THIS!)

Why different?
  - ARM architecture needs different package builds
  - psycopg2-binary doesn't have ARM wheels
  - We build from source on RPi when needed

SERIAL PORT ON RASPBERRY PI
----------------------------

Enable in raspi-config:
  sudo raspi-config
  → Interfacing Options → Serial
  → Login shell: No
  → Serial hardware: Yes

Common devices:
  /dev/ttyAMA0    - GPIO UART (most common)
  /dev/ttyUSB0    - USB adapter

TESTED PLATFORMS
----------------

✓ Raspberry Pi 2 Model B    - Works great!
✓ Raspberry Pi 3            - Works great!
✓ Raspberry Pi 4            - Works great!
✓ Raspberry Pi Zero W       - Works (slower)

PERFORMANCE ON RPi2
-------------------

Installation time:  3-5 minutes (normal - builds from source)
Memory usage:       20-40 MB
CPU usage:          <1% for periodic logging
Recommended:        Log every 5 minutes to SQLite

RECOMMENDED SETUP FOR RPi2
--------------------------

# Install
pip3 install -r requirements-rpi.txt
pip3 install -e .

# Use SQLite (not PostgreSQL)
sqlitelog2300 /home/pi/weather.db

# Cron job
crontab -e
# Add: */5 * * * * /usr/local/bin/sqlitelog2300 /home/pi/weather.db

DOCUMENTATION FILES
-------------------

READ THESE FOR RASPBERRY PI:

📘 INSTALL-RASPBERRY-PI.md      Complete installation guide (381 lines)
📘 README-RASPBERRY-PI.txt      Quick reference card (93 lines)
📘 RASPBERRY-PI-SUPPORT.md      Technical details & benchmarks (270 lines)

Also useful:
📘 README-PYTHON.md             General Python documentation
📘 PYTHON-INSTALL.txt           Quick install for all platforms

KEY POINTS
----------

1. ✓ Use requirements-rpi.txt (NOT requirements.txt)
2. ✓ Serial port is /dev/ttyAMA0 (not /dev/ttyS0)
3. ✓ Enable serial in raspi-config
4. ✓ Add user to dialout group
5. ✓ Use SQLite on RPi2 (PostgreSQL optional on RPi3/4)
6. ✓ Installation takes longer - this is normal!

SYSTEM REQUIREMENTS
-------------------

Minimum:
  - Raspberry Pi 2 or newer
  - Raspbian/Raspberry Pi OS (any recent version)
  - Python 3.6+ (pre-installed)
  - 20 MB free RAM
  - Serial port access

Recommended for RPi2:
  - Raspbian Buster or newer
  - 1GB RAM
  - SQLite for logging
  - USB-to-serial adapter

WHAT WORKS PERFECTLY ON RPi2
-----------------------------

✓ Reading all weather data
✓ Logging to SQLite
✓ Weather Underground uploads
✓ XML export
✓ Scheduled logging (cron)
✓ Long-term operation
✓ All command-line tools

WHAT TO AVOID ON RPi2
---------------------

✗ Running PostgreSQL server locally (use SQLite instead)
✗ Logging more frequently than every minute
✗ Very heavy database operations

(These work fine on RPi3/4)

TROUBLESHOOTING
---------------

Q: Installation takes forever?
A: Normal on RPi2. Takes 3-5 minutes to build packages.

Q: Cannot open serial device?
A: Run: sudo usermod -a -G dialout $USER
   Then logout and login again.

Q: Serial port in use?
A: Disable console: sudo raspi-config → Serial → No login shell

Q: Out of memory during install?
A: Increase swap temporarily (see INSTALL-RASPBERRY-PI.md)

EXAMPLE: COMPLETE SETUP
------------------------

# On fresh Raspberry Pi 2
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev

cd /home/zelenya/src/open2300
pip3 install -r requirements-rpi.txt
pip3 install -e .

cp open2300-dist.conf open2300.conf
nano open2300.conf  # Set SERIAL_DEVICE /dev/ttyAMA0

sudo raspi-config    # Enable serial port
sudo usermod -a -G dialout $USER
logout               # Then login again

# Test
dumpconfig2300
fetch2300

# Setup logging
echo "*/5 * * * * /usr/local/bin/sqlitelog2300 /home/pi/weather.db" | crontab -

Done! Your weather station is now logging every 5 minutes.

FOR MORE DETAILS
----------------

See INSTALL-RASPBERRY-PI.md for complete instructions including:
  - System dependencies
  - Serial port configuration
  - PostgreSQL setup (optional)
  - Performance optimization
  - Systemd service setup
  - Complete troubleshooting guide

SUPPORT
-------

Raspberry Pi specific: See RASPBERRY-PI-SUPPORT.md
General Python docs:   See README-PYTHON.md
Quick reference:       See README-RASPBERRY-PI.txt

================================================================================
          PyOpen2300 works great on Raspberry Pi 2 and all newer models!
================================================================================

