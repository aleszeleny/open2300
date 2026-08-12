# Debug Guide for WS2300 Python Implementation

## Overview

The Python implementation now includes detailed debug tracing for diagnosing communication issues with the WS2300 weather station.

## Enabling Debug Output

Debug output is controlled by the `WS2300_DEBUG` environment variable:

```bash
export WS2300_DEBUG=1    # Enable debug
export WS2300_DEBUG=0    # Disable debug (default)
```

Or run inline:

```bash
WS2300_DEBUG=1 fetch2300
```

## What Gets Logged

When debug is enabled, you'll see detailed traces of:

### Serial Communication Layer
- Serial port open/close operations
- Every byte written to the serial port
- Every byte read from the serial port
- Read/write timing information
- Timeout information

### Weather Station Protocol Layer
- Reset sequence (reset_06)
- Address encoding
- Command transmission
- ACK/NACK responses
- Data byte reception
- Checksum verification
- Retry attempts

### High-Level Operations
- Function entry/exit
- Temperature/humidity/pressure reads
- Data parsing and conversion

## Debug Output Format

```
DEBUG[SERIAL]: <message about serial I/O>
DEBUG[WS2300]: <message about protocol>
```

All debug output goes to **stderr** so it doesn't interfere with data output.

## Example Debug Output

```bash
$ WS2300_DEBUG=1 fetch2300

DEBUG[SERIAL]: Opening serial device: /dev/ttyUSB0
DEBUG[SERIAL]: Serial port opened successfully: /dev/ttyUSB0
DEBUG[SERIAL]: Baudrate: 2400, Timeout: 1.0s
DEBUG[SERIAL]: Input and output buffers flushed
DEBUG[WS2300]: temperature_indoor: Starting read from address 0x346
DEBUG[WS2300]: read_safe: Starting read from 0x0346, 2 bytes (max 50 retries)
DEBUG[WS2300]: read_safe: Attempt 1/50
DEBUG[WS2300]: reset_06: Starting reset sequence
DEBUG[WS2300]: reset_06: Attempt 1/100
DEBUG[WS2300]: reset_06: Input buffer flushed
DEBUG[WS2300]: reset_06: Sending command 0x06
DEBUG[SERIAL]: Writing 1 byte(s): 0x06
DEBUG[SERIAL]: Wrote 1 byte(s), flushed
DEBUG[WS2300]: reset_06: Reading response byte 1
DEBUG[SERIAL]: Reading 1 byte(s) from serial (timeout=1.0s)...
DEBUG[SERIAL]: Read 1/1 byte(s) in 0.042s: 0x02
DEBUG[WS2300]: reset_06: Received byte: 0x02
DEBUG[WS2300]: reset_06: SUCCESS - received 0x02
DEBUG[WS2300]: read_safe: Reset complete, attempting read
DEBUG[WS2300]: read_data: Reading 2 bytes from address 0x0346
DEBUG[WS2300]: read_data: Command bytes: 0x96 0xc2 0x93 0xc6 0xca
DEBUG[WS2300]: read_data: Sending address byte 0: 0x96
DEBUG[SERIAL]: Writing 1 byte(s): 0x96
DEBUG[SERIAL]: Wrote 1 byte(s), flushed
DEBUG[WS2300]: read_data: Reading ACK for address byte 0
DEBUG[SERIAL]: Reading 1 byte(s) from serial (timeout=1.0s)...
DEBUG[SERIAL]: Read 1/1 byte(s) in 0.035s: 0x05
DEBUG[WS2300]: read_data: Received ACK: 0x05, expected: 0x05
...
```

## Troubleshooting with Debug Output

### Issue: Hangs at "Reading indoor temperature"

Enable debug to see where exactly it's hanging:

```bash
WS2300_DEBUG=1 fetch2300 2>&1 | tee debug.log
```

Look for:
1. **Hangs in reset_06**: Weather station not responding to reset command
2. **Hangs reading ACK**: Communication protocol issue
3. **Timeout messages**: Serial port timing issues

### Issue: Always times out on read

Look for messages like:
```
DEBUG[SERIAL]: Read 0/1 byte(s) - TIMEOUT after 1.000s
```

This indicates the weather station is not responding. Possible causes:
- Wrong serial device
- Weather station not powered
- Cable connection issue
- Serial port configuration issue

