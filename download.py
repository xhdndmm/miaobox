#by xhdndmm & Seikoa & dsx120209
#https://github.com/xhdndmm/miaobox
#
#开发环境：
#xhdndmm:windows10_22h2,python_3.13
#seikoa:windows10/11_22h2,python_3.13

import requests
import os
import threading
from flask import Flask, request, jsonify , render_template
import re
import webbrowser

app = Flask(__name__)

# 全局变量，用于存储下载状态和线程对象
download_thread = None  # 当前下载线程
downloader = None       # Downloader实例，用于控制下载任务

class Downloader:
    """文件下载器类，负责执行下载任务并支持取消操作"""

    def __init__(self, url, save_path, max_retries=3, language='en'):
        """初始化下载器，设置下载URL、保存路径、最大重试次数和语言选项"""
        self.url = url
        self.save_path = save_path
        self.max_retries = max_retries
        self.cancelled = False  # 取消下载的标志
        self.messages = {       # 提示消息字典
            'en': {'download_cancelled': "Download cancelled.", 'downloaded': "Downloaded: {}"},
            'zh': {'download_cancelled': "下载已取消。", 'downloaded': "已下载: {}"}
        }

    def clean_filename(self, url):
        """清理URL中的非法字符，生成有效的文件名"""
        return re.sub(r'[<>:"/\\|?*]', '_', os.path.basename(url.split('?')[0]))

    def download(self):
        """执行文件下载的核心方法"""
        # 创建保存路径（如果不存在）
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))

        # 开始下载文件
        with requests.get(self.url, stream=True) as response:
            response.raise_for_status()  # 检查请求状态
            with open(self.save_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    if self.cancelled:  # 如果取消标志为True，则停止下载
                        print(self.messages[self.language]['download_cancelled'])
                        return
                    file.write(data)

    def start_download(self):
        """启动下载任务并处理失败重试"""
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.download()  # 下载文件
                print(self.messages[self.language]['downloaded'].format(self.save_path))
                break
            except Exception as e:
                attempts += 1
                if attempts == self.max_retries:
                    print("Max retries exceeded")
                    break

    def cancel_download(self):
        """取消下载"""
        self.cancelled = True

@app.route('/')
def index():
    return render_template('index.html')

# API端点：启动下载
@app.route('/start_download', methods=['POST'])
def start_download():
    """
    接收POST请求启动下载任务。请求体格式为JSON，包含以下字段：
    - url (str): 必填，文件下载链接
    - path (str): 可选，保存文件的本地路径，默认为当前目录
    - retries (int): 可选，下载失败重试次数，默认3次
    - language (str): 可选，消息语言，支持 'en' 或 'zh'，默认为英文

    返回JSON对象，包括：
    - status (str): 下载状态信息，如 'Download started'
    - file (str): 保存的文件名
    """
    global download_thread, downloader

    url = request.json.get('url')
    save_path = request.json.get('path', './')
    retries = request.json.get('retries', 3)
    language = request.json.get('language', 'en')

    file_name = Downloader(url, '', retries, language).clean_filename(url)
    save_path = os.path.join(save_path, file_name)

    # 创建 Downloader 实例并启动下载线程
    downloader = Downloader(url, save_path, retries, language)
    download_thread = threading.Thread(target=downloader.start_download)
    download_thread.start()
    return jsonify({'status': 'Download started', 'file': file_name})

# API端点：取消下载
@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    """
    接收POST请求以取消当前下载任务。
    
    返回JSON对象，包括：
    - status (str): 取消下载的状态信息，如 'Download cancelled' 或 'No active download'
    """
    global download_thread, downloader

    if downloader:
        downloader.cancel_download()  # 调用取消下载
        if download_thread.is_alive():
            download_thread.join()  # 等待线程结束
        return jsonify({'status': 'Download cancelled'})
    return jsonify({'status': 'No active download'})  # 没有下载任务时返回

# API端点：获取下载状态
@app.route('/download_status', methods=['GET'])
def download_status():
    """
    接收GET请求以查询当前下载状态。

    返回JSON对象，包括：
    - status (str): 下载状态信息，可为以下几种情况：
        - 'Downloading'：下载中
        - 'Cancelled'：下载已取消
        - 'Completed'：下载已完成
        - 'No download started'：当前无下载任务
    """
    if download_thread and download_thread.is_alive():
        return jsonify({'status': 'Downloading'})
    elif downloader and downloader.cancelled:
        return jsonify({'status': 'Cancelled'})
    elif downloader:
        return jsonify({'status': 'Completed'})
    return jsonify({'status': 'No download started'})  # 无下载任务时返回

def open_browser():
    webbrowser.open("http://127.0.0.1")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=80)
