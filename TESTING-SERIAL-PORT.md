# Serial Port Testing Tools

This directory contains two scripts for testing and diagnosing serial port access for the WS2300 weather station.

## Scripts Overview

### 1. Python Script: `python-implementation/test_serial_port.py`
**Full-featured testing tool with advanced diagnostics**

- Comprehensive system information
- Serial port enumeration with details
- Device file permission checking
- Actual serial port open/read/write testing
- Configuration file validation
- Colored output with detailed troubleshooting guide

### 2. Shell Script: `test_serial_port.sh`
**Basic testing tool requiring only bash**

- System information display
- Available serial ports listing
- Device file checks
- Permission diagnostics
- Kernel messages inspection
- USB device detection
- Configuration file validation

## Usage

### Python Script (Recommended)

```bash
# Basic usage (auto-detects device from config)
python3 python-implementation/test_serial_port.py

# Test a specific device
python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0

# Test with custom baudrate
python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0 -b 9600

# Disable colored output (for logging to file)
python3 python-implementation/test_serial_port.py --no-color > test_results.txt

# Show help
python3 python-implementation/test_serial_port.py --help
```

### Shell Script

```bash
# Test default device (/dev/ttyS0)
./test_serial_port.sh

# Test specific device
./test_serial_port.sh /dev/ttyUSB0

# Save output to file
./test_serial_port.sh /dev/ttyUSB0 > test_results.txt 2>&1
```

## Requirements

### Python Script Requirements
- Python 3.6 or later
- `pyserial` module (install: `pip3 install pyserial`)
- Optional: `pyopen2300` package for config file support

**Raspberry Pi:** Fully supported on all models (Pi 2, 3, 4, Zero)

### Shell Script Requirements
- Bash shell (standard on most Linux systems)
- Optional tools for enhanced diagnostics:
  - `setserial` - Serial port configuration utility
  - `screen` - Terminal emulator
  - `minicom` - Serial communication program
  - `lsusb` - USB device lister

**Raspberry Pi:** Works out of the box

## Common Issues and Solutions

### 1. Permission Denied

**Problem:** Cannot access serial port due to permissions

**Solution:**
```bash
# Add your user to the dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
# Or use: newgrp dialout
```

**Verify:**
```bash
groups | grep dialout
```

### 2. Device Not Found

**Problem:** `/dev/ttyS0` or `/dev/ttyUSB0` doesn't exist

**Solution:**
```bash
# List all serial devices
ls -la /dev/tty* | grep -E "(USB|ACM|S[0-9])"

# Check kernel messages for serial devices
dmesg | grep -i "tty\|serial"

# For USB adapters
lsusb | grep -i "serial\|uart\|ftdi\|prolific"
```

**Common locations:**
- `/dev/ttyS0`, `/dev/ttyS1` - Built-in serial ports
- `/dev/ttyUSB0`, `/dev/ttyUSB1` - USB-to-serial adapters
- `/dev/ttyACM0`, `/dev/ttyACM1` - USB CDC devices
- `/dev/ttyAMA0`, `/dev/serial0` - Raspberry Pi GPIO serial (enable via raspi-config)
- `/dev/ttyS0` - Raspberry Pi mini UART (some models)

### 3. Device Busy

**Problem:** Port is already in use by another program

**Solution:**
```bash
# Find processes using the device
sudo fuser -v /dev/ttyUSB0

# Or using lsof
sudo lsof | grep /dev/ttyUSB0

# Kill the process if needed
sudo fuser -k /dev/ttyUSB0
```

### 4. USB Device Keeps Changing

**Problem:** Device name changes between `/dev/ttyUSB0` and `/dev/ttyUSB1`

**Solution:** Create a udev rule for persistent device naming

```bash
# Find device attributes
udevadm info -a -n /dev/ttyUSB0 | grep -E "ATTRS{serial}|ATTRS{idVendor}|ATTRS{idProduct}"

# Create udev rule in /etc/udev/rules.d/99-weather-station.rules
# Example:
# SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="weather-station"

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 5. Wrong Baudrate

**Problem:** Cannot communicate with device (default is 2400 for WS2300)

**Solution:**
```bash
# Test with different baudrates
python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0 -b 2400
python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0 -b 9600
```

**WS2300 uses:** 2400 baud, 8 data bits, no parity, 1 stop bit

## Raspberry Pi Specific Instructions

### Enabling Serial Port on Raspberry Pi

The GPIO serial port must be enabled before use:

```bash
# Configure serial port
sudo raspi-config

# Navigate to:
# Interfacing Options → Serial Port
# "Would you like a login shell accessible over serial?" → No
# "Would you like the serial port hardware to be enabled?" → Yes

