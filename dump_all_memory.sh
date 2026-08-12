#!/bin/bash
# Dump entire WS2300 memory for comparison
# Usage: ./dump_all_memory.sh <output_file> [config_file]

OUTPUT_FILE="${1:-ws2300_memory_dump_$(date +%Y%m%d_%H%M%S).txt}"
CONFIG_FILE="${2:-}"

echo "Dumping entire WS2300 memory to: $OUTPUT_FILE"
echo "This may take a few minutes..."
echo ""

# Use dump2300 to dump entire memory range (0x000 to 0x1FFF in nibbles = 0x0000 to 0x3FFE)
# But dump2300 uses byte addresses, so 0x000 to 0x1FFF bytes = 0x000 to 0x1FFF

if command -v ./dump2300 &> /dev/null; then
    # C version
    if [ -n "$CONFIG_FILE" ]; then
        echo "Note: C dump2300 doesn't support config file parameter"
    fi
    LD_LIBRARY_PATH=. ./dump2300 "$OUTPUT_FILE" 0x000 0x1FFF
elif command -v python3 &> /dev/null && python3 -c "import sys; sys.path.insert(0, 'python-implementation'); from pyopen2300.cli.dump2300 import main" 2>/dev/null; then
    # Python version
    cd python-implementation
    if [ -n "$CONFIG_FILE" ]; then
        python3 -m pyopen2300.cli.dump2300 "$OUTPUT_FILE" 0x000 0x1FFF "$CONFIG_FILE"
    else
        python3 -m pyopen2300.cli.dump2300 "$OUTPUT_FILE" 0x000 0x1FFF
    fi
    cd ..
else
    echo "Error: Neither dump2300 nor Python dump2300 found"
    echo "Please compile dump2300: make dump2300"
    exit 1
fi

echo ""
echo "Memory dump complete: $OUTPUT_FILE"
echo "File size: $(wc -l < "$OUTPUT_FILE") lines"
echo ""
echo "To compare two dumps:"
echo "  diff -u dump1.txt dump2.txt"
echo "  or:"
echo "  vimdiff dump1.txt dump2.txt"

