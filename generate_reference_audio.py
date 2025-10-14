"""
参照音声ファイル生成スクリプト

実際のビサヤ語ネイティブスピーカーの音声を録音して、
reference_audio/ ディレクトリに配置してください。

このスクリプトは、テスト用のダミー音声を生成するためのサンプルです。
本番環境では実際のネイティブ音声に置き換えてください。
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import librosa


def generate_dummy_audio(duration: float = 2.0, sample_rate: int = 22050) -> np.ndarray:
    """
    テスト用のダミー音声を生成
    
    Parameters:
    - duration: 音声の長さ（秒）
    - sample_rate: サンプリングレート
    
    Returns:
    - audio: 音声データ
    """
    # 複数の周波数を持つ正弦波を生成（音声らしく）
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 基本周波数とハーモニクス
    frequencies = [200, 400, 600, 800]  # Hz
    audio = np.zeros_like(t)
    
    for i, freq in enumerate(frequencies):
        amplitude = 0.3 / (i + 1)  # 高次ハーモニクスは小さく
        audio += amplitude * np.sin(2 * np.pi * freq * t)
    
    # エンベロープを適用（自然な音声のように）
    envelope = np.exp(-t * 0.5)  # 減衰
    audio = audio * envelope
    
    # ノーマライズ
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    return audio.astype(np.float32)


def create_reference_audio_files():
    """
    ビサヤ語の基本的なフレーズの参照音声ファイルを生成
    """
    reference_dir = Path("reference_audio")
    reference_dir.mkdir(exist_ok=True)
    
    # ビサヤ語の基本フレーズリスト
    phrases = [
        "maayong_buntag",      # おはよう
        "maayong_hapon",       # こんにちは
        "maayong_gabii",       # こんばんは
        "salamat",             # ありがとう
        "palihug",             # お願いします
        "oo",                  # はい
        "dili",                # いいえ
        "kumusta",             # 元気ですか
        "maayo",               # 良い
        "pangalan",            # 名前
    ]
    
    sample_rate = 22050
    
    for phrase in phrases:
        filename = f"{phrase}_ref.wav"
        filepath = reference_dir / filename
        
        # ダミー音声を生成（実際にはネイティブ音声を録音して使用）
        audio = generate_dummy_audio(duration=1.5, sample_rate=sample_rate)
        
        # WAVファイルとして保存
        sf.write(filepath, audio, sample_rate)
        print(f"Created: {filepath}")
    
    print(f"\n✓ Generated {len(phrases)} reference audio files")
    print(f"📁 Location: {reference_dir.absolute()}")
    print("\n⚠️  IMPORTANT: These are dummy audio files for testing.")
    print("   Replace them with actual Bisaya native speaker recordings for production use.")


def create_readme():
    """
    参照音声ディレクトリのREADMEを作成
    """
    readme_content = """# Reference Audio Files

このディレクトリには、ビサヤ語の発音評価に使用する参照音声ファイルを配置します。

## ファイル命名規則

参照音声ファイルは以下の命名規則に従ってください：

```
{word_or_phrase}_ref.wav
```

例：
- `maayong_buntag_ref.wav` - "maayong buntag"（おはよう）の参照音声
- `salamat_ref.wav` - "salamat"（ありがとう）の参照音声

## 音声ファイルの要件

- **フォーマット**: WAV形式を推奨（MP3, M4A, OGG, FLACも対応）
- **サンプリングレート**: 22050 Hz 以上
- **チャンネル**: モノラル推奨
- **長さ**: 1-5秒程度
- **品質**: クリアな音声、背景ノイズなし

## 録音ガイドライン

1. **ネイティブスピーカー**: ビサヤ語のネイティブスピーカーによる録音
2. **環境**: 静かな環境で録音
3. **マイク**: 高品質なマイクを使用
4. **発音**: 自然なスピードと明瞭な発音
5. **複数バージョン**: 可能であれば複数の話者による録音を用意

## 現在の参照音声

以下のフレーズの参照音声が用意されています：

- `maayong_buntag_ref.wav` - おはよう
- `maayong_hapon_ref.wav` - こんにちは
- `maayong_gabii_ref.wav` - こんばんは
- `salamat_ref.wav` - ありがとう
- `palihug_ref.wav` - お願いします
- `oo_ref.wav` - はい
- `dili_ref.wav` - いいえ
- `kumusta_ref.wav` - 元気ですか
- `maayo_ref.wav` - 良い
- `pangalan_ref.wav` - 名前

⚠️ **注意**: 現在のファイルはテスト用のダミー音声です。
本番環境では実際のネイティブスピーカーの音声に置き換えてください。

## 新しい単語の追加方法

1. ネイティブスピーカーに単語/フレーズを録音してもらう
2. 音声ファイルを適切な形式に変換
3. 命名規則に従ってファイル名を設定
4. このディレクトリに配置
5. サーバーを再起動（不要、自動的に認識されます）

## テスト方法

```bash
# APIエンドポイントにリクエストを送信
curl -X POST "http://localhost:8000/api/pronounce/check" \\
  -F "audio=@user_audio.wav" \\
  -F "word=maayong buntag" \\
  -F "level=beginner"
```
"""
    
    readme_path = Path("reference_audio") / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"\n✓ Created README: {readme_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Bisaya Speak AI - Reference Audio Generator")
    print("=" * 60)
    
    create_reference_audio_files()
    create_readme()
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
