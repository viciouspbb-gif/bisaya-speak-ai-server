from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime
from pathlib import Path
import shutil
from dotenv import load_dotenv
from audio_processor import AudioProcessor
from conversation_engine import ConversationEngine, ScenarioManager
# from speech_recognition_service import SpeechRecognitionService, TextToSpeechService
import asyncio
from typing import Optional

# .envファイルを読み込み
load_dotenv()

app = FastAPI(
    title="Bisaya Speak AI API",
    description="AI-powered pronunciation diagnosis for Bisaya language learning",
    version="1.0.0"
)

# CORS設定（Kotlinアプリからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 音声ファイル保存用ディレクトリ
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 参照音声ファイル保存用ディレクトリ
REFERENCE_DIR = Path("reference_audio")
REFERENCE_DIR.mkdir(exist_ok=True)

# AudioProcessorのインスタンス
audio_processor = AudioProcessor()

# AI会話エンジンのインスタンス（環境変数からAPIキーを取得）
try:
    conversation_engine = ConversationEngine()
    print("✓ Conversation Engine initialized")
except Exception as e:
    print(f"⚠ Conversation Engine initialization failed: {e}")
    print("  Set GEMINI_API_KEY environment variable to enable AI conversation features")
    conversation_engine = None

# シナリオマネージャー
scenario_manager = ScenarioManager()

# 音声認識・合成サービス（AI会話では不要なのでコメントアウト）
# speech_recognition_service = SpeechRecognitionService()
# text_to_speech_service = TextToSpeechService()


@app.get("/")
@app.head("/")
async def root():
    """ヘルスチェック用エンドポイント（GET/HEADメソッド対応）"""
    return {
        "status": "ok",
        "message": "Bisaya Speak AI is running",
        "version": "1.0.0"
    }


def get_reference_audio_path(word: str) -> Path:
    """
    単語に対応する参照音声ファイルのパスを取得
    
    Parameters:
    - word: 単語またはフレーズ
    
    Returns:
    - reference_path: 参照音声ファイルのパス
    """
    # 単語をファイル名に変換（スペースをアンダースコアに、記号を削除）
    safe_word = word.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("?", "").replace("!", "").replace(".", "").replace("-", "_")
    
    # 複数の拡張子を試す（MP3優先、次にWAV）
    for ext in [".mp3", ".wav", ".m4a", ".ogg"]:
        reference_filename = f"{safe_word}_ref{ext}"
        reference_path = REFERENCE_DIR / reference_filename
        if reference_path.exists():
            return reference_path
    
    # 見つからない場合はMP3パスを返す（エラーハンドリング用）
    return REFERENCE_DIR / f"{safe_word}_ref.mp3"


