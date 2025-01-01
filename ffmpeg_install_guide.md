# FFmpeg 安装指南

## Windows 系统手动安装步骤

1. 下载 FFmpeg
   - 访问 https://github.com/BtbN/FFmpeg-Builds/releases
   - 找到最新的 `ffmpeg-master-latest-win64-gpl.zip`
   - 点击下载

2. 解压文件
   - 创建文件夹 `C:\ffmpeg`
   - 将下载的zip文件解压到该文件夹
   - 确保 `C:\ffmpeg\bin` 目录存在

3. 设置环境变量
   - 右键点击"此电脑"或"我的电脑"
   - 选择"属性"
   - 点击"高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"
   - 点击"编辑"
   - 点击"新建"
   - 输入 `C:\ffmpeg\bin`
   - 点击"确定"保存所有设置

4. 验证安装
   - 打开命令提示符（CMD）或PowerShell
   - 输入 `ffmpeg -version`
   - 如果显示版本信息，说明安装成功

## Windows 系统使用 Chocolatey 安装（推荐）

1. 安装 Chocolatey
   - 以管理员身份运行 PowerShell
   - 复制并运行以下命令：
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. 安装 FFmpeg
   - 在管理员 PowerShell 中运行：
   ```powershell
   choco install ffmpeg
   ```
   - 等待安装完成

3. 验证安装
   - 在 PowerShell 中运行：
   ```powershell
   ffmpeg -version
   ```

## Linux 系统安装

### Ubuntu/Debian
```bash
# 更新包列表
sudo apt update

# 安装 FFmpeg
sudo apt install ffmpeg

# 验证安装
ffmpeg -version
```

### CentOS/RHEL
```bash
# 添加 EPEL 仓库
sudo yum install epel-release

# 安装 FFmpeg
sudo yum install ffmpeg ffmpeg-devel

# 验证安装
ffmpeg -version
```

## macOS 系统安装

1. 安装 Homebrew（如果未安装）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. 安装 FFmpeg
```bash
brew install ffmpeg
```

3. 验证安装
```bash
ffmpeg -version
```

## 常见问题

1. Windows 环境变量设置后不生效
   - 重启命令提示符或PowerShell
   - 如果仍不生效，重启电脑

2. 提示"ffmpeg不是内部或外部命令"
   - 检查环境变量是否正确设置
   - 确认FFmpeg文件是否正确解压
   - 验证bin目录下是否有ffmpeg.exe

3. Linux安装时提示权限错误
   - 确保使用sudo运行安装命令
   - 检查系统源是否正确配置

4. macOS安装时Homebrew报错
   - 更新Homebrew：`brew update`
   - 如果仍有问题，运行：`brew doctor`

## 其他说明

1. FFmpeg版本
   - 建议使用最新版本
   - 本下载器支持所有较新版本的FFmpeg

2. 系统要求
   - Windows 7及以上
   - Ubuntu 18.04及以上
   - macOS 10.13及以上

3. 性能建议
   - 视频处理需要一定的CPU性能
   - 建议有4GB以上内存
   - 保证足够的硬盘空间 