#!/bin/bash
# TransUnion CRA Report Analyzer - Linux launcher
# Same behavior as launch_cra_app.bat on Windows

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv if it exists (full path so it works when launched from app icon)
if [ -d "$SCRIPT_DIR/venv" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python"
else
    # Use absolute path so it works when launched from app icon (minimal PATH)
    PYTHON="/usr/bin/python3"
fi

# Open browser once shortly after Streamlit starts (Streamlit's own browser open is disabled)
(sleep 3 && xdg-open "http://localhost:8501" 2>/dev/null) &

# Run with explicit python; --server.headless true stops Streamlit from opening a second tab
if ! "$PYTHON" -m streamlit run app.py --server.headless true; then
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi
