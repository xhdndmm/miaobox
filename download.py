#https://github.com/xhdndmm/miaobox

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
from flask import Flask, request, jsonify, render_template, Response
import requests
from tqdm import tqdm
import re
import webbrowser
from urllib.parse import urlparse
import youtube_dl #youtube_dl库可能不支持部分功能，目前测试无法下载B站的视频

app = Flask(__name__)
download_thread = None  # 下载线程
downloader = None  # 下载器实例
lock = threading.Lock()  # 线程锁

# 配置类
class Config:
    LOG_FILE = "miaobox_log.log"
    SAVE_PATH = os.path.join(os.path.expanduser("~"), "Downloads")  # 默认下载路径
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0" #自定义UA信息伪装正常用户

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
            downloaded_size = 0
            progress = tqdm(total=total_size, unit='B', unit_scale=True, disable=None)
            with open(file_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    if self.cancelled:
                        progress.close()
                        logging.info("下载取消：%s", file_path)
                        return
                    file.write(data)
                    downloaded_size += len(data)
                    progress.update(len(data))
                    self.update_progress(downloaded_size, total_size)
            progress.close()
            logging.info("下载完成：%s", file_path)

    def update_progress(self, downloaded_size, total_size):
        """更新下载进度"""
        progress_percentage = (downloaded_size / total_size) * 100
        with app.app_context():
            app.config['PROGRESS'] = progress_percentage

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

    @classmethod
    def batch_download(cls, urls, save_path=None, max_retries=3, user_agent=None):
        """批量下载多个文件"""
        results = []
        for url in urls:
            try:
                downloader = cls(url, save_path, max_retries, user_agent)
                downloader.start_download()
                results.append({"url": url, "status": "success"})
            except Exception as e:
                results.append({"url": url, "status": "failed", "error": str(e)})
        return results

class VideoDownloader:
    def __init__(self, url, save_path=None, user_agent=None):
        self.url = url
        self.save_path = os.path.abspath(save_path or app.config["SAVE_PATH"])
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        self.cancelled = False
        self.user_agent = user_agent or app.config["USER_AGENT"]

    def download(self):
        ydl_opts = {
            'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'http_headers': {'User-Agent': self.user_agent},
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([self.url]) #下载B站视频可能会出现问题（在这里出现错误 报错403）
            except Exception as e:
                logging.error("视频下载失败：%s", e)
                raise

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                progress_percentage = (downloaded_bytes / total_bytes) * 100
                with app.app_context():
                    app.config['PROGRESS'] = progress_percentage

    def start_download(self):
        try:
            self.download()
        except Exception as e:
            logging.error("视频下载失败：%s", e)
            raise

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

@app.route('/start_video_download', methods=['POST'])
def start_video_download():
    global download_thread, downloader
    with lock:
        if download_thread and download_thread.is_alive():
            return jsonify({'status': 'Error', 'message': 'A download is already in progress'}), 409
        try:
            video_url = request.json.get('videoUrl')
            save_path = app.config["SAVE_PATH"]
            user_agent = app.config["USER_AGENT"]

            if not is_valid_url(video_url):
                return jsonify({'status': 'Error', 'message': 'Invalid URL'}), 400

            downloader = VideoDownloader(video_url, save_path, user_agent)
            download_thread = threading.Thread(target=downloader.start_download, daemon=True)
            download_thread.start()
            return jsonify({'status': 'Download started', 'file': os.path.basename(save_path)})
        except Exception as e:
            logging.error("启动视频下载失败：%s", e)
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
        progress = app.config.get('PROGRESS', 0)
        return jsonify({'status': status, 'file': file_name, 'progress': progress})
    return jsonify({'status': 'No download started'})

def open_browser():
    """自动打开浏览器"""
    webbrowser.open("http://localhost:5000/")

@app.route('/start_batch_download', methods=['POST'])
def start_batch_download():
    """处理批量下载请求"""
    try:
        urls = request.json.get('urls', [])
        user_path = request.json.get('path')
        save_path = os.path.abspath(user_path) if user_path else app.config["SAVE_PATH"]
        
        if not urls:
            return jsonify({'status': 'Error', 'message': '未提供下载链接'}), 400

        # 验证所有URL
        invalid_urls = [url for url in urls if not is_valid_url(url)]
        if invalid_urls:
            return jsonify({
                'status': 'Error',
                'message': '存在无效的URL',
                'invalid_urls': invalid_urls
            }), 400

        # 确保保存路径存在
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)

        # 创建批量下载线程
        def batch_download_task():
            results = Downloader.batch_download(urls, save_path)
            with app.app_context():
                app.config['BATCH_RESULTS'] = results

        global download_thread
        download_thread = threading.Thread(target=batch_download_task, daemon=True)
        download_thread.start()

        return jsonify({
            'status': 'Batch download started',
            'total_files': len(urls)
        })

    except Exception as e:
        logging.error("批量下载启动失败：%s", e)
        return jsonify({'status': 'Error', 'message': str(e)}), 500

@app.route('/batch_download_status', methods=['GET'])
def batch_download_status():
    """获取批量下载状态"""
    results = app.config.get('BATCH_RESULTS', [])
    is_running = download_thread and download_thread.is_alive() if download_thread else False
    
    return jsonify({
        'status': 'running' if is_running else 'completed',
        'results': results
    })

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
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)  # 启动 Flask 服务 并且可以局域网访问