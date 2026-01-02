# Weather Station Time - Final Implementation

## Overview

The final implementation provides both **station-read UTC** and **calculated UTC** values, allowing users to verify which is accurate and choose the appropriate source for their needs.

## Implementation Details

### Three Time Functions

#### 1. `ws_time_local()` - Local Time from Station
- **Address:** 0x239 (time) + 0x240 (date)
- **Source:** DCF77-synchronized local time
- **Reliability:** ✅ **Highly reliable** (radio-synchronized)
- **Use:** Display local time, calculate UTC

#### 2. `ws_time_utc_from_station()` - UTC from Station Memory
- **Address:** 0x200 (time) + 0x207 (date)
- **Source:** Station's internal UTC calculation
- **Reliability:** ⚠️ **Depends on station timezone configuration**
- **Use:** Primary UTC source when station is properly configured

#### 3. `ws_time_utc_calculated()` - Calculated UTC
- **Source:** Local time - Config timezone offset
- **Reliability:** ✅ **Reliable if config timezone is correct**
- **Use:** Backup UTC source, verification

## Testing Results

### After Station DCF77 Synchronization

**Station Memory (Raw bytes):**
```
Local (0x239+0x240):  21:07:00  2026-01-01
UTC   (0x200+0x207):  20:07:39  2026-01-01
Difference: 1 hour ✓ (Correct for UTC+1)
```

**fetch2300 Output:**
```
C Version:
  WSDateLocal    2026-01-01
  WSTimeLocal    21:06
  WSDateUTC      2026-01-01  ← From station (0x200/0x207)
  WSTimeUTC      20:06       ← Correct!
  WSDateUTCCalc  2026-01-01  ← Calculated (local - TZ)
  WSTimeUTCCalc  20:06       ← Matches station UTC!

Python Version:
  WSDateLocal    2026-01-01
  WSTimeLocal    21:07
  WSDateUTC      2026-01-01  ← From station
  WSTimeUTC      20:07       ← Correct!
  WSDateUTCCalc  2026-01-01  ← Calculated
  WSTimeUTCCalc  20:07       ← Matches station UTC!
```

**Conclusion:** Station UTC is now correct and matches calculated UTC! ✅

## Verbose Mode

### C Implementation (fetch2300.c)
Controlled by `DEBUG` compile flag:
```c
#define DEBUG 1  // Enable verbose output
```

When DEBUG is enabled, fetch2300 prints:
- `WSDateLocal` / `WSTimeLocal` - Station local time
- `WSDateUTC` / `WSTimeUTC` - Station UTC (from memory)
- `WSDateUTCCalc` / `WSTimeUTCCalc` - Calculated UTC
- `ConfigTZ` - Timezone from config file

### Python Implementation (fetch2300.py)
Controlled by `LOG_LEVEL` in config file:
```ini
LOG_LEVEL 2  # 0=none, 1=min, 2=max (verbose)
```

When `LOG_LEVEL >= 2`, fetch2300 prints the same verbose output.

## Usage Recommendations

### When Station UTC is Correct
```c
// Use station UTC directly
ws_time_utc_from_station(ws2300, &utc_timestamp);
```

**Advantages:**
- Direct read from station
- Automatically updated by DCF77
- No manual timezone configuration needed

### When Station UTC is Wrong
```c
// Use calculated UTC
ws_time_utc_calculated(ws2300, atof(config.timezone), &utc_timestamp);
```

**Advantages:**
- Always accurate if config timezone is correct
- Independent of station configuration
- Predictable behavior

### Verification Strategy
```c
// Read both and compare
struct timestamp station_utc, calculated_utc;
ws_time_utc_from_station(ws2300, &station_utc);
ws_time_utc_calculated(ws2300, atof(config.timezone), &calculated_utc);

// If they match, station UTC is correct
if (station_utc.hour == calculated_utc.hour && 
    station_utc.minute == calculated_utc.minute) {
    // Station UTC is reliable, use it
} else {
    // Use calculated UTC
}
```

## Database Integration

### Current Implementation (pgsql2300)
Uses **station UTC** (`ws_time_utc_from_station`):
```c
ws_time_utc_from_station(ws2300, &ws_data.ws_datetime_utc);
```

