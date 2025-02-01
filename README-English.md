# Miaobox File Downloader
[中文版](README.md)|[English](README-English.md)|[日本語](README_JP.md)
## What is this?
A super simple file download tool that can help you download:
- Various files from the internet
- YouTube videos (supports subtitle download)
- Bilibili videos (supports premium content)
- Content from other video websites

## Features
- 🎥 Automatically selects the highest video quality
- 💾 Supports resuming interrupted downloads
- 📥 Can batch download multiple files
- 📝 Saves download history
- 🚀 Simple and easy-to-use interface

## Beginner's Guide (Super Detailed)

### Step 1: Install Necessary Software

#### For Windows Users:

1. Install Python (only once)
   - Open this website: https://www.python.org/downloads/
   - Click the big "Download Python" button to download
   - Double-click the downloaded installer to run it
   - ⚠️Important: Make sure to check the "Add Python to PATH" option during installation!
   - Click "Install Now" and wait for the installation to complete

2. Install FFmpeg (only once)
   - Simple method (recommended):
     1. Press the Windows key, type "PowerShell"
     2. Right-click "Windows PowerShell" in the search results and select "Run as administrator"
     3. Copy the command below, right-click to paste it into the PowerShell window, and press Enter:
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
     ```
     4. After installation, enter the following command and press Enter:
     ```powershell
     choco install ffmpeg
     ```

   - Manual installation method:
     1. Open the website: https://github.com/BtbN/FFmpeg-Builds/releases
     2. Download the zip file with "win64-gpl" in its name
     3. Extract it to the root directory of the C drive, ensuring there is a `C:\ffmpeg` folder
     4. Set system variables:
        - Press the Windows key, type "Environment Variables"
        - Click "Edit the system environment variables"
        - Click the "Environment Variables" button at the bottom
        - Find "Path" in the "System variables" section and double-click it
        - Click "New" and enter `C:\ffmpeg\bin`
        - Click "OK" to save all settings

#### For Mac Users:

1. Open "Terminal" (search for "Terminal" in Launchpad)
2. Copy and paste the following command and press Enter:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Then enter this command to install necessary software:
   ```bash
   brew install python ffmpeg
   ```

### Step 2: Download and Install Miaobox

1. Download the program files
   - Visit: https://github.com/xhdndmm/miaobox/releases
   - Download the latest version zip file
   - Extract it to the desktop or any location you prefer

2. Install the program
   - For Windows users:
     1. Press Windows key + R, type cmd, and press Enter
     2. Enter: `cd Desktop\miaobox` (modify the path if you extracted it elsewhere)
     3. Enter: `pip install -r requirements.txt`

   - For Mac users:
     1. Open Terminal
     2. Enter: `cd Desktop/miaobox` (modify the path if you extracted it elsewhere)
     3. Enter: `pip3 install -r requirements.txt`

### Step 3: Use the Program

1. Start the program
   - For Windows users: Double-click the `start.bat` file
   - For Mac users: Enter `python3 app.py` in Terminal

2. Access the program using a browser
   - The program will automatically open a browser
   - If it doesn't open automatically, manually open a browser and visit: http://localhost:5000

### Video Download Tutorial

#### YouTube Video Download:

1. Regular download
   - Find the video you want to download on YouTube
   - Copy the video URL (from the browser's address bar)
   - Paste it into the downloader's input box
   - Click "Start Download"

2. Download videos with subtitles
   - Copy the video URL
   - Add `&sub=true` to the end of the URL
   - For example: `https://youtube.com/watch?v=XXXX&sub=true`
   - Paste it into the input box and click download

3. Download videos with specified quality
   - Add `&quality=720p` to the end of the URL (options: 360p, 480p, 720p, 1080p)
   - For example: `https://youtube.com/watch?v=XXXX&quality=720p`

#### Bilibili Video Download:

1. Regular video download
   - Copy the Bilibili video URL
   - Directly paste it into the input box
   - Click download

2. Download premium videos
   - First, log in to your account on the Bilibili website
   - Click the "Manage Cookies" button in the downloader
   - Follow the prompts to import your login information
   - Then you can download premium videos

### Common Issues and Solutions

1. What to do if the download fails?
   - Check if the network is normal
   - Confirm if the video requires login
   - If it's a Bilibili premium video, check if cookies are correctly imported
   - Try downloading again

2. Can't find the downloaded files?
   - By default, they are saved in the "Downloads" folder
   - You can specify the save location during download
   - You can directly open the file location from the download history

3. Download speed is very slow?
   - Check the network connection
   - Try using another network
   - The video source may limit the download speed

4. The program won't start?
   - Confirm if Python is correctly installed
   - Check if all dependencies are installed
   - See if any antivirus software is blocking it

### Need Help?

- Try restarting the program if there are issues
- If you encounter unsolvable problems, you can submit an issue on GitHub: https://github.com/xhdndmm/miaobox/issues

### Privacy Statement

- This program does not collect any personal information
- Your Bilibili login information is only stored locally
- All download records are stored only on your computer

### Disclaimer

- Do not download infringing content
- For personal learning use only
- Please delete downloaded content within 24 hours