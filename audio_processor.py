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
        
        # ファイルの存在確認
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # ファイル拡張子を取得
        file_extension = Path(file_path).suffix.lower()
        print(f"ファイル拡張子: {file_extension}")
        
        # 3GP/AMRファイルの場合、FFmpegで変換
        if file_extension in ['.3gp', '.amr']:
            try:
                import subprocess
                import tempfile
                import os
                
                print(f"3GP/AMRファイルを変換中: {file_path}")
                
                # 一時WAVファイルを作成
                temp_wav = tempfile.mktemp(suffix='.wav')
                
                # FFmpegで変換（より堅牢な方法）
                try:
                    result = subprocess.run([
                        'ffmpeg', '-i', file_path,
                        '-ar', str(self.sample_rate),
                        '-ac', '1',
                        '-y',
                        temp_wav
                    ], check=True, capture_output=True, text=True, timeout=30)
                    print(f"FFmpeg変換成功")
                except subprocess.CalledProcessError as e:
                    print(f"FFmpeg変換エラー: {e.stderr}")
                    raise Exception(f"FFmpeg conversion failed: {e.stderr}")
                except FileNotFoundError:
                    print("FFmpegが見つかりません。pydubで試します。")
                    # pydubで変換を試みる
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(file_path)
                    audio = audio.set_channels(1)
                    audio = audio.set_frame_rate(self.sample_rate)
                    audio.export(temp_wav, format="wav")
                    print(f"pydub変換成功")
                
                # WAVファイルを読み込み
                audio_data, sr = librosa.load(temp_wav, sr=self.sample_rate, mono=True)
                
                # 一時ファイルを削除
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
                
                print(f"3GP/AMR変換成功: {len(audio_data)} samples")
                return audio_data, sr
                
            except Exception as e:
                print(f"Error converting 3GP/AMR: {e}")
                import traceback
                print(traceback.format_exc())
                raise Exception(f"Failed to convert 3GP/AMR file: {str(e)}")
        
        # WAVファイルの場合、scipyで試す（軽量）
        if file_extension == '.wav':
            try:
                from scipy.io import wavfile
                sr, audio_data = wavfile.read(file_path)
                print(f"scipy読み込み成功: sr={sr}, shape={audio_data.shape}, dtype={audio_data.dtype}")
                
                # 正規化
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                elif audio_data.dtype == np.uint8:
                    audio_data = (audio_data.astype(np.float32) - 128) / 128.0
                
                # モノラルに変換
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                # リサンプリング
                if sr != self.sample_rate:
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                
                print(f"scipy処理完了: 最終shape={audio_data.shape}")
                return audio_data, self.sample_rate
            except Exception as e:
                print(f"scipy読み込みエラー: {e}")
                # 次の方法にフォールバック
        
        # MP3, M4A, OGG, FLACなどの場合、soundfileまたはlibrosaで読み込み
        try:
            import soundfile as sf
            audio_data, sr = sf.read(file_path, dtype='float32')
            print(f"soundfile読み込み成功: sr={sr}, shape={audio_data.shape}")
            
            # モノラルに変換
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # リサンプリング
            if sr != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            
            print(f"soundfile処理完了: 最終shape={audio_data.shape}")
            return audio_data, self.sample_rate
        except Exception as e:
            print(f"soundfile読み込みエラー: {e}")
            
            # 最終フォールバック：librosaで読み込み（最も汎用的だが遅い）
            try:
                audio_data, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
                print(f"librosa読み込み成功: shape={audio_data.shape}")
                return audio_data, self.sample_rate
            except Exception as e2:
                print(f"librosa読み込みエラー: {e2}")
                raise Exception(f"Could not load audio file with any method. File: {file_path}, Extension: {file_extension}. Errors: {str(e)}, {str(e2)}")
    
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
        # 非常に厳しい基準:
        # - 素晴らしい: 2500以下 → 85-100点
        # - 良い: 2500-6000 → 70-85点
        # - まあまあ: 6000-12000 → 50-70点
        # - 要改善: 12000-20000 → 30-50点
        # - 悪い: 20000-30000 → 10-30点
        # - 不合格: 30000以上 → 0-10点
        
        if distance < 2500:
            # 素晴らしい発音（ネイティブに近い）
            similarity_score = 85 + (1 - distance / 2500) * 15
        elif distance < 6000:
            # 良い発音
            similarity_score = 70 + (1 - (distance - 2500) / 3500) * 15
        elif distance < 12000:
            # まあまあ
            similarity_score = 50 + (1 - (distance - 6000) / 6000) * 20
        elif distance < 20000:
            # 要改善
            similarity_score = 30 + (1 - (distance - 12000) / 8000) * 20
        elif distance < 30000:
            # 悪い（手本と大きく異なる）
            similarity_score = 10 + (1 - (distance - 20000) / 10000) * 20
        else:
            # 不合格（無音または全く違う発音）
            similarity_score = max(0, 10 - (distance - 30000) / 5000)
        
        print(f"スコア: {similarity_score:.2f}")
        
        return float(max(0, min(100, similarity_score)))
    
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
        
        # 無音検出：RMSエネルギーが非常に低い場合は0点
        if user_features['rms_mean'] < 0.001:
            print(f"無音検出: RMS={user_features['rms_mean']}")
            # 参照音声も読み込んで特徴量を取得（レスポンス用）
            reference_audio, _ = self.load_audio(reference_audio_path)
            reference_features = self.extract_features(reference_audio)
            
            feedback = self.generate_feedback(
                0,  # スコア0
                user_features,
                reference_features,
                user_level
            )
            
            return {
                "similarity_score": 0,
                "user_features": {
                    "duration": float(user_features['duration']),
                    "pitch_mean": float(user_features['pitch_mean']),
                    "pitch_std": float(user_features['pitch_std']),
                },
                "reference_features": {
                    "duration": float(reference_features['duration']),
                    "pitch_mean": float(reference_features['pitch_mean']),
                    "pitch_std": float(reference_features['pitch_std']),
                },
                "feedback": feedback,
                "level": user_level
            }
        
        # 参照音声を読み込み
        reference_audio, _ = self.load_audio(reference_audio_path)
        reference_features = self.extract_features(reference_audio)
        
        # DTWで類似度を計算
        dtw_score = self.calculate_dtw_similarity(
            user_features['mfcc'],
            reference_features['mfcc']
        )
        
        print(f"DTWスコア: {dtw_score:.2f}")
        
        # ピッチの差をペナルティとして計算
        pitch_diff = abs(user_features['pitch_mean'] - reference_features['pitch_mean'])
        pitch_diff_percent = (pitch_diff / reference_features['pitch_mean'] * 100) if reference_features['pitch_mean'] > 0 else 0
        pitch_penalty = min(30, pitch_diff_percent / 2)  # 最大30点減点
        print(f"ピッチ差: {pitch_diff:.2f}Hz ({pitch_diff_percent:.1f}%), ペナルティ: {pitch_penalty:.1f}点")
        
        # 音量の差をペナルティとして計算
        rms_diff = abs(user_features['rms_mean'] - reference_features['rms_mean'])
        rms_diff_percent = (rms_diff / reference_features['rms_mean'] * 100) if reference_features['rms_mean'] > 0 else 0
        rms_penalty = min(20, rms_diff_percent / 3)  # 最大20点減点
        print(f"音量差: {rms_diff:.4f} ({rms_diff_percent:.1f}%), ペナルティ: {rms_penalty:.1f}点")
        
        # 長さの差をペナルティとして計算
        duration_diff = abs(user_features['duration'] - reference_features['duration'])
        duration_diff_percent = (duration_diff / reference_features['duration'] * 100) if reference_features['duration'] > 0 else 0
        duration_penalty = min(20, duration_diff_percent / 2)  # 最大20点減点
        print(f"長さ差: {duration_diff:.2f}秒 ({duration_diff_percent:.1f}%), ペナルティ: {duration_penalty:.1f}点")
        
        # 総合スコア = DTWスコア - ペナルティ
        total_penalty = pitch_penalty + rms_penalty + duration_penalty
        similarity_score = max(0, dtw_score - total_penalty)
        print(f"総合ペナルティ: {total_penalty:.1f}点")
        print(f"最終スコア: {similarity_score:.2f} (DTW: {dtw_score:.2f} - ペナルティ: {total_penalty:.1f})")
        
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
                "duration": float(user_features['duration']),
                "pitch_mean": float(user_features['pitch_mean']),
                "pitch_std": float(user_features['pitch_std']),
            },
            "reference_features": {
                "duration": float(reference_features['duration']),
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
        # 明確な評価基準（全レベル共通）
        # ユーザーが理解しやすいシンプルな基準
        if similarity_score >= 85:
            overall_rating = "素晴らしい"
            overall_message = "✨ 素晴らしい発音です！ネイティブに近い発音ができています。"
            rating_emoji = "🌟"
        elif similarity_score >= 70:
            overall_rating = "良い"
            overall_message = "👍 良い発音です！この調子で練習を続けましょう。"
            rating_emoji = "😊"
        elif similarity_score >= 50:
            overall_rating = "まあまあ"
            overall_message = "📝 まあまあの発音です。下記の詳細を参考に改善しましょう。"
            rating_emoji = "🤔"
        elif similarity_score >= 30:
            overall_rating = "要改善"
            overall_message = "💪 練習が必要です。下記のフィードバックに注意してください。"
            rating_emoji = "😓"
        else:
            overall_rating = "不合格"
            overall_message = "❌ 発音が大きく異なります。参照音声をよく聞いて、繰り返し練習してください。"
            rating_emoji = "😢"
        
        # 詳細なフィードバックを生成
        details = []
        
        # スコアに応じたフィードバックレベル
        is_very_low_score = similarity_score < 30  # 非常に悪い
        is_low_score = 30 <= similarity_score < 50  # 悪い
        is_medium_score = 50 <= similarity_score < 70  # 普通
        
        # ピッチの比較
        pitch_diff = abs(user_features['pitch_mean'] - reference_features['pitch_mean'])
        pitch_diff_percent = (pitch_diff / reference_features['pitch_mean'] * 100) if reference_features['pitch_mean'] > 0 else 0
        
        # ピッチスコアを計算（0-100）
        pitch_score = max(0, min(100, 100 - pitch_diff_percent))
        
        # 総合スコアが低い場合は、ピッチスコアも厳しく評価
        if is_very_low_score:
            pitch_score = min(pitch_score, 29)  # 最大29点
        elif is_low_score:
            pitch_score = min(pitch_score, 49)  # 最大49点
        
        # ピッチスコアに基づいてコメントを生成
        if pitch_score >= 70:
            pitch_comment = "✅ ピッチが良いです！"
        elif pitch_score >= 50:
            if user_features['pitch_mean'] > reference_features['pitch_mean']:
                pitch_comment = "⚠️ ピッチが少し高めです。もう少し低く話してみましょう。"
            else:
                pitch_comment = "⚠️ ピッチが少し低めです。もう少し高く話してみましょう。"
        else:
            if user_features['pitch_mean'] > reference_features['pitch_mean']:
                pitch_comment = "❌ ピッチが違います。声が高すぎます。参照音声のように低く話してください。"
            else:
                pitch_comment = "❌ ピッチが違います。声が低すぎます。参照音声のように高く話してください。"
        
        details.append({
            "aspect": "ピッチ",
            "comment": pitch_comment,
            "score": round(pitch_score, 1)
        })
        
        # 音声の長さ（タイミング）の比較
        duration_diff = abs(user_features['duration'] - reference_features['duration'])
        duration_diff_percent = (duration_diff / reference_features['duration'] * 100) if reference_features['duration'] > 0 else 0
        
        # タイミングスコアを計算（0-100）
        timing_score = max(0, min(100, 100 - duration_diff_percent))
        
        # 総合スコアが低い場合は、タイミングスコアも厳しく評価
        if is_very_low_score:
            timing_score = min(timing_score, 29)  # 最大29点
        elif is_low_score:
            timing_score = min(timing_score, 49)  # 最大49点
        
        # タイミングスコアに基づいてコメントを生成
        if timing_score >= 70:
            timing_comment = "✅ タイミングが素晴らしいです！"
        elif timing_score >= 50:
            if user_features['duration'] > reference_features['duration']:
                timing_comment = "⚠️ 少しゆっくり話しています。ネイティブのペースに合わせてみましょう。"
            else:
                timing_comment = "⚠️ 少し早口です。もう少しゆっくり話してみましょう。"
        else:
            if user_features['duration'] > reference_features['duration']:
                timing_comment = "❌ タイミングが違います。かなりゆっくり話しています。参照音声のペースに合わせてください。"
            else:
                timing_comment = "❌ タイミングが違います。かなり早口です。参照音声のようにゆっくり話してください。"
        
        details.append({
            "aspect": "タイミング",
            "comment": timing_comment,
            "score": round(timing_score, 1)
        })
        
        # エネルギー（音量）の比較
        rms_diff = abs(user_features['rms_mean'] - reference_features['rms_mean'])
        rms_diff_percent = (rms_diff / reference_features['rms_mean'] * 100) if reference_features['rms_mean'] > 0 else 0
        
        # 音量スコアを計算（0-100）
        volume_score = max(0, min(100, 100 - rms_diff_percent))
        
        # 総合スコアが低い場合は、音量スコアも厳しく評価
        if is_very_low_score:
            volume_score = min(volume_score, 29)  # 最大29点
        elif is_low_score:
            volume_score = min(volume_score, 49)  # 最大49点
        
        # 音量スコアに基づいてコメントを生成
        if volume_score >= 70:
            volume_comment = "✅ 音量が良いです！"
        elif volume_score >= 50:
            if user_features['rms_mean'] > reference_features['rms_mean']:
                volume_comment = "⚠️ もう少し小さな声で話してみましょう。"
            else:
                volume_comment = "⚠️ もう少し大きな声ではっきりと話してみましょう。"
        else:
            if user_features['rms_mean'] > reference_features['rms_mean']:
                volume_comment = "❌ 音量が違います。声が大きすぎます。参照音声のように小さな声で話してください。"
            else:
                volume_comment = "❌ 音量が違います。声が小さすぎます。参照音声のようにはっきりと話してください。"
        
        details.append({
            "aspect": "音量",
            "comment": volume_comment,
            "score": round(volume_score, 1)
        })
        
        # スコアが非常に低い場合は、全体的な改善点を追加
        if is_very_low_score:
            details.append({
                "aspect": "全体評価",
                "comment": "❌ 発音が参照音声と大きく異なります。参照音声をよく聞いて、繰り返し練習してください。",
                "score": round(similarity_score, 1)
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
