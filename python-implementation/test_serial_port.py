#!/usr/bin/env python3
"""
Serial Port Testing Script for WS2300 Weather Station
Provides verbose debug output for troubleshooting serial port access
"""

import sys
import os
import stat
import grp
import pwd
import argparse
from pathlib import Path

# Try to import serial, but give helpful error if not available
try:
    import serial
    from serial.tools import list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("WARNING: pyserial not installed. Install with: pip install pyserial")

# Try to import pyopen2300 modules
try:
    from pyopen2300.config import Config
    from pyopen2300.constants import BAUDRATE, DEFAULT_SERIAL_DEVICE
    PYOPEN2300_AVAILABLE = True
except ImportError:
    PYOPEN2300_AVAILABLE = False
    BAUDRATE = 2400
    DEFAULT_SERIAL_DEVICE = "/dev/ttyS0"
    print("WARNING: pyopen2300 not installed. Using default values.")


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def check_system_info():
    """Display system information"""
    print_header("SYSTEM INFORMATION")
    
    print_info(f"Python version: {sys.version}")
    print_info(f"Operating system: {os.name}")
    print_info(f"Platform: {sys.platform}")
    
    try:
        import platform
        print_info(f"System: {platform.system()} {platform.release()}")
        print_info(f"Machine: {platform.machine()}")
    except Exception as e:
        print_warning(f"Could not get platform info: {e}")
    
    print_info(f"Current user: {os.getlogin()} (UID: {os.getuid()})")
    
    # List user groups
    try:
        import subprocess
        groups = subprocess.check_output(['groups']).decode().strip()
        print_info(f"User groups: {groups}")
    except Exception as e:
        print_warning(f"Could not get user groups: {e}")


def check_pyserial():
    """Check if pyserial is installed and working"""
    print_header("PYSERIAL MODULE CHECK")
    
    if not SERIAL_AVAILABLE:
        print_error("pyserial module NOT installed")
        print_info("Install with: pip install pyserial")
        return False
    
    print_success("pyserial module is installed")
    print_info(f"pyserial version: {serial.__version__}")
    return True


def list_available_ports():
    """List all available serial ports"""
    print_header("AVAILABLE SERIAL PORTS")
    
    if not SERIAL_AVAILABLE:
        print_error("Cannot list ports - pyserial not installed")
        return
    
    ports = list(list_ports.comports())
    
    if not ports:
        print_warning("No serial ports detected by pyserial")
    else:
        print_success(f"Found {len(ports)} serial port(s):")
        for port in ports:
            print(f"\n  Port: {Colors.BOLD}{port.device}{Colors.ENDC}")
            print(f"    Description: {port.description}")
            print(f"    Hardware ID: {port.hwid}")
            if port.manufacturer:
                print(f"    Manufacturer: {port.manufacturer}")
            if port.product:
                print(f"    Product: {port.product}")
            if port.serial_number:
                print(f"    Serial Number: {port.serial_number}")
    
    # Check for Raspberry Pi GPIO serial ports (not always detected by pyserial)
    rpi_serial_ports = ['/dev/ttyAMA0', '/dev/serial0', '/dev/ttyS0']
    print_info("\nChecking for Raspberry Pi GPIO serial ports:")
    for rpi_port in rpi_serial_ports:
        if Path(rpi_port).exists():
            print_success(f"  Found: {rpi_port}")
        else:
            print(f"  Not found: {rpi_port}")


def check_device_file(device_path):
    """Check if device file exists and its properties"""
    print_header(f"DEVICE FILE CHECK: {device_path}")
    
    path = Path(device_path)
    
    # Check if device exists
    if not path.exists():
        print_error(f"Device does NOT exist: {device_path}")
        print_info("Common serial port locations on Linux:")
        print_info("  - /dev/ttyS0, /dev/ttyS1, ... (built-in serial ports)")
        print_info("  - /dev/ttyUSB0, /dev/ttyUSB1, ... (USB-to-serial adapters)")
        print_info("  - /dev/ttyACM0, /dev/ttyACM1, ... (USB CDC devices)")
        print_info("Raspberry Pi specific:")
        print_info("  - /dev/ttyAMA0, /dev/serial0 (GPIO serial port)")
        print_info("  - /dev/ttyS0 (mini UART on some models)")
        print_info("  Note: Enable via 'sudo raspi-config' → Interfacing Options → Serial")
        return False
    
    print_success(f"Device exists: {device_path}")
    
    # Get file stats
    try:
        st = path.stat()
        
        # Check if it's a character device
        if stat.S_ISCHR(st.st_mode):
            print_success("Device is a character device (correct type)")
        else:
            print_error("Device is NOT a character device")
        
        # Get permissions
        mode = st.st_mode
        perms = stat.filemode(mode)
        print_info(f"Permissions: {perms} (octal: {oct(stat.S_IMODE(mode))})")
        
        # Get owner and group
        try:
            owner = pwd.getpwuid(st.st_uid).pw_name
            print_info(f"Owner: {owner} (UID: {st.st_uid})")
        except KeyError:
            print_info(f"Owner UID: {st.st_uid}")
        
        try:
            group = grp.getgrgid(st.st_gid).gr_name
            print_info(f"Group: {group} (GID: {st.st_gid})")
        except KeyError:
            print_info(f"Group GID: {st.st_gid}")
        
        # Check read/write permissions for current user
        can_read = os.access(device_path, os.R_OK)
        can_write = os.access(device_path, os.W_OK)
        
        if can_read and can_write:
            print_success("Current user has READ and WRITE access")
        elif can_read:
            print_warning("Current user has READ access only (WRITE access missing)")
        elif can_write:
            print_warning("Current user has WRITE access only (READ access missing)")
        else:
            print_error("Current user has NO READ or WRITE access")
            print_info(f"You need to be added to the '{group}' group or run as root")
            print_info(f"Try: sudo usermod -a -G {group} {os.getlogin()}")
            print_info("(You'll need to log out and back in for group changes to take effect)")
        
        return can_read and can_write
        
    except Exception as e:
        print_error(f"Error checking device stats: {e}")
        return False


