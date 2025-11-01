@echo off
chcp 65001 >nul
echo.
echo 🎨 启动 BBDC Word Tool GUI (Python版)
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    pause
    exit /b 1
)

:: 检查依赖
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到tkinter（GUI库）
    echo 请重新安装Python并确保勾选tkinter组件
    pause
    exit /b 1
)

python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺少依赖，正在安装...
    pip install -r requirements.txt
)

:: 启动GUI
python fast_gui.py



