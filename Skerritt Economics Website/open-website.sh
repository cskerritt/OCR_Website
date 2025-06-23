#!/bin/bash

# Open Skerritt Economics Website in default browser
# This script opens the index.html file in your default web browser

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Open index.html in the default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$SCRIPT_DIR/index.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$SCRIPT_DIR/index.html"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start "$SCRIPT_DIR/index.html"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Opening Skerritt Economics Website..."