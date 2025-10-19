"""
AI会話エンジン - Gemini APIを使用したビサヤ語会話システム
"""

import google.generativeai as genai
import os
from typing import Dict, List, Optional
from datetime import datetime
import json

class ConversationEngine:
    """AI会話エンジン - ビサヤ語学習用の対話システム"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Parameters:
        - api_key: Gemini APIキー（環境変数から取得も可能）
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 会話履歴を保存
        self.sessions: Dict[str, List[Dict]] = {}
        
    def create_session(self, session_id: str, mode: str, level: str) -> Dict:
        """
        新しい会話セッションを作成
        
        Parameters:
        - session_id: セッションID
        - mode: 会話モード（shadowing, word_drill, roleplay, free_talk）
        - level: ユーザーレベル（beginner, intermediate, advanced）
        
        Returns:
        - セッション情報
        """
        system_prompt = self._get_system_prompt(mode, level)
        
        self.sessions[session_id] = {
            "mode": mode,
            "level": level,
            "system_prompt": system_prompt,
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "session_id": session_id,
            "mode": mode,
            "level": level,
            "status": "created"
        }
    
    def _get_system_prompt(self, mode: str, level: str) -> str:
        """
        モードとレベルに応じたシステムプロンプトを生成
        """
        base_prompt = """
あなたはビサヤ語（セブアノ語）を母語とするフィリピン人です。日本人の友達と会話しています。

【重要】ユーザーの言葉をそのまま繰り返さないでください。新しい内容で返答してください。

【応答ルール】
1. 必ず新しい情報や質問を含める
2. ユーザーと同じ文を使わない
3. 会話を発展させる

【良い例】
ユーザー: Maayong buntag
あなた: Maayong buntag! Nindot nga adlaw karon, dili ba? （おはよう！今日はいい天気ですね？）

ユーザー: Oo, nindot kaayo
あなた: Unsa imong plano karon? （今日の予定は？）

【悪い例（絶対にしないこと）】
ユーザー: Maayong buntag
あなた: Maayong buntag （ただの繰り返し - NG）

【フォーマット】
ビサヤ語の文 （日本語訳）

説明や解説は一切不要です。友達との会話として返答してください。

"""
        
        level_prompts = {
            "beginner": """
レベル：初級
- 基本的な300語以内の語彙を使用
- 現在形のみを使用
- ゆっくりとしたペースで
- 頻繁にヒントを提供
- 簡単な文法構造のみ
""",
            "intermediate": """
レベル：中級
- 1000語程度の語彙を使用
- 過去形・未来形も使用
- 通常のペースで
- 必要に応じてヒントを提供
- やや複雑な文法も使用
""",
            "advanced": """
レベル：上級
- 語彙制限なし
- すべての時制と文法を使用
- ネイティブレベルのペースで
- ヒントは最小限
- 慣用句や高度な表現も使用
"""
        }
        
        mode_prompts = {
            "shadowing": """
モード：シャドーイング練習
- フレーズを提示し、ユーザーに繰り返させる
- 発音の良い点と改善点を具体的に指摘
- 正しい発音のコツを教える
""",
            "word_drill": """
モード：単語ドリル
- 単語を提示し、例文を作らせる
- 文法と発音の両方をチェック
- 代替表現も提案
""",
            "roleplay": """
モード：ロールプレイ
- 実際の場面を想定した会話
- 自然な会話の流れを重視
- 適切な表現を使っているか確認
""",
            "free_talk": """
