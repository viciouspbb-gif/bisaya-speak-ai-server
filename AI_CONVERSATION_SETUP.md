# AI会話機能セットアップガイド

## 📋 概要

Bisaya Speak AIに本格的なAI会話機能が追加されました！

### 新機能
- ✅ **リアルタイムAI会話** - Gemini APIによる自然な対話
- ✅ **音声認識** - ユーザーの発話を自動認識
- ✅ **音声合成** - AIの応答を音声で再生
- ✅ **シナリオ練習** - 実践的な会話シミュレーション
- ✅ **フレーズ指導** - AIが講師として文法・発音を教える
- ✅ **学習フィードバック** - 会話後の詳細な分析とアドバイス

---

## 🚀 セットアップ手順

### 1. 必要なパッケージのインストール

```powershell
cd C:\Users\katsunori\CascadeProjects\bisaya-pronunciation-server
pip install -r requirements.txt
```

### 2. Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. APIキーをコピー

### 3. 環境変数の設定

`.env`ファイルを作成（`.env.example`をコピー）：

```powershell
copy .env.example .env
```

`.env`ファイルを編集してAPIキーを設定：

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. サーバーの起動

```powershell
python main.py
```

サーバーが起動すると、以下のメッセージが表示されます：

```
✓ Conversation Engine initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🎯 API エンドポイント

### 1. 会話セッションの作成

**エンドポイント:** `POST /api/conversation/session/create`

**パラメータ:**
- `mode`: 会話モード
  - `shadowing` - シャドーイング練習
  - `word_drill` - 単語ドリル
  - `roleplay` - ロールプレイ
  - `free_talk` - フリートーク
- `level`: ユーザーレベル（`beginner`, `intermediate`, `advanced`）
- `scenario_id`: シナリオID（roleplayモードの場合）

**例:**
```bash
curl -X POST "http://localhost:8000/api/conversation/session/create" \
  -F "mode=free_talk" \
  -F "level=beginner"
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session_20251019_093700",
    "mode": "free_talk",
    "level": "beginner",
    "status": "created"
  }
}
```

### 2. メッセージの送信

**エンドポイント:** `POST /api/conversation/message`

**パラメータ:**
- `session_id`: セッションID
- `audio`: 音声ファイル（オプション）
- `text`: テキストメッセージ（オプション）

**例（テキスト）:**
```bash
curl -X POST "http://localhost:8000/api/conversation/message" \
  -F "session_id=session_20251019_093700" \
  -F "text=Maayong buntag"
```

**例（音声）:**
```bash
curl -X POST "http://localhost:8000/api/conversation/message" \
  -F "session_id=session_20251019_093700" \
  -F "audio=@recording.wav"
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "ai_message": "Maayong buntag sad! （おはようございます！）\n\n発音のポイント：'ng'の音は鼻音です。",
    "bisaya_text": "Maayong buntag sad!",
    "japanese_translation": "おはようございます！",
    "pronunciation_tips": "発音のポイント：'ng'の音は鼻音です。",
    "audio_url": "/api/audio/response_20251019_093701.mp3"
  },
  "transcription": "Maayong buntag"
}
```

### 3. シナリオ一覧の取得

**エンドポイント:** `GET /api/scenarios`

**パラメータ:**
- `difficulty`: 難易度フィルター（オプション）

**例:**
```bash
curl "http://localhost:8000/api/scenarios?difficulty=beginner"
```

**レスポンス:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "market_001",
      "title": "市場で値切る",
      "title_bisaya": "Pagpamalit sa merkado",
      "description": "地元の市場でフルーツを買います",
      "difficulty": "beginner",
      "estimated_turns": 7,
      "key_phrases": [
        "Pila ni? (いくらですか)",
        "Mahal kaayo (高すぎます)"
      ]
    }
  ]
}
```

### 4. 会話サマリーの取得

**エンドポイント:** `GET /api/conversation/session/{session_id}/summary`

**例:**
```bash
curl "http://localhost:8000/api/conversation/session/session_20251019_093700/summary"
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session_20251019_093700",
    "mode": "free_talk",
    "level": "beginner",
    "total_turns": 5,
    "duration_estimate": 150,
    "user_messages_count": 5,
    "ai_messages_count": 5
  }
}
```

