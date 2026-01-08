"""
Weather Station protocol implementation for WS2300
Equivalent to rw2300.c in the original C implementation
"""

from typing import Tuple, Optional
import sys
import time
import os
from datetime import datetime
from .serial_comm import SerialDevice, sleep_short
from .constants import (
    MAXRETRIES,
    MAXWINDRETRIES,
    WRITENIB,
    SETBIT,
    UNSETBIT,
    WRITEACK,
    SETACK,
    UNSETACK,
    RESET_MIN,
    RESET_MAX,
    CELSIUS,
    FAHRENHEIT
)

# Debug flag - set via environment variable WS2300_DEBUG=1
DEBUG = os.environ.get('WS2300_DEBUG', '0') == '1'

def debug_print(msg):
    """Print debug message if DEBUG is enabled"""
    if DEBUG:
        print(f"DEBUG[WS2300]: {msg}", file=sys.stderr, flush=True)


class Timestamp:
    """Timestamp structure for weather data"""
    def __init__(self):
        self.minute = 0
        self.hour = 0
        self.day = 0
        self.month = 0
        self.year = 0
    
    def to_datetime(self):
        """Convert to Python datetime"""
        try:
            return datetime(self.year, self.month, self.day, self.hour, self.minute)
        except ValueError:
            return None


