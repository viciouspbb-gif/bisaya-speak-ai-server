# Bisaya Speak AI

ビサヤ語の発音診断機能を提供するAI搭載Python APIサーバーです。Kotlinアプリからの音声データを受け取り、発音の評価とフィードバックを返します。

## 機能

- **音声ファイル受信**: Kotlinアプリから送信された音声ファイルを受け取る
- **発音分析**: Librosaを使用した音声特徴量の抽出
- **評価フィードバック**: 発音スコアと改善点の提供
- **RESTful API**: FastAPIベースの高速なAPIエンドポイント

## 技術スタック

- **フレームワーク**: FastAPI
- **音声処理**: Librosa, SoundFile
- **機械学習**: NumPy, SciPy, scikit-learn
- **サーバー**: Uvicorn

## セットアップ

### 1. 仮想環境の作成

```bash
python -m venv venv
```

### 2. 仮想環境の有効化

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 参照音声ファイルの生成

```bash
python generate_reference_audio.py
```

このスクリプトは、テスト用のダミー参照音声を生成します。
**本番環境では、実際のビサヤ語ネイティブスピーカーの音声に置き換えてください。**

### 5. 環境変数の設定（オプション）

```bash
cp .env.example .env
```

`.env`ファイルを編集して、必要に応じて設定を変更してください。

## サーバーの起動

### 開発モード（自動リロード有効）

```bash
python main.py
```

または

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 本番モード

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下のURLでアクセスできます：
- API: http://localhost:8000
- ドキュメント（Swagger UI）: http://localhost:8000/docs (Bisaya Speak AI API)
- 代替ドキュメント（ReDoc）: http://localhost:8000/redoc

## APIエンドポイント

### 1. ヘルスチェック

```
GET /
```

サーバーの稼働状況を確認します。

**レスポンス例:**
```json
{
  "status": "ok",
  "message": "Bisaya Pronunciation API is running",
  "version": "1.0.0"
}
```

### 2. 発音診断

```
POST /api/pronounce/check
```

音声ファイルを送信して発音診断を受けます。

**パラメータ:**
- `audio` (file, required): 音声ファイル（WAV, MP3, M4A, OGG, FLAC）
- `word` (string, optional): 発音対象の単語
- `language` (string, optional): 言語（デフォルト: "bisaya"）
- `level` (string, optional): ユーザーのレベル（beginner/intermediate/advanced、デフォルト: "beginner"）

**リクエスト例（curl）:**
```bash
curl -X POST "http://localhost:8000/api/pronounce/check" \
  -F "audio=@test_audio.wav" \
  -F "word=maayong buntag" \
  -F "language=bisaya" \
  -F "level=beginner"
```

**レスポンス例:**
```json
{
  "status": "success",
  "message": "Audio file received and processed with reference comparison",
  "data": {
    "filename": "test_audio.wav",
    "saved_as": "20241011_173000_test_audio.wav",
    "file_size": 156432,
    "word": "maayong buntag",
    "language": "bisaya",
    "level": "beginner",
    "pronunciation_score": 82.5,
    "feedback": {
      "overall": "Good pronunciation! Keep practicing to improve further.",
      "rating": "Good",
      "details": [
        {
          "aspect": "Pitch",
          "comment": "Your pitch is good!"
        },
        {
          "aspect": "Timing",
          "comment": "Your timing is excellent!"
        }
      ],
      "tips": "Focus on listening to native speakers and repeating after them."
    },
    "comparison_details": {
      "user_features": {
        "duration": 1.52,
        "pitch_mean": 215.3,
        "pitch_std": 12.5
      },
      "reference_features": {
        "duration": 1.48,
        "pitch_mean": 210.8,
        "pitch_std": 10.2
      }
    },
    "timestamp": "20241011_173000"
  }
}
```

### 3. 詳細ヘルスチェック

```
GET /api/health
```

サーバーの詳細な状態を確認します。

## Kotlinアプリからの接続例

```kotlin
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import org.json.JSONObject

fun uploadAudioFile(audioFile: File, word: String, level: String = "beginner") {
    val client = OkHttpClient()
    
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart(
            "audio",
            audioFile.name,
            audioFile.asRequestBody("audio/*".toMediaType())
        )
        .addFormDataPart("word", word)
        .addFormDataPart("language", "bisaya")
        .addFormDataPart("level", level)
        .build()
    
    val request = Request.Builder()
        .url("http://YOUR_SERVER_IP:8000/api/pronounce/check")
        .post(requestBody)
        .build()
    
    client.newCall(request).enqueue(object : Callback {
        override fun onFailure(call: Call, e: IOException) {
            // エラーハンドリング
            println("Error: ${e.message}")
        }
        
        override fun onResponse(call: Call, response: Response) {
            val responseBody = response.body?.string()
            if (response.isSuccessful && responseBody != null) {
                val json = JSONObject(responseBody)
                val data = json.getJSONObject("data")
                
                val score = data.getDouble("pronunciation_score")
                val feedback = data.getJSONObject("feedback")
                val rating = feedback.getString("rating")
                val overall = feedback.getString("overall")
                
                println("Score: $score")
                println("Rating: $rating")
                println("Feedback: $overall")
                
                // UIを更新
                // updateUI(score, rating, overall)
            }
        }
    })
}
```

## ディレクトリ構造

```
bisaya-pronunciation-server/
├── main.py                      # FastAPIアプリケーション本体
├── audio_processor.py           # 音声処理モジュール（DTW評価ロジック）
├── generate_reference_audio.py # 参照音声生成スクリプト
├── test_pronunciation.py        # 発音評価テストスクリプト
├── test_api.py                  # 基本APIテストスクリプト
├── requirements.txt             # 依存パッケージ
├── .env.example                # 環境変数のサンプル
├── .gitignore                  # Git除外設定
├── README.md                   # このファイル
├── uploads/                    # ユーザー音声保存ディレクトリ（自動生成）
└── reference_audio/            # 参照音声ディレクトリ（自動生成）
    ├── README.md               # 参照音声の説明
    ├── maayong_buntag_ref.wav  # 参照音声ファイル
    ├── salamat_ref.wav
    └── ...
```

## 実装済み機能

- ✅ **DTWベースの発音評価**: MFCCを使用した類似度計算
- ✅ **レベル対応フィードバック**: 初級/中級/上級に応じた評価基準
- ✅ **詳細な音声分析**: ピッチ、タイミング、音量の比較
- ✅ **参照音声システム**: ネイティブ音声との比較機能
- ✅ **RESTful API**: FastAPIによる高速なエンドポイント

## 今後の実装予定

- [ ] ディープラーニングモデルによる高度な発音評価
- [ ] ビサヤ語の音素別評価
- [ ] 音素レベルのフィードバック
- [ ] ユーザー認証機能
- [ ] 発音履歴の保存とトラッキング
- [ ] リアルタイム音声処理
- [ ] より多くのビサヤ語フレーズの参照音声

## トラブルシューティング

### PyAudioのインストールエラー

PyAudioはオプションのパッケージです。インストールに失敗する場合は、以下を試してください：

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

### ポート8000が使用中

別のポートを使用する場合：
```bash
uvicorn main:app --port 8001
```

## ライセンス

MIT License

## 開発者向けメモ

- 音声ファイルは`uploads/`ディレクトリに保存されます
- 本番環境では適切なCORS設定を行ってください
- ファイルサイズの制限を設定することを推奨します
#   b i s a y a - s p e a k - s e r v e r  
 