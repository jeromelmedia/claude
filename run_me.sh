#!/bin/bash

echo "========================================"
echo "AI VIDEO GENERATION MACRO"
echo "========================================"
echo ""
echo "This will automatically install dependencies and run the macro."
echo ""

python3 run_video_macro.py

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "ERROR OCCURRED"
    echo "========================================"
    exit 1
fi
