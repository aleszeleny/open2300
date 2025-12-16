"""
Weather Station protocol implementation for WS2300
Equivalent to rw2300.c in the original C implementation
"""

from typing import Tuple, Optional
import sys
import time
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
        """
        command = bytes([0x06])
        
        for i in range(100):
            # Discard input buffer
            try:
                self.device.ser.reset_input_buffer()
            except:
                pass
            
            self.device.write(command)
            
            # Read responses until we get a 2
            while True:
                answer = self.device.read(1)
                if len(answer) == 0:
                    break
                if answer[0] == 2:
                    return
            
            # Sleep longer for each retry
            time.sleep(0.05 * i)
        
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
        # Encode address
        commanddata = bytearray(self.address_encoder(address))
        commanddata.append(self.numberof_encoder(number))
        
        # Send 4 address bytes
        for i in range(4):
            if self.device.write(bytes([commanddata[i]])) != 1:
                return None, bytes(commanddata)
            answer = self.device.read(1)
            if len(answer) != 1:
                return None, bytes(commanddata)
            if answer[0] != self.command_check0123(commanddata[i], i):
                return None, bytes(commanddata)
        
        # Send number-of-bytes command
        if self.device.write(bytes([commanddata[4]])) != 1:
            return None, bytes(commanddata)
        answer = self.device.read(1)
        if len(answer) != 1:
            return None, bytes(commanddata)
        if answer[0] != self.command_check4(number):
            return None, bytes(commanddata)
        
        # Read data bytes
        readdata = bytearray()
        for i in range(number):
            data = self.device.read(1)
            if len(data) != 1:
                return None, bytes(commanddata)
            readdata.append(data[0])
        
        # Read and verify checksum
        answer = self.device.read(1)
        if len(answer) != 1:
            return None, bytes(commanddata)
        if answer[0] != self.data_checksum(bytes(readdata), number):
            return None, bytes(commanddata)
        
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
        for j in range(MAXRETRIES):
            self.reset_06()
            data, _ = self.read_data(address, number)
            if data is not None and len(data) == number:
                return data
        
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
        data = self.read_safe(0x346, 2)
        if data is None:
            raise IOError("Failed to read indoor temperature")
        
        temp_c = (((data[1] >> 4) * 10 + (data[1] & 0xF) +
                   (data[0] >> 4) / 10.0 + (data[0] & 0xF) / 100.0) - 30.0)
        
        if temperature_conv == FAHRENHEIT:
            return temp_c * 9 / 5 + 32
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
        data = self.read_safe(0x5D8, 3)
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

