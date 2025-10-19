@echo off
echo ========================================
echo   SPR Sensor Analyst - 完整功能版
echo ========================================
echo.

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 找不到Python！
    echo 请确保Python已安装并添加到系统PATH。
    pause
    exit /b 1
)

REM 激活虚拟环境（如果存在）
if exist ".venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境...
    call ".venv\Scripts\activate.bat"
) else (
    echo [信息] 使用系统Python
)

REM 检查依赖
echo [信息] 检查依赖...
python -c "import PySide6" >nul 2>nul
if %errorlevel% neq 0 (
    echo [警告] PySide6未安装，正在安装...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo   启动SPR Sensor Analyst (完整版)
echo ========================================
echo.

REM 运行程序
python app_full.py

echo.
echo ========================================
echo   程序已退出
echo ========================================
pause

