"""
PostgreSQL logger with prepared statements and connection pooling
"""

import psycopg2
from psycopg2 import sql
from datetime import datetime
from typing import Optional


class PostgreSQLLogger:
    """
    PostgreSQL logger optimized for weather station data logging
    
    Features:
    - Autocommit mode for immediate writes
    - Parameterized queries (query plan caching)
    - Connection reuse for multiple inserts
    - Proper cleanup and error handling
    """
    
    def __init__(self, connection_string: str, table_name: str, station_name: str):
        """
        Initialize PostgreSQL logger
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to insert into
            station_name: Name of this weather station
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.station_name = station_name
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self.insert_query = None
        
    def connect(self):
        """
        Connect to database and prepare statement
        
        Raises:
            IOError: If connection fails
        """
        try:
            # Connect with autocommit mode enabled
            # This ensures each INSERT is committed immediately
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            
            self.cursor = self.conn.cursor()
            
            # Create parameterized INSERT query
            # PostgreSQL will cache the execution plan after first use
            self.insert_query = sql.SQL("""
                INSERT INTO {} 
                (timestamp, station, temp_in, temp_out, dewpoint, 
                 humidity_in, humidity_out, wind_speed, wind_direction, pressure)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(sql.Identifier(self.table_name))
            
        except psycopg2.Error as e:
            raise IOError(f"Failed to connect to PostgreSQL: {e}")
    
    def log_data(self, timestamp: datetime, temp_in: float, temp_out: float, 
                 dewpoint: float, humidity_in: int, humidity_out: int,
                 wind_speed: float, wind_direction: float, pressure: float):
        """
        Log weather data using prepared statement
        
        With autocommit enabled, data is written immediately without
        needing explicit commit() calls.
        
        Args:
            timestamp: Datetime of measurement
            temp_in: Indoor temperature
            temp_out: Outdoor temperature
            dewpoint: Dewpoint temperature
            humidity_in: Indoor humidity (%)
            humidity_out: Outdoor humidity (%)
            wind_speed: Wind speed
            wind_direction: Wind direction (degrees)
            pressure: Atmospheric pressure
            
        Raises:
            RuntimeError: If not connected to database
            IOError: If insert fails
        """
        if not self.cursor or not self.insert_query:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        try:
            # Execute with parameters
            # With autocommit enabled, this commits immediately
            self.cursor.execute(self.insert_query, (
                timestamp,
                self.station_name,
                temp_in,
                temp_out,
                dewpoint,
                humidity_in,
                humidity_out,
                wind_speed,
                wind_direction,
                pressure
            ))
            
        except psycopg2.Error as e:
            raise IOError(f"Failed to insert data: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if database connection is active
        
        Returns:
            True if connected and operational
        """
        if not self.conn:
            return False
        try:
            # Test connection with a simple query
            cur = self.conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return True
        except:
            return False
    
    def reconnect(self):
        """
        Reconnect to database if connection was lost
        
        Raises:
            IOError: If reconnection fails
        """
        self.close()
        self.connect()
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            try:
                self.cursor.close()
            except:
                pass
            self.cursor = None
        
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
    
    def __del__(self):
        """Destructor - ensure connection is closed"""
        self.close()


class PersistentPostgreSQLLogger(PostgreSQLLogger):
    """
    PostgreSQL logger that maintains a persistent connection
    
    Useful for long-running processes that log frequently.
    Automatically reconnects if connection is lost.
    """
    
    def __init__(self, connection_string: str, table_name: str, 
                 station_name: str, auto_reconnect: bool = True):
        """
        Initialize persistent logger
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to insert into
            station_name: Name of this weather station
            auto_reconnect: Automatically reconnect on connection loss
        """
        super().__init__(connection_string, table_name, station_name)
        self.auto_reconnect = auto_reconnect
        self.connect()
    
    def log_data(self, timestamp: datetime, temp_in: float, temp_out: float,
                 dewpoint: float, humidity_in: int, humidity_out: int,
                 wind_speed: float, wind_direction: float, pressure: float):
        """
        Log data with automatic reconnection on failure
        
        Args: Same as parent class
        
        Raises:
            IOError: If insert fails after reconnection attempt
        """
        try:
            super().log_data(timestamp, temp_in, temp_out, dewpoint,
                           humidity_in, humidity_out, wind_speed, 
                           wind_direction, pressure)
        except (IOError, psycopg2.Error) as e:
            if self.auto_reconnect:
                # Try to reconnect and retry once
                try:
                    self.reconnect()
                    super().log_data(timestamp, temp_in, temp_out, dewpoint,
                                   humidity_in, humidity_out, wind_speed,
                                   wind_direction, pressure)
                except Exception as retry_error:
                    raise IOError(f"Failed to log data after reconnection: {retry_error}")
            else:
                raise IOError(f"Failed to log data: {e}")