モード：フリートーク
- 自由な会話を楽しむ
- トピックに応じて適切に応答
- 間違いは会話を止めずに自然に訂正
"""
        }
        
        return base_prompt + level_prompts.get(level, level_prompts["beginner"]) + mode_prompts.get(mode, mode_prompts["free_talk"])
    
    async def send_message(self, session_id: str, user_message: str, user_audio_transcription: Optional[str] = None) -> Dict:
        """
        ユーザーメッセージを送信し、AIの応答を取得
        
        Parameters:
        - session_id: セッションID
        - user_message: ユーザーのメッセージ（テキスト）
        - user_audio_transcription: 音声認識結果（オプション）
        
        Returns:
        - AI応答
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # ユーザーメッセージを履歴に追加
        session["history"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # プロンプトを構築
        full_prompt = session["system_prompt"] + "\n\n会話履歴:\n"
        for msg in session["history"][-5:]:  # 直近5件のみ使用
            role = "ユーザー" if msg["role"] == "user" else "AI"
            full_prompt += f"{role}: {msg['content']}\n"
        
        full_prompt += "\nAI: "
        
        try:
            # Gemini APIで応答を生成
            response = self.model.generate_content(full_prompt)
            ai_message = response.text
            
            # AI応答を履歴に追加
            session["history"].append({
                "role": "assistant",
                "content": ai_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # 応答を解析（ビサヤ語と日本語訳を分離）
            parsed_response = self._parse_response(ai_message)
            
            # 音声ファイルを生成
            audio_url = None
            if parsed_response["bisaya"]:
                try:
                    audio_url = self._generate_audio(parsed_response["bisaya"], session_id)
                    print(f"✓ Audio generated: {audio_url}")
                except Exception as audio_error:
                    print(f"⚠ Audio generation failed: {audio_error}")
            
            return {
                "status": "success",
                "ai_message": ai_message,
                "bisaya_text": parsed_response["bisaya"],
                "japanese_translation": parsed_response["japanese"],
                "pronunciation_tips": parsed_response["tips"],
                "audio_url": audio_url,
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    def _parse_response(self, response: str) -> Dict:
        """
        AI応答を解析してビサヤ語、日本語訳、発音のヒントを抽出
        """
        lines = response.split('\n')
        bisaya = ""
        japanese = ""
        tips = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 日本語訳を検出（括弧内または「訳：」の後）
            if '（' in line and '）' in line:
                parts = line.split('（')
                bisaya = parts[0].strip()
                japanese = parts[1].replace('）', '').strip()
            elif '訳：' in line or '訳:' in line:
                japanese = line.split('：')[-1].split(':')[-1].strip()
            elif '発音' in line or 'ヒント' in line or 'コツ' in line:
                tips += line + " "
            elif not japanese and not bisaya:
                bisaya = line
        
        return {
            "bisaya": bisaya or response,
            "japanese": japanese,
            "tips": tips.strip()
        }
    
    def _generate_audio(self, text: str, session_id: str) -> str:
        """
        テキストから音声ファイルを生成
        
        Parameters:
        - text: ビサヤ語テキスト
        - session_id: セッションID
        
        Returns:
        - 音声ファイルのURL
        """
        from gtts import gTTS
        import os
        import re
        
        # 括弧内の日本語訳を削除（ビサヤ語のみを抽出）
        # 例: "Maayong buntag! （おはよう）" → "Maayong buntag!"
        clean_text = re.sub(r'[（(].*?[）)]', '', text).strip()
        
        # 音声ファイルの保存先
        audio_dir = "audio_files"
        os.makedirs(audio_dir, exist_ok=True)
        
        # ファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"tts_{session_id}_{timestamp}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Google TTSで音声生成
        # ビサヤ語は直接サポートされていないため、タガログ語(tl)を使用
        # slow=Trueで少しゆっくり話すことで聞き取りやすくする
        tts = gTTS(text=clean_text, lang='tl', slow=True)
        tts.save(filepath)
        
        # URLを返す
        return f"/audio/{filename}"
    
    def get_session_summary(self, session_id: str) -> Dict:
        """
        会話セッションのサマリーを生成
        
        Parameters:
        - session_id: セッションID
        
        Returns:
        - セッションサマリー
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        history = session["history"]
        
        # 統計情報を計算
        user_messages = [msg for msg in history if msg["role"] == "user"]
        ai_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        return {
            "session_id": session_id,
            "mode": session["mode"],
            "level": session["level"],
            "created_at": session["created_at"],
            "total_turns": len(user_messages),
            "duration_estimate": len(history) * 30,  # 1ターン30秒と仮定
            "user_messages_count": len(user_messages),
            "ai_messages_count": len(ai_messages)
        }
    
    def generate_feedback(self, session_id: str) -> Dict:
        """
        会話セッションのフィードバックを生成
        
        Parameters:
        - session_id: セッションID
        
        Returns:
        - フィードバック
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # フィードバック生成用のプロンプト
        feedback_prompt = f"""
以下の会話セッションを分析し、学習者へのフィードバックを日本語で生成してください：

レベル: {session['level']}
モード: {session['mode']}

会話履歴:
"""
        for msg in session["history"]:
            role = "学習者" if msg["role"] == "user" else "講師"
            feedback_prompt += f"{role}: {msg['content']}\n"
        
        feedback_prompt += """

以下の形式でフィードバックを提供してください：
1. 良かった点（2-3個）
2. 改善点（2-3個）
3. 次回の学習アドバイス（1-2個）
4. 覚えるべき新しいフレーズ（3-5個）
"""
        
        try:
            response = self.model.generate_content(feedback_prompt)
            return {
                "status": "success",
                "feedback": response.text,
                "session_id": session_id
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }


class ScenarioManager:
    """シナリオベースの会話管理"""
    
    def __init__(self):
        self.scenarios = self._load_scenarios()
    
    def _load_scenarios(self) -> Dict:
        """シナリオデータをロード"""
        return {
            "market_001": {
                "id": "market_001",
                "title": "市場で値切る",
                "title_bisaya": "Pagpamalit sa merkado",
                "description": "地元の市場でフルーツを買います",
                "difficulty": "beginner",
                "ai_role": "果物売り",
                "user_role": "買い物客",
                "estimated_turns": 7,
                "key_phrases": [
                    "Pila ni? (いくらですか)",
                    "Mahal kaayo (高すぎます)",
                    "Pwede ba og diskwento? (割引できますか)",
                    "Sige, ihatag nako (OK、買います)"
                ],
                "opening": {
                    "bisaya": "Maayong buntag! Unsa imong gusto?",
                    "japanese": "おはよう！何が欲しいですか？"
                }
            },
            "taxi_001": {
                "id": "taxi_001",
                "title": "タクシーに乗る",
                "title_bisaya": "Pagsakay sa taxi",
                "description": "タクシーで目的地まで行きます",
                "difficulty": "beginner",
                "ai_role": "タクシー運転手",
                "user_role": "乗客",
                "estimated_turns": 5,
                "key_phrases": [
                    "Asa ka paingon? (どこに行きますか)",
                    "Palihug, adto sa... (お願いします、...へ)",
                    "Pila ang bayad? (料金はいくらですか)",
                    "Salamat (ありがとう)"
                ],
                "opening": {
                    "bisaya": "Maayong hapon! Asa ka paingon?",
                    "japanese": "こんにちは！どこに行きますか？"
                }
            },
            "restaurant_001": {
                "id": "restaurant_001",
                "title": "レストランで注文",
                "title_bisaya": "Pag-order sa restaurant",
                "description": "レストランで食事を注文します",
                "difficulty": "intermediate",
                "ai_role": "ウェイター",
                "user_role": "客",
                "estimated_turns": 8,
                "key_phrases": [
                    "Unsa ang imong gusto? (何が欲しいですか)",
                    "Gusto ko og... (私は...が欲しいです)",
                    "Pila ang tanan? (全部でいくらですか)",
                    "Lami kaayo! (とても美味しい)"
                ],
                "opening": {
                    "bisaya": "Maayong gabii! Unsa ang imong gusto nga kaon?",
                    "japanese": "こんばんは！何を食べたいですか？"
                }
            }
        }
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """シナリオを取得"""
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self, difficulty: Optional[str] = None) -> List[Dict]:
        """シナリオ一覧を取得"""
        scenarios = list(self.scenarios.values())
        if difficulty:
            scenarios = [s for s in scenarios if s["difficulty"] == difficulty]
        return scenarios
