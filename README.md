# 文件下载程序

这是一个支持多语言的文件下载程序，具有进度显示、错误处理和 MD5 校验功能。

## 特性

- 支持通过 URL 下载文件
- 显示下载进度
- 支持取消下载
- 自动重试功能
- 支持文件的 MD5 校验
- 中英文消息支持

## 安装

确保您的环境中安装了 Python 3.x 和 `requests` 库。可以使用以下命令安装所需的库：

```bash
pip install requests tqdm
```

## 使用

可以通过命令行运行程序，传入要下载的文件的 URL：

```python
python download.py <url>
```

### 参数说明

- `url`：要下载的文件的 URL。
- `--path`：保存文件的路径，默认为当前目录。
- `--retries`：下载失败时的最大重试次数，默认为 3。
- `--md5`：期望的文件 MD5 校验和，用于验证下载的文件。
- `--language`：消息的语言，支持 `en`（英文）和 `zh`（中文），默认为英文。

### 示例

```bash	
python download.py "https://example.com/file.iso" --path "./downloads" --retries 5 --md5 "expected_md5_hash" --language "zh"

```

## 取消下载

在下载进行时，您可以输入 `cancel` 以取消下载：

```python
Type 'cancel' to cancel the download: 
```

## MD5 校验

如果提供了 `--md5` 参数，程序将在下载完成后验证下载文件的 MD5 校验和。如果校验成功，将输出匹配信息，否则将输出不匹配的信息。

## 示例输出

```bash
Downloading file.iso: 100%|██████████| 1.00M/1.00M [00:01<00:00, 500kB/s]
Downloaded: ./downloads/file.iso
MD5 checksum matched.
```

## 许可证

此项目采用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。