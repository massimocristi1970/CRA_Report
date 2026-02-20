@echo off
title TransUnion CRA Report Analyzer

cd /d "%~dp0"

call venv\Scripts\activate.bat

streamlit run app.py

start "" http://localhost:8501
streamlit run app.py