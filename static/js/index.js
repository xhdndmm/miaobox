function updateProgress(progressData) {
    const progressBar = document.getElementById('progress-bar');
    const progressContainer = document.getElementById('progress-container');
    const downloadedSize = document.getElementById('downloaded-size');
    const totalSize = document.getElementById('total-size');
    const downloadSpeed = document.getElementById('download-speed');
    const remainingTime = document.getElementById('remaining-time');
    const percentage = document.getElementById('percentage');

    progressContainer.style.display = 'block';
    progressBar.style.width = progressData.percentage + '%';
    
    // 更新详细信息
    downloadedSize.textContent = progressData.downloaded;
    totalSize.textContent = progressData.total;
    downloadSpeed.textContent = progressData.speed;
    remainingTime.textContent = progressData.eta;
    percentage.textContent = progressData.percentage.toFixed(1) + '%';
}

function startDownload() {
    const url = document.getElementById('url').value;
    const path = document.getElementById('path').value || "";
    const status = document.getElementById('status');
    status.innerText = "下载状态：正在启动下载...";
    status.classList.remove('error');
    const progressContainer = document.getElementById('progress-container');
    progressContainer.style.display = 'block';

    // 解析YouTube下载参数
    const params = {};
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        const urlObj = new URL(url);
        params.sub = urlObj.searchParams.get('sub') === 'true';
        params.quality = urlObj.searchParams.get('quality');
        // 清理URL中的参数
        urlObj.searchParams.delete('sub');
        urlObj.searchParams.delete('quality');
        params.url = urlObj.toString();
    } else {
        params.url = url;
    }

    fetch('/start_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, path })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || "未知错误");
            });
        }
        return response.json();
    })
    .then(data => {
        status.innerText = `下载状态：${data.status}，文件名：${data.file}`;
        if (data.status === 'Download started') {
            const interval = setInterval(() => {
                fetch('/download_status')
                    .then(response => response.json())
                    .then(statusData => {
                        if (statusData.status === 'Downloading') {
                            updateProgress(statusData.progress);
                        } else {
                            clearInterval(interval);
                            progressContainer.style.display = 'none';
                        }
                    });
            }, 1000);
        }
    })
    .catch(err => {
        status.innerText = `下载状态：错误 - ${err.message}`;
        status.classList.add('error');
    });
}

function cancelDownload() {
    const status = document.getElementById('status');
    status.innerText = "下载状态：正在取消下载...";
    status.classList.remove('error');
    fetch('/cancel_download', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            status.innerText = `下载状态：${data.status}`;
        })
        .catch(() => {
            status.innerText = "取消失败";
            status.classList.add('error');
        });
}

function startVideoDownload() {
    const videoUrl = document.getElementById('video-url').value;
    const status = document.getElementById('status');
    status.innerText = "下载状态：正在启动视频下载...";
    status.classList.remove('error');
    const progressContainer = document.getElementById('progress-container');
    progressContainer.style.display = 'block';

    fetch('/start_video_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videoUrl })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || "未知错误");
            });
        }
        return response.json();
    })
    .then(data => {
        status.innerText = `下载状态：${data.status}，文件名：${data.file}`;
        if (data.status === 'Download started') {
            const interval = setInterval(() => {
                fetch('/download_status')
                    .then(response => response.json())
                    .then(statusData => {
                        if (statusData.status === 'Downloading') {
                            updateProgress(statusData);
                        } else {
                            clearInterval(interval);
                            progressContainer.style.display = 'none';
                        }
                    });
            }, 1000);
        }
    })
    .catch(err => {
        status.innerText = `下载状态：错误 - ${err.message}`;
        status.classList.add('error');
    });
}

function startBatchDownload() {
    const urlsText = document.getElementById('batch-urls').value;
    const path = document.getElementById('path').value || "";
    const status = document.getElementById('status');
    const batchResults = document.getElementById('batch-results');
    
    // 分割URL（支持换行符分隔的URL列表）
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
        
    if (urls.length === 0) {
        status.innerText = "请输入至少一个下载链接";
        status.classList.add('error');
        return;
    }

    status.innerText = "批量下载状态：正在启动...";
    status.classList.remove('error');
    batchResults.style.display = 'none';

    fetch('/start_batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls, path })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Batch download started') {
            status.innerText = `批量下载已开始，共 ${data.total_files} 个文件`;
            checkBatchStatus();
        } else {
            throw new Error(data.message);
        }
    })
    .catch(err => {
        status.innerText = `错误：${err.message}`;
        status.classList.add('error');
    });
}