def check_config_file():
    """Check for open2300 configuration file"""
    print_header("CONFIGURATION FILE CHECK")
    
    if not PYOPEN2300_AVAILABLE:
        print_warning("pyopen2300 not available, skipping config check")
        return None
    
    config_paths = [
        './open2300.conf',
        '/usr/local/etc/open2300.conf',
        '/etc/open2300.conf'
    ]
    
    found_config = None
    for config_path in config_paths:
        if os.path.exists(config_path):
            print_success(f"Found config file: {config_path}")
            found_config = config_path
            break
    
    if not found_config:
        print_warning("No config file found in default locations")
        print_info("Searched paths:")
        for path in config_paths:
            print_info(f"  - {path}")
        return None
    
    # Try to load config
    try:
        config = Config(found_config)
        print_success("Configuration loaded successfully")
        print_info(f"Serial device from config: {config.serial_device_name}")
        print_info(f"Log level: {config.log_level}")
        return config
    except Exception as e:
        print_error(f"Error loading config: {e}")
        return None


def test_serial_open(device_path, baudrate=BAUDRATE):
    """Attempt to open the serial port"""
    print_header(f"SERIAL PORT OPEN TEST: {device_path}")
    
    if not SERIAL_AVAILABLE:
        print_error("Cannot test - pyserial not installed")
        return None
    
    print_info(f"Attempting to open: {device_path}")
    print_info(f"Baudrate: {baudrate}")
    print_info("Settings: 8 data bits, no parity, 1 stop bit")
    
    try:
        ser = serial.Serial(
            port=device_path,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        print_success("Serial port opened successfully!")
        
        # Display port properties
        print_info(f"Port name: {ser.name}")
        print_info(f"Baudrate: {ser.baudrate}")
        print_info(f"Timeout: {ser.timeout}")
        print_info(f"Is open: {ser.is_open}")
        
        # Get control signals if possible
        try:
            if hasattr(ser, 'cts'):
                print_info(f"CTS (Clear To Send): {ser.cts}")
            if hasattr(ser, 'dsr'):
                print_info(f"DSR (Data Set Ready): {ser.dsr}")
            if hasattr(ser, 'ri'):
                print_info(f"RI (Ring Indicator): {ser.ri}")
            if hasattr(ser, 'cd'):
                print_info(f"CD (Carrier Detect): {ser.cd}")
        except Exception:
            pass
        
        # Check buffer status
        try:
            in_waiting = ser.in_waiting
            print_info(f"Bytes in input buffer: {in_waiting}")
            out_waiting = ser.out_waiting
            print_info(f"Bytes in output buffer: {out_waiting}")
        except Exception:
            pass
        
        return ser
        
    except serial.SerialException as e:
        print_error(f"Failed to open serial port: {e}")
        
        # Provide troubleshooting hints
        if "Permission denied" in str(e):
            print_warning("Permission denied - you need access to the device")
            print_info("Solutions:")
            print_info("  1. Add your user to the dialout group: sudo usermod -a -G dialout $USER")
            print_info("  2. Run as root (not recommended): sudo python3 test_serial_port.py")
            print_info("  3. Change device permissions (temporary): sudo chmod 666 " + device_path)
        elif "No such file or directory" in str(e):
            print_warning("Device not found - check if it's the correct path")
            print_info("Try: ls -la /dev/tty* | grep -E '(USB|ACM|S[0-9])'")
        elif "Device or resource busy" in str(e):
            print_warning("Device is busy - another program may be using it")
            print_info("Try: sudo lsof | grep " + device_path)
        
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None


def test_serial_readwrite(ser):
    """Test basic read/write operations"""
    print_header("SERIAL PORT READ/WRITE TEST")
    
    if ser is None:
        print_error("Serial port not open - skipping read/write test")
        return
    
    try:
        # Flush buffers
        print_info("Flushing input and output buffers...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print_success("Buffers flushed")
        
        # Check for any data in input buffer
        print_info("Checking for incoming data (1 second timeout)...")
        data = ser.read(100)
        if data:
            print_success(f"Received {len(data)} bytes: {data.hex()}")
            print_info(f"ASCII representation: {data}")
        else:
            print_warning("No data received (this is normal if weather station is idle)")
        
        # Note: We don't actually write to the device in this test
        # because we don't want to send garbage to the weather station
        print_info("Skipping write test to avoid sending invalid data to weather station")
        
    except Exception as e:
        print_error(f"Error during read/write test: {e}")


def print_troubleshooting_guide():
    """Print troubleshooting guide"""
    print_header("TROUBLESHOOTING GUIDE")
    
    print(f"\n{Colors.BOLD}Common Issues and Solutions:{Colors.ENDC}\n")
    
    print(f"{Colors.YELLOW}1. Permission Denied Error{Colors.ENDC}")
    print("   Solution: Add your user to the dialout group")
    print("   Command: sudo usermod -a -G dialout $USER")
    print("   Note: Log out and log back in for changes to take effect\n")
    
    print(f"{Colors.YELLOW}2. Device Not Found{Colors.ENDC}")
    print("   Solution: Find the correct serial port")
    print("   Command: ls -la /dev/tty* | grep -E '(USB|ACM|S[0-9]|AMA)'")
    print("   Check: /dev/ttyUSB0 (USB adapter) or /dev/ttyS0 (built-in port)\n")
    
    print(f"{Colors.YELLOW}3. Device Busy{Colors.ENDC}")
    print("   Solution: Find and close the program using the port")
    print("   Command: sudo lsof | grep /dev/ttyUSB0")
    print("   Or: sudo fuser /dev/ttyUSB0\n")
    
    print(f"{Colors.YELLOW}4. Wrong Device{Colors.ENDC}")
    print("   Solution: Update open2300.conf with correct device")
    print("   Check config at: ./open2300.conf or /etc/open2300.conf")
    print("   Edit line: SERIAL_DEVICE /dev/ttyUSB0\n")
    
    print(f"{Colors.YELLOW}5. USB Device Keeps Changing (ttyUSB0 vs ttyUSB1){Colors.ENDC}")
    print("   Solution: Use udev rules to create a persistent device name")
    print("   See: https://wiki.archlinux.org/title/Udev\n")
    
    print(f"{Colors.YELLOW}6. Raspberry Pi - Serial Port Not Available{Colors.ENDC}")
    print("   Solution: Enable serial hardware in raspi-config")
    print("   Command: sudo raspi-config")
    print("   Navigate: Interfacing Options → Serial")
    print("   Set: Login shell over serial = No, Serial hardware = Yes")
    print("   Then: sudo reboot")
    print("   Device: /dev/ttyAMA0 or /dev/serial0\n")
    
    print(f"\n{Colors.BOLD}Testing Commands:{Colors.ENDC}\n")
    print("  List USB devices:        lsusb")
    print("  List serial ports:       dmesg | grep tty")
    print("  Check port permissions:  ls -l /dev/ttyUSB0")
    print("  Test with screen:        screen /dev/ttyUSB0 2400")
    print("  Test with minicom:       minicom -D /dev/ttyUSB0 -b 2400")


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(
        description='Test serial port access for WS2300 weather station',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-d', '--device',
        help=f'Serial device to test (default: from config or {DEFAULT_SERIAL_DEVICE})',
        default=None
    )
    parser.add_argument(
        '-b', '--baudrate',
        help=f'Baudrate (default: {BAUDRATE})',
        type=int,
        default=BAUDRATE
    )
    parser.add_argument(
        '--no-color',
        help='Disable colored output',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  WS2300 Weather Station - Serial Port Testing Tool                ║")
    print("║  Verbose debug mode for troubleshooting serial port access        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Run tests
    check_system_info()
    check_pyserial()
    list_available_ports()
    
    # Load config and determine device
    config = check_config_file()
    
    if args.device:
        device = args.device
        print_info(f"Using device from command line: {device}")
    elif config:
        device = config.serial_device_name
        print_info(f"Using device from config file: {device}")
    else:
        device = DEFAULT_SERIAL_DEVICE
        print_info(f"Using default device: {device}")
    
    # Check device file
    has_access = check_device_file(device)
    
    # Try to open serial port
    ser = test_serial_open(device, args.baudrate)
    
    # Test read/write if successful
    if ser:
        test_serial_readwrite(ser)
        
        # Close port
        print_info("Closing serial port...")
        ser.close()
        print_success("Serial port closed")
    
    # Print troubleshooting guide
    print_troubleshooting_guide()
    
    # Summary
    print_header("TEST SUMMARY")
    
    if SERIAL_AVAILABLE and has_access and ser:
        print_success("All tests PASSED - serial port is accessible")
        print_info("You should be able to run the open2300 tools")
        return 0
    else:
        print_error("Some tests FAILED - see above for details")
        print_info("Follow the troubleshooting guide to fix issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())

