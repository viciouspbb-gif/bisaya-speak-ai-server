# Python 3.12ベースイメージ
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージを更新し、FFmpegをインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