function checkBatchStatus() {
    const interval = setInterval(() => {
        fetch('/batch_download_status')
            .then(response => response.json())
            .then(data => {
                const batchResults = document.getElementById('batch-results');
                const status = document.getElementById('status');
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    status.innerText = "批量下载已完成";
                    
                    // 显示详细结果
                    let resultsHtml = '<h3>下载结果：</h3><ul>';
                    data.results.forEach(result => {
                        resultsHtml += `<li>${result.url}: ${result.status}`;
                        if (result.error) {
                            resultsHtml += ` - ${result.error}`;
                        }
                        resultsHtml += '</li>';
                    });
                    resultsHtml += '</ul>';
                    
                    batchResults.innerHTML = resultsHtml;
                    batchResults.style.display = 'block';
                }
            });
    }, 1000);
}

function loadDownloadHistory() {
    fetch('/download_history')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayHistory(data.history);
            }
        })
        .catch(err => {
            console.error('加载历史记录失败:', err);
        });
}

function displayHistory(history) {
    const container = document.getElementById('history-container');
    if (!history || history.length === 0) {
        container.innerHTML = '<p>暂无下载记录</p>';
        return;
    }
    
    let html = '<h3>下载历史</h3>';
    history.forEach(item => {
        html += `
            <div class="history-item">
                <div class="history-info">
                    <div>${item.file_name}</div>
                    <div class="file-size">大小: ${formatSize(item.file_size)}</div>
                    <div class="download-time">下载时间: ${item.download_time}</div>
                </div>
                <div class="history-actions">
                    <button onclick="openFile('${item.file_path}')">打开文件夹</button>
                    <button class="delete-btn" onclick="deleteDownload('${item.file_path}', true)">删除</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function openFile(filePath) {
    // 打开文件所在文件夹
    const dirPath = filePath.substring(0, filePath.lastIndexOf('/'));
    window.open('file:///' + dirPath);
}

function deleteDownload(filePath, deleteFile = false) {
    if (!confirm('确定要删除这条记录吗？' + (deleteFile ? '（文件也会被删除）' : ''))) {
        return;
    }
    
    fetch('/delete_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath, delete_file: deleteFile })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadDownloadHistory();  // 重新加载历史记录
        } else {
            alert('删除失败：' + data.message);
        }
    })
    .catch(err => {
        console.error('删除失败:', err);
        alert('删除失败，请重试');
    });
}

// 页面加载完成后加载历史记录
document.addEventListener('DOMContentLoaded', function() {
    loadDownloadHistory();
});

function updateProgress(data) {
    if (data.status === 'Downloading') {
        $('#progress').show();
        const progress = data.progress;
        $('#progress-percentage').text(progress.percentage.toFixed(1));
        $('#downloaded-size').text(progress.downloaded);
        $('#total-size').text(progress.total);
        $('#download-speed').text(progress.speed);
        $('#eta').text(progress.eta);
        $('#progress-bar').css('width', progress.percentage + '%');

        // 更新线程进度
        if (progress.threads) {
            const threadList = $('#thread-list');
            threadList.empty();
            progress.threads.forEach(thread => {
                const threadHtml = `
                    <div class="thread-item">
                        <div class="thread-info">
                            <span>线程 ${thread.thread_id}</span>
                            <span>${thread.percentage.toFixed(1)}%</span>
                        </div>
                        <div class="progress thread-progress">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${thread.percentage}%" 
                                 title="下载范围: ${thread.range}">
                            </div>
                        </div>
                        <div class="thread-info">
                            <small>已下载: ${thread.downloaded}</small>
                            <small>总大小: ${thread.total}</small>
                        </div>
                    </div>
                `;
                threadList.append(threadHtml);
            });
        }
    } else {
        $('#progress').hide();
    }
}