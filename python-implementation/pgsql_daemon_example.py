#!/usr/bin/env python3
"""Compatibility wrapper for the packaged C-compatible reporting daemon."""

from pyopen2300.cli.pgsql2300_daemon import main


if __name__ == '__main__':
    raise SystemExit(main())
