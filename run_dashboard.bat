@echo off
chcp 65001 >nul
title AURA-ICU Dashboard Launcher
color 0B
echo.
echo  ====================================================
echo   AURA-ICU: Clinical Decision Support System
echo   D. Y. Patil School of Engineering and Management
echo   (Deemed-to-be-University), Kolhapur
echo  ====================================================
echo.
echo  Starting dashboard... Please wait.
echo  Browser will open automatically at:
echo  http://localhost:8501
echo.
echo  Press Ctrl+C to stop the dashboard.
echo  ====================================================
echo.

cd /d D:\ICU_Mortality_Prediction

streamlit run dashboard\app.py ^
    --server.port 8501 ^
    --server.headless false ^
    --server.fileWatcherType none ^
    --browser.gatherUsageStats false

pause