**Rationale:** 
- Station is now properly synchronized
- Automatically maintained by DCF77
- No manual DST updates needed

### Alternative (if station UTC unreliable)
Switch to calculated UTC:
```c
ws_time_utc_calculated(ws2300, atof(config.timezone), &ws_data.ws_datetime_utc);
```

**Note:** Requires manual timezone updates for DST changes.

## Configuration

### Config File (open2300.conf)
```ini
TIMEZONE 1    # UTC+1 (Central European Time, winter)
# Change to 2 for summer time (CEST)
```

### Station Configuration
The weather station's timezone is configured via:
1. DCF77 signal (automatic)
2. Manual setting via station menu

**Current Status:** Station timezone is correctly set to UTC+1 ✅

## Memory Addresses

| Purpose | Address | Bytes | Content |
|---------|---------|-------|---------|
| Local Time | 0x239 | 3 | second, minute, hour (BCD) |
| Local Date | 0x240 | 3 | day, month, year (BCD) |
| UTC Time | 0x200 | 3 | second, minute, hour (BCD) |
| UTC Date | 0x207 | 3 | day, month, year (BCD) |
| Timezone? | 0x238 | 1 | Unknown (shows 0x00) |

**Note:** Timezone register location is unclear. Station may calculate UTC internally without exposing the offset.

## API Reference

### C Functions

```c
// Read local time (DCF77-synchronized)
void ws_time_local(WEATHERSTATION ws2300, struct timestamp *timestamp);

// Read UTC from station memory
void ws_time_utc_from_station(WEATHERSTATION ws2300, struct timestamp *timestamp);

// Calculate UTC from local + timezone
void ws_time_utc_calculated(WEATHERSTATION ws2300, double timezone_offset, 
                            struct timestamp *timestamp);
```

### Python Methods

```python
# Read local time (DCF77-synchronized)
def ws_time_local(self) -> Timestamp

# Read UTC from station memory
def ws_time_utc_from_station(self) -> Timestamp

# Calculate UTC from local + timezone
def ws_time_utc_calculated(self, timezone_offset: float) -> Timestamp
```

## Files Modified

### C Implementation
- `rw2300.c` - Added `ws_time_utc_from_station()` and `ws_time_utc_calculated()`
- `rw2300.h` - Added function declarations
- `fetch2300.c` - Shows both station UTC and calculated UTC (in DEBUG mode)
- `pgsql2300.c` - Uses `ws_time_utc_from_station()`
- `xml2300.c` - Uses `ws_time_utc_from_station()`

### Python Implementation
- `weatherstation.py` - Added `ws_time_utc_from_station()` and `ws_time_utc_calculated()`
- `fetch2300.py` - Shows both station UTC and calculated UTC (in verbose mode)
- `pgsql2300.py` - Uses `ws_time_utc_from_station()`
- `xml2300.py` - Uses `ws_time_utc_from_station()`

## Troubleshooting

### Station UTC is Wrong
**Symptoms:** `WSDateUTC` / `WSTimeUTC` doesn't match `WSDateUTCCalc` / `WSTimeUTCCalc`

**Solutions:**
1. Wait for DCF77 synchronization (can take several hours)
2. Check station timezone setting via menu
3. Use `ws_time_utc_calculated()` instead of `ws_time_utc_from_station()`

### Calculated UTC is Wrong
**Symptoms:** `WSTimeUTCCalc` is off by 1+ hours

**Solutions:**
1. Check `TIMEZONE` setting in `open2300.conf`
2. Update for DST changes (1 for winter, 2 for summer in CET)
3. Verify config file is being read correctly

### Both UTC Values are Wrong
**Symptoms:** Both station and calculated UTC are incorrect

**Solutions:**
1. Check if local time is correct (DCF77 synchronized?)
2. Verify system time on Raspberry Pi
3. Check if station needs battery replacement

## Summary

✅ **Station UTC is now correct** after DCF77 synchronization  
✅ **Both station and calculated UTC match** (20:06 vs 20:06)  
✅ **Verbose mode available** for verification  
✅ **Dual implementation** provides redundancy  
✅ **Database uses station UTC** (automatically maintained)  

The implementation provides maximum flexibility and reliability for UTC timestamp management in the weather station system.

