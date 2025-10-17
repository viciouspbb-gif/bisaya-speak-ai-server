"""
音声処理モジュール
Librosaを使用した音声分析機能を提供
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw


class AudioProcessor:
    """音声ファイルの処理と分析を行うクラス"""
    
    def __init__(self, sample_rate: int = 22050):
        """
        Parameters:
        - sample_rate: サンプリングレート（Hz）
        """
        self.sample_rate = sample_rate
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        音声ファイルを読み込む
        
        Returns:
        - audio_data: 音声データ（numpy配列）
        - sample_rate: サンプリングレート
        """
        import warnings
        warnings.filterwarnings('ignore')
        
        print(f"load_audio呼び出し: file_path={file_path}, type={type(file_path)}")
        print(f"ファイル拡張子チェック: lower={file_path.lower()}, endswith 3gp={file_path.lower().endswith('.3gp')}")
        
        # 3GPファイルの場合、pydubで変換
        if file_path.lower().endswith(('.3gp', '.amr')):
            try:
                from pydub import AudioSegment
                from pydub.utils import which
                import tempfile
                import os
                import subprocess
                
                print(f"3GPファイルを変換中: {file_path}")
                
                # FFmpegの存在確認
                ffmpeg_path = which("ffmpeg")
                print(f"FFmpeg path: {ffmpeg_path}")
                
                if not ffmpeg_path:
                    # FFmpegが見つからない場合、subprocessで直接変換
                    print("FFmpegが見つかりません。直接変換を試みます。")
                    temp_wav = tempfile.mktemp(suffix='.wav')
                    subprocess.run([
                        'ffmpeg', '-i', file_path,
                        '-ar', str(self.sample_rate),
                        '-ac', '1',
                        '-y',
                        temp_wav
                    ], check=True, capture_output=True)
                    
                    audio_data, sr = librosa.load(temp_wav, sr=self.sample_rate, mono=True)
                    os.remove(temp_wav)
                    print(f"FFmpeg直接変換成功: {len(audio_data)} samples")
                    return audio_data, sr
                
                # 3GPファイルを読み込み
                audio = AudioSegment.from_file(file_path, format="3gp")
                
                # モノラルに変換
                audio = audio.set_channels(1)
                
                # サンプリングレートを設定
                audio = audio.set_frame_rate(self.sample_rate)
                
                # 一時WAVファイルを作成
                temp_wav = tempfile.mktemp(suffix='.wav')
                
                # WAVとしてエクスポート
                audio.export(temp_wav, format="wav")
                
                # WAVファイルを読み込み
                audio_data, sr = librosa.load(temp_wav, sr=self.sample_rate, mono=True)
                
                # 一時ファイルを削除
                os.remove(temp_wav)
                
                print(f"3GP変換成功: {len(audio_data)} samples")
                return audio_data, sr
            except Exception as e:
                print(f"Error converting 3GP with pydub: {e}")
                import traceback
                print(traceback.format_exc())
                # pydubが失敗したら通常の方法を試す
        
        # soundfileで読み込み（Python 3.13対応）
        # Updated: 2025-10-17 - Use soundfile instead of librosa
        try:
            import soundfile as sf
            audio_data, sr = sf.read(file_path, dtype='float32')
            # モノラルに変換
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            # リサンプリング
            if sr != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            return audio_data, self.sample_rate
        except Exception as e:
            print(f"Error loading audio with soundfile: {e}")
            # フォールバック：scipyで読み込み
            try:
                from scipy.io import wavfile
                sr, audio_data = wavfile.read(file_path)
                # 正規化
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                # モノラルに変換
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                # リサンプリング
                if sr != self.sample_rate:
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                return audio_data, self.sample_rate
            except Exception as e2:
                print(f"Error loading audio with scipy: {e2}")
                raise Exception(f"Could not load audio file. Tried soundfile and scipy. Errors: {str(e)}, {str(e2)}")
    
    def extract_features(self, audio_data: np.ndarray) -> Dict:
        """
        音声から特徴量を抽出
        
        Returns:
        - features: 抽出された特徴量の辞書
        """
        features = {}
        
        # MFCC (Mel-frequency cepstral coefficients)
        mfcc = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
        features['mfcc'] = mfcc
        features['mfcc_mean'] = np.mean(mfcc, axis=1)
        features['mfcc_std'] = np.std(mfcc, axis=1)
        
        # ピッチ（基本周波数）
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        features['pitch_mean'] = np.mean(pitch_values) if pitch_values else 0
        features['pitch_std'] = np.std(pitch_values) if pitch_values else 0
        
        # スペクトル重心
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)[0]
        features['spectral_centroid_mean'] = np.mean(spectral_centroids)
        features['spectral_centroid_std'] = np.std(spectral_centroids)
        
        # ゼロ交差率
        zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)[0]
        features['zero_crossing_rate_mean'] = np.mean(zero_crossing_rate)
        
        # RMS エネルギー
        rms = librosa.feature.rms(y=audio_data)[0]
        features['rms_mean'] = np.mean(rms)
        features['rms_std'] = np.std(rms)
        
        # 音声の長さ
        features['duration'] = len(audio_data) / self.sample_rate
        
        return features
    
    def analyze_pronunciation(self, file_path: str) -> Dict:
        """
        発音を分析して評価を返す
        
        Returns:
        - analysis: 分析結果の辞書
        """
        # 音声を読み込み
        audio_data, sr = self.load_audio(file_path)
        
        # 特徴量を抽出
        features = self.extract_features(audio_data)
        
        # TODO: 機械学習モデルを使った実際の発音評価を実装
        # 現在はダミーの分析結果を返す
        
        analysis = {
            "duration": features['duration'],
            "pitch_mean": float(features['pitch_mean']),
            "pitch_std": float(features['pitch_std']),
            "spectral_centroid_mean": float(features['spectral_centroid_mean']),
            "rms_mean": float(features['rms_mean']),
            "features_extracted": True
        }
        
        return analysis
    
    def calculate_dtw_similarity(
        self,
        user_mfcc: np.ndarray,
        reference_mfcc: np.ndarray
    ) -> float:
        """
        DTW（動的時間伸縮法）を使用してMFCC特徴量の類似度を計算
        
        Parameters:
        - user_mfcc: ユーザー音声のMFCC
        - reference_mfcc: 参照音声のMFCC
        
        Returns:
        - similarity_score: 類似度スコア（0-100）
        """
        # MFCCを転置（時間軸を第一次元に）
        user_mfcc_t = user_mfcc.T
        reference_mfcc_t = reference_mfcc.T
        
        # DTWで距離を計算
        distance, _ = fastdtw(user_mfcc_t, reference_mfcc_t, dist=euclidean)
        
        print(f"DTW距離: {distance}")
        
        # 距離を類似度スコアに変換（0-100の範囲）
        # 距離が小さいほど類似度が高い
        # 実際の測定値に基づいて調整:
        # - 完璧な発音: 5000以下 → 90-100点
        # - 良い発音: 5000-15000 → 60-90点
        # - まあまあ: 15000-25000 → 30-60点
        # - 悪い/無音: 25000以上 → 0-30点
        
        if distance < 5000:
            # 完璧な発音
            similarity_score = 90 + (1 - distance / 5000) * 10
        elif distance < 15000:
            # 良い発音
            similarity_score = 60 + (1 - (distance - 5000) / 10000) * 30
        elif distance < 25000:
            # まあまあ
            similarity_score = 30 + (1 - (distance - 15000) / 10000) * 30
        else:
            # 悪い/無音
            similarity_score = max(0, 30 - (distance - 25000) / 1000)
        
        print(f"スコア: {similarity_score:.2f}")
        
        return max(0, min(100, similarity_score))
    
    def compare_pronunciation(
        self,
        user_audio_path: str,
        reference_audio_path: str,
        user_level: str = "beginner"
    ) -> Dict:
        """
        ユーザーの発音と参照音声を比較（DTWベース）
        
        Parameters:
        - user_audio_path: ユーザー音声のパス
        - reference_audio_path: 参照音声のパス
        - user_level: ユーザーのレベル（beginner/intermediate/advanced）
        
        Returns:
        - comparison: 比較結果
        """
        # ユーザー音声を読み込み
        user_audio, _ = self.load_audio(user_audio_path)
        user_features = self.extract_features(user_audio)
        
        # 参照音声を読み込み
        reference_audio, _ = self.load_audio(reference_audio_path)
        reference_features = self.extract_features(reference_audio)
        
        # DTWで類似度を計算
        similarity_score = self.calculate_dtw_similarity(
            user_features['mfcc'],
            reference_features['mfcc']
        )
        
        # レベルに応じたフィードバックを生成
        feedback = self.generate_feedback(
            similarity_score,
            user_features,
            reference_features,
            user_level
        )
        
        comparison = {
            "similarity_score": round(similarity_score, 2),
            "user_features": {
                "duration": user_features['duration'],
                "pitch_mean": float(user_features['pitch_mean']),
                "pitch_std": float(user_features['pitch_std']),
            },
            "reference_features": {
                "duration": reference_features['duration'],
                "pitch_mean": float(reference_features['pitch_mean']),
                "pitch_std": float(reference_features['pitch_std']),
            },
            "feedback": feedback,
            "level": user_level
        }
        
        return comparison
    
    def generate_feedback(
        self,
        similarity_score: float,
        user_features: Dict,
        reference_features: Dict,
        user_level: str
    ) -> Dict:
        """
        レベルに応じたフィードバックを生成
        
        Parameters:
        - similarity_score: 類似度スコア（0-100）
        - user_features: ユーザー音声の特徴量
        - reference_features: 参照音声の特徴量
        - user_level: ユーザーのレベル
        
        Returns:
        - feedback: フィードバック辞書
        """
        # レベル別の評価基準
        thresholds = {
            "beginner": {"excellent": 75, "good": 60, "fair": 45},
            "intermediate": {"excellent": 85, "good": 70, "fair": 55},
            "advanced": {"excellent": 90, "good": 80, "fair": 65}
        }
        
        level_thresholds = thresholds.get(user_level, thresholds["beginner"])
        
        # 総合評価を決定（日本語）
        if similarity_score >= level_thresholds["excellent"]:
            overall_rating = "素晴らしい"
            overall_message = "とても良い発音です！ネイティブに近い発音ができています。"
        elif similarity_score >= level_thresholds["good"]:
            overall_rating = "良い"
            overall_message = "良い発音です！さらに練習して上達しましょう。"
        elif similarity_score >= level_thresholds["fair"]:
            overall_rating = "まあまあ"
            overall_message = "まあまあの発音です。下記の詳細を参考に改善しましょう。"
        else:
            overall_rating = "要改善"
            overall_message = "練習を続けましょう！下記のフィードバックに注意してください。"
        
        # 詳細なフィードバックを生成
        details = []
        
        # ピッチの比較
        pitch_diff = abs(user_features['pitch_mean'] - reference_features['pitch_mean'])
        if pitch_diff > 50:
            if user_features['pitch_mean'] > reference_features['pitch_mean']:
                details.append({
                    "aspect": "ピッチ",
                    "comment": "ピッチが少し高めです。もう少し低く話してみましょう。"
                })
            else:
                details.append({
                    "aspect": "ピッチ",
                    "comment": "ピッチが少し低めです。もう少し高く話してみましょう。"
                })
        else:
            details.append({
                "aspect": "ピッチ",
                "comment": "ピッチが良いです！"
            })
        
        # 音声の長さの比較
        duration_diff = abs(user_features['duration'] - reference_features['duration'])
        if duration_diff > 0.5:
            if user_features['duration'] > reference_features['duration']:
                details.append({
                    "aspect": "タイミング",
                    "comment": "少しゆっくり話しています。ネイティブのペースに合わせてみましょう。"
                })
            else:
                details.append({
                    "aspect": "タイミング",
                    "comment": "少し早口です。もう少しゆっくり話してみましょう。"
                })
        else:
            details.append({
                "aspect": "タイミング",
                "comment": "タイミングが素晴らしいです！"
            })
        
        # エネルギー（音量）の比較
        rms_diff = abs(user_features['rms_mean'] - reference_features['rms_mean'])
        if rms_diff > 0.05:
            if user_features['rms_mean'] > reference_features['rms_mean']:
                details.append({
                    "aspect": "音量",
                    "comment": "もう少し小さな声で話してみましょう。"
                })
            else:
                details.append({
                    "aspect": "音量",
                    "comment": "もう少し大きな声ではっきりと話してみましょう。"
                })
        
        # レベル別の追加アドバイス
        if user_level == "beginner":
            additional_tips = "ネイティブスピーカーの音声を聞いて、繰り返し練習しましょう。"
        elif user_level == "intermediate":
            additional_tips = "細かい音の違いやイントネーションのパターンに注意しましょう。"
        else:  # advanced
            additional_tips = "ニュアンスや自然な話し方の流れを完璧にしましょう。"
        
        feedback = {
            "overall": overall_message,
            "rating": overall_rating,
            "details": details,
            "tips": additional_tips
        }
        
        return feedback


def get_audio_info(file_path: str) -> Dict:
    """
    音声ファイルの基本情報を取得
    
    Returns:
    - info: ファイル情報
    """
    audio_data, sr = librosa.load(file_path, sr=None)
    duration = len(audio_data) / sr
    
    info = {
        "sample_rate": sr,
        "duration": duration,
        "samples": len(audio_data),
        "channels": 1 if audio_data.ndim == 1 else audio_data.shape[0]
    }
    
    return info
