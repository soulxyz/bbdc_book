@echo off
chcp 65001 >nul
title 不背单词单词本制作工具 - 演示

echo.
echo ========================================
echo    📚 不背单词单词本制作工具 - 演示
echo ========================================
echo.

python demo.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 演示程序运行出错
    echo.
    pause
)