# Reboot
sudo reboot
```

### Raspberry Pi Serial Devices

| Device | Description | Configuration |
|--------|-------------|---------------|
| `/dev/ttyAMA0` | Primary UART on GPIO | Recommended for WS2300 |
| `/dev/serial0` | Symlink to primary UART | Alternative |
| `/dev/ttyS0` | Mini UART (some models) | Less reliable |
| `/dev/ttyUSB0` | USB-to-serial adapter | Works well |

### Testing on Raspberry Pi

```bash
# Test with Python script
python3 python-implementation/test_serial_port.py -d /dev/ttyAMA0

# Or test USB adapter
python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0

# Check if serial port exists
ls -l /dev/ttyAMA0 /dev/serial0

# Disable serial console if needed
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
```

### Raspberry Pi Configuration Example

In `/etc/open2300.conf`:
```ini
SERIAL_DEVICE /dev/ttyAMA0
# or
SERIAL_DEVICE /dev/ttyUSB0
```

### Performance Notes

The test scripts work excellently on all Raspberry Pi models:

- **Raspberry Pi 4/3:** Full speed, all features
- **Raspberry Pi 2:** Tested and working (may take 3-5 minutes to install pyserial)
- **Raspberry Pi Zero:** Works fine, slightly slower

For complete Raspberry Pi setup, see:
- `python-implementation/INSTALL-RASPBERRY-PI.md`
- `python-implementation/RASPBERRY-PI-SUPPORT.md`

## Testing Serial Communication

### Using screen
```bash
# Connect to serial port
screen /dev/ttyUSB0 2400

# Exit: Ctrl-A then K (and confirm with y)
```

### Using minicom
```bash
# Configure and connect
minicom -D /dev/ttyUSB0 -b 2400

# Exit: Ctrl-A then X
```

### Using stty and cat (manual test)
```bash
# Configure port
stty -F /dev/ttyUSB0 2400 cs8 -cstopb -parenb

# Read from port (Ctrl-C to stop)
cat /dev/ttyUSB0

# In another terminal, write to port
echo "test" > /dev/ttyUSB0
```

## Configuration File

The scripts check for configuration files in these locations:
1. `./open2300.conf` (current directory)
2. `/usr/local/etc/open2300.conf`
3. `/etc/open2300.conf`

### Example configuration:
```ini
SERIAL_DEVICE /dev/ttyUSB0
LOG_LEVEL 1
TIMEZONE 1
```

## Interpreting Test Results

### Success Indicators
- ✓ Device exists and is accessible
- ✓ User has READ and WRITE permissions
- ✓ Serial port opens successfully
- ✓ Can read from/write to the port

### Warning Signs
- ⚠ No serial ports detected
- ⚠ READ access only (missing WRITE)
- ⚠ Device is busy (used by another program)

### Failures
- ✗ Device does not exist
- ✗ No READ or WRITE access
- ✗ Cannot open serial port
- ✗ pyserial module not installed

## Advanced Diagnostics

### Check kernel modules
```bash
# List loaded serial modules
lsmod | grep -E "serial|usb|ftdi|pl2303"

# Load USB serial module if needed
sudo modprobe usbserial
```

### Monitor serial port activity
```bash
# Watch for kernel messages when connecting USB device
sudo dmesg -w

# Then plug in the USB-to-serial adapter
```

### Check system logs
```bash
# Recent serial-related logs
journalctl -xe | grep -i "tty\|serial"

# Follow logs in real-time
journalctl -f | grep -i "tty\|serial"
```

## Exit Codes

Both scripts return:
- `0` - All tests passed, serial port is accessible
- `1` - Some tests failed, see output for details

Use in scripts:
```bash
if ./test_serial_port.sh /dev/ttyUSB0; then
    echo "Serial port is ready"
    ./open2300 /dev/ttyUSB0
else
    echo "Serial port is not accessible"
    exit 1
fi
```

## Getting Help

If you're still having issues after running these tests:

1. Run the Python test script and save the full output:
   ```bash
   python3 python-implementation/test_serial_port.py --no-color > diagnostic.txt 2>&1
   ```

2. Check the open2300 documentation at `/usr/share/doc/open2300/`

3. Verify your hardware:
   - Check cable connections
   - Try a different USB port
   - Test with a different USB-to-serial adapter
   - Verify the weather station is powered on

4. Look for similar issues in the project's issue tracker or forum

## Developer Information

These scripts are part of the open2300 project for interfacing with LaCrosse WS2300 weather stations.

- Project: open2300
- Serial Protocol: 2400 baud, 8N1
- Device Type: WS2300 weather station
- Connection: RS-232 serial or USB-to-serial adapter

For more information, see the main README and documentation files in the project root.

