# https://github.com/xhdndmm/miaobox

"""
MiaoBox - 一个简单的文件和视频下载器

这个模块提供了一个基于 Flask 的 Web 应用，支持：
- 多线程文件下载
- 视频下载（支持 YouTube、Bilibili 等）
- 下载历史记录管理
- 实时下载进度显示
"""

import json
import time
from datetime import datetime
import hashlib
import re
import os
import sys
import threading
import logging
import webbrowser
from urllib.parse import urlparse
from pathvalidate import sanitize_filename
import magic
import requests
from flask import Flask, request, jsonify, render_template


# 检查并添加虚拟环境路径
base_dir = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(base_dir, '.venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
    logging.info("成功加载yt-dlp模块")
except ImportError as e:
    YTDLP_AVAILABLE = False
    logging.error("加载yt-dlp模块失败：%s", e)
    logging.error("请确保在正确的Python环境中运行程序，当前Python路径：%s", sys.executable)
    logging.error("您可以尝试运行：pip install yt-dlp")


app = Flask(__name__)
download_thread = None
downloader = None
lock = threading.Lock()


class Config:
    """应用程序配置类"""
    # 文件和路径配置
    LOG_FILE = "miaobox_log.log"
    SAVE_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
    HISTORY_FILE = "download_history.json"

    # 下载配置
    MAX_RETRIES = 3
    DOWNLOAD_TIMEOUT = 30  # 下载超时时间（秒）
    PROGRESS_UPDATE_INTERVAL = 0.1  # 进度更新间隔（秒）
    MAX_THREADS = 8  # 最大线程数
    MIN_CHUNK_SIZE = 1024 * 1024  # 最小分块大小（1MB）

    # 请求头配置
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) "
        "Gecko/20100101 Firefox/132.0"
    )


app.config.from_object(Config)

logging.basicConfig(
    filename=app.config['LOG_FILE'],
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)


