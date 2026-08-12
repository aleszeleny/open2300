# WS2300 Python Implementation - Fix Summary

## Problem

`fetch2300` was hanging at "Reading indoor temperature" on Raspberry Pi. The serial port test worked fine, but communication with the weather station failed.

## Root Cause

The Python implementation was missing **critical serial port control line settings** that are required for the WS2300 hardware to function:

- **DTR (Data Terminal Ready)** must be set LOW
- **RTS (Request To Send)** must be set HIGH

The C implementation in `linux2300.c` includes this code:
```c
// Set DTR low and RTS high
portstatus &= ~TIOCM_DTR;
portstatus |= TIOCM_RTS;
ioctl(ws2300, TIOCMSET, &portstatus);
```

The Python implementation was not setting these control lines.

## Symptoms

Without the correct DTR/RTS settings:
- The weather station would respond with `0x00` to reset commands
- It would never send the expected `0x02` response
- Communication would timeout after many retry attempts
- `fetch2300` would hang indefinitely

## The Fix

### File: `pyopen2300/serial_comm.py`

Added DTR/RTS control line settings after opening the serial port:

```python
def _open(self):
    """Open serial port connection"""
    self.ser = serial.Serial(
        port=self.device,
        baudrate=BAUDRATE,
        # ... other settings ...
    )
    
    # Set DTR low and RTS high (required for WS2300)
    self.ser.dtr = False  # DTR low
    self.ser.rts = True   # RTS high
    
    # Flush buffers
    self.ser.reset_input_buffer()
    self.ser.reset_output_buffer()
```

### File: `pyopen2300/weatherstation.py`

Also improved the `reset_06()` function to properly handle the WS2300 reset protocol:

- Keep reading bytes until timeout (station may send 0x00 first, then 0x02)
- Accept success if 0x02 is received at any point during the read loop
- Added small delays after flush and write operations

## Debug Infrastructure Added

To diagnose this issue, comprehensive debug tracing was added:

### Environment Variable: `WS2300_DEBUG=1`

Enables detailed tracing of:
- Serial port operations (open, read, write)
- Every byte sent/received (with hex values)
- Protocol operations (reset, address encoding, ACKs)
- Timing information
- Retry attempts

### Files Added:

1. **DEBUG-GUIDE.md** - Complete debugging documentation
2. **test_fetch_debug.sh** - Helper script to run with debug enabled
3. **RPI-TEST-INSTRUCTIONS.txt** - Raspberry Pi testing guide

### Debug Output Example:

```
DEBUG[SERIAL]: Opening serial device: /dev/ttyUSB0
DEBUG[SERIAL]: Setting DTR=low, RTS=high
DEBUG[WS2300]: reset_06: Sending command 0x06
DEBUG[SERIAL]: Writing 1 byte(s): 0x06
DEBUG[SERIAL]: Read 1/1 byte(s) in 0.001s: 0x02
DEBUG[WS2300]: reset_06: SUCCESS
DEBUG[WS2300]: read_data: Reading 2 bytes from address 0x0346
DEBUG[WS2300]: read_data: Received ACK: 0x00, expected: 0x00
...
```

## Testing

After the fix:

```bash
$ fetch2300
Date 2025-Dec-31
Time 20:09:15
Ti 22.2
To -0.6
DP -4.9
RHi 42
RHo 73
WS 60.2
DIRtext N
RP 963.600
Tendency Falling
Forecast Rainy
```

✅ All sensor readings work correctly
✅ No more hangs or timeouts
✅ Matches expected output format

## Why This Wasn't Caught Earlier

1. **Serial port test tool** doesn't communicate with the weather station, so it worked fine
2. **Different hardware** may not require these settings (some USB-to-serial adapters handle it automatically)
3. **Python's pyserial** defaults to `dsrdtr=False` but doesn't explicitly set DTR/RTS
4. The C implementation's DTR/RTS code was easy to miss when porting

## Lessons Learned

1. **Always check hardware control lines** when porting serial communication code
2. **Match the C implementation exactly** - even "minor" hardware settings matter
3. **Debug infrastructure is essential** - the detailed tracing made diagnosis possible
4. **Test on actual hardware** - simulators won't catch hardware-specific issues

## Hardware Requirements for WS2300

The WS2300 weather station requires:
- **Baud rate:** 2400 bps
- **Data bits:** 8
- **Parity:** None
- **Stop bits:** 1
- **Flow control:** None (software or hardware)
- **DTR:** LOW ⚠️ **Critical**
- **RTS:** HIGH ⚠️ **Critical**

## Related Files Modified

### Core Files:
- `pyopen2300/serial_comm.py` - Added DTR/RTS settings
- `pyopen2300/weatherstation.py` - Improved reset_06() logic
- `pyopen2300/cli/fetch2300.py` - Already had verbose logging

### Documentation:
- `DEBUG-GUIDE.md` - Debug documentation
- `FIX-SUMMARY.md` - This file
- `RPI-TEST-INSTRUCTIONS.txt` - Testing guide

### Test Scripts:
- `test_fetch_debug.sh` - Debug helper
- `test_serial_port.py` - Serial port tester (already existed)

## Future Considerations

1. Consider adding a warning if DTR/RTS cannot be set
2. Add unit tests for serial port initialization
3. Document hardware requirements more prominently
4. Consider adding a hardware compatibility check tool

## References

- C implementation: `linux2300.c` lines 105-108
- WS2300 Protocol: See `memory_map_2300.txt` and `api.txt`
- pyserial documentation: https://pyserial.readthedocs.io/

---

**Date:** December 31, 2025  
**Issue:** fetch2300 hangs on Raspberry Pi  
**Resolution:** Add DTR=low, RTS=high settings to serial port initialization  
**Status:** ✅ Fixed and tested on Raspberry Pi with USB-to-serial adapter

