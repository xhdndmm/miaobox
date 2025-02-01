import os
import yt_dlp
from flask import Flask, request, jsonify
from urllib.parse import urlparse
import threading
import time

app = Flask(__name__)

# 全局变量存储下载状态
download_status = {
    'status': 'idle',
    'progress': {
        'percentage': 0,
        'downloaded': '0 MB',
        'total': '0 MB',
        'speed': '0 MB/s',
        'eta': '未知'
    }
}

def format_size(bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def format_time(seconds):
    """格式化时间"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        return f"{seconds//60:.0f}分{seconds%60:.0f}秒"
    else:
        return f"{seconds//3600:.0f}时{(seconds%3600)//60:.0f}分"

class DownloadProgress:
    """下载进度回调类"""
    def __init__(self):
        self.start_time = time.time()
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                percentage = (downloaded / total) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                download_status['progress'] = {
                    'percentage': percentage,
                    'downloaded': format_size(downloaded),
                    'total': format_size(total),
                    'speed': format_size(speed) + '/s' if speed else '计算中',
                    'eta': format_time(eta) if eta else '计算中'
                }
                
        elif d['status'] == 'finished':
            download_status['status'] = 'completed'

def download_youtube(url, output_path, sub=False, quality=None):
    """下载YouTube视频"""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]' if quality else 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'progress_hooks': [DownloadProgress()],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }
    
    if sub:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh-Hans', 'en'],  # 下载中文和英文字幕
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            download_status['status'] = 'downloading'
            ydl.download([url])
            return True, "下载完成"
    except Exception as e:
        return False, str(e)

@app.route('/start_download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url')
    path = data.get('path', 'downloads')  # 默认下载目录
    
    if not url:
        return jsonify({'status': 'error', 'message': '请提供下载链接'}), 400
        
    # 创建下载目录
    os.makedirs(path, exist_ok=True)
    
    # 重置下载状态
    download_status['status'] = 'starting'
    download_status['progress'] = {
        'percentage': 0,
        'downloaded': '0 MB',
        'total': '0 MB',
        'speed': '0 MB/s',
        'eta': '未知'
    }
    
    # 判断是否是YouTube链接
    if 'youtube.com' in url or 'youtu.be' in url:
        sub = data.get('sub', False)
        quality = data.get('quality', '').replace('p', '')  # 移除质量后缀的'p'
        if quality and not quality.isdigit():
            quality = None
            
        # 在新线程中启动下载
        thread = threading.Thread(
            target=download_youtube,
            args=(url, path, sub, quality)
        )
        thread.start()
        
        return jsonify({
            'status': 'Download started',
            'file': '正在获取视频信息...',
            'message': '开始下载YouTube视频'
        })
    else:
        # 处理普通文件下载的逻辑...
        pass

@app.route('/download_status')
def get_download_status():
    return jsonify({
        'status': download_status['status'],
        'progress': download_status['progress']
    })

@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    global download_status
    download_status['status'] = 'cancelled'
    # 这里可以添加实际取消下载的逻辑
    return jsonify({'status': '下载已取消'})

if __name__ == '__main__':
    app.run(debug=True) 