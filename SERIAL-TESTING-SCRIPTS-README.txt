╔═══════════════════════════════════════════════════════════════════════╗
║                 SERIAL PORT TESTING SCRIPTS                           ║
║                     Installation Summary                              ║
╚═══════════════════════════════════════════════════════════════════════╝

OVERVIEW
--------
Three new files have been added to help you test and diagnose serial port 
access for the WS2300 weather station:

1. python-implementation/test_serial_port.py  - Full-featured Python script
2. test_serial_port.sh                        - Basic shell script
3. TESTING-SERIAL-PORT.md                     - Comprehensive documentation
4. SERIAL-PORT-QUICK-REFERENCE.txt           - Quick command reference


QUICK START
-----------

Run the Python test script (recommended):

    python3 python-implementation/test_serial_port.py

This will:
    ✓ Check system information
    ✓ Verify pyserial is installed
    ✓ List all available serial ports
    ✓ Check device file permissions
    ✓ Attempt to open the serial port
    ✓ Test basic read/write operations
    ✓ Validate configuration file
    ✓ Provide troubleshooting guidance


If you don't have Python/pyserial, run the shell script:

    ./test_serial_port.sh

This provides basic diagnostics using standard shell commands.


To test a specific device:

    python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0
    ./test_serial_port.sh /dev/ttyUSB0


SCRIPT FEATURES
---------------

Python Script (test_serial_port.py):
    • Colored output for easy reading
    • Comprehensive port enumeration with hardware details
    • Actual serial port open/close testing
    • Read/write buffer testing
    • Control signal status (CTS, DSR, etc.)
    • Configuration file loading and validation
    • Detailed error messages with solutions
    • Command-line options for device and baudrate
    • No-color mode for logging to files

Shell Script (test_serial_port.sh):
    • No dependencies except bash
    • System information display
    • Permission checking
    • Kernel message inspection
    • USB device detection
    • Process detection (who's using the port)
    • Works even without Python installed


COMMON USE CASES
----------------

1. First time setup - check if you can access the serial port:
   python3 python-implementation/test_serial_port.py

2. Permission issues - see detailed permission diagnostics:
   python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0

3. Finding the right device - list all available ports:
   python3 python-implementation/test_serial_port.py
   (Look at "AVAILABLE SERIAL PORTS" section)

4. Save diagnostics to file for troubleshooting:
   python3 python-implementation/test_serial_port.py --no-color > diag.txt 2>&1

5. Quick check without Python:
   ./test_serial_port.sh

6. Test USB adapter after connecting:
   python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0


VERBOSE DEBUG OUTPUT
--------------------

Both scripts provide detailed verbose output showing:

• System information (OS, user, groups)
• Serial port availability and hardware details
• Device file permissions and ownership
• Read/write access status
• Port open/close operations
• Buffer status
• Control signal states
• Configuration file validation
• Kernel messages about serial devices
• USB device information
• Process using the port
• Common solutions to problems


TYPICAL OUTPUT SECTIONS
-----------------------

1. SYSTEM INFORMATION
   - Python version, OS, current user, groups

2. PYSERIAL MODULE CHECK
   - Whether pyserial is installed

3. AVAILABLE SERIAL PORTS
   - All detected serial ports with hardware details

4. DEVICE FILE CHECK
   - File existence, permissions, ownership, access rights

5. CONFIGURATION FILE CHECK
   - Whether config file exists and loads correctly

6. SERIAL PORT OPEN TEST
   - Attempt to open port, show port properties

7. SERIAL PORT READ/WRITE TEST
   - Test actual communication with the device

8. TROUBLESHOOTING GUIDE
   - Solutions for common problems


EXIT CODES
----------

0 = SUCCESS - Serial port is accessible, you can run open2300 tools
1 = FAILURE - Some tests failed, follow troubleshooting guide


DOCUMENTATION
-------------

For detailed information, see:
    TESTING-SERIAL-PORT.md       - Full documentation (7KB)
    SERIAL-PORT-QUICK-REFERENCE.txt - Quick command reference (8KB)

These include:
    • Step-by-step troubleshooting
    • Permission fix procedures
    • USB device setup
    • Creating persistent device names with udev
    • Manual serial testing with screen/minicom
    • Advanced diagnostics
    • Developer information


INSTALLATION REQUIREMENTS
-------------------------

Python Script:
    Required:
        • Python 3.6+
        • pyserial module: pip3 install pyserial

    Optional (for full features):
        • pyopen2300 package (auto-detected)
        • Configuration file in standard location

Shell Script:
    Required:
        • Bash (standard on Linux)

    Optional (enhanced diagnostics):
        • setserial, screen, minicom
        • lsusb, fuser, dmesg access


EXAMPLES
--------

Example 1: First time testing
    $ python3 python-implementation/test_serial_port.py
    [Shows complete diagnostics and finds available ports]

Example 2: Test specific USB adapter
    $ python3 python-implementation/test_serial_port.py -d /dev/ttyUSB0
    [Tests /dev/ttyUSB0 specifically]

Example 3: Permission denied - see solution
    $ python3 python-implementation/test_serial_port.py
    ✗ Current user has NO READ or WRITE access
    ℹ You need to be added to the 'dialout' group
    ℹ Try: sudo usermod -a -G dialout zelenya

Example 4: Generate report for support
    $ python3 python-implementation/test_serial_port.py --no-color > report.txt 2>&1
    [Creates plain text report file]

Example 5: Basic shell test
    $ ./test_serial_port.sh
    [Shows basic diagnostics without Python]


WHAT TO DO IF TESTS FAIL
-------------------------

1. If "Permission Denied":
   sudo usermod -a -G dialout $USER
   # Log out and back in

2. If "Device Not Found":
   ls -la /dev/tty* | grep -E "(USB|ACM|S[0-9])"
   # Use the device shown in the list

3. If "Device Busy":
   sudo fuser -v /dev/ttyUSB0
   # Close the program using the port

4. If pyserial not installed:
   pip3 install pyserial

See TESTING-SERIAL-PORT.md for complete solutions.


INTEGRATION WITH OPEN2300
--------------------------

Before running any open2300 tool, you can verify serial port access:

    if python3 python-implementation/test_serial_port.py; then
        ./open2300
    else
        echo "Fix serial port issues first"
    fi

Or update your configuration after finding the correct device:

    1. Run: python3 python-implementation/test_serial_port.py
    2. Note the working device (e.g., /dev/ttyUSB0)
    3. Edit: /etc/open2300.conf
    4. Set: SERIAL_DEVICE /dev/ttyUSB0


SUPPORT
-------

If tests continue to fail:

1. Run with no-color and save output:
   python3 python-implementation/test_serial_port.py --no-color > diag.txt 2>&1

2. Check the generated report for specific errors

3. Follow solutions in TROUBLESHOOTING GUIDE section

4. Verify hardware:
   - Cable connections
   - USB adapter functionality
   - Weather station power

5. Consult project documentation in README and INSTALL files


═══════════════════════════════════════════════════════════════════════

Created: December 31, 2025
For: open2300 weather station project
Purpose: Serial port access testing and diagnostics

═══════════════════════════════════════════════════════════════════════

