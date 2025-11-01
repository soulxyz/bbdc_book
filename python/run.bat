@echo off
chcp 65001 >nul
echo.
echo 🚀 启动 BBDC Word Tool (Python版)
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    pause
    exit /b 1
)

:: 检查依赖
python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺少依赖，正在安装...
    pip install -r requirements.txt
)

:: 启动程序
python extract_words.py

pause



