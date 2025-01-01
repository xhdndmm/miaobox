# Miaobox 安装指南

## 目录
- [自动安装](#自动安装)
- [手动安装](#手动安装)
- [FFmpeg安装](#ffmpeg安装)
- [常见问题](#常见问题)

## 自动安装

### 使用安装脚本(除windows外)
1. 打开终端，进入程序目录
2. 运行以下命令：
```bash
chmod +x install.sh  # 添加执行权限
./install.sh         # 运行安装脚本
```

### 使用安装脚本(windows)
1.进入项目目录
2.管理员运行install.bat即可
安装脚本会自动：
- 检测您的操作系统
- 安装所需的Python依赖
- 安装FFmpeg
- 创建桌面快捷方式（Linux）
- 设置必要的权限

## 手动安装

如果自动安装失败，您可以按照以下步骤手动安装：

### 1. 安装Python
确保您的系统已安装Python 3.7或更高版本。

#### Windows
- 访问 https://www.python.org/downloads/ 下载并安装Python
- 安装时勾选"Add Python to PATH"

#### macOS
```bash
# 使用Homebrew
brew install python3

# 或从官网下载
# https://www.python.org/downloads/
```

#### Linux
根据您的发行版选择相应命令：

Ubuntu/Debian：
```bash
sudo apt update
sudo apt install python3 python3-pip
```

CentOS/RHEL：
```bash
sudo yum install python3 python3-pip
```

Fedora：
```bash
sudo dnf install python3 python3-pip
```

Arch Linux：
```bash
sudo pacman -S python python-pip
```

openSUSE：
```bash
sudo zypper install python3 python3-pip
```

### 2. 安装Python依赖
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## FFmpeg安装

FFmpeg是视频处理的必要组件，以下是各系统的安装方法：

### Windows
1. 使用Chocolatey（推荐）：
```powershell
choco install ffmpeg
```

2. 手动安装：
- 访问 https://ffmpeg.org/download.html
- 下载Windows版本
- 解压到任意目录
- 将FFmpeg的bin目录添加到系统PATH

### macOS
```bash
# 使用Homebrew
brew install ffmpeg
```

### Linux

Ubuntu/Debian：
```bash
sudo apt update
sudo apt install ffmpeg
```

CentOS/RHEL：
```bash
sudo yum install epel-release
sudo yum install ffmpeg ffmpeg-devel
```

Fedora：
```bash
sudo dnf install ffmpeg ffmpeg-devel
```

Arch Linux：
```bash
sudo pacman -S ffmpeg
```

openSUSE：
```bash
sudo zypper install ffmpeg
```

## 常见问题

### 1. Python相关问题

#### pip安装失败
```bash
# 尝试使用国内镜像
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 提示"Python未找到"
- 确保Python已正确安装
- 检查系统PATH环境变量
- 尝试重启终端或系统

### 2. FFmpeg相关问题

#### 提示"ffmpeg: command not found"
- 确保FFmpeg已正确安装
- 检查系统PATH环境变量
- Windows用户确保添加了FFmpeg的bin目录到PATH

#### 视频下载没有声音
- 确保FFmpeg正确安装
- 检查FFmpeg版本是否最新
```bash
ffmpeg -version
```

### 3. 权限问题

#### Linux/macOS权限错误
```bash
# 设置正确的权限
chmod +x install.sh
chmod +x download.py
```

#### Windows权限错误
- 以管理员身份运行命令提示符
- 检查杀毒软件是否阻止了程序运行

### 4. 其他问题

#### 下载速度慢
- 检查网络连接
- 尝试使用代理
- 确认视频源是否可用

#### 桌面快捷方式无法使用
- 检查Python路径是否正确
- 确认程序目录路径是否正确
- 重新运行安装脚本

如果您遇到其他问题，请：
1. 检查错误信息
2. 查看程序日志
3. 确保所有依赖都已正确安装
4. 尝试重新运行安装脚本

如果问题仍然存在，请提交issue并附上详细的错误信息。 