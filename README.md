# Miaobox 文件下载器
中文版|[English](README-English.md)
## 这是什么？
一个超级简单的文件下载工具，可以帮你下载：
- 网络上的各种文件
- YouTube视频（支持下载字幕）
- B站视频（支持大会员内容）
- 其他视频网站的内容

## 功能特点
- 🎥 自动选择最清晰的视频质量
- 💾 支持断点续传（下载中断后可以继续）
- 📥 可以批量下载多个文件
- 📝 保存下载历史记录
- 🚀 界面简单易用

## 新手使用指南（超详细）

### 第一步：安装必要的软件

#### Windows电脑用户：

1. 安装Python（只需安装一次）
   - 打开这个网站：https://www.python.org/downloads/
   - 点击大大的"Download Python"按钮下载
   - 双击运行下载的安装程序
   - ⚠️重要：安装时必须勾选"Add Python to PATH"选项！
   - 点击"Install Now"等待安装完成

2. 安装FFmpeg（只需安装一次）
   - 简单方法（推荐）：
     1. 按Windows键，输入"PowerShell"
     2. 在搜索结果中右键点击"Windows PowerShell"，选择"以管理员身份运行"
     3. 复制下面的命令，右键粘贴到PowerShell窗口中，按回车：
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
     ```
     4. 等待安装完成后，输入下面的命令，按回车：
     ```powershell
     choco install ffmpeg
     ```

   - 手动安装方法：
     1. 打开网站：https://github.com/BtbN/FFmpeg-Builds/releases
     2. 下载名字带有"win64-gpl"的zip文件
     3. 解压到C盘根目录，确保有一个`C:\ffmpeg`文件夹
     4. 设置系统变量：
        - 按Windows键，输入"环境变量"
        - 点击"编辑系统环境变量"
        - 点击下方的"环境变量"按钮
        - 在下面的"系统变量"中找到"Path"并双击
        - 点击"新建"，输入`C:\ffmpeg\bin`
        - 点击"确定"保存所有设置

#### Mac电脑用户：

1. 打开"终端"（在启动台中搜索"终端"或"Terminal"）
2. 复制粘贴以下命令，按回车：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. 然后输入这个命令安装必要软件：
   ```bash
   brew install python ffmpeg
   ```

### 第二步：下载并安装Miaobox

1. 下载程序文件
   - 访问：https://github.com/xhdndmm/miaobox/releases
   - 下载最新版本的zip文件
   - 解压到桌面或其他你喜欢的位置

2. 安装程序
   - Windows用户：
     1. 按Windows键+R，输入cmd，按回车
     2. 输入：`cd 桌面\miaobox`（如果你解压到了其他位置，要相应修改路径）
     3. 输入：`pip install -r requirements.txt`

   - Mac用户：
     1. 打开终端
     2. 输入：`cd Desktop/miaobox`（如果你解压到了其他位置，要相应修改路径）
     3. 输入：`pip3 install -r requirements.txt`

### 第三步：使用程序

1. 启动程序
   - Windows用户：双击运行`start.bat`文件
   - Mac用户：在终端中输入`python3 app.py`

2. 使用浏览器访问程序
   - 程序会自动打开浏览器
   - 如果没有自动打开，请手动打开浏览器访问：http://localhost:5000

### 下载视频教程

#### YouTube视频下载：

1. 普通下载
   - 在YouTube上找到想下载的视频
   - 复制视频网址（浏览器地址栏的内容）
   - 粘贴到下载器的输入框
   - 点击"开始下载"

2. 下载带字幕的视频
   - 复制视频网址
   - 在网址后面加上`&sub=true`
   - 例如：`https://youtube.com/watch?v=XXXX&sub=true`
   - 粘贴到输入框，点击下载

3. 下载指定清晰度的视频
   - 在网址后面加上`&quality=720p`（可选：360p、480p、720p、1080p）
   - 例如：`https://youtube.com/watch?v=XXXX&quality=720p`

#### B站视频下载：

1. 普通视频下载
   - 复制B站视频网址
   - 直接粘贴到输入框
   - 点击下载即可

2. 下载大会员视频
   - 先在B站网页上登录你的账号
   - 点击下载器中的"管理Cookies"按钮
   - 按照提示导入你的登录信息
   - 然后就可以下载大会员视频了

### 常见问题解决

1. 下载失败怎么办？
   - 检查网络是否正常
   - 确认视频是否需要登录
   - 如果是B站大会员视频，检查是否正确导入了cookies
   - 尝试重新下载

2. 找不到下载的文件？
   - 默认保存在"下载"文件夹中
   - 可以在下载时指定保存位置
   - 在下载历史中可以直接打开文件所在位置

3. 下载速度很慢？
   - 检查网络连接
   - 尝试使用其他网络
   - 可能是视频源限制了下载速度

4. 程序无法启动？
   - 确认是否正确安装了Python
   - 检查是否安装了所有依赖
   - 查看是否有杀毒软件拦截

### 需要帮助？

- 程序出现问题可以尝试重启
- 如果遇到无法解决的问题，可以到GitHub提交问题：https://github.com/xhdndmm/miaobox/issues

### 隐私说明

- 本程序不会收集任何个人信息
- 你的B站登录信息只会保存在本地
- 所有下载记录都只存储在你的电脑上

### 免责声明

- 请勿下载侵权内容
- 仅供个人学习使用
- 下载的内容请在24小时内删除 