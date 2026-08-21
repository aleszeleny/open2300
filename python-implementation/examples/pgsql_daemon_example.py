#!/usr/bin/env python3
"""Compatibility wrapper for the packaged C-compatible reporting daemon."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyopen2300.cli.pgsql2300_daemon import main


if __name__ == '__main__':
    raise SystemExit(main())
