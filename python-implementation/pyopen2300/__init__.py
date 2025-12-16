"""
PyOpen2300 - Python implementation of open2300 weather station tools
Version 1.11

Control WS2300 weather station from Python

Copyright 2003-2006, Kenneth Lavrsen (original C implementation)
Python reimplementation 2025
This program is published under the GNU General Public License version 2.0
"""

__version__ = "1.11"
__author__ = "Kenneth Lavrsen (C), Python port 2025"

from .config import Config
from .weatherstation import WeatherStation
from .constants import *

__all__ = [
    'Config',
    'WeatherStation',
    '__version__'
]

