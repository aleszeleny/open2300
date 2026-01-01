#!/bin/bash
# Test script for fetch2300 with debug output enabled

echo "================================================================"
echo "  fetch2300 Debug Test Script"
echo "================================================================"
echo ""
echo "This will run fetch2300 with WS2300_DEBUG=1 to show detailed"
echo "serial communication and protocol traces."
echo ""
echo "Press Ctrl+C to abort if it hangs."
echo ""
echo "================================================================"
echo ""

# Enable debug output
export WS2300_DEBUG=1

# Set log level to max for fetch2300
export LOG_LEVEL=3

echo "Running: WS2300_DEBUG=1 fetch2300"
echo ""

# Run fetch2300
fetch2300

echo ""
echo "================================================================"
echo "Test complete"
echo "================================================================"

