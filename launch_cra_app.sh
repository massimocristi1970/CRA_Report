#!/bin/bash
# TransUnion CRA Report Analyzer - Linux launcher
# Same behavior as launch_cra_app.bat on Windows

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Open browser shortly after Streamlit starts
(sleep 3 && xdg-open "http://localhost:8501" 2>/dev/null) &

streamlit run app.py
