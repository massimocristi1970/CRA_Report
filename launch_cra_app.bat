@echo off
title TransUnion CRA Report Analyzer

cd /d "%~dp0"

set "STREAMLIT_EXE="

if exist ".venv\Scripts\streamlit.exe" (
    set "STREAMLIT_EXE=.venv\Scripts\streamlit.exe"
) else if exist "venv\Scripts\streamlit.exe" (
    set "STREAMLIT_EXE=venv\Scripts\streamlit.exe"
)

if "%STREAMLIT_EXE%"=="" (
    echo Could not find Streamlit in .venv or venv.
    echo Install dependencies first with: pip install -r requirements.txt
    pause
    exit /b 1
)

start "" http://localhost:8501
"%STREAMLIT_EXE%" run app.py
