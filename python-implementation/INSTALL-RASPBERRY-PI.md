# Installing PyOpen2300 on Raspberry Pi

This guide covers installation on Raspberry Pi, including older models like RPi2 with Raspbian/Raspberry Pi OS.

## Tested Platforms

- ✅ Raspberry Pi 2 Model B (Raspbian Stretch/Buster/Bullseye)
- ✅ Raspberry Pi 3 (all models)
- ✅ Raspberry Pi 4
- ✅ Raspberry Pi Zero W/WH (may be slower due to limited resources)

## Prerequisites

### System Requirements

- Raspberry Pi OS (formerly Raspbian) - any recent version
- Python 3.6 or higher (pre-installed on recent Raspberry Pi OS)
- Serial port access (usually `/dev/ttyAMA0` or `/dev/ttyUSB0`)

### Check Python Version

```bash
python3 --version
# Should be 3.6 or higher
```

If you have an older version, update your system:

```bash
sudo apt-get update
sudo apt-get upgrade
```

## Installation

### Step 1: System Dependencies

Install system packages needed for serial communication and optional PostgreSQL support:

```bash
# Update package list
sudo apt-get update

# Install basic dependencies
sudo apt-get install -y python3-pip python3-dev

# Optional: For PostgreSQL support
sudo apt-get install -y libpq-dev

# Optional: For building Python packages from source
sudo apt-get install -y build-essential
```

### Step 2: Install Python Package

```bash
cd /home/zelenya/src/open2300

# Use the RPi-specific requirements file
pip3 install -r requirements-rpi.txt

# Install the package
pip3 install -e .
```

**Note:** On older RPi models (RPi2, RPi Zero), installation may take a few minutes as some packages build from source.

### Step 3: Serial Port Configuration

On Raspberry Pi, the serial port may need special configuration:

#### Option A: Using GPIO Serial (Recommended for weather stations)

1. Enable serial port:
```bash
sudo raspi-config
# Navigate to: Interfacing Options → Serial
# "Would you like a login shell accessible over serial?" → No
# "Would you like the serial port hardware to be enabled?" → Yes
```

2. The serial port will be `/dev/ttyAMA0` or `/dev/serial0`

#### Option B: Using USB-to-Serial Adapter

If using a USB-to-serial adapter:
```bash
# Find the device
ls -l /dev/ttyUSB*
# Usually /dev/ttyUSB0
```

### Step 4: Serial Port Permissions

```bash
# Add your user to the dialout group
sudo usermod -a -G dialout $USER

# Or set permissions directly (not recommended for production)
sudo chmod 666 /dev/ttyAMA0  # or /dev/ttyUSB0
```

**Important:** Logout and login again for group changes to take effect.

### Step 5: Configure PyOpen2300

```bash
cd /home/zelenya/src/open2300

# Copy configuration file
cp open2300-dist.conf open2300.conf

# Edit configuration
nano open2300.conf
```

Set the serial device for Raspberry Pi:
```ini
SERIAL_DEVICE /dev/ttyAMA0
# or
SERIAL_DEVICE /dev/ttyUSB0
```

### Step 6: Test Installation

```bash
# Test configuration
dumpconfig2300

# Test with weather station connected
fetch2300
```

## PostgreSQL Support (Optional)

For database logging on Raspberry Pi:

### Option 1: Install PostgreSQL locally

```bash
# Install PostgreSQL server and client
sudo apt-get install -y postgresql postgresql-contrib

# Install Python PostgreSQL adapter
sudo apt-get install -y python3-psycopg2
# OR build from source:
pip3 install psycopg2>=2.8.0
```

### Option 2: Connect to remote PostgreSQL

If your PostgreSQL database is on another machine, you only need the client:

```bash
# Install development libraries
sudo apt-get install -y libpq-dev

# Install Python adapter
pip3 install psycopg2>=2.8.0
```

## SQLite Support (Built-in)

SQLite works out of the box on Raspberry Pi - no additional installation needed:

```bash
sqlitelog2300 weather.db
```

## Performance Notes

### Raspberry Pi 2 and Older Models

- **Slower installation**: Building packages from source takes longer
- **Memory usage**: Monitor memory if running many services
- **CPU usage**: Data logging is lightweight and runs fine

