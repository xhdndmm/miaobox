#Python3.X
#by xhdndmm & Seikoa
#https://github.com/xhdndmm/miaobox

import requests
import os
import sys
import threading
from tqdm import tqdm
import hashlib
import argparse
import re
from flask import render_template, Flask, request, jsonify

app = Flask(__name__)

# 全局变量存储下载状态
download_thread = None
downloader = None

class Downloader:
    def __init__(self, url, save_path, max_retries=3, language='en'):
        self.url = url
        self.save_path = save_path
        self.max_retries = max_retries
        self.cancelled = False
        self.language = language
        self.messages = {
            'en': {
                'download_cancelled': "Download cancelled.",
                'downloaded': "Downloaded: {}",
                'error': "Error: {}. Retrying {}/{}...",
                'max_retries_exceeded': "Max retries exceeded.",
                'md5_matched': "MD5 checksum matched.",
                'md5_mismatch': "MD5 checksum does not match! Expected: {}, Found: {}",
                'progress_desc': "Downloading {}"
            },
            'zh': {
                'download_cancelled': "下载已取消。",
                'downloaded': "已下载: {}",
                'error': "错误: {}。重试 {}/{}...",
                'max_retries_exceeded': "超过最大重试次数。",
                'md5_matched': "MD5 校验和匹配。",
                'md5_mismatch': "MD5 校验和不匹配！预期: {}, 发现: {}",
                'progress_desc': "正在下载 {}"
            }
        }

    def clean_filename(self, url):
        return re.sub(r'[<>:"/\\|?*]', '_', os.path.basename(url.split('?')[0]))

    def download(self):
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))

        with requests.get(self.url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(self.save_path, 'wb') as file, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=self.messages[self.language]['progress_desc'].format(os.path.basename(self.save_path)),
                leave=True
            ) as bar:
                for data in response.iter_content(chunk_size=4096):
                    if self.cancelled:
                        print(self.messages[self.language]['download_cancelled'])
                        return
                    file.write(data)
                    bar.update(len(data))

    def start_download(self):
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.download()
                print(self.messages[self.language]['downloaded'].format(self.save_path))
                break
            except Exception as e:
                attempts += 1
                print(self.messages[self.language]['error'].format(e, attempts, self.max_retries))
                if attempts == self.max_retries:
                    print(self.messages[self.language]['max_retries_exceeded'])
                    sys.exit(1)

    def cancel_download(self):
        self.cancelled = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    global download_thread, downloader

    url = request.json.get('url')
    save_path = request.json.get('path', './')
    retries = request.json.get('retries', 3)
    language = request.json.get('language', 'en')

    file_name = Downloader(url, '', retries, language).clean_filename(url)
    save_path = os.path.join(save_path, file_name)

    downloader = Downloader(url, save_path, retries, language)

    download_thread = threading.Thread(target=downloader.start_download)
    download_thread.start()
    return jsonify({'status': 'Download started', 'file': file_name})

@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    global download_thread, downloader

    if downloader:
        downloader.cancel_download()
        if download_thread.is_alive():
            download_thread.join()
        return jsonify({'status': 'Download cancelled'})
    return jsonify({'status': 'No active download'})

@app.route('/download_status', methods=['GET'])
def download_status():
    if download_thread and download_thread.is_alive():
        return jsonify({'status': 'Downloading'})
    elif downloader and downloader.cancelled:
        return jsonify({'status': 'Cancelled'})
    elif downloader:
        return jsonify({'status': 'Completed'})
    return jsonify({'status': 'No download started'})

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80)

