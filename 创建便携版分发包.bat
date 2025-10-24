@echo off
chcp 65001 >nul
echo ========================================
echo   创建 SPR Analysis 便携版分发包
echo ========================================
echo.

echo [1/4] 准备输出目录...
if exist "SPR_Analysis_便携版" rmdir /s /q "SPR_Analysis_便携版"
mkdir "SPR_Analysis_便携版"

echo [2/4] 复制程序文件...
xcopy /E /I /Y ".venv" "SPR_Analysis_便携版\.venv" >nul
copy /Y "app_full.py" "SPR_Analysis_便携版\" >nul
copy /Y "config.py" "SPR_Analysis_便携版\" >nul
copy /Y "启动程序.bat" "SPR_Analysis_便携版\" >nul
copy /Y "便携版使用说明.txt" "SPR_Analysis_便携版\使用说明.txt" >nul
xcopy /E /I /Y "src" "SPR_Analysis_便携版\src" >nul
xcopy /E /I /Y "XlementFitting" "SPR_Analysis_便携版\XlementFitting" >nul
xcopy /E /I /Y "custom_widgets" "SPR_Analysis_便携版\custom_widgets" >nul

echo [3/4] 创建exports文件夹...
mkdir "SPR_Analysis_便携版\exports" >nul 2>&1
mkdir "SPR_Analysis_便携版\sessions" >nul 2>&1

echo [4/4] 压缩打包...
powershell -Command "Compress-Archive -Path 'SPR_Analysis_便携版' -DestinationPath 'SPR_Analysis_v1.0_便携版.zip' -Force"

echo.
echo ========================================
echo   完成！
echo ========================================
echo.
echo 分发文件: SPR_Analysis_v1.0_便携版.zip
echo 文件大小: 
powershell -Command "Get-Item 'SPR_Analysis_v1.0_便携版.zip' | Select-Object @{N='Size_MB';E={[math]::Round($_.Length/1MB,0)}}"
echo.
echo 用户使用方法:
echo 1. 解压zip文件
echo 2. 双击 "启动程序.bat"
echo 3. 开始使用
echo.
pause

