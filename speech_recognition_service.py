"""
音声認識サービス - Whisper APIを使用した音声認識
"""

import os
from pathlib import Path
from typing import Optional, Dict
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

class SpeechRecognitionService:
    """音声認識サービス"""
    
    def __init__(self):
        """初期化"""
        self.recognizer = sr.Recognizer()
    
    def transcribe_audio(self, audio_file_path: str, language: str = "ceb") -> Dict:
        """
        音声ファイルを文字起こし
        
        Parameters:
        - audio_file_path: 音声ファイルのパス
        - language: 言語コード（ceb=セブアノ語、en=英語、ja=日本語）
        
        Returns:
        - 文字起こし結果
        """
        try:
            # ファイル形式を確認
            file_path = Path(audio_file_path)
            if not file_path.exists():
                return {
                    "status": "error",
                    "error": "Audio file not found"
                }
            
            # WAV形式に変換（必要な場合）
            wav_path = self._convert_to_wav(audio_file_path)
            
            # 音声認識を実行
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                
                try:
                    # Google Speech Recognitionを使用（無料）
                    # ビサヤ語の認識精度は限定的だが、基本的な単語は認識可能
                    text = self.recognizer.recognize_google(
                        audio_data,
                        language=self._get_language_code(language)
                    )
                    
                    return {
                        "status": "success",
                        "transcription": text,
                        "language": language,
                        "confidence": 0.8  # Google APIは信頼度を返さないため固定値
                    }
                    
                except sr.UnknownValueError:
                    return {
                        "status": "error",
                        "error": "Could not understand audio",
                        "transcription": ""
                    }
                    
                except sr.RequestError as e:
                    return {
                        "status": "error",
                        "error": f"API request failed: {str(e)}",
                        "transcription": ""
                    }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Transcription failed: {str(e)}",
                "transcription": ""
            }
        finally:
            # 一時ファイルを削除
            if wav_path != audio_file_path and Path(wav_path).exists():
                Path(wav_path).unlink()
    
    def _convert_to_wav(self, audio_file_path: str) -> str:
        """
        音声ファイルをWAV形式に変換
        
        Parameters:
        - audio_file_path: 元の音声ファイルパス
        
        Returns:
        - WAVファイルのパス
        """
        file_path = Path(audio_file_path)
        file_ext = file_path.suffix.lower()
        
        # すでにWAV形式の場合はそのまま返す
        if file_ext == '.wav':
            return audio_file_path
        
        try:
            # 音声ファイルを読み込み
            if file_ext == '.mp3':
                audio = AudioSegment.from_mp3(audio_file_path)
            elif file_ext == '.m4a':
                audio = AudioSegment.from_file(audio_file_path, format='m4a')
            elif file_ext == '.ogg':
                audio = AudioSegment.from_ogg(audio_file_path)
            elif file_ext == '.flac':
                audio = AudioSegment.from_file(audio_file_path, format='flac')
            elif file_ext in ['.3gp', '.amr']:
                audio = AudioSegment.from_file(audio_file_path)
            else:
                # 不明な形式の場合は元のパスを返す
                return audio_file_path
            
            # 一時WAVファイルを作成
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav_path = temp_wav.name
            temp_wav.close()
            
            # WAV形式でエクスポート
            audio.export(temp_wav_path, format='wav')
            
            return temp_wav_path
            
        except Exception as e:
            print(f"Audio conversion error: {e}")
            return audio_file_path
    
    def _get_language_code(self, language: str) -> str:
        """
        言語コードを取得
        
        Parameters:
        - language: 言語識別子
        
        Returns:
        - Google Speech Recognition用の言語コード
        """
        language_map = {
            "bisaya": "ceb-PH",
            "ceb": "ceb-PH",
            "cebuano": "ceb-PH",
            "en": "en-US",
            "english": "en-US",
            "ja": "ja-JP",
            "japanese": "ja-JP",
            "tl": "tl-PH",
            "tagalog": "tl-PH"
        }
        
        return language_map.get(language.lower(), "ceb-PH")
    
    def analyze_pronunciation_features(self, audio_file_path: str) -> Dict:
        """
        発音の特徴を分析
        
        Parameters:
        - audio_file_path: 音声ファイルのパス
        
        Returns:
        - 発音特徴の分析結果
        """
        try:
            import librosa
            import numpy as np
            
            # 音声ファイルを読み込み
            y, sr = librosa.load(audio_file_path, sr=None)
            
            # 基本的な特徴量を抽出
            duration = librosa.get_duration(y=y, sr=sr)
            
            # ピッチ（基本周波数）を抽出
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            pitch_mean = np.mean(pitch_values) if pitch_values else 0
            pitch_std = np.std(pitch_values) if pitch_values else 0
            
            # エネルギー（音量）を計算
            rms = librosa.feature.rms(y=y)[0]
            energy_mean = np.mean(rms)
            energy_std = np.std(rms)
            
            # 発話速度を推定（ゼロ交差率から）
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            speech_rate = np.mean(zcr)
            
            return {
                "status": "success",
                "features": {
                    "duration": float(duration),
                    "pitch_mean": float(pitch_mean),
                    "pitch_std": float(pitch_std),
                    "energy_mean": float(energy_mean),
                    "energy_std": float(energy_std),
                    "speech_rate": float(speech_rate)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Feature extraction failed: {str(e)}"
            }


class TextToSpeechService:
    """音声合成サービス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def generate_speech(self, text: str, language: str = "ceb", output_path: Optional[str] = None) -> Dict:
        """
        テキストから音声を生成
        
        Parameters:
        - text: 音声化するテキスト
        - language: 言語コード
        - output_path: 出力ファイルパス（Noneの場合は一時ファイル）
        
        Returns:
        - 生成結果
        """
        try:
            from gtts import gTTS
            
            # 出力パスが指定されていない場合は一時ファイルを作成
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                output_path = temp_file.name
                temp_file.close()
            
            # 言語コードを取得
            lang_code = self._get_tts_language_code(language)
            
            # 音声を生成
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(output_path)
            
            return {
                "status": "success",
                "audio_path": output_path,
                "text": text,
                "language": language
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Speech generation failed: {str(e)}"
            }
    
    def _get_tts_language_code(self, language: str) -> str:
        """
        gTTS用の言語コードを取得
        
        Note: gTTSはビサヤ語（セブアノ語）を直接サポートしていないため、
        タガログ語（tl）またはフィリピン英語（en）を使用
        """
        language_map = {
            "bisaya": "tl",  # タガログ語で代用
            "ceb": "tl",
            "cebuano": "tl",
            "en": "en",
            "english": "en",
            "ja": "ja",
            "japanese": "ja",
            "tl": "tl",
            "tagalog": "tl"
        }
        
        return language_map.get(language.lower(), "tl")
