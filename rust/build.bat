@echo off
chcp 65001 >nul
echo ====================================
echo   Rust版本构建脚本
echo ====================================
echo.

:: 检查Rust
rustc --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Rust，请先安装Rust
    echo 下载地址: https://www.rust-lang.org/tools/install
    pause
    exit /b 1
)

echo ✅ Rust已安装
rustc --version
cargo --version
echo.

:: 选择构建类型
echo 请选择构建类型:
echo [1] Debug（快速编译，包含调试信息）
echo [2] Release（优化编译，生成最终版本）
echo.
set /p BUILD_TYPE="请选择 (1/2): "

if "%BUILD_TYPE%"=="1" (
    echo.
    echo 🔨 开始Debug构建...
    cargo build
    
    if errorlevel 1 (
        echo ❌ 构建失败
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ Debug构建完成！
    echo 📂 可执行文件位于: target\debug\bbdc_word_tool.exe
    
) else if "%BUILD_TYPE%"=="2" (
    echo.
    echo 🔨 开始Release构建（这可能需要几分钟）...
    cargo build --release
    
    if errorlevel 1 (
        echo ❌ 构建失败
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ Release构建完成！
    echo 📂 可执行文件位于: target\release\bbdc_word_tool.exe
    
    :: 显示文件大小
    for %%F in (target\release\bbdc_word_tool.exe) do (
        echo 📦 文件大小: %%~zF bytes
    )
    
    :: 询问是否复制到根目录
    echo.
    echo 是否复制到根目录? (Y/N)
    set /p COPY_TO_ROOT="请选择: "
    
    if /i "%COPY_TO_ROOT%"=="Y" (
        copy /Y target\release\bbdc_word_tool.exe ..\bbdc_word_tool.exe
        echo ✅ 已复制到根目录
    )
    
) else (
    echo ❌ 无效的选择
    pause
    exit /b 1
)

echo.
echo 运行程序:
if "%BUILD_TYPE%"=="1" (
    echo    .\target\debug\bbdc_word_tool.exe --help
) else (
    echo    .\target\release\bbdc_word_tool.exe --help
)

echo.
echo ✨ 构建完成！
pause



