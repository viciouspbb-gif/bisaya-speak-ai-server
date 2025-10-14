# Reference Audio Files

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
curl -X POST "http://localhost:8000/api/pronounce/check" \
  -F "audio=@user_audio.wav" \
  -F "word=maayong buntag" \
  -F "level=beginner"
```
