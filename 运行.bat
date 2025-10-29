@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo   单词提取工具 - 启动中...
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.6或更高版本
    echo.
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo [提示] 检测到缺少依赖库，正在安装...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败，请手动运行：pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo.
    echo [完成] 依赖库安装成功
    echo.
)

REM 运行程序
python extract_words.py

pause