### Recommended Configuration for RPi2

```bash
# Log data every 5 minutes (adjust as needed)
# Add to crontab:
crontab -e

# Add these lines:
*/5 * * * * /usr/local/bin/log2300 /var/log/weather.log
*/15 * * * * /usr/local/bin/wu2300

# For database logging (if using SQLite)
*/5 * * * * /usr/local/bin/sqlitelog2300 /home/pi/weather.db
```

## Troubleshooting

### Serial Port Issues

**Problem:** Cannot open serial device

```bash
# Check if device exists
ls -l /dev/ttyAMA0
ls -l /dev/ttyUSB0

# Check permissions
groups  # Should include 'dialout'

# Test serial port
python3 -c "import serial; s=serial.Serial('/dev/ttyAMA0', 2400); print('OK')"
```

**Problem:** Serial port in use

```bash
# Check what's using the port
sudo lsof /dev/ttyAMA0

# Disable serial console if needed
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
```

### Memory Issues on RPi2

If you encounter memory issues:

```bash
# Check memory usage
free -h

# Reduce memory usage by stopping unnecessary services
sudo systemctl stop bluetooth
sudo systemctl stop avahi-daemon
```

### Installation Errors

**Problem:** Building psycopg2 fails

```bash
# Install all required development packages
sudo apt-get install -y python3-dev libpq-dev build-essential

# Retry installation
pip3 install psycopg2>=2.8.0
```

**Problem:** pip3 command not found

```bash
# Install pip for Python 3
sudo apt-get install -y python3-pip
```

## Performance Optimization

### For Continuous Logging

If running continuously on RPi, consider:

1. **Use SQLite instead of PostgreSQL** for local logging (lower overhead)
2. **Increase logging interval** to reduce CPU usage
3. **Disable debug output** in configuration
4. **Use logrotate** to manage log file sizes

Example logrotate configuration (`/etc/logrotate.d/weather`):
```
/var/log/weather.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 pi pi
}
```

## Starting on Boot

To start weather logging on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/weather-log.service
```

Add:
```ini
[Unit]
Description=Weather Station Logger
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /usr/local/bin/sqlitelog2300 /home/pi/weather.db
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable weather-log.service
sudo systemctl start weather-log.service
```

## Differences from x86 Installation

| Aspect | x86/x64 | Raspberry Pi |
|--------|---------|--------------|
| Requirements file | `requirements.txt` | `requirements-rpi.txt` |
| psycopg2 | Binary package | Build from source |
| Serial device | `/dev/ttyS0` | `/dev/ttyAMA0` or `/dev/ttyUSB0` |
| Installation time | Fast | Slower on older models |
| PostgreSQL | Optional | Optional (SQLite recommended) |

## Hardware Setup

### Connecting WS2300 to Raspberry Pi

**Option 1: Direct GPIO connection** (requires level shifter for 5V signals)
```
WS2300 Serial → Level Shifter → GPIO pins (TXD/RXD)
```

**Option 2: USB-to-Serial adapter** (recommended, simpler)
```
WS2300 Serial → USB-to-Serial → Raspberry Pi USB port
```

## Example: Complete Setup on Fresh RPi2

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-dev git

# Clone/copy project
cd ~
# (copy your project files here)

# Install
cd open2300
pip3 install -r requirements-rpi.txt
pip3 install -e .

# Configure
cp open2300-dist.conf open2300.conf
nano open2300.conf  # Set SERIAL_DEVICE /dev/ttyAMA0

# Setup permissions
sudo usermod -a -G dialout $USER

# Logout and login again
logout

# Test
dumpconfig2300
fetch2300

# Setup cron job
crontab -e
# Add: */5 * * * * /usr/local/bin/sqlitelog2300 /home/pi/weather.db
```

## Summary

PyOpen2300 works well on Raspberry Pi, including older models like RPi2. Key points:

- ✅ Use `requirements-rpi.txt` for installation
- ✅ Serial port is usually `/dev/ttyAMA0` or `/dev/ttyUSB0`
- ✅ SQLite recommended over PostgreSQL for lighter load
- ✅ Add user to `dialout` group for serial access
- ✅ Installation may take longer on older RPi due to building from source

For issues specific to Raspberry Pi, check the Troubleshooting section above.

