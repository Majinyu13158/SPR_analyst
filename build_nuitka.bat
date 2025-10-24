@echo off
chcp 65001 >nul
echo ========================================
echo     Nuitka 打包 SPR Analysis
echo ========================================
echo.
echo 警告: 首次打包需要 20-30 分钟
echo 请耐心等待，不要关闭窗口
echo.
pause

echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo [2/3] 开始打包 (这将需要很长时间)...
echo 开始时间: %time%
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --enable-plugin=pyside6 ^
    --include-package=pyqtgraph ^
    --include-package=numpy ^
    --include-package=pandas ^
    --include-package=scipy ^
    --include-package=openpyxl ^
    --include-package=src ^
    --include-package=XlementFitting ^
    --include-package=custom_widgets ^
    --nofollow-import-to=torch ^
    --nofollow-import-to=tensorflow ^
    --nofollow-import-to=matplotlib ^
    --output-dir=dist_nuitka ^
    --output-filename=SPR_Analysis.exe ^
    app_full.py

echo.
echo [3/3] 完成!
echo 结束时间: %time%
echo.
echo 可执行文件: dist_nuitka\SPR_Analysis.exe
echo.
pause

