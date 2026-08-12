#!/bin/bash
#
# Simple shell script for testing serial port access
# Provides verbose debug output for troubleshooting
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default serial device
DEFAULT_DEVICE="/dev/ttyS0"

# Parse arguments
DEVICE="${1:-$DEFAULT_DEVICE}"

echo -e "${BOLD}${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  WS2300 Weather Station - Serial Port Testing Tool (Shell)        ║"
echo "║  Basic serial port access diagnostics                             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${BOLD}Usage:${NC}"
echo "  $0 [device_path]"
echo "  Default device: $DEFAULT_DEVICE"
echo ""

# System Information
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}SYSTEM INFORMATION${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

echo -e "${CYAN}ℹ Current user: $(whoami) (UID: $(id -u))${NC}"
echo -e "${CYAN}ℹ Groups: $(groups)${NC}"
echo -e "${CYAN}ℹ System: $(uname -s) $(uname -r)${NC}"
echo -e "${CYAN}ℹ Machine: $(uname -m)${NC}"

# Check for common serial port tools
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}AVAILABLE SERIAL PORT TOOLS${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

if command -v setserial &> /dev/null; then
    echo -e "${GREEN}✓ setserial is installed${NC}"
else
    echo -e "${YELLOW}⚠ setserial not found (optional)${NC}"
fi

if command -v screen &> /dev/null; then
    echo -e "${GREEN}✓ screen is installed${NC}"
else
    echo -e "${YELLOW}⚠ screen not found (install: apt-get install screen)${NC}"
fi

if command -v minicom &> /dev/null; then
    echo -e "${GREEN}✓ minicom is installed${NC}"
else
    echo -e "${YELLOW}⚠ minicom not found (install: apt-get install minicom)${NC}"
fi

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ python3 is installed (version: $(python3 --version))${NC}"
    if python3 -c "import serial" 2>/dev/null; then
        echo -e "${GREEN}✓ pyserial module is installed${NC}"
    else
        echo -e "${YELLOW}⚠ pyserial not installed (install: pip3 install pyserial)${NC}"
    fi
else
    echo -e "${RED}✗ python3 not found${NC}"
fi

# List available serial ports
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}AVAILABLE SERIAL PORTS${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

echo ""
echo -e "${CYAN}ℹ Serial ports (ttyS*):{NC}"
ls -la /dev/ttyS* 2>/dev/null || echo -e "${YELLOW}  No ttyS* devices found${NC}"

echo ""
echo -e "${CYAN}ℹ USB serial adapters (ttyUSB*):{NC}"
ls -la /dev/ttyUSB* 2>/dev/null || echo -e "${YELLOW}  No ttyUSB* devices found${NC}"

echo ""
echo -e "${CYAN}ℹ USB CDC devices (ttyACM*):{NC}"
ls -la /dev/ttyACM* 2>/dev/null || echo -e "${YELLOW}  No ttyACM* devices found${NC}"

# Check specific device
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}DEVICE CHECK: $DEVICE${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

if [ -e "$DEVICE" ]; then
    echo -e "${GREEN}✓ Device exists: $DEVICE${NC}"
    
    # Check if it's a character device
    if [ -c "$DEVICE" ]; then
        echo -e "${GREEN}✓ Device is a character device (correct type)${NC}"
    else
        echo -e "${RED}✗ Device is NOT a character device${NC}"
    fi
    
    # Show permissions
    echo -e "${CYAN}ℹ Permissions:${NC}"
    ls -l "$DEVICE"
    
    # Check read/write access
    if [ -r "$DEVICE" ] && [ -w "$DEVICE" ]; then
        echo -e "${GREEN}✓ Current user has READ and WRITE access${NC}"
    elif [ -r "$DEVICE" ]; then
        echo -e "${YELLOW}⚠ Current user has READ access only (WRITE access missing)${NC}"
    elif [ -w "$DEVICE" ]; then
        echo -e "${YELLOW}⚠ Current user has WRITE access only (READ access missing)${NC}"
    else
        echo -e "${RED}✗ Current user has NO READ or WRITE access${NC}"
        GROUP=$(ls -l "$DEVICE" | awk '{print $4}')
        echo -e "${CYAN}ℹ Device group: $GROUP${NC}"
        echo -e "${CYAN}ℹ To fix, run: sudo usermod -a -G $GROUP $(whoami)${NC}"
        echo -e "${CYAN}ℹ Then log out and log back in${NC}"
    fi
    
    # Try to get device info with setserial
    if command -v setserial &> /dev/null; then
        echo ""
        echo -e "${CYAN}ℹ Device info from setserial:${NC}"
        setserial -a "$DEVICE" 2>&1 || echo -e "${YELLOW}  Could not query device${NC}"
    fi
    
else
    echo -e "${RED}✗ Device does NOT exist: $DEVICE${NC}"
    echo -e "${CYAN}ℹ Common serial port locations:${NC}"
    echo -e "${CYAN}  - /dev/ttyS0, /dev/ttyS1 (built-in serial ports)${NC}"
    echo -e "${CYAN}  - /dev/ttyUSB0, /dev/ttyUSB1 (USB-to-serial adapters)${NC}"
    echo -e "${CYAN}  - /dev/ttyACM0, /dev/ttyACM1 (USB CDC devices)${NC}"
fi

# Check for kernel messages about serial ports
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}KERNEL MESSAGES (last 20 lines mentioning tty/serial)${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

if [ -r /var/log/dmesg ]; then
    grep -i "tty\|serial\|usb.*serial" /var/log/dmesg 2>/dev/null | tail -20 || echo -e "${YELLOW}No messages found${NC}"
else
    dmesg 2>/dev/null | grep -i "tty\|serial\|usb.*serial" | tail -20 || echo -e "${YELLOW}Cannot read kernel messages (try with sudo)${NC}"
fi

# Check USB devices
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}USB DEVICES${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

if command -v lsusb &> /dev/null; then
    lsusb
else
    echo -e "${YELLOW}⚠ lsusb not found${NC}"
fi

# Check process using the device
if [ -e "$DEVICE" ]; then
    echo ""
    echo -e "${BOLD}${CYAN}==================================================================${NC}"
    echo -e "${BOLD}${CYAN}PROCESSES USING DEVICE${NC}"
    echo -e "${BOLD}${CYAN}==================================================================${NC}"
    
    if command -v fuser &> /dev/null; then
        PROCS=$(fuser "$DEVICE" 2>/dev/null)
        if [ -n "$PROCS" ]; then
            echo -e "${YELLOW}⚠ Device is being used by processes: $PROCS${NC}"
            ps -p $PROCS -o pid,user,command 2>/dev/null
        else
            echo -e "${GREEN}✓ No processes are using the device${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ fuser command not available${NC}"
    fi
fi

# Configuration file check
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}CONFIGURATION FILE CHECK${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

CONFIG_FOUND=0
for CONFIG_PATH in "./open2300.conf" "/usr/local/etc/open2300.conf" "/etc/open2300.conf"; do
    if [ -f "$CONFIG_PATH" ]; then
        echo -e "${GREEN}✓ Found config file: $CONFIG_PATH${NC}"
        CONFIG_FOUND=1
        echo -e "${CYAN}ℹ Serial device in config:${NC}"
        grep "^SERIAL_DEVICE" "$CONFIG_PATH" || echo -e "${YELLOW}  SERIAL_DEVICE not set${NC}"
        break
    fi
done

if [ $CONFIG_FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠ No config file found in default locations${NC}"
    echo -e "${CYAN}ℹ Searched:${NC}"
    echo -e "${CYAN}  - ./open2300.conf${NC}"
    echo -e "${CYAN}  - /usr/local/etc/open2300.conf${NC}"
    echo -e "${CYAN}  - /etc/open2300.conf${NC}"
fi

# Troubleshooting guide
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}TROUBLESHOOTING GUIDE${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"

echo ""
echo -e "${BOLD}Common Issues and Solutions:${NC}"
echo ""

echo -e "${YELLOW}1. Permission Denied Error${NC}"
echo "   Solution: Add your user to the dialout group"
echo "   Command: sudo usermod -a -G dialout \$USER"
echo "   Note: Log out and log back in for changes to take effect"
echo ""

echo -e "${YELLOW}2. Device Not Found${NC}"
echo "   Solution: Find the correct serial port"
echo "   Command: ls -la /dev/tty* | grep -E '(USB|ACM|S[0-9])'"
echo "   Check: /dev/ttyUSB0 (USB adapter) or /dev/ttyS0 (built-in port)"
echo ""

echo -e "${YELLOW}3. Device Busy${NC}"
echo "   Solution: Find and close the program using the port"
echo "   Command: sudo fuser -v $DEVICE"
echo "   Or: sudo lsof | grep $DEVICE"
echo ""

echo -e "${YELLOW}4. Testing with Serial Terminal${NC}"
echo "   Test with screen:  screen $DEVICE 2400"
echo "   Test with minicom: minicom -D $DEVICE -b 2400"
echo "   (Press Ctrl-A then K to exit screen)"
echo ""

echo -e "${YELLOW}5. For more detailed testing${NC}"
echo "   Run the Python version with more features:"
echo "   python3 python-implementation/test_serial_port.py -d $DEVICE"
echo ""

# Summary
echo ""
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo -e "${BOLD}${CYAN}TEST SUMMARY${NC}"
echo -e "${BOLD}${CYAN}==================================================================${NC}"
echo ""

if [ -e "$DEVICE" ] && [ -r "$DEVICE" ] && [ -w "$DEVICE" ]; then
    echo -e "${GREEN}✓ All basic tests PASSED - device exists and is accessible${NC}"
    echo -e "${CYAN}ℹ You should be able to run the open2300 tools${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests FAILED - see above for details${NC}"
    echo -e "${CYAN}ℹ Follow the troubleshooting guide to fix issues${NC}"
    exit 1
fi

