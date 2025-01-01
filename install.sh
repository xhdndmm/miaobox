#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[信息] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[警告] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

echo "===================================="
echo "     Miaobox 文件下载器安装程序"
echo "===================================="
echo

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    # 检测Linux发行版
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        LINUX_DIST=$ID
    elif [ -f /etc/debian_version ]; then
        LINUX_DIST="debian"
    elif [ -f /etc/redhat-release ]; then
        LINUX_DIST="rhel"
    elif [ -f /etc/arch-release ]; then
        LINUX_DIST="arch"
    elif [ -f /etc/SuSE-release ]; then
        LINUX_DIST="suse"
    elif [ -f /etc/fedora-release ]; then
        LINUX_DIST="fedora"
    else
        print_warning "无法识别的Linux发行版，将尝试通用安装方法"
        LINUX_DIST="unknown"
    fi
    print_info "检测到Linux发行版: $LINUX_DIST"
else
    print_error "不支持的操作系统"
    exit 1
fi

# 检查是否有sudo权限
if ! sudo -v; then
    print_error "需要管理员权限来安装依赖"
    exit 1
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    print_error "未检测到Python 3"
    echo "请先安装Python 3.7或更高版本"
    case $OS_TYPE in
        "macos")
            echo "您可以从 https://www.python.org/downloads/ 下载安装"
            echo "或使用Homebrew安装: brew install python3"
            ;;
        "linux")
            case $LINUX_DIST in
                "debian"|"ubuntu")
                    echo "运行: sudo apt install python3 python3-pip"
                    ;;
                "rhel"|"centos"|"fedora")
                    echo "运行: sudo yum install python3 python3-pip"
                    ;;
                "arch")
                    echo "运行: sudo pacman -S python python-pip"
                    ;;
                "suse")
                    echo "运行: sudo zypper install python3 python3-pip"
                    ;;
                *)
                    echo "请访问 https://www.python.org/downloads/ 下载安装"
                    ;;
            esac
            ;;
    esac
    exit 1
fi

print_info "[1/3] 正在安装Python依赖..."
python3 -m pip install --upgrade pip
if ! python3 -m pip install -r requirements.txt; then
    print_error "Python依赖安装失败"
    exit 1
fi

print_info "[2/3] 正在检查FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    print_warning "FFmpeg未安装，正在安装..."
    
    case $OS_TYPE in
        "macos")
            if ! command -v brew &> /dev/null; then
                print_info "正在安装Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                if [ $? -ne 0 ]; then
                    print_error "Homebrew安装失败"
                    echo "请访问 https://brew.sh/ 手动安装"
                    exit 1
                fi
            fi
            print_info "[3/3] 正在通过Homebrew安装FFmpeg..."
            if ! brew install ffmpeg; then
                print_error "FFmpeg安装失败"
                echo "请查看 ffmpeg_install_guide.md 手动安装"
                exit 1
            fi
            ;;
        "linux")
            case $LINUX_DIST in
                "debian"|"ubuntu")
                    sudo apt update
                    sudo apt install -y ffmpeg
                    ;;
                "rhel"|"centos")
                    sudo yum install -y epel-release
                    sudo yum install -y ffmpeg ffmpeg-devel
                    ;;
                "fedora")
                    sudo dnf install -y ffmpeg ffmpeg-devel
                    ;;
                "arch")
                    sudo pacman -S --noconfirm ffmpeg
                    ;;
                "suse")
                    sudo zypper install -y ffmpeg
                    ;;
                *)
                    print_error "未知的Linux发行版，请手动安装FFmpeg"
                    echo "请查看 ffmpeg_install_guide.md 获取安装指南"
                    exit 1
                    ;;
            esac
            if [ $? -ne 0 ]; then
                print_error "FFmpeg安装失败"
                echo "请查看 ffmpeg_install_guide.md 手动安装"
                exit 1
            fi
            ;;
    esac
else
    print_success "FFmpeg已安装，跳过安装步骤"
fi

# 设置执行权限
chmod +x download.py

# 创建桌面快捷方式（仅限Linux桌面环境）
if [ "$OS_TYPE" == "linux" ] && [ -d "$HOME/Desktop" ]; then
    print_info "正在创建桌面快捷方式..."
    cat > "$HOME/Desktop/miaobox.desktop" << EOF
[Desktop Entry]
Name=Miaobox下载器
Comment=视频下载工具
Exec=python3 $(pwd)/download.py
Terminal=false
Type=Application
Categories=Utility;
EOF
    chmod +x "$HOME/Desktop/miaobox.desktop"
fi

echo
echo "===================================="
print_success "          安装完成！"
echo "===================================="
echo
echo "您现在可以通过以下方式启动程序："
echo "1. 命令行启动：python3 download.py"
if [ "$OS_TYPE" == "linux" ] && [ -d "$HOME/Desktop" ]; then
    echo "2. 双击桌面上的"Miaobox下载器"图标"
fi
echo
echo "如需了解使用方法，请查看 README.md"
echo "如遇到问题，请查看 ffmpeg_install_guide.md"
echo

# 询问是否立即启动
read -p "是否立即启动程序？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 download.py
fi 