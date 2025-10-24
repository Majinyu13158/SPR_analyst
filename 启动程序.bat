@echo off
chcp 65001 >nul
title SPR Analysis
echo ========================================
echo     SPR Analysis 正在启动...
echo ========================================
echo.

REM 检查Python是否存在
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 找不到Python环境！
    echo 请确保 .venv 文件夹完整。
    pause
    exit /b 1
)

echo [信息] 正在启动程序...
echo.

REM 启动程序
".venv\Scripts\python.exe" app_full.py

REM 如果程序异常退出，显示错误
if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出！
    pause
)