### 5. 学習フィードバックの取得

**エンドポイント:** `GET /api/conversation/session/{session_id}/feedback`

**例:**
```bash
curl "http://localhost:8000/api/conversation/session/session_20251019_093700/feedback"
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "feedback": "【良かった点】\n1. 基本的な挨拶の発音が正確でした\n2. 積極的に会話に参加していました\n\n【改善点】\n1. 動詞の活用に注意しましょう\n2. 発話速度をもう少し上げましょう\n\n【次回のアドバイス】\n1. 疑問文の練習をしましょう\n2. 日常会話のフレーズを増やしましょう"
  }
}
```

### 6. 音声認識

**エンドポイント:** `POST /api/speech/transcribe`

**パラメータ:**
- `audio`: 音声ファイル
- `language`: 言語（`bisaya`, `en`, `ja`）

**例:**
```bash
curl -X POST "http://localhost:8000/api/speech/transcribe" \
  -F "audio=@recording.wav" \
  -F "language=bisaya"
```

---

## 📱 Android アプリとの統合

### Kotlin コード例

```kotlin
// 1. 会話セッションを作成
suspend fun createConversationSession(mode: String, level: String): ConversationSession {
    val response = apiService.createConversationSession(mode, level)
    return response.data
}

// 2. 音声メッセージを送信
suspend fun sendAudioMessage(sessionId: String, audioFile: File): ConversationResponse {
    val audioPart = MultipartBody.Part.createFormData(
        "audio",
        audioFile.name,
        audioFile.asRequestBody("audio/wav".toMediaTypeOrNull())
    )
    val sessionIdPart = sessionId.toRequestBody("text/plain".toMediaTypeOrNull())
    
    val response = apiService.sendConversationMessage(sessionIdPart, audioPart, null)
    return response.data
}

// 3. テキストメッセージを送信
suspend fun sendTextMessage(sessionId: String, text: String): ConversationResponse {
    val response = apiService.sendConversationMessage(
        sessionId.toRequestBody("text/plain".toMediaTypeOrNull()),
        null,
        text.toRequestBody("text/plain".toMediaTypeOrNull())
    )
    return response.data
}

// 4. フィードバックを取得
suspend fun getSessionFeedback(sessionId: String): String {
    val response = apiService.getSessionFeedback(sessionId)
    return response.data.feedback
}
```

### API Service インターフェース

```kotlin
interface BisayaSpeakApiService {
    @Multipart
    @POST("api/conversation/session/create")
    suspend fun createConversationSession(
        @Part("mode") mode: RequestBody,
        @Part("level") level: RequestBody,
        @Part("scenario_id") scenarioId: RequestBody? = null
    ): ApiResponse<ConversationSession>
    
    @Multipart
    @POST("api/conversation/message")
    suspend fun sendConversationMessage(
        @Part("session_id") sessionId: RequestBody,
        @Part audio: MultipartBody.Part?,
        @Part("text") text: RequestBody?
    ): ApiResponse<ConversationResponse>
    
    @GET("api/scenarios")
    suspend fun getScenarios(
        @Query("difficulty") difficulty: String? = null
    ): ApiResponse<List<Scenario>>
    
    @GET("api/conversation/session/{session_id}/summary")
    suspend fun getSessionSummary(
        @Path("session_id") sessionId: String
    ): ApiResponse<SessionSummary>
    
    @GET("api/conversation/session/{session_id}/feedback")
    suspend fun getSessionFeedback(
        @Path("session_id") sessionId: String
    ): ApiResponse<FeedbackResponse>
}
```

---

## 🧪 テスト方法

### 1. 基本的な会話テスト

```powershell
# セッション作成
$session = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/conversation/session/create" -Form @{
    mode = "free_talk"
    level = "beginner"
}

$sessionId = $session.data.session_id
Write-Host "Session ID: $sessionId"

# メッセージ送信
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/conversation/message" -Form @{
    session_id = $sessionId
    text = "Kumusta ka?"
}

Write-Host "AI Response: $($response.data.ai_message)"
```

### 2. シナリオテスト

