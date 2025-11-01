@echo off
chcp 65001 >nul
echo ====================================
echo   Python版本构建脚本
echo ====================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

:: 创建虚拟环境（可选）
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ⚠️  创建虚拟环境失败，继续使用全局环境
    ) else (
        echo ✅ 虚拟环境创建成功
    )
)

:: 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 安装依赖
echo.
echo 📦 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成
echo.

:: 询问是否打包
echo 是否打包为可执行文件? (Y/N)
set /p PACKAGE="请选择: "

if /i "%PACKAGE%"=="Y" (
    echo.
    echo 📦 开始打包...
    
    :: 安装pyinstaller
    pip install pyinstaller
    
    :: 打包
    pyinstaller --onefile ^
                --name bbdc_word_tool ^
                --add-data ".env.example;." ^
                --hidden-import "dotenv" ^
                extract_words.py
    
    if errorlevel 1 (
        echo ❌ 打包失败
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ 打包完成！
    echo 📂 可执行文件位于: dist\bbdc_word_tool.exe
) else (
    echo.
    echo ℹ️  跳过打包，直接运行请使用:
    echo    python extract_words.py
)

echo.
echo ✨ 构建完成！
pause



