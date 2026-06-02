@echo off
chcp 65001 > nul
title Stock Analysis Platform

echo.
echo  ================================================
echo    Stock Analysis Platform - Starting Servers
echo  ================================================
echo.
echo  Portfolio   : http://localhost:8500
echo  Stock App   : http://localhost:8501
echo.
echo  Close this window to stop all servers.
echo  ------------------------------------------------

start "Portfolio (8500)" /MIN C:\ProgramData\anaconda3\python.exe -m streamlit run portfolio.py --server.port 8500

timeout /t 3 /nobreak > nul

start "StockApp (8501)" /MIN C:\ProgramData\anaconda3\python.exe -m streamlit run app.py --server.port 8501

timeout /t 3 /nobreak > nul
start "" http://localhost:8500

echo.
echo  Both servers are running in the background.
echo.
pause
