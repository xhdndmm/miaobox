#https://github.com/xhdndmm/miaobox

import os
import threading
import logging
import webbrowser
from urllib.parse import urlparse
import yt_dlp
from flask import Flask, request, jsonify, render_template
import requests
import re
import magic
from pathvalidate import sanitize_filename
import hashlib
from datetime import datetime
import time

app = Flask(__name__)
download_thread = None
downloader = None
lock = threading.Lock()

class Config:
    LOG_FILE = "miaobox_log.log"
    SAVE_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    MAX_FILE_SIZE = 1024 * 1024 * 1024 * 5  # 5GB
    ALLOWED_MIME_TYPES = {
        'application/pdf', 'application/zip', 'application/x-rar-compressed',
        'application/x-7z-compressed', 'application/x-tar', 'application/gzip',
        'application/x-bzip2', 'application/msword', 'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'audio/mpeg', 'audio/wav', 'audio/ogg',
        'video/mp4', 'video/webm', 'video/x-msvideo'
    }
    DOWNLOAD_TIMEOUT = 30  # 下载超时时间（秒）
    PROGRESS_UPDATE_INTERVAL = 0.1  # 进度更新间隔（秒）

app.config.from_object(Config)

logging.basicConfig(
    filename=app.config['LOG_FILE'],
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

class Downloader:
    def __init__(self, url, save_path=None, max_retries=3, user_agent=None):
        self.url = url
        self.save_path = os.path.abspath(save_path or app.config["SAVE_PATH"])
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        self.max_retries = max_retries
        self.cancelled = False
        self.user_agent = user_agent or app.config["USER_AGENT"]
        self.mime = magic.Magic(mime=True)
        # 初始化进度相关变量
        self.last_update_time = time.time()
        self.last_downloaded_size = 0

    def is_safe_path(self, path):
        """验证保存路径的安全性"""
        try:
            base_path = os.path.abspath(app.config["SAVE_PATH"])
            abs_path = os.path.abspath(path)
            return os.path.commonpath([base_path]) == os.path.commonpath([base_path, abs_path])
        except ValueError:
            return False

    def is_allowed_file_type(self, file_content):
        """检查文件类型是否允许下载"""
        try:
            mime_type = self.mime.from_buffer(file_content[:2048])
            return mime_type in app.config['ALLOWED_MIME_TYPES']
        except Exception as e:
            logging.error(f"文件类型检查失败: {e}")
            return False

    def generate_safe_filename(self, original_name, content):
        """生成安全的文件名，包含内容哈希"""
        name, ext = os.path.splitext(original_name)
        content_hash = hashlib.md5(content[:8192]).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = sanitize_filename(f"{name}_{timestamp}_{content_hash}{ext}")
        return safe_name

    def extract_filename(self, response, default_name="downloaded_file"):
        """从响应头中提取文件名"""
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

    def sanitize_filename(self, filename):
        """生成合法的文件名"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename or "unknown_file")

    def clean_filename(self, url, response=None):
        """生成合法的文件名"""
        filename = self.extract_filename(response) if response else os.path.basename(url.split('?')[0])
        return self.sanitize_filename(filename)

    def download(self):
        """下载文件，支持取消和进度显示"""
        headers = {"User-Agent": self.user_agent}
        try:
            with requests.get(self.url, stream=True, headers=headers, timeout=app.config['DOWNLOAD_TIMEOUT']) as response:
                response.raise_for_status()
                
                # 检查文件大小
                content_length = int(response.headers.get('content-length', 0))
                if content_length > app.config['MAX_FILE_SIZE']:
                    raise ValueError(f"文件大小超过限制: {content_length} > {app.config['MAX_FILE_SIZE']}")

                # 下载前1KB用于文件类型检查
                initial_content = next(response.iter_content(chunk_size=2048))
                if not self.is_allowed_file_type(initial_content):
                    raise ValueError("不支持的文件类型")

                # 生成安全的文件名
                original_filename = self.extract_filename(response)
                safe_filename = self.generate_safe_filename(original_filename, initial_content)
                file_path = os.path.join(self.save_path, safe_filename)

                if not self.is_safe_path(file_path):
                    raise ValueError("不安全的文件路径")

                downloaded_size = len(initial_content)
                with open(file_path, 'wb') as file:
                    file.write(initial_content)
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancelled:
                            logging.info(f"下载取消：{file_path}")
                            return
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            self.update_progress(downloaded_size, content_length)

                logging.info(f"下载完成：{file_path}")
                return safe_filename

        except requests.Timeout:
            logging.error("下载超时")
            raise TimeoutError("下载超时，请稍后重试")
        except requests.RequestException as e:
            logging.error(f"网络错误：{e}")
            raise
        except Exception as e:
            logging.error(f"下载错误：{e}")
            raise

    def update_progress(self, downloaded_size, total_size):
        """更新下载进度"""
        try:
            progress_percentage = (downloaded_size / total_size) * 100 if total_size > 0 else 0
            
            # 计算下载速度
            current_time = time.time()
            if hasattr(self, 'last_update_time') and hasattr(self, 'last_downloaded_size'):
                time_diff = current_time - self.last_update_time
                size_diff = downloaded_size - self.last_downloaded_size
                speed = size_diff / time_diff if time_diff > 0 else 0
                
                # 计算剩余时间
                remaining_size = total_size - downloaded_size
                eta = remaining_size / speed if speed > 0 else 0
                
                # 更新进度信息
                with app.app_context():
                    app.config['PROGRESS'] = {
                        'percentage': progress_percentage,
                        'downloaded': format_size(downloaded_size),
                        'total': format_size(total_size),
                        'speed': format_size(speed) + '/s',
                        'eta': format_time(eta)
                    }
            
            # 保存当前状态用于下次计算
            self.last_update_time = current_time
            self.last_downloaded_size = downloaded_size
            
        except Exception as e:
            logging.error(f"更新进度时出错：{e}")

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
        self.current_filename = None
        self.cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
        # 初始化进度相关变量
        self.last_update_time = time.time()
        self.last_downloaded_bytes = 0
        self.download_speed = 0
        self.total_bytes = 0
        self.downloaded_bytes = 0

    def is_bilibili_url(self, url):
        """检查是否为B站URL"""
        return 'bilibili.com' in url or 'b23.tv' in url

    def clean_temp_files(self, base_filename):
        """清理临时文件和非mp4文件"""
        try:
            dir_path = os.path.dirname(base_filename)
            filename_without_ext = os.path.splitext(os.path.basename(base_filename))[0]
            
            # 获取目录下所有相关文件
            for file in os.listdir(dir_path):
                if file.startswith(filename_without_ext):
                    filepath = os.path.join(dir_path, file)
                    # 保留mp4文件，删除其他文件
                    if not file.endswith('.mp4'):
                        try:
                            os.remove(filepath)
                            logging.info(f"已删除临时文件：{filepath}")
                        except Exception as e:
                            logging.error(f"删除文件失败：{filepath}, 错误：{e}")
        except Exception as e:
            logging.error(f"清理临时文件时出错：{e}")

    def update_progress(self, downloaded_bytes, total_bytes, speed=None, eta=None):
        """更新下载进度"""
        try:
            # 更新字节计数
            self.downloaded_bytes = downloaded_bytes
            self.total_bytes = total_bytes or self.total_bytes  # 保留之前的总大小如果新值为0

            # 计算下载速度
            current_time = time.time()
            time_diff = current_time - self.last_update_time
            if time_diff >= 1:  # 每秒更新一次速度
                bytes_diff = downloaded_bytes - self.last_downloaded_bytes
                self.download_speed = bytes_diff / time_diff
                self.last_update_time = current_time
                self.last_downloaded_bytes = downloaded_bytes

            # 使用传入的速度，如果没有则使用计算的速度
            current_speed = speed or self.download_speed

            # 计算进度百分比
            if self.total_bytes > 0:
                progress_percentage = (self.downloaded_bytes / self.total_bytes) * 100
                
                # 如果没有提供eta，则计算
                if not eta and current_speed > 0:
                    remaining_bytes = self.total_bytes - self.downloaded_bytes
                    eta = remaining_bytes / current_speed

                # 更新进度信息
                with app.app_context():
                    app.config['PROGRESS'] = {
                        'percentage': progress_percentage,
                        'downloaded': format_size(self.downloaded_bytes),
                        'total': format_size(self.total_bytes),
                        'speed': format_size(current_speed) + '/s',
                        'eta': format_time(eta) if eta else '计算中...'
                    }

                # 记录日志
                logging.info(
                    f"下载进度: {progress_percentage:.1f}%, "
                    f"速度: {format_size(current_speed)}/s, "
                    f"已下载: {format_size(self.downloaded_bytes)}/{format_size(self.total_bytes)}"
                )

        except Exception as e:
            logging.error(f"更新进度时出错：{e}")

    def progress_hook(self, d):
        """处理下载进度回调"""
        try:
            if d['status'] == 'downloading':
                self.current_filename = d.get('filename')
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # 使用update_progress方法更新进度
                self.update_progress(downloaded_bytes, total_bytes, speed, eta)

            elif d['status'] == 'finished':
                logging.info(f"视频下载完成：{self.current_filename}")
                # 在下载完成后清理临时文件
                if self.current_filename:
                    self.clean_temp_files(self.current_filename)
                    
            elif d['status'] == 'error':
                error_message = d.get('error', '未知错误')
                logging.error(f"下载出错：{error_message}")
                
        except Exception as e:
            logging.error(f"处理进度回调时出错：{e}")

    def download(self):
        ydl_opts = {
            'outtmpl': os.path.join(self.save_path, '%(title)s_%(id)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'http_headers': {'User-Agent': self.user_agent},
            'format': 'best',  # 下载最佳质量
            'writethumbnail': True,  # 下载缩略图
            'writesubtitles': True,  # 下载字幕（如果有）
            'writeautomaticsub': True,  # 下载自动生成的字幕（如果有）
            'subtitleslangs': ['zh-CN', 'en'],  # 优先下载中文和英文字幕
            'ignoreerrors': True,  # 忽略错误继续下载
            'no_warnings': True,  # 不显示警告
            'quiet': True,  # 不显示标准输出
            'extract_flat': False,  # 不提取平面列表
            'retries': app.config['MAX_RETRIES'],  # 重试次数
        }

        # B站视频的特殊处理
        if self.is_bilibili_url(self.url):
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',  # B站视频需要合并音视频
                'merge_output_format': 'mp4',  # 输出MP4格式
                'cookiesfrombrowser': ('chrome',),  # 尝试从Chrome获取cookies
                'cookiefile': self.cookies_file if os.path.exists(self.cookies_file) else None,  # 使用cookies文件
                'extractor_args': {
                    'bilibili': {
                        'window_size': '1920x1080',  # 设置窗口大小以获取高质量视频
                    },
                },
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info.get('_type') == 'playlist':
                    logging.info(f"检测到播放列表，共{len(info['entries'])}个视频")
                    for entry in info['entries']:
                        if self.cancelled:
                            logging.info("下载取消")
                            return
                        try:
                            ydl.download([entry['webpage_url']])
                        except Exception as e:
                            logging.error(f"下载视频失败：{e}")
                else:
                    ydl.download([self.url])
        except Exception as e:
            if self.is_bilibili_url(self.url):
                logging.error(f"B站视频下载失败，可能需要登录或更新cookies：{e}")
                if not os.path.exists(self.cookies_file):
                    logging.info("提示：请将B站cookies保存到cookies.txt文件中")
            else:
                logging.error(f"视频下载失败：{e}")
            raise

    def start_download(self):
        try:
            self.download()
        except Exception as e:
            logging.error(f"视频下载失败：{e}")
            raise

    def cancel_download(self):
        self.cancelled = True

def is_valid_url(url):
    """验证 URL 合法性"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def format_size(size):
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}TB"

def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f}分钟"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.0f}小时{minutes:.0f}分钟"

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
        status = "Downloading" if download_thread and download_thread.is_alive() else "Completed"
        progress = app.config.get('PROGRESS', {
            'percentage': 0,
            'downloaded': '0B',
            'total': '0B',
            'speed': '0B/s',
            'eta': '未知'
        })
        return jsonify({
            'status': status,
            'file': file_name,
            'progress': progress
        })
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