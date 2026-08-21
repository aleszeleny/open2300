"""Persistent PostgreSQL sink for the complete WS-2300 weather snapshot."""

import psycopg2
from psycopg2 import sql

from .sql_identifier import table_identifier


class PostgreSQLLogger:
    """Persistent, autocommitted PostgreSQL logger using a server PREPARE."""

    prepared_statement_name = 'open2300_insert_weather'

    def __init__(self, connection_string, table_name, station_name=None,
                 auto_reconnect=True, version='pgsql2300.py 1.11'):
        self.connection_string = connection_string
        self.table_name = table_name
        self.station_name = station_name
        self.auto_reconnect = auto_reconnect
        self.version = version
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.close()
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            types = ', '.join(_PARAMETER_TYPES)
            placeholders = ', '.join(f'${index}' for index in range(1, 52))
            execute_placeholders = ', '.join(['%s'] * 51)
            statement = sql.SQL(f"""
                PREPARE {self.prepared_statement_name} ({types}) AS
                INSERT INTO {{}} (
                      rec_datetime, temperature_indoor, temperature_outdoor,
                      dewpoint, humidity_indoor, humidity_outdoor,
                      wind_speed_min, wind_speed_max, wind_speed_min_datetime,
                      wind_speed_max_datetime, station_datetime, ws_datetime_local,
                      ws_datetime_utc, wind_speed, wind_angle_current,
                      wind_angle_previous_1, wind_angle_previous_2,
                      wind_angle_previous_3, wind_angle_previous_4,
                      wind_angle_previous_5, wind_direction, wind_chill, rain_1h,
                      rain_24h, rain_total, rel_pressure, tendency, forecast,
                      pgsql2300_version
                ) VALUES (
                      now(), {placeholders}
                )
            """).format(table_identifier(self.table_name))
            self.cursor.execute(statement)
            self._execute_placeholders = execute_placeholders
        except Exception as exc:
            self.close()
            raise IOError(f'Failed to connect to PostgreSQL: {exc}') from exc

    def log_snapshot(self, snapshot):
        if not self.cursor or not self.conn or self.conn.closed:
            if self.auto_reconnect:
                self.connect()
            else:
                raise RuntimeError('PostgreSQL logger is not connected')
        values = snapshot.postgres_values(self.version)
        try:
            self.cursor.execute(
                f'EXECUTE {self.prepared_statement_name} ({self._execute_placeholders})',
                values,
            )
        except psycopg2.errors.UndefinedPreparedStatement:
            if not self.auto_reconnect:
                raise
            self.connect()
            self.cursor.execute(
                f'EXECUTE {self.prepared_statement_name} ({self._execute_placeholders})',
                values,
            )
        except psycopg2.Error:
            if not self.auto_reconnect:
                raise
            self.connect()
            self.cursor.execute(
                f'EXECUTE {self.prepared_statement_name} ({self._execute_placeholders})',
                values,
            )

    def close(self):
        if self.cursor:
            try:
                self.cursor.execute(f'DEALLOCATE {self.prepared_statement_name}')
            except Exception:
                pass
            try:
                self.cursor.close()
            except Exception:
                pass
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        self.cursor = None
        self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


PersistentPostgreSQLLogger = PostgreSQLLogger


_PARAMETER_TYPES = (
    'double precision', 'double precision', 'double precision', 'smallint', 'smallint',
    'double precision', 'double precision',
    'integer', 'integer', 'integer', 'integer', 'integer',
    'integer', 'integer', 'integer', 'integer', 'integer',
    'integer', 'integer', 'integer', 'integer', 'integer', 'integer',
    'integer', 'integer', 'integer', 'integer', 'integer', 'integer',
    'integer', 'integer', 'integer', 'integer', 'integer', 'integer',
    'double precision', 'double precision', 'double precision', 'double precision',
    'double precision', 'double precision', 'double precision',
    'text', 'double precision', 'double precision', 'double precision',
    'double precision', 'double precision', 'text', 'text', 'text',
)
