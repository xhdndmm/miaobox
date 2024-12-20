#by xhdndmm & Seikoa
#https://github.com/xhdndmm/miaobox
#使用chatgpt辅助制作
#
#开发环境：
#xhdndmm:windows11_24h2,python_3.12.8
#seikoa:windows10/11_22h2,python_3.13

"""
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            佛祖保佑       永无BUG
"""

import os
import threading
import logging
from flask import Flask, request, jsonify, render_template
import requests
from tqdm import tqdm
import re
import webbrowser
from urllib.parse import urlparse

app = Flask(__name__)
download_thread = None  # 下载线程
downloader = None  # 下载器实例
lock = threading.Lock()  # 线程锁

# 配置类
class Config:
    LOG_FILE = "miaobox_log.log"
    SAVE_PATH = os.path.join(os.path.expanduser("~"), "Downloads")  # 默认下载路径
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"

app.config.from_object(Config)

# 设置日志记录，指定 UTF-8 编码
logging.basicConfig(
    filename=app.config['LOG_FILE'],
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

class Downloader:
    def __init__(self, url, save_path=None, max_retries=3, user_agent=None):
        self.url = url
        self.save_path = os.path.abspath(save_path or app.config["SAVE_PATH"])  # 转为绝对路径
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)  # 创建目录
        self.max_retries = max_retries
        self.cancelled = False
        self.user_agent = user_agent or app.config["USER_AGENT"]

    @staticmethod
    def extract_filename(response, default_name="downloaded_file"):
        cd = response.headers.get("Content-Disposition")
        if cd:
            filename_match = re.findall(r"filename\*=(?:UTF-8'')?(.+)", cd)
            if not filename_match:
                filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                try:
                    return requests.utils.unquote(filename_match[0]).encode("latin1").decode("utf-8")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    return requests.utils.unquote(filename_match[0])
        return default_name

    @staticmethod
    def sanitize_filename(filename):
        """生成合法的文件名"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename or "unknown_file")

    @staticmethod
    def clean_filename(url, response=None):
        """生成合法的文件名"""
        filename = Downloader.extract_filename(response) if response else os.path.basename(url.split('?')[0])
        return Downloader.sanitize_filename(filename)

    def download(self):
        """下载文件，支持取消和进度显示"""
        headers = {
            "User-Agent": self.user_agent
        }
        with requests.get(self.url, stream=True, headers=headers) as response:
            response.raise_for_status()
            filename = self.clean_filename(self.url, response)
            file_path = os.path.join(self.save_path, filename)  # 确保保存到正确的目录
            total_size = int(response.headers.get('content-length', 0))
            progress = tqdm(total=total_size, unit='B', unit_scale=True, disable=None)
            with open(file_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    if self.cancelled:
                        progress.close()
                        logging.info("下载取消：%s", file_path)
                        return
                    file.write(data)
                    progress.update(len(data))
            progress.close()
            logging.info("下载完成：%s", file_path)
            
    def start_download(self):
        """启动下载，支持多次重试"""
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.download()
                break
            except requests.exceptions.RequestException as e:
                attempts += 1
                logging.error("网络错误（尝试 %d/%d）：%s", attempts, self.max_retries, e)
            except Exception as e:
                logging.error("未知错误：%s", e)
                raise

    def cancel_download(self):
        """取消当前下载任务"""
        self.cancelled = True

def is_valid_url(url):
    """验证 URL 合法性"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    """启动下载任务"""
    global download_thread, downloader
    with lock:
        if download_thread and download_thread.is_alive():
            return jsonify({'status': 'Error', 'message': 'A download is already in progress'}), 409
        try:
            url = request.json.get('url')
            user_path = request.json.get('path')  # 用户传入的路径
            save_path = os.path.abspath(user_path) if user_path else app.config["SAVE_PATH"]
            retries = request.json.get('retries', app.config['MAX_RETRIES'])

            if not is_valid_url(url):
                return jsonify({'status': 'Error', 'message': 'Invalid URL'}), 400

            # 确保路径存在
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)

            downloader = Downloader(url, save_path, retries)
            download_thread = threading.Thread(target=downloader.start_download, daemon=True)
            download_thread.start()
            return jsonify({'status': 'Download started', 'file': downloader.clean_filename(url)})
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
    global downloader
    if downloader and not downloader.cancelled:
        file_name = os.path.basename(downloader.save_path)
        status = "Downloading" if download_thread.is_alive() else "Completed"
        return jsonify({'status': status, 'file': file_name})
    return jsonify({'status': 'No download started'})

def open_browser():
    """自动打开浏览器"""
    webbrowser.open("http://127.0.0.1")

if __name__ == "__main__":
    # 确保默认保存路径存在
    default_save_path = app.config['SAVE_PATH']
    try:
        if not os.path.exists(default_save_path):
            os.makedirs(default_save_path, exist_ok=True)
        print(f"默认保存路径已准备好: {default_save_path}")
    except Exception as e:
        print(f"无法创建默认保存路径: {e}")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=80, debug=True, threaded=True)  # 启动 Flask 服务