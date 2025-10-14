"""
発音評価機能のテストスクリプト
"""

import requests
import json
from pathlib import Path
import numpy as np
import soundfile as sf


def create_test_audio(filename: str = "test_user_audio.wav", duration: float = 1.5):
    """
    テスト用のユーザー音声を生成
    """
    sample_rate = 22050
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 参照音声と少し異なる周波数で生成
    frequencies = [220, 440, 660, 880]  # 参照音声より少し高め
    audio = np.zeros_like(t)
    
    for i, freq in enumerate(frequencies):
        amplitude = 0.25 / (i + 1)
        audio += amplitude * np.sin(2 * np.pi * freq * t)
    
    envelope = np.exp(-t * 0.6)
    audio = audio * envelope
    audio = audio / np.max(np.abs(audio)) * 0.7
    
    sf.write(filename, audio.astype(np.float32), sample_rate)
    print(f"✓ Created test audio: {filename}")
    return filename


def test_pronunciation_api(audio_file: str, word: str, level: str = "beginner"):
    """
    発音評価APIをテスト
    """
    url = "http://localhost:8000/api/pronounce/check"
    
    print(f"\n{'='*60}")
    print(f"Testing pronunciation for: '{word}' (Level: {level})")
    print(f"{'='*60}")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'audio': (audio_file, f, 'audio/wav')}
            data = {
                'word': word,
                'language': 'bisaya',
                'level': level
            }
            
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ Status: {result['status']}")
                print(f"✓ Message: {result['message']}")
                
                if 'data' in result:
                    data = result['data']
                    print(f"\n📊 Results:")
                    print(f"  - Word: {data.get('word')}")
                    print(f"  - Level: {data.get('level')}")
                    print(f"  - Pronunciation Score: {data.get('pronunciation_score')}")
                    
                    if 'feedback' in data:
                        feedback = data['feedback']
                        print(f"\n💬 Feedback:")
                        print(f"  - Rating: {feedback.get('rating')}")
                        print(f"  - Overall: {feedback.get('overall')}")
                        
                        if 'details' in feedback and feedback['details']:
                            print(f"\n  📝 Details:")
                            for detail in feedback['details']:
                                print(f"    • {detail.get('aspect')}: {detail.get('comment')}")
                        
                        if 'tips' in feedback:
                            print(f"\n  💡 Tips: {feedback.get('tips')}")
                    
                    if 'comparison_details' in data:
                        print(f"\n🔍 Comparison Details:")
                        user_feat = data['comparison_details']['user_features']
                        ref_feat = data['comparison_details']['reference_features']
                        print(f"  User Duration: {user_feat['duration']:.2f}s")
                        print(f"  Reference Duration: {ref_feat['duration']:.2f}s")
                        print(f"  User Pitch: {user_feat['pitch_mean']:.2f} Hz")
                        print(f"  Reference Pitch: {ref_feat['pitch_mean']:.2f} Hz")
                
                return True
            else:
                print(f"✗ Error: Status code {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False


def test_all_levels(audio_file: str, word: str):
    """
    全レベルでテスト
    """
    levels = ["beginner", "intermediate", "advanced"]
    
    print(f"\n{'='*60}")
    print(f"Testing all levels for word: '{word}'")
    print(f"{'='*60}")
    
    results = {}
    for level in levels:
        success = test_pronunciation_api(audio_file, word, level)
        results[level] = success
        print()  # 空行
    
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for level, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{level.capitalize()}: {status}")


def main():
    """
    メインテスト実行
    """
    print("=" * 60)
    print("Bisaya Speak AI - Test Suite")
    print("=" * 60)
    
    # サーバーの稼働確認
    print("\n1. Checking server status...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✓ Server is running")
        else:
            print("✗ Server returned unexpected status")
            return
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("\nPlease start the server first:")
        print("  python main.py")
        return
    
    # テスト音声を生成
    print("\n2. Creating test audio...")
    test_audio = create_test_audio()
    
    # 単一テスト
    print("\n3. Testing pronunciation evaluation...")
    test_pronunciation_api(test_audio, "maayong buntag", "beginner")
    
    # 全レベルテスト
    print("\n4. Testing all difficulty levels...")
    test_all_levels(test_audio, "maayong buntag")
    
    # クリーンアップ
    print("\n5. Cleanup...")
    if Path(test_audio).exists():
        Path(test_audio).unlink()
        print(f"✓ Removed test file: {test_audio}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
