#by xhdndmm & Seikoa
#https://github.com/xhdndmm/miaobox
#使用chatgpt辅助制作
#
#开发环境：
#xhdndmm:windows10_22h2,python_3.13
#seikoa:windows10/11_22h2,python_3.13

import os
import threading
import logging
from flask import Flask, request, jsonify, render_template
import requests
from tqdm import tqdm
import re
import webbrowser

app = Flask(__name__)
download_thread = None  # 下载线程
downloader = None  # 下载器实例

# 设置日志记录，指定 UTF-8 编码
logging.basicConfig(
    filename="download.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"  # 确保日志文件为 UTF-8 编码
)


class Downloader:
    """文件下载器类"""

    def __init__(self, url, save_path, max_retries=3):
        self.url = url  # 下载链接
        self.save_path = save_path  # 保存路径
        self.max_retries = max_retries  # 最大重试次数
        self.cancelled = False  # 取消下载的标志

    @staticmethod
    def extract_filename(response, default_name="downloaded_file"):
        """从 Content-Disposition 中提取文件名"""
        cd = response.headers.get("Content-Disposition")
        if cd:
            filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                return filename_match[0]
        return default_name

    @staticmethod
    def clean_filename(url, response=None):
        """生成合法的文件名"""
        if response:
            filename = Downloader.extract_filename(response)
        else:
            filename = os.path.basename(url.split('?')[0])
        return re.sub(r'[<>:"/\\|?*]', '_', filename or "unknown_file")

    def download(self):
        """下载文件，支持取消和进度显示"""
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))  # 确保保存路径存在

        with requests.get(self.url, stream=True) as response:
            response.raise_for_status()  # 如果请求失败，抛出异常
            filename = self.clean_filename(self.url, response)  # 提取文件名
            self.save_path = os.path.join(os.path.dirname(self.save_path), filename)
            total_size = int(response.headers.get('content-length', 0))  # 获取文件总大小
            progress = tqdm(total=total_size, unit='B', unit_scale=True)  # 初始化进度条
            with open(self.save_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):  # 每次下载块大小
                    if self.cancelled:
                        progress.close()  # 停止进度条
                        logging.info("下载取消：%s", self.save_path)
                        return
                    file.write(data)
                    progress.update(len(data))  # 更新进度条
            progress.close()
            logging.info("下载完成：%s", self.save_path)  # 记录成功日志

    def start_download(self):
        """启动下载，支持多次重试"""
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.download()  # 执行下载
                break
            except Exception as e:
                attempts += 1
                logging.error("下载失败（尝试 %d/%d）：%s", attempts, self.max_retries, e)  # 记录失败日志
                if attempts == self.max_retries:
                    logging.error("超出最大重试次数：%s", self.url)  # 最后一次失败记录
                    raise e

    def cancel_download(self):
        """取消当前下载任务"""
        self.cancelled = True


@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')


@app.route('/start_download', methods=['POST'])
def start_download():
    """启动下载任务"""
    global download_thread, downloader
    try:
        url = request.json.get('url')  # 获取下载链接
        save_path = request.json.get('path', os.path.expanduser("~/Downloads"))  # 默认保存路径
        retries = request.json.get('retries', 3)  # 默认重试次数

        file_name = Downloader.clean_filename(url)
        save_path = os.path.join(save_path, file_name)
        downloader = Downloader(url, save_path, retries)  # 初始化下载器
        download_thread = threading.Thread(target=downloader.start_download)  # 启动下载线程
        download_thread.start()
        return jsonify({'status': 'Download started', 'file': file_name})
    except Exception as e:
        logging.error("启动下载失败：%s", e)
        return jsonify({'status': 'Error', 'message': str(e)}), 500


@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    """取消下载任务"""
    global download_thread, downloader

    if downloader:
        downloader.cancel_download()
        if download_thread.is_alive():
            download_thread.join()  # 等待线程结束
        return jsonify({'status': 'Download cancelled'})
    return jsonify({'status': 'No active download'})


@app.route('/download_status', methods=['GET'])
def download_status():
    """查询下载状态"""
    if download_thread and download_thread.is_alive():
        return jsonify({'status': 'Downloading'})
    elif downloader and downloader.cancelled:
        return jsonify({'status': 'Cancelled'})
    elif downloader:
        return jsonify({'status': 'Completed'})
    return jsonify({'status': 'No download started'})


def open_browser():
    """自动打开浏览器"""
    webbrowser.open("http://127.0.0.1")


if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=80, debug=True)  # 启动 Flask 服务
