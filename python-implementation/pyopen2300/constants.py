"""
Constants used throughout the pyopen2300 package
"""

# Protocol constants
MAXRETRIES = 50
MAXWINDRETRIES = 20
WRITENIB = 0x42
SETBIT = 0x12
UNSETBIT = 0x32
WRITEACK = 0x10
SETACK = 0x04
UNSETACK = 0x0C
RESET_MIN = 0x01
RESET_MAX = 0x02

# Unit conversion factors
METERS_PER_SECOND = 1.0
KILOMETERS_PER_HOUR = 3.6
MILES_PER_HOUR = 2.23693629

# Temperature units
CELSIUS = 0
FAHRENHEIT = 1

# Rain units
MILLIMETERS = 1
INCHES = 25.4

# Pressure units
HECTOPASCAL = 1.0
MILLIBARS = 1.0
INCHES_HG = 33.8638864

# Logging levels
LOG_OFF = 0
LOG_MIN = 1
LOG_MED = 2
LOG_MAX = 3

# Weather Underground settings
WEATHER_UNDERGROUND_BASEURL = "weatherstation.wunderground.com"
WEATHER_UNDERGROUND_PATH = "/weatherstation/updateweatherstation.php"
WEATHER_UNDERGROUND_SOFTWARETYPE = "pyopen2300"

# Maximum APRS hosts
MAX_APRS_HOSTS = 6

# Serial port settings
BAUDRATE = 2400
DEFAULT_SERIAL_DEVICE = "/dev/ttyS0"

# Wind directions
WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]

