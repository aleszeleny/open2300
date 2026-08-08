#!/usr/bin/env python3
"""
Setup script for pyopen2300
"""

from setuptools import setup, find_packages
import os

# Read README
readme_file = "README-PYTHON.md"
if os.path.exists(readme_file):
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "Python implementation of open2300 weather station tools"

setup(
    name='pyopen2300',
    version='1.11',
    description='Python tools for WS-2300 weather station',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Kenneth Lavrsen (C), Python port 2025',
    url='https://github.com/lavrsen/open2300',
    license='GPL-2.0-or-later',
    
    packages=find_packages(),
    python_requires='>=3.6',
    
    install_requires=[
        'pyserial>=3.4',  # Compatible with older systems including RPi2
        'psycopg2-binary>=2.9.0',
    ],
    
    extras_require={
        'postgresql': ['psycopg2-binary>=2.9.0'],
    },
    
    entry_points={
        'console_scripts': [
            'open2300=pyopen2300.cli.open2300:main',
            'dump2300=pyopen2300.cli.dump2300:main',
            'bin2300=pyopen2300.cli.bin2300:main',
            'fetch2300=pyopen2300.cli.fetch2300:main',
            'log2300=pyopen2300.cli.log2300:main',
            'light2300=pyopen2300.cli.light2300:main',
            'xml2300=pyopen2300.cli.xml2300:main',
            'wu2300=pyopen2300.cli.wu2300:main',
            'pgsql2300=pyopen2300.cli.pgsql2300:main',
            'sqlitelog2300=pyopen2300.cli.sqlitelog2300:main',
            'minmax2300=pyopen2300.cli.minmax2300:main',
            'interval2300=pyopen2300.cli.interval2300:main',
            'history2300=pyopen2300.cli.history2300:main',
            'histlog2300=pyopen2300.cli.histlog2300:main',
            'dumpconfig2300=pyopen2300.cli.dumpconfig2300:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Home Automation',
        'Environment :: Console',
    ],
    
    keywords='weather station ws2300 lacrosse',
)
