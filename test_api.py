"""
APIテスト用スクリプト
サーバーが正常に動作しているか確認するためのテストコード
"""

import requests
import json
from pathlib import Path


def test_root_endpoint():
    """ルートエンドポイントのテスト"""
    print("Testing root endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_health_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    print("\nTesting health endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_pronunciation_check(audio_file_path: str = None):
    """発音診断エンドポイントのテスト"""
    print("\nTesting pronunciation check endpoint...")
    
    # テスト用の音声ファイルがない場合はスキップ
    if not audio_file_path or not Path(audio_file_path).exists():
        print("No audio file provided or file not found. Skipping this test.")
        print("To test this endpoint, provide a valid audio file path.")
        return None
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {
                'word': 'maayong buntag',
                'language': 'bisaya'
            }
            
            response = requests.post(
                "http://localhost:8000/api/pronounce/check",
                files=files,
                data=data
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """メインテスト実行"""
    print("=" * 50)
    print("Bisaya Speak AI - API Test")
    print("=" * 50)
    
    results = []
    
    # 各エンドポイントをテスト
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Health Endpoint", test_health_endpoint()))
    
    # 音声ファイルのパスを指定してテスト（オプション）
    # audio_file = "path/to/your/test_audio.wav"
    # results.append(("Pronunciation Check", test_pronunciation_check(audio_file)))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print("\nNote: To test the pronunciation check endpoint,")
    print("uncomment the lines in main() and provide a valid audio file path.")


if __name__ == "__main__":
    main()
