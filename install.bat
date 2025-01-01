@echo off
chcp 65001 > nul
title Miaobox 安装程序

echo ====================================
echo      Miaobox 文件下载器安装程序
echo ====================================
echo.

:: 检查 Python 是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7 或更高版本
    echo 您可以从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本
    echo 右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo [1/4] 正在安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 正在检查 FFmpeg...
ffmpeg -version > nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg 未安装，正在通过 Chocolatey 安装...
    
    :: 检查 Chocolatey 是否已安装
    choco -v > nul 2>&1
    if %errorlevel% neq 0 (
        echo [3/4] 正在安装 Chocolatey...
        @powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
        if %errorlevel% neq 0 (
            echo [错误] Chocolatey 安装失败
            pause
            exit /b 1
        )
    )
    
    echo [4/4] 正在安装 FFmpeg...
    choco install ffmpeg -y
    if %errorlevel% neq 0 (
        echo [错误] FFmpeg 安装失败
        echo 请尝试手动安装，详见 ffmpeg_install_guide.md
        pause
        exit /b 1
    )
) else (
    echo FFmpeg 已安装，跳过安装步骤
)

echo.
echo ====================================
echo          安装完成！
echo ====================================
echo.
echo 您现在可以运行 download.py 来启动程序
echo 如需了解使用方法，请查看 README.md
echo 如遇到问题，请查看 ffmpeg_install_guide.md
echo.
pause 