```powershell
# シナリオ一覧を取得
$scenarios = Invoke-RestMethod -Uri "http://localhost:8000/api/scenarios"
$scenarios.data | Format-Table id, title, difficulty

# ロールプレイセッションを作成
$session = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/conversation/session/create" -Form @{
    mode = "roleplay"
    level = "beginner"
    scenario_id = "market_001"
}

Write-Host "First Message: $($session.data.first_message.bisaya)"
Write-Host "Translation: $($session.data.first_message.japanese)"
```

---

## 💡 使用例

### シナリオ1: フリートーク

```
ユーザー: "Maayong buntag"
AI: "Maayong buntag sad! （おはようございます！）
     発音のポイント：'ng'の音は鼻音です。舌を口蓋に付けて発音しましょう。"

ユーザー: "Kumusta ka?"
AI: "Maayo man ko, salamat! （元気です、ありがとう！）
     'Kumusta'は英語の'How are you?'に相当します。
     返事は'Maayo man ko'（元気です）が一般的です。"
```

### シナリオ2: 市場でのロールプレイ

```
AI（果物売り）: "Maayong buntag! Unsa imong gusto?"
                （おはよう！何が欲しいですか？）

ユーザー: "Pila ang mangga?"
         （マンゴーはいくらですか？）

AI: "Lima ka pesos ang usa. （1個5ペソです）
     ヒント：値切りたい場合は'Mahal kaayo'（高すぎます）と言いましょう。"

ユーザー: "Mahal kaayo. Pwede ba og diskwento?"
         （高すぎます。割引できますか？）

AI: "Sige, upat ka pesos na lang. （OK、4ペソにします）
     素晴らしい！値切りの表現を上手に使えました！"
```

---

## 🎓 学習モード

### 1. シャドーイング（Shadowing）
- AIがフレーズを提示
- ユーザーが繰り返し発音
- 発音スコアと改善点を即座にフィードバック

### 2. 単語ドリル（Word Drill）
- AIが単語を提示
- ユーザーがその単語を使った例文を作成
- 文法と発音の両方をチェック

### 3. ロールプレイ（Roleplay）
- 実際の場面を想定した会話
- 市場、タクシー、レストランなどのシナリオ
- 自然な会話の流れを重視

### 4. フリートーク（Free Talk）
- 自由な会話
- レベルに応じて語彙と文法を調整
- 間違いを自然に訂正

---

## 📊 料金について

### Gemini API（無料枠）
- **月間リクエスト**: 60回/分
- **1ユーザーあたり**: 1日10会話 = 月300会話
- **無料で対応可能**: 約100ユーザー

### 有料プラン（必要になった場合）
- **Gemini Pro**: $0.00025/1Kトークン
- **1会話（平均2000トークン）**: $0.0005
- **月1000ユーザー × 10会話**: 約$5/月

**結論**: 初期は無料枠で十分対応可能

---

## 🔧 トラブルシューティング

### エラー: "Conversation engine not available"

**原因**: Gemini APIキーが設定されていない

**解決方法**:
1. `.env`ファイルに`GEMINI_API_KEY`を設定
2. サーバーを再起動

### エラー: "Could not understand audio"

**原因**: 音声認識が失敗

**解決方法**:
1. 音声ファイルの形式を確認（WAV, MP3推奨）
2. 音声が明瞭か確認
3. 背景ノイズを減らす

### エラー: "Session not found"

**原因**: セッションIDが無効または期限切れ

**解決方法**:
1. 新しいセッションを作成
2. セッションIDを正しくコピー

---

## 📝 次のステップ

1. ✅ **バックエンド実装完了**
2. ⏳ **Android アプリのUI実装**
   - 会話画面の作成
   - 音声録音機能の統合
   - フィードバック表示
3. ⏳ **テスト**
   - 統合テスト
   - ユーザビリティテスト
4. ⏳ **デプロイ**
   - サーバーのクラウドデプロイ
   - Google Playストアへの公開

---

## 🎉 完成した機能

- ✅ AI会話エンジン（Gemini API統合）
- ✅ 音声認識サービス
- ✅ 音声合成サービス
- ✅ シナリオ管理システム
- ✅ 会話セッション管理
- ✅ 学習フィードバック生成
- ✅ RESTful API エンドポイント

**これで有料版の基盤が完成しました！** 🚀

次は Android アプリ側の実装に進みましょう。
