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
                'cancel_prompt': "Type 'cancel' to cancel the download: ",
                'progress_desc': "Downloading {}"
            },
            'zh': {
                'download_cancelled': "下载已取消。",
                'downloaded': "已下载: {}",
                'error': "错误: {}。重试 {}/{}...",
                'max_retries_exceeded': "超过最大重试次数。",
                'md5_matched': "MD5 校验和匹配。",
                'md5_mismatch': "MD5 校验和不匹配！预期: {}, 发现: {}",
                'cancel_prompt': "输入 'cancel' 以取消下载: ",
                'progress_desc': "正在下载 {}"
            }
        }

    def clean_filename(self, url):
        # 使用正则表达式替换非法字符
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

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Download files with progress and error handling.")
    parser.add_argument('url', type=str, help='The URL of the file to download')
    parser.add_argument('--path', type=str, default='./', help='The path to save the downloaded file')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries on failure')
    parser.add_argument('--md5', type=str, help='Expected MD5 checksum for file validation')
    parser.add_argument('--language', type=str, choices=['en', 'zh'], default='en', help='Language for messages')

    args = parser.parse_args()

    # 清理文件名
    file_name = Downloader(args.url, '', args.retries, args.language).clean_filename(args.url)
    save_path = os.path.join(args.path, file_name)

    downloader = Downloader(args.url, save_path, args.retries, args.language)

    download_thread = threading.Thread(target=downloader.start_download)
    download_thread.start()

    try:
        while download_thread.is_alive():
            command = input(downloader.messages[args.language]['cancel_prompt'])
            if command.lower() == 'cancel':
                downloader.cancel_download()
                download_thread.join()
                break
    except KeyboardInterrupt:
        downloader.cancel_download()
        download_thread.join()

    if args.md5 and os.path.exists(save_path):
        downloaded_md5 = calculate_md5(save_path)
        if downloaded_md5 == args.md5:
            print(downloader.messages[args.language]['md5_matched'])
        else:
            print(downloader.messages[args.language]['md5_mismatch'].format(args.md5, downloaded_md5))

if __name__ == "__main__":
    main()
