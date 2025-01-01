# Miaobox 文件下载器

一个支持普通文件和视频下载的工具，支持B站视频下载。

## 安装说明

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 安装 FFmpeg（必需，用于视频下载）：

### Windows 系统：

方法1：使用 Chocolatey（推荐）
```bash
# 1. 以管理员身份运行 PowerShell，安装 Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. 安装 FFmpeg
choco install ffmpeg
```

方法2：手动安装
1. 访问 https://github.com/BtbN/FFmpeg-Builds/releases
2. 下载 `ffmpeg-master-latest-win64-gpl.zip`
3. 解压到任意目录（如 `C:\ffmpeg`）
4. 将 `C:\ffmpeg\bin` 添加到系统环境变量 Path 中

### Linux 系统：

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

CentOS/RHEL:
```bash
sudo yum install epel-release
sudo yum install ffmpeg ffmpeg-devel
```

### macOS 系统：
```bash
# 使用 Homebrew 安装
brew install ffmpeg
```

## 使用说明

1. 启动程序：
```bash
python download.py
```

2. 访问网页界面：
- 程序会自动打开浏览器访问 `http://localhost:5000`
- 也可以通过局域网访问：`http://[你的IP]:5000`

3. 下载功能：
- 普通文件下载：输入文件URL，点击"开始下载"
- 视频下载：输入视频URL，点击"下载视频"
- 批量下载：每行输入一个URL，点击"开始批量下载"

4. B站视频下载说明：
- 支持下载B站视频（包括普通视频和番剧）
- 自动选择最高清晰度
- 需要大会员权限的视频请先登录
- 如需使用cookies，请将B站cookies保存到程序目录下的`cookies.txt`文件中

5. 下载管理：
- 可以查看下载历史
- 支持打开文件所在文件夹
- 可以删除下载记录和文件
- 显示下载进度、速度和剩余时间

## 注意事项

1. 视频下载：
- 确保已正确安装FFmpeg
- B站视频下载可能需要登录
- 部分视频可能需要大会员权限

2. 下载路径：
- 默认保存在用户主目录的Downloads文件夹
- 可以在界面中指定自定义保存路径

3. 网络问题：
- 支持断点续传
- 自动重试失败的下载
- 可以随时取消下载

## 常见问题

1. FFmpeg相关：
- 如果提示找不到FFmpeg，请确保正确安装并添加到环境变量
- Windows用户建议使用Chocolatey安装，更简单可靠

2. B站视频问题：
- 无法下载：检查是否需要登录或大会员权限
- 清晰度受限：检查账号权限
- 下载失败：尝试更新cookies

3. 其他问题：
- 下载速度慢：可能是网络问题或服务器限制
- 文件名乱码：程序会自动处理，一般不会出现
- 程序崩溃：查看日志文件`miaobox_log.log`

## 更新日志

### v1.0.0
- 支持普通文件下载
- 支持视频下载（B站等）
- 添加下载历史管理
- 支持批量下载
- 美化界面，添加进度显示 