class WeatherStation:
    """
    Main weather station communication class
    Handles low-level protocol communication with WS2300
    """
    
    def __init__(self, device: str):
        """
        Initialize weather station connection
        
        Args:
            device: Serial device path
        """
        self.device = SerialDevice(device)
    
    def close(self):
        """Close weather station connection"""
        self.device.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
    
    # Low-level protocol functions
    
    @staticmethod
    def address_encoder(address: int) -> bytes:
        """
        Convert 16-bit address to WS2300 command format
        
        Args:
            address: 16-bit address
            
        Returns:
            4 bytes of encoded address
        """
        result = bytearray(4)
        for i in range(4):
            nibble = (address >> (4 * (3 - i))) & 0x0F
            result[i] = 0x82 + (nibble * 4)
        return bytes(result)
    
    @staticmethod
    def data_encoder(number: int, encode_constant: int, data_in: bytes) -> bytes:
        """
        Encode data bytes for writing to WS2300
        
        Args:
            number: Number of data bytes
            encode_constant: Encoding constant (WRITENIB, SETBIT, UNSETBIT)
            data_in: Input data bytes
            
        Returns:
            Encoded data bytes
        """
        result = bytearray(number)
        for i in range(number):
            result[i] = encode_constant + (data_in[i] * 4)
        return bytes(result)
    
    @staticmethod
    def numberof_encoder(number: int) -> int:
        """
        Encode the number of bytes to read
        
        Args:
            number: Number of bytes (max 15)
            
        Returns:
            Encoded number
        """
        coded = 0xC2 + number * 4
        if coded > 0xFE:
            coded = 0xFE
        return coded
    
    @staticmethod
    def command_check0123(command: int, sequence: int) -> int:
        """
        Calculate checksum for first 4 address commands
        
        Args:
            command: Command byte
            sequence: Sequence number (0-3)
            
        Returns:
            Expected response
        """
        return sequence * 16 + (command - 0x82) // 4
    
    @staticmethod
    def command_check4(number: int) -> int:
        """
        Calculate checksum for data request command
        
        Args:
            number: Number of bytes requested
            
        Returns:
            Expected response
        """
        return 0x30 + number
    
    @staticmethod
    def data_checksum(data: bytes, number: int) -> int:
        """
        Calculate checksum for data bytes
        
        Args:
            data: Data bytes
            number: Number of bytes
            
        Returns:
            Checksum
        """
        checksum = sum(data[:number]) & 0xFF
        return checksum
    
    def reset_06(self):
        """
        Reset weather station by sending 0x06 command
        
        Note: From C code comments:
        "Occasionally 0, then 2 is returned. If zero comes back, continue
        reading as this is more efficient than sending an out-of sync
        reset and letting the data reads restore synchronization.
        Occasionally, multiple 2's are returned. Read with a fast timeout
        until all data is exhausted, if we got a two back at all, we
        consider it a success"
        """
        debug_print("reset_06: Starting reset sequence")
        command = bytes([0x06])
        
        for i in range(100):
            debug_print(f"reset_06: Attempt {i+1}/100")
            # Discard input buffer
            try:
                self.device.ser.reset_input_buffer()
                debug_print("reset_06: Input buffer flushed")
            except Exception as e:
                debug_print(f"reset_06: Error flushing buffer: {e}")
                pass
            
            # # Small delay to let the flush complete and line stabilize
            # time.sleep(0.001)  # 1ms delay
            
            debug_print(f"reset_06: Sending command 0x06")
            self.device.write(command)
            
            # # Small delay to let the device process the command
            # time.sleep(0.01)  # 10ms delay (enough for 2-3 bytes at 2400 baud)
            debug_print("reset_06: Waiting for response...")
            
            # Read responses until we get a 2 OR timeout
            # Keep reading as long as data comes back
            # The station may send 0x00 first, then 0x02
            # This matches the C implementation which reads until no more data
            read_count = 0
            got_two = False
            while True:
                debug_print(f"reset_06: Reading response byte {read_count+1}")
                answer = self.device.read(1)
                if len(answer) == 0:
                    # Timeout - no more data
                    debug_print(f"reset_06: Timeout after {read_count} bytes")
                    break
                read_count += 1
                debug_print(f"reset_06: Received byte {read_count}: 0x{answer[0]:02x}")
                if answer[0] == 2:
                    debug_print(f"reset_06: Got 0x02 at byte {read_count}")
                    got_two = True
                    # Keep reading to drain any additional 0x02 bytes
                elif answer[0] == 0:
                    debug_print(f"reset_06: Got 0x00 at byte {read_count}, continuing...")
                    # Continue reading, 0x02 may follow
                else:
                    debug_print(f"reset_06: Got unexpected byte 0x{answer[0]:02x}")
            
            # If we got a 0x02 at any point, consider it success
            if got_two:
                debug_print(f"reset_06: SUCCESS - received 0x02 (total {read_count} bytes read)")
                return
            
            debug_print(f"reset_06: No 0x02 received in {read_count} bytes")
            
            # Sleep longer for each retry (matches C: usleep(50000 * i) = 0.05s * i)
            if i > 0:
                sleep_time = 0.05 * i
                debug_print(f"reset_06: Sleeping {sleep_time:.3f}s before retry")
                time.sleep(sleep_time)
        
        debug_print("reset_06: FAILED after 100 attempts")
        print("Could not reset weather station", file=sys.stderr)
        sys.exit(1)
    
    def initialize(self) -> bool:
        """
        Initialize weather station (cold start)
        
        Returns:
            True on success, False on failure
        """
        command = bytes([0x06])
        
        self.device.write(command)
        answer = self.device.read(1)
        if len(answer) != 1:
            return False
        
        self.device.write(command)
        self.device.write(command)
        answer = self.device.read(1)
        if len(answer) != 1:
            return False
        
        self.device.write(command)
        answer = self.device.read(1)
        if len(answer) != 1:
            return False
        
        self.device.write(command)
        answer = self.device.read(1)
        if len(answer) != 1:
            return False
        
        if answer[0] != 2:
            return False
        
        return True
    
    def read_data(self, address: int, number: int) -> Tuple[Optional[bytes], bytes]:
        """
        Read data from weather station
        
        Args:
            address: Memory address (16-bit)
            number: Number of bytes to read (max 15)
            
        Returns:
            Tuple of (data bytes, command bytes) or (None, command) on failure
        """
        debug_print(f"read_data: Reading {number} bytes from address 0x{address:04x}")
        
        # Encode address
        commanddata = bytearray(self.address_encoder(address))
        commanddata.append(self.numberof_encoder(number))
        debug_print(f"read_data: Command bytes: {' '.join(f'0x{b:02x}' for b in commanddata)}")
        
        # Send 4 address bytes
        for i in range(4):
            debug_print(f"read_data: Sending address byte {i}: 0x{commanddata[i]:02x}")
            if self.device.write(bytes([commanddata[i]])) != 1:
                debug_print(f"read_data: FAILED to write address byte {i}")
                return None, bytes(commanddata)
            
            debug_print(f"read_data: Reading ACK for address byte {i}")
            answer = self.device.read(1)
            if len(answer) != 1:
                debug_print(f"read_data: No ACK received for address byte {i} (timeout)")
                return None, bytes(commanddata)
            
            expected = self.command_check0123(commanddata[i], i)
            debug_print(f"read_data: Received ACK: 0x{answer[0]:02x}, expected: 0x{expected:02x}")
            if answer[0] != expected:
                debug_print(f"read_data: ACK mismatch for address byte {i}")
                return None, bytes(commanddata)
        
        # Send number-of-bytes command
        debug_print(f"read_data: Sending number-of-bytes command: 0x{commanddata[4]:02x}")
        if self.device.write(bytes([commanddata[4]])) != 1:
            debug_print("read_data: FAILED to write number-of-bytes command")
            return None, bytes(commanddata)
        
        debug_print("read_data: Reading ACK for number-of-bytes")
        answer = self.device.read(1)
        if len(answer) != 1:
            debug_print("read_data: No ACK received for number-of-bytes (timeout)")
            return None, bytes(commanddata)
        
        expected = self.command_check4(number)
        debug_print(f"read_data: Received ACK: 0x{answer[0]:02x}, expected: 0x{expected:02x}")
        if answer[0] != expected:
            debug_print("read_data: ACK mismatch for number-of-bytes")
            return None, bytes(commanddata)
        
        # Read data bytes
        debug_print(f"read_data: Reading {number} data bytes")
        readdata = bytearray()
        for i in range(number):
            debug_print(f"read_data: Reading data byte {i+1}/{number}")
            data = self.device.read(1)
            if len(data) != 1:
                debug_print(f"read_data: Timeout reading data byte {i+1}")
                return None, bytes(commanddata)
            debug_print(f"read_data: Data byte {i+1}: 0x{data[0]:02x}")
            readdata.append(data[0])
        
        # Read and verify checksum
        debug_print("read_data: Reading checksum")
        answer = self.device.read(1)
        if len(answer) != 1:
            debug_print("read_data: Timeout reading checksum")
            return None, bytes(commanddata)
        
        expected_checksum = self.data_checksum(bytes(readdata), number)
        debug_print(f"read_data: Received checksum: 0x{answer[0]:02x}, expected: 0x{expected_checksum:02x}")
        if answer[0] != expected_checksum:
            debug_print("read_data: Checksum mismatch")
            return None, bytes(commanddata)
        
        debug_print(f"read_data: SUCCESS - Read data: {' '.join(f'0x{b:02x}' for b in readdata)}")
        return bytes(readdata), bytes(commanddata)
    
    def write_data(self, address: int, number: int, encode_constant: int, 
                   writedata: bytes) -> Tuple[int, bytes]:
        """
        Write data to weather station
        
        Args:
            address: Memory address (16-bit)
            number: Number of nibbles to write
            encode_constant: WRITENIB, SETBIT, or UNSETBIT
            writedata: Data to write (hex nibbles)
            
        Returns:
            Tuple of (number of bytes written, command bytes)
        """
        # Determine ACK constant
        if encode_constant == SETBIT:
            ack_constant = SETACK
        elif encode_constant == UNSETBIT:
            ack_constant = UNSETACK
        else:
            ack_constant = WRITEACK
        
        # Encode address and data
        commanddata = bytearray(self.address_encoder(address))
        encoded_data = self.data_encoder(number, encode_constant, writedata)
        
        # Send 4 address bytes
        for i in range(4):
            if self.device.write(bytes([commanddata[i]])) != 1:
                return -1, bytes(commanddata)
            answer = self.device.read(1)
            if len(answer) != 1:
                return -1, bytes(commanddata)
            if answer[0] != self.command_check0123(commanddata[i], i):
                return -1, bytes(commanddata)
        
        # Write data nibbles
        for i in range(number):
            if self.device.write(bytes([encoded_data[i]])) != 1:
                return -1, bytes(commanddata)
            answer = self.device.read(1)
            if len(answer) != 1:
                return -1, bytes(commanddata)
            if answer[0] != (writedata[i] + ack_constant):
                return -1, bytes(commanddata)
            commanddata.append(encoded_data[i])
        
        return number, bytes(commanddata)
    
    def read_safe(self, address: int, number: int) -> Optional[bytes]:
        """
        Read data with retries until success or max retries
        
        Args:
            address: Memory address
            number: Number of bytes to read
            
        Returns:
            Data bytes or None on failure
        """
        debug_print(f"read_safe: Starting read from 0x{address:04x}, {number} bytes (max {MAXRETRIES} retries)")
        
        for j in range(MAXRETRIES):
            debug_print(f"read_safe: Attempt {j+1}/{MAXRETRIES}")
            self.reset_06()
            debug_print(f"read_safe: Reset complete, attempting read")
            data, _ = self.read_data(address, number)
            if data is not None and len(data) == number:
                debug_print(f"read_safe: SUCCESS on attempt {j+1}")
                return data
            debug_print(f"read_safe: Attempt {j+1} failed, will retry")
        
        debug_print(f"read_safe: FAILED after {MAXRETRIES} attempts")
        return None
    
    def write_safe(self, address: int, number: int, encode_constant: int,
                   writedata: bytes) -> int:
        """
        Write data with retries until success or max retries
        
        Args:
            address: Memory address
            number: Number of nibbles to write
            encode_constant: WRITENIB, SETBIT, or UNSETBIT
            writedata: Data to write
            
        Returns:
            Number of bytes written, or -1 on failure
        """
        for j in range(MAXRETRIES):
            self.reset_06()
            written, _ = self.write_data(address, number, encode_constant, writedata)
            if written == number:
                return number
        
        return -1
    
    # High-level data reading functions
    
    def temperature_indoor(self, temperature_conv: int = CELSIUS) -> float:
        """
        Read current indoor temperature
        
        Args:
            temperature_conv: CELSIUS or FAHRENHEIT
            
        Returns:
            Temperature in specified units
        """
        debug_print("temperature_indoor: Starting read from address 0x346")
        data = self.read_safe(0x346, 2)
        if data is None:
            debug_print("temperature_indoor: FAILED - read_safe returned None")
            raise IOError("Failed to read indoor temperature")
        
        debug_print(f"temperature_indoor: Raw data: 0x{data[0]:02x} 0x{data[1]:02x}")
        temp_c = (((data[1] >> 4) * 10 + (data[1] & 0xF) +
                   (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0)
        debug_print(f"temperature_indoor: Calculated temperature: {temp_c:.1f}°C")
        
        if temperature_conv == FAHRENHEIT:
            temp_f = temp_c * 9 / 5 + 32
            debug_print(f"temperature_indoor: Converted to Fahrenheit: {temp_f:.1f}°F")
            return temp_f
        return temp_c
    
    def temperature_outdoor(self, temperature_conv: int = CELSIUS) -> float:
        """
        Read current outdoor temperature
        
        Args:
            temperature_conv: CELSIUS or FAHRENHEIT
            
        Returns:
            Temperature in specified units
        """
        data = self.read_safe(0x373, 2)
        if data is None:
            raise IOError("Failed to read outdoor temperature")
        
        temp_c = (((data[1] >> 4) * 10 + (data[1] & 0xF) +
                   (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0)
        
        if temperature_conv == FAHRENHEIT:
            return temp_c * 9 / 5 + 32
        return temp_c
    
    def humidity_indoor(self) -> int:
        """
        Read current indoor humidity
        
        Returns:
            Humidity percentage
        """
        data = self.read_safe(0x3FB, 1)
        if data is None:
            raise IOError("Failed to read indoor humidity")
        
        return (data[0] >> 4) * 10 + (data[0] & 0xF)
    
    def humidity_outdoor(self) -> int:
        """
        Read current outdoor humidity
        
        Returns:
            Humidity percentage
        """
        data = self.read_safe(0x419, 1)
        if data is None:
            raise IOError("Failed to read outdoor humidity")
        
        return (data[0] >> 4) * 10 + (data[0] & 0xF)
    
    def dewpoint(self, temperature_conv: int = CELSIUS) -> float:
        """
        Read dewpoint temperature
        
        Args:
            temperature_conv: CELSIUS or FAHRENHEIT
            
        Returns:
            Dewpoint in specified units
        """
        data = self.read_safe(0x3CE, 2)
        if data is None:
            raise IOError("Failed to read dewpoint")
        
        temp_c = (((data[1] >> 4) * 10 + (data[1] & 0xF) +
                   (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0)
        
        if temperature_conv == FAHRENHEIT:
            return temp_c * 9 / 5 + 32
        return temp_c
    
    def rel_pressure(self, pressure_conv_factor: float = 1.0) -> float:
        """
        Read relative pressure
        
        Args:
            pressure_conv_factor: Conversion factor
            
        Returns:
            Pressure in specified units
        """
        # Address 0x5E2 for relative pressure (not 0x5D8!)
        data = self.read_safe(0x5E2, 3)
        if data is None:
            raise IOError("Failed to read pressure")
        
        pressure = ((data[2] & 0xF) * 1000 + (data[1] >> 4) * 100 +
                    (data[1] & 0xF) * 10 + (data[0] >> 4) +
                    (data[0] & 0xF) / 10.0)
        
        return pressure / pressure_conv_factor
    
    def tendency_forecast(self) -> Tuple[str, str]:
        """
        Read tendency and forecast
        
        Returns:
            Tuple of (tendency string, forecast string)
        """
        data = self.read_safe(0x26B, 1)
        if data is None:
            raise IOError("Failed to read tendency/forecast")
        
        tendencies = ["Steady", "Rising", "Falling"]
        forecasts = ["Rainy", "Cloudy", "Sunny"]
        
        tendency_val = data[0] >> 4
        forecast_val = data[0] & 0xF
        
        tendency = tendencies[tendency_val] if tendency_val < 3 else "Unknown"
        forecast = forecasts[forecast_val] if forecast_val < 3 else "Unknown"
        
        return tendency, forecast
    
    def ws_time_local(self) -> Timestamp:
        """
        Read weather station's local time (DCF77-synchronized)
        
        Returns:
            Timestamp object with weather station's current local time
        """
        # Read local time (second, minute, hour) from 0x239
        time_data = self.read_safe(0x239, 3)
        if time_data is None:
            raise IOError("Failed to read weather station local time")
        
        # Read local date (day, month, year) from 0x240
        date_data = self.read_safe(0x240, 3)
        if date_data is None:
            raise IOError("Failed to read weather station local date")
        
        # Decode BCD time/date from weather station
        timestamp = Timestamp()
        # time_data[0] is seconds (not stored in Timestamp struct)
        timestamp.minute = ((time_data[1] >> 4) * 10) + (time_data[1] & 0xF)
        timestamp.hour = ((time_data[2] >> 4) * 10) + (time_data[2] & 0xF)
        timestamp.day = ((date_data[0] >> 4) * 10) + (date_data[0] & 0xF)
        timestamp.month = ((date_data[1] >> 4) * 10) + (date_data[1] & 0xF)
        timestamp.year = 2000 + ((date_data[2] >> 4) * 10) + (date_data[2] & 0xF)
        
        return timestamp
    
    def ws_time_utc_from_station(self) -> Timestamp:
        """
        Read UTC time directly from weather station memory
        
        NOTE: This reads the station's UTC memory (0x200/0x207) which may
              or may not be correctly synchronized. Use ws_time_utc_calculated()
              for a more reliable UTC based on DCF77 local time + config offset.
        
        Returns:
            Timestamp object with station's UTC time
        """
        # Read UTC time (second, minute, hour) from 0x200
        time_data = self.read_safe(0x200, 3)
        if time_data is None:
            raise IOError("Failed to read weather station UTC time")
        
        # Read UTC date (day, month, year) from 0x207
        date_data = self.read_safe(0x207, 3)
        if date_data is None:
            raise IOError("Failed to read weather station UTC date")
        
        # Decode BCD time/date from weather station
        timestamp = Timestamp()
        # time_data[0] is seconds (not stored in Timestamp struct)
        timestamp.minute = ((time_data[1] >> 4) * 10) + (time_data[1] & 0xF)
        timestamp.hour = ((time_data[2] >> 4) * 10) + (time_data[2] & 0xF)
        timestamp.day = ((date_data[0] >> 4) * 10) + (date_data[0] & 0xF)
        timestamp.month = ((date_data[1] >> 4) * 10) + (date_data[1] & 0xF)
        timestamp.year = 2000 + ((date_data[2] >> 4) * 10) + (date_data[2] & 0xF)
        
        return timestamp
    
    def ws_time_utc_calculated(self, timezone_offset: float) -> Timestamp:
        """
        Calculate UTC time from local time using timezone offset
        
        NOTE: This calculates UTC from the DCF77-synchronized local time
              using the timezone offset from the config file. This is more
              reliable than reading station UTC if the station's timezone
              setting is incorrect.
        
        Args:
            timezone_offset: Hours relative to UTC (e.g., 1.0 for UTC+1,
                           positive for east, negative for west)
        
        Returns:
            Timestamp object with calculated UTC time
        """
        from datetime import datetime, timedelta
        
        # First read local time (DCF77-synchronized, reliable)
        local_time = self.ws_time_local()
        
        # Convert to datetime for easier calculation
        try:
            local_dt = datetime(local_time.year, local_time.month, local_time.day,
                              local_time.hour, local_time.minute)
        except ValueError:
            raise IOError(f"Invalid local time from station: {local_time.year}-{local_time.month}-{local_time.day} {local_time.hour}:{local_time.minute}")
        
        # Calculate UTC by subtracting timezone offset
        utc_dt = local_dt - timedelta(hours=timezone_offset)
        
        # Create UTC timestamp
        utc_timestamp = Timestamp()
        utc_timestamp.year = utc_dt.year
        utc_timestamp.month = utc_dt.month
        utc_timestamp.day = utc_dt.day
        utc_timestamp.hour = utc_dt.hour
        utc_timestamp.minute = utc_dt.minute
        
        return utc_timestamp
    
    def ws_timezone_offset_from_station(self) -> float:
        """
        Calculate timezone offset by comparing station's local and UTC times
        
        Returns the timezone offset in hours (e.g., 1.0 for UTC+1) based on
        the difference between the station's local time and UTC time.
        
        Returns:
            Timezone offset in hours (positive for east of UTC)
        """
        from datetime import datetime, timedelta
        
        # Read both local and UTC times
        local_time = self.ws_time_local()
        utc_time = self.ws_time_utc_from_station()
        
        # Convert to datetime for easier calculation
        try:
            local_dt = datetime(local_time.year, local_time.month, local_time.day,
                              local_time.hour, local_time.minute)
            utc_dt = datetime(utc_time.year, utc_time.month, utc_time.day,
                            utc_time.hour, utc_time.minute)
        except ValueError:
            raise IOError("Invalid time values from station")
        
        # Calculate difference
        diff = local_dt - utc_dt
        
        # Convert to hours
        hours_diff = diff.total_seconds() / 3600.0
        
        # Round to nearest 0.5 (for half-hour timezones)
        hours_diff = round(hours_diff * 2) / 2
        
        return hours_diff
    
    def ws_dcf77_sync_status(self, timezone_offset: float) -> int:
        """
        Read DCF77 synchronization status from station register
        
        NOTE: Address 0x020 contains alarm active flags, with bit 2 marked
              as "Time?" in the memory map. This bit appears to indicate
              DCF77 synchronization status based on the station's display icon.
        
        Args:
            timezone_offset: Hours relative to UTC (unused, kept for API compatibility)
        
        Returns:
            1 if synced (bit 2 set), 0 if not synced (bit 2 clear), -1 if error
        """
        # Read status register at address 0x020
        data = self.read_safe(0x020, 1)
        if data is None:
            return -1  # Error reading
        
        # Check bit 2 (Time? bit) - this appears to indicate DCF77 sync status
        # Bit 2 = 1 means synced, Bit 2 = 0 means not synced
        sync_bit = (data[0] >> 2) & 0x01
        
        return sync_bit
    
    def ws_connection_type(self) -> int:
        """
        Read connection type from weather station
        
        Address: 0x54D
        Values: 0x0 = Cable, 0x3 = Lost, 0xF = Wireless
        
        Returns:
            Connection type (0=Cable, 3=Lost, 15=Wireless), -1 if error
        """
        # Read connection type register at address 0x54D
        data = self.read_safe(0x54D, 1)
        if data is None:
            return -1  # Error reading
        
        return int(data[0])
    
    def temperature_indoor_minmax(self, temperature_conv: int = CELSIUS) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read indoor temperature min/max with timestamps
        
        Args:
            temperature_conv: Temperature conversion (CELSIUS or FAHRENHEIT)
            
        Returns:
            Tuple of (temp_min, temp_max, time_min, time_max)
        """
        data = self.read_safe(0x34B, 15)
        if data is None:
            raise IOError("Failed to read indoor temperature min/max")
        
        temp_min = ((data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                    (data[0] & 0xF) / 100.0) - 30.0
        temp_max = ((data[4] & 0xF) * 10 + (data[3] >> 4) + (data[3] & 0xF) / 10.0 +
                    (data[2] >> 4) / 100.0) - 30.0
        
        if temperature_conv == FAHRENHEIT:
            temp_min = temp_min * 9 / 5 + 32
            temp_max = temp_max * 9 / 5 + 32
        
        time_min = Timestamp()
        time_min.minute = ((data[5] & 0xF) * 10) + (data[4] >> 4)
        time_min.hour = ((data[6] & 0xF) * 10) + (data[5] >> 4)
        time_min.day = ((data[7] & 0xF) * 10) + (data[6] >> 4)
        time_min.month = ((data[8] & 0xF) * 10) + (data[7] >> 4)
        time_min.year = 2000 + ((data[9] & 0xF) * 10) + (data[8] >> 4)
        
        time_max = Timestamp()
        time_max.minute = ((data[10] & 0xF) * 10) + (data[9] >> 4)
        time_max.hour = ((data[11] & 0xF) * 10) + (data[10] >> 4)
        time_max.day = ((data[12] & 0xF) * 10) + (data[11] >> 4)
        time_max.month = ((data[13] & 0xF) * 10) + (data[12] >> 4)
        time_max.year = 2000 + ((data[14] & 0xF) * 10) + (data[13] >> 4)
        
        return temp_min, temp_max, time_min, time_max
    
    def temperature_outdoor_minmax(self, temperature_conv: int = CELSIUS) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read outdoor temperature min/max with timestamps
        
        Args:
            temperature_conv: Temperature conversion (CELSIUS or FAHRENHEIT)
            
        Returns:
            Tuple of (temp_min, temp_max, time_min, time_max)
        """
        data = self.read_safe(0x378, 15)
        if data is None:
            raise IOError("Failed to read outdoor temperature min/max")
        
        temp_min = ((data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                    (data[0] & 0xF) / 100.0) - 30.0
        temp_max = ((data[4] & 0xF) * 10 + (data[3] >> 4) + (data[3] & 0xF) / 10.0 +
                    (data[2] >> 4) / 100.0) - 30.0
        
        if temperature_conv == FAHRENHEIT:
            temp_min = temp_min * 9 / 5 + 32
            temp_max = temp_max * 9 / 5 + 32
        
        time_min = Timestamp()
        time_min.minute = ((data[5] & 0xF) * 10) + (data[4] >> 4)
        time_min.hour = ((data[6] & 0xF) * 10) + (data[5] >> 4)
        time_min.day = ((data[7] & 0xF) * 10) + (data[6] >> 4)
        time_min.month = ((data[8] & 0xF) * 10) + (data[7] >> 4)
        time_min.year = 2000 + ((data[9] & 0xF) * 10) + (data[8] >> 4)
        
        time_max = Timestamp()
        time_max.minute = ((data[10] & 0xF) * 10) + (data[9] >> 4)
        time_max.hour = ((data[11] & 0xF) * 10) + (data[10] >> 4)
        time_max.day = ((data[12] & 0xF) * 10) + (data[11] >> 4)
        time_max.month = ((data[13] & 0xF) * 10) + (data[12] >> 4)
        time_max.year = 2000 + ((data[14] & 0xF) * 10) + (data[13] >> 4)
        
        return temp_min, temp_max, time_min, time_max
    
    def dewpoint_minmax(self, temperature_conv: int = CELSIUS) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read dewpoint min/max with timestamps
        
        Args:
            temperature_conv: Temperature conversion (CELSIUS or FAHRENHEIT)
            
        Returns:
            Tuple of (dewpoint_min, dewpoint_max, time_min, time_max)
        """
        data = self.read_safe(0x3D3, 15)
        if data is None:
            raise IOError("Failed to read dewpoint min/max")
        
        dp_min = ((data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                  (data[0] & 0xF) / 100.0) - 30.0
        dp_max = ((data[4] & 0xF) * 10 + (data[3] >> 4) + (data[3] & 0xF) / 10.0 +
                  (data[2] >> 4) / 100.0) - 30.0
        
        if temperature_conv == FAHRENHEIT:
            dp_min = dp_min * 9 / 5 + 32
            dp_max = dp_max * 9 / 5 + 32
        
        time_min = Timestamp()
        time_min.minute = ((data[5] & 0xF) * 10) + (data[4] >> 4)
        time_min.hour = ((data[6] & 0xF) * 10) + (data[5] >> 4)
        time_min.day = ((data[7] & 0xF) * 10) + (data[6] >> 4)
        time_min.month = ((data[8] & 0xF) * 10) + (data[7] >> 4)
        time_min.year = 2000 + ((data[9] & 0xF) * 10) + (data[8] >> 4)
        
        time_max = Timestamp()
        time_max.minute = ((data[10] & 0xF) * 10) + (data[9] >> 4)
        time_max.hour = ((data[11] & 0xF) * 10) + (data[10] >> 4)
        time_max.day = ((data[12] & 0xF) * 10) + (data[11] >> 4)
        time_max.month = ((data[13] & 0xF) * 10) + (data[12] >> 4)
        time_max.year = 2000 + ((data[14] & 0xF) * 10) + (data[13] >> 4)
        
        return dp_min, dp_max, time_min, time_max
    
    def humidity_indoor_all(self) -> Tuple[int, int, int, Timestamp, Timestamp]:
        """
        Read indoor humidity current, min, max with timestamps
        
        Returns:
            Tuple of (humidity_current, humidity_min, humidity_max, time_min, time_max)
        """
        data = self.read_safe(0x3FB, 13)
        if data is None:
            raise IOError("Failed to read indoor humidity all")
        
        humidity_current = (data[0] >> 4) * 10 + (data[0] & 0xF)
        humidity_min = (data[1] >> 4) * 10 + (data[1] & 0xF)
        humidity_max = (data[2] >> 4) * 10 + (data[2] & 0xF)
        
        time_min = Timestamp()
        time_min.minute = ((data[3] >> 4) * 10) + (data[3] & 0xF)
        time_min.hour = ((data[4] >> 4) * 10) + (data[4] & 0xF)
        time_min.day = ((data[5] >> 4) * 10) + (data[5] & 0xF)
        time_min.month = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_min.year = 2000 + ((data[7] >> 4) * 10) + (data[7] & 0xF)
        
        time_max = Timestamp()
        time_max.minute = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_max.hour = ((data[9] >> 4) * 10) + (data[9] & 0xF)
        time_max.day = ((data[10] >> 4) * 10) + (data[10] & 0xF)
        time_max.month = ((data[11] >> 4) * 10) + (data[11] & 0xF)
        time_max.year = 2000 + ((data[12] >> 4) * 10) + (data[12] & 0xF)
        
        return humidity_current, humidity_min, humidity_max, time_min, time_max
    
    def humidity_outdoor_all(self) -> Tuple[int, int, int, Timestamp, Timestamp]:
        """
        Read outdoor humidity current, min, max with timestamps
        
        Returns:
            Tuple of (humidity_current, humidity_min, humidity_max, time_min, time_max)
        """
        data = self.read_safe(0x419, 13)
        if data is None:
            raise IOError("Failed to read outdoor humidity all")
        
        humidity_current = (data[0] >> 4) * 10 + (data[0] & 0xF)
        humidity_min = (data[1] >> 4) * 10 + (data[1] & 0xF)
        humidity_max = (data[2] >> 4) * 10 + (data[2] & 0xF)
        
        time_min = Timestamp()
        time_min.minute = ((data[3] >> 4) * 10) + (data[3] & 0xF)
        time_min.hour = ((data[4] >> 4) * 10) + (data[4] & 0xF)
        time_min.day = ((data[5] >> 4) * 10) + (data[5] & 0xF)
        time_min.month = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_min.year = 2000 + ((data[7] >> 4) * 10) + (data[7] & 0xF)
        
        time_max = Timestamp()
        time_max.minute = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_max.hour = ((data[9] >> 4) * 10) + (data[9] & 0xF)
        time_max.day = ((data[10] >> 4) * 10) + (data[10] & 0xF)
        time_max.month = ((data[11] >> 4) * 10) + (data[11] & 0xF)
        time_max.year = 2000 + ((data[12] >> 4) * 10) + (data[12] & 0xF)
        
        return humidity_current, humidity_min, humidity_max, time_min, time_max

    
    def wind_all(self, wind_speed_conv_factor: float = 1.0) -> Tuple[float, int, list]:
        """
        Read wind speed, direction index, and last 6 directions
        
        Args:
            wind_speed_conv_factor: Wind speed conversion factor
            
        Returns:
            Tuple of (wind_speed, direction_index, direction_degrees_list)
        """
        for i in range(MAXWINDRETRIES):
            data = self.read_safe(0x527, 6)
            if data is None:
                raise IOError("Failed to read wind data")
            
            # Check for invalid wind data
            if (data[0] != 0x00 or 
                (data[1] == 0xFF and ((data[2] & 0xF) == 0 or (data[2] & 0xF) == 1))):
                if i < MAXWINDRETRIES - 1:
                    time.sleep(10)  # Wait 10 seconds for new wind measurement
                    continue
                else:
                    raise IOError("Invalid wind data after max retries")
            else:
                break
        
        # Calculate wind directions
        winddir_index = (data[2] >> 4)
        winddir = [
            (data[2] >> 4) * 22.5,  # Current direction
            (data[3] & 0xF) * 22.5,  # -1
            (data[3] >> 4) * 22.5,   # -2
            (data[4] & 0xF) * 22.5,  # -3
            (data[4] >> 4) * 22.5,   # -4
            (data[5] & 0xF) * 22.5   # -5
        ]
        
        # Calculate raw wind speed - convert from m/s to whatever
        wind_speed = (((data[2] & 0xF) << 8) + data[1]) / 10.0 * wind_speed_conv_factor
        
        return wind_speed, winddir_index, winddir
    
    def windchill(self, temperature_conv: int = CELSIUS) -> float:
        """
        Read windchill temperature
        
        Args:
            temperature_conv: Temperature conversion (CELSIUS or FAHRENHEIT)
            
        Returns:
            Windchill temperature in specified units
        """
        data = self.read_safe(0x3A0, 2)
        if data is None:
            raise IOError("Failed to read windchill")
        
        wc_c = ((data[1] >> 4) * 10 + (data[1] & 0xF) +
                (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0
        
        if temperature_conv == FAHRENHEIT:
            return wc_c * 9 / 5 + 32
        return wc_c
    
    def windchill_minmax(self, temperature_conv: int = CELSIUS) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read windchill min/max with timestamps
        
        Args:
            temperature_conv: Temperature conversion (CELSIUS or FAHRENHEIT)
            
        Returns:
            Tuple of (wc_min, wc_max, time_min, time_max)
        """
        data = self.read_safe(0x3A5, 15)
        if data is None:
            raise IOError("Failed to read windchill min/max")
        
        wc_min = ((data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                  (data[0] & 0xF) / 100.0) - 30.0
        wc_max = ((data[4] & 0xF) * 10 + (data[3] >> 4) + (data[3] & 0xF) / 10.0 +
                  (data[2] >> 4) / 100.0) - 30.0
        
        if temperature_conv == FAHRENHEIT:
            wc_min = wc_min * 9 / 5 + 32
            wc_max = wc_max * 9 / 5 + 32
        
        time_min = Timestamp()
        time_min.minute = ((data[5] & 0xF) * 10) + (data[4] >> 4)
        time_min.hour = ((data[6] & 0xF) * 10) + (data[5] >> 4)
        time_min.day = ((data[7] & 0xF) * 10) + (data[6] >> 4)
        time_min.month = ((data[8] & 0xF) * 10) + (data[7] >> 4)
        time_min.year = 2000 + ((data[9] & 0xF) * 10) + (data[8] >> 4)
        
        time_max = Timestamp()
        time_max.minute = ((data[10] & 0xF) * 10) + (data[9] >> 4)
        time_max.hour = ((data[11] & 0xF) * 10) + (data[10] >> 4)
        time_max.day = ((data[12] & 0xF) * 10) + (data[11] >> 4)
        time_max.month = ((data[13] & 0xF) * 10) + (data[12] >> 4)
        time_max.year = 2000 + ((data[14] & 0xF) * 10) + (data[13] >> 4)
        
        return wc_min, wc_max, time_min, time_max
    
    def wind_minmax(self, wind_speed_conv_factor: float = 1.0) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read wind speed min/max with timestamps
        
        Args:
            wind_speed_conv_factor: Wind speed conversion factor
            
        Returns:
            Tuple of (wind_min, wind_max, time_min, time_max)
        """
        data = self.read_safe(0x4EE, 15)
        if data is None:
            raise IOError("Failed to read wind min/max")
        
        wind_min = (data[1] * 256 + data[0]) / 360.0 * wind_speed_conv_factor
        wind_max = (data[4] * 256 + data[3]) / 360.0 * wind_speed_conv_factor
        
        time_min = Timestamp()
        time_min.minute = ((data[5] >> 4) * 10) + (data[5] & 0xF)
        time_min.hour = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_min.day = ((data[7] >> 4) * 10) + (data[7] & 0xF)
        time_min.month = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_min.year = 2000 + ((data[9] >> 4) * 10) + (data[9] & 0xF)
        
        time_max = Timestamp()
        time_max.minute = ((data[10] >> 4) * 10) + (data[10] & 0xF)
        time_max.hour = ((data[11] >> 4) * 10) + (data[11] & 0xF)
        time_max.day = ((data[12] >> 4) * 10) + (data[12] & 0xF)
        time_max.month = ((data[13] >> 4) * 10) + (data[13] & 0xF)
        time_max.year = 2000 + ((data[14] >> 4) * 10) + (data[14] & 0xF)
        
        return wind_min, wind_max, time_min, time_max
    
    def rain_1h_all(self, rain_conv_factor: float = 1.0) -> Tuple[float, float, Timestamp]:
        """
        Read rain 1h current and max with timestamp
        
        Args:
            rain_conv_factor: Rain conversion factor
            
        Returns:
            Tuple of (rain_1h, rain_1h_max, time_max)
        """
        data = self.read_safe(0x4B4, 11)
        if data is None:
            raise IOError("Failed to read rain 1h data")
        
        rain_1h = ((data[2] >> 4) * 1000 + (data[2] & 0xF) * 100 +
                   (data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                   (data[0] & 0xF) / 100.0) / rain_conv_factor
        
        rain_1h_max = ((data[5] >> 4) * 1000 + (data[5] & 0xF) * 100 +
                       (data[4] >> 4) * 10 + (data[4] & 0xF) + (data[3] >> 4) / 10.0 +
                       (data[3] & 0xF) / 100.0) / rain_conv_factor
        
        time_max = Timestamp()
        time_max.minute = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_max.hour = ((data[7] >> 4) * 10) + (data[7] & 0xF)
        time_max.day = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_max.month = ((data[9] >> 4) * 10) + (data[9] & 0xF)
        time_max.year = 2000 + ((data[10] >> 4) * 10) + (data[10] & 0xF)
        
        return rain_1h, rain_1h_max, time_max
    
    def rain_24h_all(self, rain_conv_factor: float = 1.0) -> Tuple[float, float, Timestamp]:
        """
        Read rain 24h current and max with timestamp
        
        Args:
            rain_conv_factor: Rain conversion factor
            
        Returns:
            Tuple of (rain_24h, rain_24h_max, time_max)
        """
        data = self.read_safe(0x497, 11)
        if data is None:
            raise IOError("Failed to read rain 24h data")
        
        rain_24h = ((data[2] >> 4) * 1000 + (data[2] & 0xF) * 100 +
                    (data[1] >> 4) * 10 + (data[1] & 0xF) + (data[0] >> 4) / 10.0 +
                    (data[0] & 0xF) / 100.0) / rain_conv_factor
        
        rain_24h_max = ((data[5] >> 4) * 1000 + (data[5] & 0xF) * 100 +
                        (data[4] >> 4) * 10 + (data[4] & 0xF) + (data[3] >> 4) / 10.0 +
                        (data[3] & 0xF) / 100.0) / rain_conv_factor
        
        time_max = Timestamp()
        time_max.minute = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_max.hour = ((data[7] >> 4) * 10) + (data[7] & 0xF)
        time_max.day = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_max.month = ((data[9] >> 4) * 10) + (data[9] & 0xF)
        time_max.year = 2000 + ((data[10] >> 4) * 10) + (data[10] & 0xF)
        
        return rain_24h, rain_24h_max, time_max
    
    def rain_total_all(self, rain_conv_factor: float = 1.0) -> Tuple[float, Timestamp]:
        """
        Read rain total with timestamp since last reset
        
        Args:
            rain_conv_factor: Rain conversion factor
            
        Returns:
            Tuple of (rain_total, time_since)
        """
        data = self.read_safe(0x4D2, 8)
        if data is None:
            raise IOError("Failed to read rain total data")
        
        rain_total = ((data[2] >> 4) * 1000 + (data[2] & 0xF) * 100 +
                      (data[1] >> 4) * 10 + (data[1] & 0xF) +
                      (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) / rain_conv_factor
        
        time_since = Timestamp()
        time_since.minute = ((data[3] >> 4) * 10) + (data[3] & 0xF)
        time_since.hour = ((data[4] >> 4) * 10) + (data[4] & 0xF)
        time_since.day = ((data[5] >> 4) * 10) + (data[5] & 0xF)
        time_since.month = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_since.year = 2000 + ((data[7] >> 4) * 10) + (data[7] & 0xF)
        
        return rain_total, time_since
    
    def rel_pressure_minmax(self, pressure_conv_factor: float = 1.0) -> Tuple[float, float, Timestamp, Timestamp]:
        """
        Read relative pressure min/max with timestamps
        
        Args:
            pressure_conv_factor: Pressure conversion factor
            
        Returns:
            Tuple of (pres_min, pres_max, time_min, time_max)
        """
        # Read min/max pressure values
        data = self.read_safe(0x600, 13)
        if data is None:
            raise IOError("Failed to read pressure min/max")
        
        pres_min = ((data[2] & 0xF) * 1000 + (data[1] >> 4) * 100 +
                    (data[1] & 0xF) * 10 + (data[0] >> 4) +
                    (data[0] & 0xF) / 10.0) / pressure_conv_factor
        
        pres_max = ((data[12] & 0xF) * 1000 + (data[11] >> 4) * 100 +
                    (data[11] & 0xF) * 10 + (data[10] >> 4) +
                    (data[10] & 0xF) / 10.0) / pressure_conv_factor
        
        # Read timestamps
        data = self.read_safe(0x61E, 10)
        if data is None:
            raise IOError("Failed to read pressure min/max timestamps")
        
        time_min = Timestamp()
        time_min.minute = ((data[0] >> 4) * 10) + (data[0] & 0xF)
        time_min.hour = ((data[1] >> 4) * 10) + (data[1] & 0xF)
        time_min.day = ((data[2] >> 4) * 10) + (data[2] & 0xF)
        time_min.month = ((data[3] >> 4) * 10) + (data[3] & 0xF)
        time_min.year = 2000 + ((data[4] >> 4) * 10) + (data[4] & 0xF)
        
        time_max = Timestamp()
        time_max.minute = ((data[5] >> 4) * 10) + (data[5] & 0xF)
        time_max.hour = ((data[6] >> 4) * 10) + (data[6] & 0xF)
        time_max.day = ((data[7] >> 4) * 10) + (data[7] & 0xF)
        time_max.month = ((data[8] >> 4) * 10) + (data[8] & 0xF)
        time_max.year = 2000 + ((data[9] >> 4) * 10) + (data[9] & 0xF)
        
        return pres_min, pres_max, time_min, time_max