### Issue: Wrong ACK/checksum

Look for messages like:
```
DEBUG[WS2300]: read_data: Received ACK: 0x05, expected: 0x06
DEBUG[WS2300]: read_data: ACK mismatch for address byte 1
```

This indicates protocol-level issues:
- Noise on the serial line
- Baud rate mismatch
- Timing issues

### Issue: Reset succeeds but read fails

If you see:
```
DEBUG[WS2300]: reset_06: SUCCESS - received 0x02
DEBUG[WS2300]: read_safe: Reset complete, attempting read
DEBUG[WS2300]: read_data: Reading 2 bytes from address 0x0346
... (then timeout)
```

The station resets OK but doesn't respond to data requests. This suggests:
- Protocol timing issue
- Need to add delays
- Weather station firmware issue

## Helper Scripts

### test_fetch_debug.sh

Runs fetch2300 with debug enabled:

```bash
cd python-implementation
./test_fetch_debug.sh
```

This sets `WS2300_DEBUG=1` and runs fetch2300.

## Combining with fetch2300 Logging

You can combine debug output with fetch2300's LOG_LEVEL:

```bash
# Maximum verbosity
WS2300_DEBUG=1 LOG_LEVEL=3 fetch2300
```

This shows:
- Serial I/O (from WS2300_DEBUG)
- Protocol details (from WS2300_DEBUG)
- Application-level progress (from LOG_LEVEL)

## Saving Debug Output

Save all output to a file:

```bash
WS2300_DEBUG=1 fetch2300 > data.txt 2> debug.log
```

- `data.txt`: Weather data (stdout)
- `debug.log`: All debug and log messages (stderr)

Or combine both:

```bash
WS2300_DEBUG=1 fetch2300 2>&1 | tee full_debug.log
```

## Performance Impact

Debug output has minimal performance impact:
- Adds ~1-2ms per operation
- Actual communication takes 2-5 seconds
- Debug overhead is negligible

However, debug logging is VERY verbose and will fill up logs quickly.

**Recommendation**: Only enable debug when troubleshooting, not in production.

## Interpreting Timing Information

```
DEBUG[SERIAL]: Read 1/1 byte(s) in 0.042s: 0x02
```

- Normal read time: 20-50ms per byte at 2400 baud
- Timeout: 1.000s indicates no response
- Very fast (< 5ms): Data was already in buffer

## Debug in Production

For production monitoring without verbose debug:

```bash
# Minimal logging (no debug)
LOG_LEVEL=1 fetch2300

# Medium logging (see data values)
LOG_LEVEL=2 fetch2300
```

Only use `WS2300_DEBUG=1` when you need to diagnose communication issues.

## Known Issues and Patterns

### Pattern 1: Hangs on first reset_06

```
DEBUG[WS2300]: reset_06: Attempt 1/100
DEBUG[SERIAL]: Writing 1 byte(s): 0x06
DEBUG[SERIAL]: Wrote 1 byte(s), flushed
DEBUG[WS2300]: reset_06: Reading response byte 1
DEBUG[SERIAL]: Reading 1 byte(s) from serial (timeout=1.0s)...
(hangs here forever)
```

**Solution**: Weather station may need power cycle or is on wrong serial port.

### Pattern 2: Gets garbage data

```
DEBUG[SERIAL]: Read 1/1 byte(s) in 0.035s: 0xff
DEBUG[WS2300]: reset_06: Received byte: 0xff
```

**Solution**: Wrong baud rate or serial port configuration issue.

### Pattern 3: Constant retries

```
DEBUG[WS2300]: read_safe: Attempt 1/50
... (fails)
DEBUG[WS2300]: read_safe: Attempt 2/50
... (fails)
DEBUG[WS2300]: read_safe: Attempt 3/50
```

**Solution**: Protocol issue - may need timing delays or reset logic adjustment.

## Next Steps

If you're seeing issues:

1. Run with debug: `WS2300_DEBUG=1 fetch2300 2>&1 | tee debug.log`
2. Look for the last successful operation before hang/failure
3. Compare with expected protocol sequence
4. Check timing of operations
5. Verify serial port settings

If the C version works but Python doesn't, compare:
- Protocol timing
- Reset sequence behavior
- Serial port configuration

