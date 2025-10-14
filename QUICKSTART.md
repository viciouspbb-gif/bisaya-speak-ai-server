# クイックスタートガイド - Bisaya Speak AI

Bisaya Speak AI サーバーを最速でセットアップして動作確認するためのガイドです。

## 📋 前提条件

- Python 3.8 以上がインストールされていること
- インターネット接続（パッケージのインストール用）

## 🚀 5分でセットアップ

### ステップ1: 仮想環境の作成と有効化

```powershell
# プロジェクトディレクトリに移動
cd C:\Users\katsunori\CascadeProjects\bisaya-pronunciation-server

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
venv\Scripts\activate
```

### ステップ2: 依存パッケージのインストール

```powershell
pip install -r requirements.txt
```

⏱️ **所要時間**: 約2-3分

### ステップ3: 参照音声ファイルの生成

```powershell
python generate_reference_audio.py
```

このコマンドで以下が生成されます：
- `reference_audio/` ディレクトリ
- 10個のビサヤ語フレーズのテスト用参照音声
- 参照音声の説明README

⚠️ **重要**: これらはテスト用のダミー音声です。本番環境では実際のネイティブスピーカーの音声に置き換えてください。

### ステップ4: サーバーの起動

```powershell
python main.py
```

✅ サーバーが起動したら、以下のメッセージが表示されます：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### ステップ5: 動作確認

新しいターミナルを開いて、以下のコマンドを実行：

```powershell
# 仮想環境を有効化
cd C:\Users\katsunori\CascadeProjects\bisaya-pronunciation-server
venv\Scripts\activate

# テストスクリプトを実行
python test_pronunciation.py
```

## 🧪 テスト結果の確認

テストが成功すると、以下のような出力が表示されます：

```
============================================================
Bisaya Speak AI - Test Suite
============================================================

1. Checking server status...
✓ Server is running

2. Creating test audio...
✓ Created test audio: test_user_audio.wav

3. Testing pronunciation evaluation...
============================================================
Testing pronunciation for: 'maayong buntag' (Level: beginner)
============================================================

✓ Status: success
✓ Message: Audio file received and processed with reference comparison

📊 Results:
  - Word: maayong buntag
  - Level: beginner
  - Pronunciation Score: 82.5

💬 Feedback:
  - Rating: Good
  - Overall: Good pronunciation! Keep practicing to improve further.

  📝 Details:
    • Pitch: Your pitch is good!
    • Timing: Your timing is excellent!

  💡 Tips: Focus on listening to native speakers and repeating after them.
```

## 🌐 ブラウザで確認

サーバーが起動している状態で、以下のURLにアクセス：

### API仕様書（Swagger UI）
```
http://localhost:8000/docs
```

### 代替ドキュメント（ReDoc）
```
http://localhost:8000/redoc
```

### ヘルスチェック
```
http://localhost:8000/
```

## 📡 APIの使い方

### curlでテスト

```powershell
# 音声ファイルを送信して発音評価を受ける
curl -X POST "http://localhost:8000/api/pronounce/check" `
  -F "audio=@your_audio.wav" `
  -F "word=maayong buntag" `
  -F "level=beginner"
```

### レベルの種類

- `beginner` - 初級（評価基準: 緩め）
- `intermediate` - 中級（評価基準: 標準）
- `advanced` - 上級（評価基準: 厳しめ）

## 🎯 評価スコアの見方

| スコア範囲 | 初級 | 中級 | 上級 |
|-----------|------|------|------|
| 90-100 | Excellent | Excellent | Excellent |
| 75-89 | Excellent | Good | Good |
| 60-74 | Good | Good | Fair |
| 45-59 | Good | Fair | Needs Improvement |
| 0-44 | Fair | Needs Improvement | Needs Improvement |

## 🔧 トラブルシューティング

### ポート8000が使用中

```powershell
# 別のポートで起動
uvicorn main:app --port 8001
```

### パッケージのインストールエラー

```powershell
# pipをアップグレード
python -m pip install --upgrade pip

# 再度インストール
pip install -r requirements.txt
```

### PyAudioのインストールエラー

PyAudioはオプションのパッケージです。インストールに失敗しても、基本機能は動作します。

## 📝 次のステップ

1. **実際のネイティブ音声を録音**
   - ビサヤ語ネイティブスピーカーに協力を依頼
   - 静かな環境で高品質なマイクを使用
   - `reference_audio/` ディレクトリに配置

2. **Kotlinアプリとの統合**
   - README.mdのKotlinサンプルコードを参照
   - サーバーのIPアドレスを設定
   - OkHttpを使用してAPIにリクエスト

3. **本番環境へのデプロイ**
   - CORS設定を適切に変更
   - 環境変数で設定を管理
   - HTTPSを有効化

## 📚 詳細ドキュメント

より詳しい情報は `README.md` を参照してください。

## 🆘 サポート

問題が発生した場合は、以下を確認してください：
- Python のバージョン（3.8以上）
- 仮想環境が有効化されているか
- すべての依存パッケージがインストールされているか
- ポート8000が他のプロセスで使用されていないか
