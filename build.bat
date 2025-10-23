@echo off
echo ========================================
echo  SPR Analysis 打包脚本
echo ========================================
echo.

REM 检查是否在虚拟环境中
if not defined VIRTUAL_ENV (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
)

echo.
echo [1/4] 安装 PyInstaller...
python -m pip install pyinstaller

echo.
echo [2/4] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] 开始打包...
pyinstaller build_exe.spec

echo.
echo [4/4] 打包完成！
echo.
echo 可执行文件位置: dist\SPR_Analysis.exe
echo.

pause

