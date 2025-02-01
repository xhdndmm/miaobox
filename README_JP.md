# Miaobox ファイルダウンローダー
[中文版](README.md)|[English](README-English.md)|[日本語](README_JP.md)
## これは何ですか？
非常にシンプルなファイルダウンロードツールで、以下のものをダウンロードできます：
- インターネット上のさまざまなファイル
- YouTube動画（字幕のダウンロードをサポート）
- Bilibili動画（プレミアムコンテンツをサポート）
- その他の動画サイトのコンテンツ

## 機能の特徴
- 🎥 自動で最も高画質の動画を選択
- 💾 レジューム機能をサポート（ダウンロード中断後に続行可能）
- 📥 複数ファイルの一括ダウンロードが可能
- 📝 ダウンロード履歴を保存
- 🚀 シンプルで使いやすいインターフェース

## 初心者向け使用ガイド（非常に詳細）

### ステップ1：必要なソフトウェアのインストール

#### Windowsユーザー：

1. Pythonのインストール（1回のみ）
   - このサイトを開く：https://www.python.org/downloads/
   - 大きな"Download Python"ボタンをクリックしてダウンロード
   - ダウンロードしたインストーラーをダブルクリックして実行
   - ⚠️重要：インストール時に"Add Python to PATH"オプションを必ずチェック！
   - "Install Now"をクリックしてインストール完了を待つ

2. FFmpegのインストール（1回のみ）
   - 簡単な方法（推奨）：
     1. Windowsキーを押して"PowerShell"と入力
     2. 検索結果で"Windows PowerShell"を右クリックし、"管理者として実行"を選択
     3. 以下のコマンドをコピーして、PowerShellウィンドウに右クリックで貼り付け、Enterキーを押す：
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
     ```
     4. インストール完了後、以下のコマンドを入力し、Enterキーを押す：
     ```powershell
     choco install ffmpeg
     ```

   - 手動インストール方法：
     1. サイトを開く：https://github.com/BtbN/FFmpeg-Builds/releases
     2. "win64-gpl"と名前の付いたzipファイルをダウンロード
     3. Cドライブのルートディレクトリに解凍し、`C:\ffmpeg`フォルダがあることを確認
     4. システム変数を設定：
        - Windowsキーを押して"環境変数"と入力
        - "システム環境変数の編集"をクリック
        - 下部の"環境変数"ボタンをクリック
        - 下の"システム変数"で"Path"を見つけてダブルクリック
        - "新規"をクリックし、`C:\ffmpeg\bin`を入力
        - "OK"をクリックしてすべての設定を保存

#### Macユーザー：

1. "ターミナル"を開く（ランチパッドで"ターミナル"または"Terminal"を検索）
2. 以下のコマンドをコピーして貼り付け、Enterキーを押す：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. 次にこのコマンドを入力して必要なソフトウェアをインストール：
   ```bash
   brew install python ffmpeg
   ```

### ステップ2：Miaoboxのダウンロードとインストール

1. プログラムファイルのダウンロード
   - アクセス：https://github.com/xhdndmm/miaobox/releases
   - 最新バージョンのzipファイルをダウンロード
   - デスクトップまたは好きな場所に解凍

2. プログラムのインストール
   - Windowsユーザー：
     1. Windowsキー+Rを押してcmdと入力し、Enterキーを押す
     2. 入力：`cd デスクトップ\miaobox`（解凍した場所に応じてパスを変更）
     3. 入力：`pip install -r requirements.txt`

   - Macユーザー：
     1. ターミナルを開く
     2. 入力：`cd Desktop/miaobox`（解凍した場所に応じてパスを変更）
     3. 入力：`pip3 install -r requirements.txt`

### ステップ3：プログラムの使用

1. プログラムの起動
   - Windowsユーザー：`start.bat`ファイルをダブルクリックして実行
   - Macユーザー：ターミナルで`python3 app.py`と入力

2. ブラウザでプログラムにアクセス
   - プログラムは自動でブラウザを開きます
   - 自動で開かない場合は、手動でブラウザを開いてhttp://localhost:5000にアクセス

### 動画ダウンロードのチュートリアル

#### YouTube動画のダウンロード：

1. 通常のダウンロード
   - YouTubeでダウンロードしたい動画を見つける
   - 動画のURLをコピー（ブラウザのアドレスバーの内容）
   - ダウンローダーの入力ボックスに貼り付け
   - "ダウンロード開始"をクリック

2. 字幕付き動画のダウンロード
   - 動画のURLをコピー
   - URLの後ろに`&sub=true`を追加
   - 例：`https://youtube.com/watch?v=XXXX&sub=true`
   - 入力ボックスに貼り付けてダウンロードをクリック

3. 指定の画質で動画をダウンロード
   - URLの後ろに`&quality=720p`を追加（オプション：360p、480p、720p、1080p）
   - 例：`https://youtube.com/watch?v=XXXX&quality=720p`

#### Bilibili動画のダウンロード：

1. 通常の動画ダウンロード
   - Bilibili動画のURLをコピー
   - 直接入力ボックスに貼り付け
   - ダウンロードをクリック

2. プレミアム動画のダウンロード
   - まずBilibiliのウェブページでアカウントにログイン
   - ダウンローダーの"クッキー管理"ボタンをクリック
   - 指示に従ってログイン情報をインポート
   - その後、プレミアム動画をダウンロード可能

### よくある問題の解決

1. ダウンロードが失敗した場合？
   - ネットワークが正常か確認
   - 動画がログインを必要とするか確認
   - Bilibiliのプレミアム動画の場合、クッキーが正しくインポートされたか確認
   - 再ダウンロードを試みる

2. ダウンロードしたファイルが見つからない？
   - デフォルトで"ダウンロード"フォルダに保存
   - ダウンロード時に保存場所を指定可能
   - ダウンロード履歴から直接ファイルの場所を開ける

3. ダウンロード速度が遅い？
   - ネットワーク接続を確認
   - 他のネットワークを試す
   - 動画ソースがダウンロード速度を制限している可能性

4. プログラムが起動しない？
   - Pythonが正しくインストールされているか確認
   - すべての依存関係がインストールされているか確認
   - ウイルス対策ソフトがブロックしていないか確認

### ヘルプが必要？

- プログラムに問題がある場合は再起動を試みる
- 解決できない問題がある場合は、GitHubで問題を報告：https://github.com/xhdndmm/miaobox/issues
- またはTelegramグループに参加：https://t.me/miaoboxbug

### プライバシーに関する説明

- 本プログラムは個人情報を収集しません
- あなたのBilibiliログイン情報はローカルにのみ保存されます
- すべてのダウンロード履歴はあなたのコンピュータにのみ保存されます

### 免責事項

- 著作権侵害コンテンツをダウンロードしないでください
- 個人学習目的のみで使用してください
- ダウンロードしたコンテンツは24時間以内に削除してください