from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime
from pathlib import Path
import shutil
from audio_processor import AudioProcessor

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


@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
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
    # 単語をファイル名に変換（スペースをアンダースコアに）
    safe_word = word.lower().replace(" ", "_").replace("'", "")
    reference_filename = f"{safe_word}_ref.wav"
    reference_path = REFERENCE_DIR / reference_filename
    
    return reference_path


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
        if word:
            # 参照音声ファイルのパスを取得
            reference_path = get_reference_audio_path(word)
            
            if reference_path.exists():
                # 一時的にダミースコアを返す（音声処理のバックエンドが不足しているため）
                import random
                pronunciation_score = random.randint(75, 90)
                
                # レベル別の評価（日本語）
                if level == "beginner":
                    if pronunciation_score >= 75:
                        rating = "素晴らしい"
                        message = "とても良い発音です！ネイティブに近い発音ができています。"
                    else:
                        rating = "良い"
                        message = "良い発音です！練習を続けましょう。"
                elif level == "intermediate":
                    if pronunciation_score >= 85:
                        rating = "素晴らしい"
                        message = "素晴らしい発音です！"
                    else:
                        rating = "良い"
                        message = "良い発音です！さらに練習して上達しましょう。"
                else:  # advanced
                    if pronunciation_score >= 90:
                        rating = "完璧"
                        message = "完璧な発音です！"
                    else:
                        rating = "良い"
                        message = "良い発音です！細かいニュアンスを磨きましょう。"
                
                feedback = {
                    "overall": message,
                    "rating": rating,
                    "details": [
                        {"aspect": "ピッチ", "comment": "ピッチが良いです！"},
                        {"aspect": "タイミング", "comment": "タイミングが素晴らしいです！"},
                        {"aspect": "音量", "comment": "はっきりとした発音です！"}
                    ],
                    "tips": "ネイティブスピーカーと一緒に練習を続けましょう！"
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
