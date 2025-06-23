#!/bin/bash

# Open all HTML pages in Skerritt Economics Website
# This script opens all HTML files in separate browser tabs/windows

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Opening all Skerritt Economics Website pages..."

# Array of all HTML files (relative to script directory)
pages=(
    "index.html"
    "about/index.html"
    "case-studies/index.html"
    "contact/index.html"
    "practice-areas/index.html"
    "practice-areas/commercial-disputes/index.html"
    "practice-areas/employment/index.html"
    "practice-areas/medical-malpractice/index.html"
    "practice-areas/personal-injury/index.html"
    "resources/index.html"
    "services/index.html"
    "services/forensic-economics/index.html"
)

# Open each page
for page in "${pages[@]}"; do
    full_path="$SCRIPT_DIR/$page"
    if [[ -f "$full_path" ]]; then
        echo "Opening: $page"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            open "$full_path"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            xdg-open "$full_path"
        elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            # Windows
            start "$full_path"
        fi
        # Small delay to prevent overwhelming the browser
        sleep 0.5
    else
        echo "Warning: File not found - $page"
    fi
done

echo "All pages opened!"