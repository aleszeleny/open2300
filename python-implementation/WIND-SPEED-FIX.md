# Wind Speed Calculation Fix

## Problem

Wind speed was being reported as 60.2 m/s (217 km/h, 135 mph) when there was almost no wind. This is hurricane-force winds and clearly wrong.

## Root Cause

The Python implementation was using **incorrect BCD (Binary Coded Decimal) parsing** for wind speed data, when the WS2300 actually stores it as a **12-bit binary value**.

### Python Version (WRONG):

```python
# Treated as BCD: hundreds, tens, ones, tenths
wind_speed = ((data[2] >> 4) * 100 + (data[2] & 0xF) * 10 +
             (data[1] >> 4) + (data[1] & 0xF) / 10.0)
wind_speed = wind_speed * config.wind_speed_conv_factor / 10.0
```

This was parsing:
- `data[2] >> 4` as hundreds
- `data[2] & 0xF` as tens  
- `data[1] >> 4` as ones
- `data[1] & 0xF` as tenths

### C Version (CORRECT):

```c
return ( (((data[2]&0xF)<<8)+(data[1]) ) / 10.0 * wind_speed_conv_factor);
```

This correctly interprets it as:
- Lower 4 bits of `data[2]` form the high nibble (bits 8-11)
- All 8 bits of `data[1]` form the low byte (bits 0-7)
- Result is a 12-bit value representing wind speed in 0.1 m/s units
- Divide by 10.0 to get m/s
- Multiply by conversion factor for other units

## The Fix

### Corrected Python Code:

```python
# Wind direction is in upper 4 bits of data[2]
dir_index = (data[2] >> 4) & 0x0F

# Wind speed is 12-bit value: lower 4 bits of data[2] + all of data[1]
# Formula: ((data[2] & 0xF) << 8) + data[1]) / 10.0
wind_speed_raw = (((data[2] & 0x0F) << 8) + data[1]) / 10.0
wind_speed = wind_speed_raw * config.wind_speed_conv_factor
```

## Data Format

The WS2300 stores wind data at address 0x527 in 6 bytes:

```
Byte 0: Overflow flag (usually 0x00)
Byte 1: Low byte of wind speed (bits 0-7)
Byte 2: Upper nibble = direction (0-15 for N, NNE, NE, etc.)
        Lower nibble = high bits of wind speed (bits 8-11)
Bytes 3-5: Last 5 wind direction readings
```

### Wind Speed Encoding:

- **Storage format**: 12-bit binary value in tenths of m/s
- **Example**: If wind is 1.7 m/s:
  - Stored as: 17 (decimal) = 0x011 (12-bit binary)
  - `data[1]` = 0x11 (lower 8 bits)
  - `data[2]` low nibble = 0x0 (upper 4 bits)
  - Calculation: (0x0 << 8) + 0x11 = 17
  - Result: 17 / 10.0 = 1.7 m/s ✓

### Wind Direction Encoding:

- **Storage format**: Upper 4 bits of byte 2
- **Values**: 0-15 representing 16 compass directions
- **Calculation**: `direction = (data[2] >> 4) * 22.5` degrees
  - 0 = N (0°)
  - 4 = E (90°)
  - 8 = S (180°)
  - 12 = W (270°)

## Testing Results

### Before Fix:
```
WS 60.2     # Wrong: hurricane force!
DIRtext N
```

### After Fix:
```
WS 1.7      # Correct: light breeze
DIRtext WSW
```

**1.7 m/s = 6.1 km/h = 3.8 mph** - This is a light breeze, which matches "almost no wind" ✓

## Why This Happened

1. **Misinterpreted data format**: Assumed BCD encoding like temperature/humidity
2. **Wrong bit extraction**: Used upper nibble instead of lower nibble
3. **Not comparing with C code**: The formula looked "reasonable" but was wrong

## Lessons Learned

1. **Always verify data encoding** - Don't assume similar sensors use the same format
2. **Test with known conditions** - A quick sanity check would have caught this
3. **Compare byte-by-byte with C version** - Bit manipulation needs exact matching
4. **Document the data format** - Add comments explaining the bit layout

## Related Code

### Temperature/Humidity (BCD Format):
```python
# These DO use BCD encoding
temp_c = (((data[1] >> 4) * 10 + (data[1] & 0xF) +
           (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0)
```

### Wind Speed (Binary Format):
```python
# This uses 12-bit binary, NOT BCD
wind_speed_raw = (((data[2] & 0x0F) << 8) + data[1]) / 10.0
```

## Files Modified

- `python-implementation/pyopen2300/cli/fetch2300.py`
  - Fixed wind speed calculation
  - Fixed wind direction extraction
  - Added detailed comments explaining the format

## References

- C implementation: `rw2300.c` function `wind_all()` lines 925-965
- Memory map: `memory_map_2300.txt` address 0x527
- WS2300 protocol documentation: `api.txt`

---

**Date:** December 31, 2025  
**Issue:** Wind speed 35x too high (60.2 m/s instead of 1.7 m/s)  
**Resolution:** Fixed calculation from BCD parsing to 12-bit binary  
**Status:** ✅ Fixed and tested

