@echo off
chcp 65001 >nul
title 不背单词单词本制作工具 - 快速版

echo.
echo ========================================
echo    📚 不背单词单词本制作工具 - 快速版
echo ========================================
echo.

python fast_gui.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 程序运行出错，请检查Python环境和依赖包
    echo.
    pause
)
