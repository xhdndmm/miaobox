::适用于windows的启动器

@echo off
chcp 65001 >nul
setlocal

:: 定义 Python 安装的 URL
set PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe
set PYTHON_INSTALLER=python-installer.exe

:: 检查 Python 是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 未安装。
    set /p choice="是否下载并安装 Python？(Y/N): "
    if /i "%choice%"=="Y" (
        echo 开始下载并安装 Python。
        curl -o %PYTHON_INSTALLER% %PYTHON_INSTALLER_URL%
        if exist %PYTHON_INSTALLER% (
            start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1
            del %PYTHON_INSTALLER%
            echo Python 安装完成。
            pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
            echo pip源更换完毕
        ) else (
            echo 无法下载 Python 安装文件，请检查网络连接。
            goto :end
        )
    ) else (
        echo 跳过 Python 安装。
        goto :end
    )
) else (
    echo Python 已安装。
)

:: 定义函数以检查并询问是否安装库
set libraries=requests threading flask re webbrowser

:: 循环检查并安装每个库
for %%L in (%libraries%) do (
    python -c "import %%L" >nul 2>&1
    if %errorlevel% neq 0 (
        echo %%L 库未安装。
        set /p choice="是否安装 %%L 库？(Y/N): "
        if /i "%choice%"=="Y" (
            echo 正在安装 %%L ...
            pip install %%L
            if %errorlevel% neq 0 (
                echo 安装 %%L 失败，请检查网络连接或其他问题。
                goto :end
            ) else (
                echo %%L 安装成功。
            )
        ) else (
            echo 跳过 %%L 安装。
        )
    ) else (
        echo %%L 已安装。
    )
)

:end
echo 检查并安装完成。
start download.py
pause