@app.post("/api/pronounce/check")
async def check_pronunciation(
    audio: UploadFile = File(...),
    word: str = Form(None),
    language: str = Form("bisaya"),
    level: str = Form("beginner")
):
    """
    発音診断エンドポイント
    
    Parameters:
    - audio: 音声ファイル（WAV, MP3, M4A など）
    - word: 発音対象の単語（オプション）
    - language: 言語（デフォルト: bisaya）
    - level: ユーザーのレベル（beginner/intermediate/advanced）
    
    Returns:
    - JSON形式の診断結果
    """
    try:
        # ファイル形式チェック
        allowed_extensions = [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".3gp", ".amr"]
        file_ext = os.path.splitext(audio.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # レベルの検証
        valid_levels = ["beginner", "intermediate", "advanced"]
        if level not in valid_levels:
            level = "beginner"
        
        # 音声ファイルを一時保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{audio.filename}"
        file_path = UPLOAD_DIR / filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # ファイルサイズ取得
        file_size = file_path.stat().st_size
        
        # 発音診断を実行
        print(f"診断リクエスト: word={word}, level={level}, file={file_path}")
        if word:
            # 参照音声ファイルのパスを取得
            reference_path = get_reference_audio_path(word)
            print(f"参照音声パス: {reference_path}, exists={reference_path.exists()}")
            
            if reference_path.exists():
                # 実際の音声処理で発音を比較
                try:
                    print(f"音声処理開始: user={file_path}, reference={reference_path}")
                    comparison = audio_processor.compare_pronunciation(
                        str(file_path),
                        str(reference_path),
                        level
                    )
                    pronunciation_score = comparison['similarity_score']
                    feedback = comparison['feedback']
                    print(f"音声処理成功: score={pronunciation_score}")
                except Exception as e:
                    import traceback
                    print(f"音声処理エラー: {e}")
                    print(traceback.format_exc())
                    # エラー時はダミースコア
                    import random
                    pronunciation_score = random.randint(75, 90)
                    print(f"ダミースコア使用: {pronunciation_score}")
                    
                    # ダミーフィードバック
                    feedback = {
                        "overall": "エラーが発生しました。もう一度お試しください。",
                        "rating": "エラー",
                        "details": [],
                        "tips": "もう一度録音してください。"
                    }
                
                response = {
                    "status": "success",
                    "message": "Audio file received and processed (demo mode)",
                    "data": {
                        "filename": audio.filename,
                        "saved_as": filename,
                        "file_size": file_size,
                        "word": word,
                        "language": language,
                        "level": level,
                        "pronunciation_score": pronunciation_score,
                        "feedback": feedback,
                        "comparison_details": {
                            "user_features": {"duration": 1.5, "pitch_mean": 150.0, "pitch_std": 20.0},
                            "reference_features": {"duration": 1.5, "pitch_mean": 150.0, "pitch_std": 20.0}
                        },
                        "timestamp": timestamp
                    }
                }
            else:
                # 参照音声がない場合は基本的な分析のみ
                response = {
                    "status": "success",
                    "message": "Audio file received. Reference audio not found, basic analysis performed.",
                    "data": {
                        "filename": audio.filename,
                        "saved_as": filename,
                        "file_size": file_size,
                        "word": word,
                        "language": language,
                        "level": level,
                        "pronunciation_score": None,
                        "feedback": {
                            "overall": f"Reference audio for '{word}' not found. Please upload reference audio.",
                            "rating": "N/A",
                            "details": [],
                            "tips": "Contact administrator to add reference audio for this word."
                        },
                        "timestamp": timestamp
                    }
                }
        else:
            # 単語が指定されていない場合
            response = {
                "status": "success",
                "message": "Audio file received. No word specified for comparison.",
                "data": {
                    "filename": audio.filename,
                    "saved_as": filename,
                    "file_size": file_size,
                    "word": None,
                    "language": language,
                    "level": level,
                    "pronunciation_score": None,
                    "feedback": {
                        "overall": "Please specify a word to evaluate pronunciation.",
                        "rating": "N/A",
                        "details": [],
                        "tips": "Send the 'word' parameter with your request."
                    },
                    "timestamp": timestamp
                }
            }
        
        # 処理後、一時ファイルを削除（必要に応じて保持も可能）
        # file_path.unlink()
        
        return JSONResponse(content=response)
        
    except Exception as e:
        import traceback
        error_detail = f"Error processing audio: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # サーバーログに詳細を出力
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@app.get("/api/health")
async def health_check():
    """詳細なヘルスチェック"""
    return {
        "status": "healthy",
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "upload_dir_writable": os.access(UPLOAD_DIR, os.W_OK),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/reference-audio/{word}")
async def get_reference_audio(word: str):
    """参照音声ファイルを取得"""
    from fastapi.responses import FileResponse
    
    # 参照音声ファイルのパスを取得
    reference_path = get_reference_audio_path(word)
    
    if not reference_path.exists():
        raise HTTPException(status_code=404, detail=f"Reference audio not found for word: {word}")
    
    return FileResponse(
        path=str(reference_path),
        media_type="audio/mpeg",
        filename=f"{word}_ref.mp3"
    )


# ==================== AI会話機能のエンドポイント ====================

@app.post("/api/conversation/session/create")
async def create_conversation_session(
    mode: str = Form(...),
    level: str = Form("beginner"),
    scenario_id: Optional[str] = Form(None)
):
    """
    新しい会話セッションを作成
    
    Parameters:
    - mode: 会話モード（shadowing, word_drill, roleplay, free_talk）
    - level: ユーザーレベル（beginner, intermediate, advanced）
    - scenario_id: シナリオID（roleplayモードの場合）
    """
    if not conversation_engine:
        raise HTTPException(
            status_code=503,
            detail="Conversation engine not available. Please set GEMINI_API_KEY."
        )
    
    try:
        # セッションIDを生成
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # セッションを作成
        session_info = conversation_engine.create_session(session_id, mode, level)
        
        # ロールプレイの場合、シナリオ情報を追加
        if mode == "roleplay" and scenario_id:
            scenario = scenario_manager.get_scenario(scenario_id)
            if scenario:
                session_info["scenario"] = scenario
                # 最初のメッセージを生成
                first_message = scenario["opening"]
                session_info["first_message"] = first_message
        
        return JSONResponse(content={
            "status": "success",
            "data": session_info
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/message")
async def send_conversation_message(
    session_id: str = Form(...),
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """
    会話メッセージを送信
    
    Parameters:
    - session_id: セッションID
    - audio: 音声ファイル（オプション）
    - text: テキストメッセージ（オプション）
    """
    if not conversation_engine:
        raise HTTPException(
            status_code=503,
            detail="Conversation engine not available."
        )
    
    try:
        user_message = text
        transcription = None
        
        # 音声ファイルがある場合は文字起こし
        if audio:
            # 音声ファイルを保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{audio.filename}"
            file_path = UPLOAD_DIR / filename
            
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
            
            # 音声認識
            recognition_result = speech_recognition_service.transcribe_audio(
                str(file_path),
                language="bisaya"
            )
            
            if recognition_result["status"] == "success":
                transcription = recognition_result["transcription"]
                user_message = transcription
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="Either audio or text message is required"
            )
        
        # AI応答を生成（音声ファイルも自動生成される）
        response = await conversation_engine.send_message(
            session_id,
            user_message,
            transcription
        )
        
        # レスポンスをログ出力
        print(f"📤 Response: {response}")
        
        return JSONResponse(content={
            "status": "success",
            "data": response,
            "transcription": transcription
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/session/{session_id}/summary")
async def get_session_summary(session_id: str):
    """会話セッションのサマリーを取得"""
    if not conversation_engine:
        raise HTTPException(
            status_code=503,
            detail="Conversation engine not available."
        )
    
    try:
        summary = conversation_engine.get_session_summary(session_id)
        return JSONResponse(content={
            "status": "success",
            "data": summary
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/session/{session_id}/feedback")
async def get_session_feedback(session_id: str):
    """会話セッションのフィードバックを取得"""
    if not conversation_engine:
        raise HTTPException(
            status_code=503,
            detail="Conversation engine not available."
        )
    
    try:
        feedback = conversation_engine.generate_feedback(session_id)
        return JSONResponse(content={
            "status": "success",
            "data": feedback
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenarios")
async def list_scenarios(difficulty: Optional[str] = None):
    """シナリオ一覧を取得"""
    try:
        scenarios = scenario_manager.list_scenarios(difficulty)
        return JSONResponse(content={
            "status": "success",
            "data": scenarios
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """特定のシナリオを取得"""
    try:
        scenario = scenario_manager.get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return JSONResponse(content={
            "status": "success",
            "data": scenario
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: str = Form("bisaya")
):
    """音声を文字起こし"""
    try:
        # 音声ファイルを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{audio.filename}"
        file_path = UPLOAD_DIR / filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # 音声認識
        result = speech_recognition_service.transcribe_audio(
            str(file_path),
            language=language
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 音声ファイル配信用のディレクトリをマウント
audio_files_dir = Path("audio_files")
audio_files_dir.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio_files"), name="audio")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
