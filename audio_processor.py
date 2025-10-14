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
        
        # librosaで読み込み（バックエンドに依存しない方法）
        try:
            audio_data, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            return audio_data, sr
        except Exception as e:
            print(f"Error loading audio with librosa: {e}")
            # 最終手段：scipyで読み込み
            try:
                from scipy.io import wavfile
                sr, audio_data = wavfile.read(file_path)
                # 正規化
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                # リサンプリング
                if sr != self.sample_rate:
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                return audio_data, self.sample_rate
            except Exception as e2:
                print(f"Error loading audio with scipy: {e2}")
                raise Exception(f"Could not load audio file. Tried librosa and scipy. Errors: {str(e)}, {str(e2)}")
    
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
        
        # 距離を類似度スコアに変換（0-100の範囲）
        # 距離が小さいほど類似度が高い
        # 経験的な正規化: distance が 0-1000 程度の範囲を想定
        max_distance = 1000.0
        normalized_distance = min(distance / max_distance, 1.0)
        similarity_score = (1.0 - normalized_distance) * 100
        
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
        
        # 総合評価を決定
        if similarity_score >= level_thresholds["excellent"]:
            overall_rating = "Excellent"
            overall_message = "Great job! Your pronunciation is very close to native."
        elif similarity_score >= level_thresholds["good"]:
            overall_rating = "Good"
            overall_message = "Good pronunciation! Keep practicing to improve further."
        elif similarity_score >= level_thresholds["fair"]:
            overall_rating = "Fair"
            overall_message = "Fair pronunciation. Focus on the specific sounds mentioned below."
        else:
            overall_rating = "Needs Improvement"
            overall_message = "Keep practicing! Pay attention to the feedback below."
        
        # 詳細なフィードバックを生成
        details = []
        
        # ピッチの比較
        pitch_diff = abs(user_features['pitch_mean'] - reference_features['pitch_mean'])
        if pitch_diff > 50:
            if user_features['pitch_mean'] > reference_features['pitch_mean']:
                details.append({
                    "aspect": "Pitch",
                    "comment": "Your pitch is slightly higher than the reference. Try speaking a bit lower."
                })
            else:
                details.append({
                    "aspect": "Pitch",
                    "comment": "Your pitch is slightly lower than the reference. Try speaking a bit higher."
                })
        else:
            details.append({
                "aspect": "Pitch",
                "comment": "Your pitch is good!"
            })
        
        # 音声の長さの比較
        duration_diff = abs(user_features['duration'] - reference_features['duration'])
        if duration_diff > 0.5:
            if user_features['duration'] > reference_features['duration']:
                details.append({
                    "aspect": "Timing",
                    "comment": "You're speaking a bit slowly. Try to match the native speaker's pace."
                })
            else:
                details.append({
                    "aspect": "Timing",
                    "comment": "You're speaking a bit quickly. Try to slow down slightly."
                })
        else:
            details.append({
                "aspect": "Timing",
                "comment": "Your timing is excellent!"
            })
        
        # エネルギー（音量）の比較
        rms_diff = abs(user_features['rms_mean'] - reference_features['rms_mean'])
        if rms_diff > 0.05:
            if user_features['rms_mean'] > reference_features['rms_mean']:
                details.append({
                    "aspect": "Volume",
                    "comment": "Try speaking a bit softer to match the reference."
                })
            else:
                details.append({
                    "aspect": "Volume",
                    "comment": "Try speaking a bit louder for clearer pronunciation."
                })
        
        # レベル別の追加アドバイス
        if user_level == "beginner":
            additional_tips = "Focus on listening to native speakers and repeating after them."
        elif user_level == "intermediate":
            additional_tips = "Pay attention to subtle sound differences and intonation patterns."
        else:  # advanced
            additional_tips = "Work on perfecting the nuances and natural flow of speech."
        
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
