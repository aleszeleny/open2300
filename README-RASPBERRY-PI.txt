================================================================================
  PyOpen2300 for Raspberry Pi - Quick Reference
================================================================================

TESTED PLATFORMS
----------------
✓ Raspberry Pi 2 Model B (Raspbian)
✓ Raspberry Pi 3 (all models)
✓ Raspberry Pi 4
✓ Raspberry Pi Zero W/WH

QUICK INSTALL
-------------

1. System dependencies:
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-dev

2. Install package:
   cd /home/zelenya/src/open2300
   pip3 install -r requirements-rpi.txt
   pip3 install -e .

3. Configure:
   cp open2300-dist.conf open2300.conf
   nano open2300.conf
   # Set: SERIAL_DEVICE /dev/ttyAMA0

4. Permissions:
   sudo usermod -a -G dialout $USER
   # Then logout and login

5. Test:
   dumpconfig2300
   fetch2300

SERIAL PORT SETUP
-----------------

Enable serial in raspi-config:
  sudo raspi-config
  → Interfacing Options → Serial
  → Login shell: No
  → Serial hardware: Yes

Common devices:
  /dev/ttyAMA0    - GPIO UART
  /dev/serial0    - Primary UART alias
  /dev/ttyUSB0    - USB adapter

AUTOMATIC LOGGING
-----------------

Add to crontab (crontab -e):
  */5 * * * * /usr/local/bin/sqlitelog2300 /home/pi/weather.db

REQUIREMENTS FILES
------------------

requirements.txt      - For x86/x64 systems
requirements-rpi.txt  - For Raspberry Pi (use this!)

KEY DIFFERENCES
---------------

x86/x64:
  - psycopg2-binary (pre-built wheels)
  - Fast installation

Raspberry Pi:
  - psycopg2 from source (if needed)
  - Slower installation on older models
  - SQLite recommended over PostgreSQL

TROUBLESHOOTING
---------------

Cannot open serial:
  - Check device: ls -l /dev/ttyAMA0
  - Check groups: groups (should include dialout)
  - Disable console: sudo systemctl disable serial-getty@ttyAMA0.service

Memory on RPi2:
  - Use SQLite instead of PostgreSQL
  - Reduce logging frequency
  - Stop unnecessary services

FOR FULL DETAILS
----------------
See INSTALL-RASPBERRY-PI.md for complete guide

================================================================================

