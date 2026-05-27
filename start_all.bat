@echo off
title 주식 분석 플랫폼
chcp 65001 > nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   📈  주식 분석 플랫폼  서버 시작       ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  🗂  포트폴리오   → http://localhost:8500
echo  💻 PC 버전      → http://localhost:8501
echo  📱 모바일 버전   → http://localhost:8502
echo.
echo  종료하려면 이 창을 닫아 주세요.
echo  ------------------------------------------

REM 포트폴리오 페이지 시작
start "🗂 포트폴리오 (8500)" /MIN C:\ProgramData\anaconda3\python.exe -m streamlit run portfolio.py --server.port 8500

REM 3초 대기 후 PC 버전 시작
timeout /t 3 /nobreak > nul
start "📈 PC 버전 (8501)" /MIN C:\ProgramData\anaconda3\python.exe -m streamlit run app.py --server.port 8501

REM 3초 대기 후 모바일 버전 시작
timeout /t 3 /nobreak > nul
start "📱 모바일 버전 (8502)" /MIN C:\ProgramData\anaconda3\python.exe -m streamlit run app_mobile.py --server.port 8502

REM 3초 대기 후 포트폴리오 브라우저 열기
timeout /t 3 /nobreak > nul
start "" http://localhost:8500

echo.
echo  ✅ 세 서버가 백그라운드에서 실행 중입니다.
echo  브라우저가 자동으로 열립니다.
echo.
pause
