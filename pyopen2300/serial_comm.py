"""
Serial communication module for WS2300 weather station
Equivalent to linux2300.c in the original C implementation
"""

import serial
import time
import socket
from typing import Optional
from .constants import BAUDRATE, DEFAULT_SERIAL_DEVICE


class SerialDevice:
    """Handle serial communication with WS2300 weather station"""
    
    def __init__(self, device: str = DEFAULT_SERIAL_DEVICE):
        """
        Initialize serial connection to weather station
        
        Args:
            device: Serial device path (e.g., '/dev/ttyS0')
        """
        self.device = device
        self.ser: Optional[serial.Serial] = None
        self._open()
    
    def _open(self):
        """Open serial port connection"""
        try:
            self.ser = serial.Serial(
                port=self.device,
                baudrate=BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            # Flush any existing data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except serial.SerialException as e:
            raise IOError(f"Cannot open serial device {self.device}: {e}")
    
    def close(self):
        """Close serial port connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def read(self, size: int) -> bytes:
        """
        Read data from serial device
        
        Args:
            size: Number of bytes to read
            
        Returns:
            Bytes read from device
        """
        if not self.ser or not self.ser.is_open:
            raise IOError("Serial device not open")
        
        try:
            data = self.ser.read(size)
            return data
        except serial.SerialException as e:
            raise IOError(f"Error reading from serial device: {e}")
    
    def write(self, data: bytes) -> int:
        """
        Write data to serial device
        
        Args:
            data: Bytes to write
            
        Returns:
            Number of bytes written
        """
        if not self.ser or not self.ser.is_open:
            raise IOError("Serial device not open")
        
        try:
            written = self.ser.write(data)
            self.ser.flush()
            return written
        except serial.SerialException as e:
            raise IOError(f"Error writing to serial device: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


def sleep_short(milliseconds: int):
    """
    Sleep for specified milliseconds
    
    Args:
        milliseconds: Time to sleep in milliseconds
    """
    time.sleep(milliseconds / 1000.0)


def sleep_long(seconds: int):
    """
    Sleep for specified seconds
    
    Args:
        seconds: Time to sleep in seconds
    """
    time.sleep(seconds)


def http_request_url(url: str) -> int:
    """
    Make HTTP request to URL
    
    Args:
        url: Full URL to request
        
    Returns:
        0 on success, -1 on failure
    """
    import urllib.request
    import urllib.error
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            response.read()
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"HTTP request failed: {e}")
        return -1


def citizen_weather_send(config, datastring: str) -> int:
    """
    Send data to APRS/CWOP servers
    
    Args:
        config: Configuration object with APRS host settings
        datastring: Data string to send
        
    Returns:
        0 on success, -1 on failure
    """
    # Try each APRS host in order
    for aprs_host in config.aprs_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((aprs_host.name, aprs_host.port))
            
            # Send login and data
            sock.sendall(datastring.encode('ascii'))
            
            sock.close()
            return 0
        except (socket.error, socket.timeout) as e:
            print(f"Failed to connect to {aprs_host.name}:{aprs_host.port}: {e}")
            continue
    
    return -1

