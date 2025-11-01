@echo off
chcp 65001 >nul
echo.
echo 🚀 启动 BBDC Word Tool (Rust版)
echo.

:: 检查可执行文件
if exist "target\release\bbdc_word_tool.exe" (
    echo ✅ 使用 Release 版本
    target\release\bbdc_word_tool.exe
) else if exist "target\debug\bbdc_word_tool.exe" (
    echo ⚠️  使用 Debug 版本（未优化）
    echo 💡 运行 build.bat 构建优化版本
    target\debug\bbdc_word_tool.exe
) else (
    echo ❌ 错误: 未找到可执行文件
    echo.
    echo 请先运行 build.bat 构建程序
    pause
    exit /b 1
)

pause



