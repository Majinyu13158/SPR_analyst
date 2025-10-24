@echo off
chcp 65001 >nul
title SPR Analysis
echo ========================================
echo     SPR Analysis v1.0
echo ========================================
echo.
echo 正在启动程序，请稍候...
echo.

".venv\Scripts\python.exe" app_full.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 程序异常退出！
    echo ========================================
    pause
)

