@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 阶段2修复测试
echo ========================================
echo.

REM 查找Python
set PYTHON_CMD=

REM 尝试 python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :found
)

REM 尝试 py
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :found
)

REM 尝试 python3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :found
)

echo ❌ 错误：找不到Python！
echo 请确保Python已安装并添加到PATH
pause
exit /b 1

:found
echo ✅ 使用Python: %PYTHON_CMD%
echo.

REM 运行测试
echo 正在运行测试...
echo.
%PYTHON_CMD% test_phase2_fixes.py

echo.
echo ========================================
echo 测试完成
echo ========================================
echo.
pause