class Downloader:
    """下载器类"""

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
        self.downloaded_chunks = {}
        self.chunk_ranges = {}  # 存储每个线程的下载范围
        self.total_size = 0
        self.chunk_locks = {}
        self.progress_lock = threading.Lock()

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
        except (magic.MagicException, KeyError) as e:
            logging.error("文件类型检查失败: %s", e)
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
                    decoded = requests.utils.unquote(filename_match[0])
                    return decoded.encode("latin1").decode("utf-8")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    return requests.utils.unquote(filename_match[0])
        return default_name

    def sanitize_filename(self, filename):
        """生成合法的文件名"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename or "unknown_file")

    def clean_filename(self, url, response=None):
        """生成合法的文件名"""
        filename = (self.extract_filename(response) if response
                    else os.path.basename(url.split('?')[0]))
        return self.sanitize_filename(filename)

    def download_chunk(self, start, end, chunk_id, file_path):
        """下载指定范围的文件块"""
        if self.cancelled:
            return

        headers = {
            "User-Agent": self.user_agent,
            "Range": f"bytes={start}-{end}"
        }

        try:
            response = requests.get(self.url, headers=headers, stream=True, timeout=app.config['DOWNLOAD_TIMEOUT'])
            response.raise_for_status()

            with self.chunk_locks[chunk_id]:
                with open(file_path, 'rb+') as f:
                    f.seek(start)
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancelled:
                            return
                        if chunk:
                            f.write(chunk)
                            with self.progress_lock:
                                current_size = self.downloaded_chunks.get(chunk_id, 0)
                                self.downloaded_chunks[chunk_id] = current_size + len(chunk)
                                total_downloaded = sum(self.downloaded_chunks.values())
                                self.update_progress(total_downloaded, self.total_size)

        except Exception as e:
            logging.error("下载块 %d 失败: %s", chunk_id, e)
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

                # 计算每个线程的进度
                thread_progress = []
                for chunk_id in sorted(self.downloaded_chunks.keys()):
                    chunk_downloaded = self.downloaded_chunks.get(chunk_id, 0)
                    chunk_start, chunk_end = self.chunk_ranges.get(chunk_id, (0, 0))
                    chunk_total = chunk_end - chunk_start + 1
                    chunk_percentage = 0
                    if chunk_total > 0:
                        chunk_percentage = (chunk_downloaded / chunk_total) * 100
                    thread_progress.append({
                        'thread_id': chunk_id + 1,
                        'percentage': chunk_percentage,
                        'downloaded': format_size(chunk_downloaded),
                        'total': format_size(chunk_total),
                        'range': f"{format_size(chunk_start)}-{format_size(chunk_end)}"
                    })

                # 更新进度信息
                with app.app_context():
                    app.config['PROGRESS'] = {
                        'percentage': progress_percentage,
                        'downloaded': format_size(downloaded_size),
                        'total': format_size(total_size),
                        'speed': format_size(speed) + '/s',
                        'eta': format_time(eta),
                        'threads': thread_progress
                    }

            # 保存当前状态用于下次计算
            self.last_update_time = current_time
            self.last_downloaded_size = downloaded_size

        except Exception as e:
            logging.error("更新进度时出错：%s", e)

    def download(self):
        """使用多线程下载文件"""
        headers = {"User-Agent": self.user_agent}
        try:
            # 发送HEAD请求获取文件大小
            response = requests.head(
                self.url,
                headers=headers,
                timeout=app.config['DOWNLOAD_TIMEOUT']
            )
            response.raise_for_status()
            self.total_size = int(response.headers.get('content-length', 0))

            # 检查文件大小和是否支持范围请求
            is_small_file = self.total_size < app.config['MIN_CHUNK_SIZE']
            no_range_support = 'accept-ranges' not in response.headers
            if is_small_file or no_range_support:
                return self.single_thread_download()

            # 计算分块大小和线程数
            min_chunk = app.config['MIN_CHUNK_SIZE']
            max_threads = app.config['MAX_THREADS']
            chunk_size = max(self.total_size // max_threads, min_chunk)
            num_chunks = min(max_threads, self.total_size // chunk_size)

            # 生成安全的文件名
            kwargs = {
                'url': self.url,
                'stream': True,
                'headers': headers,
                'timeout': app.config['DOWNLOAD_TIMEOUT']
            }
            with requests.get(**kwargs) as response:
                response.raise_for_status()

            original_filename = self.extract_filename(response)
            content_sample = response.content[:8192]
            safe_filename = self.generate_safe_filename(
                original_filename,
                content_sample
            )
            file_path = os.path.join(self.save_path, safe_filename)

            if not self.is_safe_path(file_path):
                raise ValueError("不安全的文件路径")

            # 创建空文件
            with open(file_path, 'wb') as f:
                f.truncate(self.total_size)

            # 初始化进度追踪
            self.downloaded_chunks = {}
            self.chunk_locks = {i: threading.Lock() for i in range(num_chunks)}
            self.chunk_ranges = {}

            # 创建并启动下载线程
            threads = []
            for i in range(num_chunks):
                start = i * chunk_size
                end = start + chunk_size - 1 if i < num_chunks - 1 else self.total_size - 1
                self.chunk_ranges[i] = (start, end)  # 记录每个线程的下载范围
                thread = threading.Thread(
                    target=self.download_chunk,
                    args=(start, end, i, file_path)
                )
                threads.append(thread)
                thread.start()
                logging.info("启动线程 %d/%d，下载范围：%s-%s",
                             i+1, num_chunks, format_size(start), format_size(end))

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            if self.cancelled:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None

            logging.info("下载完成：%s", file_path)
            download_history.add_record(self.url, file_path)
            return safe_filename

        except requests.Timeout as exc:
            logging.error("下载超时")
            raise TimeoutError("下载超时，请稍后重试") from exc
        except requests.RequestException as e:
            logging.error("网络错误：%s", e)
            raise
        except Exception as e:
            logging.error("下载错误：%s", e)
            raise

    def single_thread_download(self):
        """单线程下载方法"""
        headers = {"User-Agent": self.user_agent}
        try:
            with requests.get(self.url,
                              stream=True,
                              headers=headers,
                              timeout=app.config['DOWNLOAD_TIMEOUT']) as response:
                response.raise_for_status()

                original_filename = self.extract_filename(response)
                content_sample = response.content[:8192]
                safe_filename = self.generate_safe_filename(
                    original_filename,
                    content_sample
                )
                file_path = os.path.join(self.save_path, safe_filename)

            if not self.is_safe_path(file_path):
                raise ValueError("不安全的文件路径")

            content_length = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        logging.info("下载取消：%s", file_path)
                        download_history.add_record(self.url, file_path, status="cancelled")
                        return
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        self.update_progress(downloaded_size, content_length)

            logging.info("下载完成：%s", file_path)
            download_history.add_record(self.url, file_path)
            return safe_filename

        except Exception as e:
            logging.error("单线程下载失败：%s", e)
            raise

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
    """视频下载器类"""

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
                            logging.info("已删除临时文件：%s", filepath)
                        except Exception as e:
                            logging.error("删除文件失败：%s, 错误：%s", filepath, e)
        except Exception as e:
            logging.error("清理临时文件时出错：%s", e)

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
            logging.error("更新进度时出错：%s", e)

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
                logging.info("视频下载完成：%s", self.current_filename)
                # 在下载完成后清理临时文件
                if self.current_filename:
                    self.clean_temp_files(self.current_filename)

            elif d['status'] == 'error':
                error_message = d.get('error', '未知错误')
                logging.error("下载出错：%s", error_message)

        except Exception as e:
            logging.error("处理进度回调时出错：%s", e)

    def get_download_options(self) -> dict:
        """获取下载配置"""
        # 基础配置
        options = {
            'format': 'bestvideo+bestaudio/best',  # 选择最佳视频和音频质量
            'outtmpl': os.path.join(self.save_path, '%(title)s_%(id)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'http_headers': {'User-Agent': self.user_agent},
            'retries': app.config['MAX_RETRIES'],
            'merge_output_format': 'mp4',  # 指定输出格式为mp4
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        # B站视频特殊配置
        if self.is_bilibili_url(self.url):
            options.update({
                'format': 'bestvideo*+bestaudio/best',  # 选择最佳视频和音频
                'format_sort': [
                    'res:2160',  # 4K
                    'res:1440',  # 2K
                    'res:1080',  # 1080P
                    'res:720',   # 720P
                ],
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }, {
                    # 添加音频后处理器
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'aac',
                    'preferredquality': '192',
                }],
                'extractaudio': True,  # 确保提取音频
                'keepvideo': True,     # 保留视频
                'postprocessor_args': [
                    '-vcodec', 'copy',  # 复制视频编码，避免重新编码
                    '-acodec', 'aac',   # 使用AAC音频编码
                ],
            })

            # 添加cookies配置
            if os.path.exists(self.cookies_file):
                options.update({
                    'cookiesfrombrowser': ('chrome',),
                    'cookiefile': self.cookies_file,
                })

        return options

    def download(self):
        """下载视频"""
        ydl_opts = self.get_download_options()

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info.get('_type') == 'playlist':
                    logging.info("检测到播放列表，共%d个视频", len(info['entries']))
                    for entry in info['entries']:
                        if self.cancelled:
                            logging.info("下载取消")
                            return
                        try:
                            ydl.download([entry['webpage_url']])
                            # 添加下载记录
                            file_path = os.path.join(
                                self.save_path,
                                f"{entry.get('title', 'unknown')}_{entry.get('id', '')}.mp4"
                            )
                            download_history.add_record(
                                entry['webpage_url'],
                                file_path,
                                file_type="video"
                            )
                        except Exception as e:
                            logging.error("下载视频失败：%s", e)
                else:
                    ydl.download([self.url])
                    # 添加下载记录
                    if self.current_filename:
                        download_history.add_record(
                            self.url,
                            self.current_filename,
                            file_type="video"
                        )
        except Exception as e:
            if self.is_bilibili_url(self.url):
                logging.error("B站视频下载失败，可能需要登录或更新cookies：%s", e)
                if not os.path.exists(self.cookies_file):
                    logging.info("提示：请将B站cookies保存到cookies.txt文件中")
            else:
                logging.error("视频下载失败：%s", e)
            raise

    def start_download(self):
        """启动视频下载"""
        try:
            self.download()
        except Exception as e:
            logging.error("视频下载失败：%s", e)
            raise

    def cancel_download(self):
        """取消视频下载"""
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


def is_video_url(url):
    """检测是否为视频URL"""
    if not YTDLP_AVAILABLE:
        return False
    video_patterns = [
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'bilibili\.com/video/',
        r'b23\.tv/',
        r'\.mp4$',
        r'\.m3u8$',
        r'\.flv$',
        r'\.mkv$',
        r'\.webm$'
    ]
    return any(re.search(pattern, url, re.I) for pattern in video_patterns)


@app.route('/start_download', methods=['POST'])
def start_download():
    """统一的下载入口"""
    global download_thread, downloader
    with lock:
        if download_thread and download_thread.is_alive():
            return jsonify({'status': 'Error', 'message': '已有下载任务正在进行'}), 409
        try:
            url = request.json.get('url')
            user_path = request.json.get('path')
            save_path = os.path.abspath(user_path) if user_path else app.config["SAVE_PATH"]

            if not is_valid_url(url):
                return jsonify({'status': 'Error', 'message': '无效的URL'}), 400

            # 根据URL类型选择下载器
            if is_video_url(url):
                if not YTDLP_AVAILABLE:
                    return jsonify({
                        'status': 'Error',
                        'message': '未安装yt-dlp模块，无法下载视频。请运行: pip install yt-dlp'
                    }), 400
                downloader = VideoDownloader(url, save_path)
            else:
                downloader = Downloader(url, save_path)

            download_thread = threading.Thread(target=downloader.start_download, daemon=True)
            download_thread.start()
            return jsonify({'status': 'Download started', 'file': os.path.basename(save_path)})
        except Exception as e:
            logging.error("启动下载失败：%s", e)
            return jsonify({'status': 'Error', 'message': str(e)}), 500


@app.route('/start_video_download', methods=['POST'])
def start_video_download():
    """启动视频下载"""
    global download_thread, downloader
    with lock:
        if download_thread and download_thread.is_alive():
            return jsonify({
                'status': 'Error',
                'message': 'A download is already in progress'
            }), 409
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
    webbrowser.open("http://localhost/")


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

# 添加下载历史记录管理


class DownloadHistory:
    """下载历史记录管理"""

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.history_file = os.path.join(base_dir, Config.HISTORY_FILE)
        self.load_history()

    def load_history(self):
        """加载下载历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            logging.error("加载历史记录失败：%s", e)
            self.history = []

    def save_history(self):
        """保存下载历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error("保存历史记录失败：%s", e)

    def add_record(self, url, file_path, file_type="file", status="completed"):
        """添加下载记录"""
        try:
            record = {
                "url": url,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_type": file_type,
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": status
            }
            self.history.insert(0, record)  # 新记录插入到最前面
            self.save_history()
        except Exception as e:
            logging.error("添加下载记录失败：%s", e)

    def remove_record(self, file_path, delete_file=False):
        """删除下载记录"""
        try:
            self.history = [h for h in self.history if h["file_path"] != file_path]
            self.save_history()
            if delete_file and os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            logging.error("删除记录失败：%s", e)
            return False
        return True

    def get_history(self, limit=50):
        """获取下载历史"""
        return self.history[:limit]


# 创建全局下载历史管理器
download_history = DownloadHistory()


@app.route('/download_history', methods=['GET'])
def get_download_history():
    """获取下载历史"""
    try:
        history = download_history.get_history()
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete_download', methods=['POST'])
def delete_download():
    """删除下载记录和文件"""
    try:
        file_path = request.json.get('file_path')
        delete_file = request.json.get('delete_file', False)

        if not file_path:
            return jsonify({'status': 'error', 'message': '未提供文件路径'}), 400

        if download_history.remove_record(file_path, delete_file):
            return jsonify({'status': 'success', 'message': '删除成功'})
        else:
            return jsonify({'status': 'error', 'message': '删除失败'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)  # 启动 Flask 服务 并且可以局域网访问 不要改端口！
