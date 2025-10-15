"""
全フレーズの参照音声を生成するスクリプト
Google Text-to-Speech (gTTS) を使用してビサヤ語の音声を生成
"""

from gtts import gTTS
from pathlib import Path
import re

# 全70個のフレーズリスト
PHRASES = {
    # 初級 - 挨拶
    "maayong_buntag": "Maayong buntag",
    "maayong_hapon": "Maayong hapon",
    "maayong_gabii": "Maayong gabii",
    "kumusta": "Kumusta",
    "maayo": "Maayo",
    "adios": "Adios",
    "babay": "Babay",
    
    # 初級 - 基本単語
    "salamat": "Salamat",
    "palihug": "Palihug",
    "oo": "Oo",
    "dili": "Dili",
    "pasensya": "Pasensya",
    "walay_sapayan": "Walay sapayan",
    
    # 初級 - 自己紹介
    "pangalan": "Pangalan",
    "ako_si": "Ako si",
    "unsa_imong_pangalan": "Unsa imong pangalan",
    "nalipay_ko_nga_makaila_nimo": "Nalipay ko nga makaila nimo",
    
    # 初級 - 数字
    "usa": "Usa",
    "duha": "Duha",
    "tulo": "Tulo",
    "upat": "Upat",
    "lima": "Lima",
    
    # 初級 - 家族
    "pamilya": "Pamilya",
    "mama": "Mama",
    "papa": "Papa",
    "igsoon": "Igsoon",
    
    # 初級 - 質問
    "asa_ka_gikan": "Asa ka gikan",
    "pila_ka_tuig": "Pila ka tuig",
    "unsa_ni": "Unsa ni",
    "asa_ang_banyo": "Asa ang banyo",
    
    # 中級 - 市場
    "pila_ni": "Pila ni",
    "mahal_kaayo": "Mahal kaayo",
    "pwede_ba_nga_discount": "Pwede ba nga discount",
    "barato_lang": "Barato lang",
    "kuhaon_nako_ni": "Kuhaon nako ni",
    
    # 中級 - 交通
    "asa_ang_jeepney": "Asa ang jeepney",
    "pila_ang_pamasahe": "Pila ang pamasahe",
    "lugar_lang": "Lugar lang",
    "adto_ko_sa_ayala": "Adto ko sa Ayala",
    "unsa_ang_sakyan_paingon_sa": "Unsa ang sakyan paingon sa",
    
    # 中級 - レストラン
    "unsa_ang_imong_gusto": "Unsa ang imong gusto",
    "gusto_ko_og_tubig": "Gusto ko og tubig",
    "lami_kaayo": "Lami kaayo",
    "pila_ang_bayad": "Pila ang bayad",
    "busog_na_ko": "Busog na ko",
    
    # 中級 - ホテル
    "may_bakante_ba_mo": "May bakante ba mo",
    "pila_ang_usa_ka_gabii": "Pila ang usa ka gabii",
    "asa_ang_akong_kwarto": "Asa ang akong kwarto",
    
    # 中級 - 観光
    "asa_ang_beach": "Asa ang beach",
    "nindot_kaayo_diri": "Nindot kaayo diri",
    "pwede_ba_ko_magkuha_og_picture": "Pwede ba ko magkuha og picture",
    
    # 中級 - 日常会話
    "tabang": "Tabang",
    "nawala_akong_bag": "Nawala akong bag",
    "masakiton_ko": "Masakiton ko",
    "asa_ang_hospital": "Asa ang hospital",
    
    # 上級 - 日常会話
    "unsaon_nako_pag_adto_sa_ayala": "Unsaon nako pag-adto sa Ayala",
    "pwede_ba_nga_tabangan_nimo_ko": "Pwede ba nga tabangan nimo ko",
    "wala_koy_kasabot_sa_imong_gisulti": "Wala koy kasabot sa imong gisulti",
    "mahimo_ba_nimo_nga_hinayhinay_ang_pagsulti": "Mahimo ba nimo nga hinayhinay ang pagsulti",
    
    # 上級 - ビジネス
    "gusto_nako_nga_makigsabot_sa_imong_manager": "Gusto nako nga makigsabot sa imong manager",
    "kanus_a_ang_sunod_nga_miting": "Kanus-a ang sunod nga miting",
    
    # 上級 - 緊急時
    "kinahanglan_nako_og_doktor_dayon": "Kinahanglan nako og doktor dayon",
    "tawagi_ang_pulis": "Tawagi ang pulis",
    "gikawatan_ko_sa_akong_wallet": "Gikawatan ko sa akong wallet",
    
    # 上級 - 感情表現
    "nalipay_kaayo_ko_nga_naa_ka_dinhi": "Nalipay kaayo ko nga naa ka dinhi",
    "nasuko_ko_tungod_sa_imong_gibuhat": "Nasuko ko tungod sa imong gibuhat",
    
    # 上級 - 依頼
    "pwede_ba_nimo_nga_ipahibalo_nako_kung_human_na": "Pwede ba nimo nga ipahibalo nako kung human na",
    "palihug_ayuha_ang_akong_booking": "Palihug ayuha ang akong booking",
    
    # 上級 - 意見
    "sa_akong_hunahuna_mas_maayo_kung": "Sa akong hunahuna, mas maayo kung",
    "dili_ko_mouyon_sa_imong_plano": "Dili ko mouyon sa imong plano",
}


def sanitize_filename(text: str) -> str:
    """
    ファイル名として使用できる文字列に変換
    """
    # スペースをアンダースコアに
    text = text.replace(" ", "_")
    # 特殊文字を削除
    text = re.sub(r'[^\w\-]', '', text)
    # 小文字に
    text = text.lower()
    return text


def generate_reference_audio():
    """
    全フレーズの参照音声を生成
    """
    reference_dir = Path("reference_audio")
    reference_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Bisaya Speak AI - Reference Audio Generator (All Phrases)")
    print("=" * 70)
    print(f"\n📁 Output directory: {reference_dir.absolute()}")
    print(f"🎯 Total phrases: {len(PHRASES)}")
    print("\n⚠️  Note: Using Google TTS with Filipino language")
    print("   For best results, consider using native Bisaya recordings.\n")
    
    success_count = 0
    error_count = 0
    
    for key, text in PHRASES.items():
        try:
            filename = f"{key}_ref.mp3"
            filepath = reference_dir / filename
            
            # gTTSでフィリピン語（タガログ語）の音声を生成
            # ビサヤ語は直接サポートされていないが、フィリピン語で近い発音が得られる
            tts = gTTS(text=text, lang='tl', slow=False)  # 'tl' = Tagalog/Filipino
            tts.save(str(filepath))
            
            print(f"✓ Created: {filename} - '{text}'")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Error creating {key}: {e}")
            error_count += 1
    
    print("\n" + "=" * 70)
    print(f"✓ Successfully generated: {success_count} files")
    if error_count > 0:
        print(f"✗ Errors: {error_count} files")
    print("=" * 70)
    
    print("\n📝 Next steps:")
    print("1. Review the generated audio files")
    print("2. Replace with native Bisaya recordings if available")
    print("3. Restart the server to use the new reference audio")
    print("\n💡 Tip: For production, consider using:")
    print("   - ElevenLabs API for better quality")
    print("   - Native Bisaya speaker recordings")
    print("   - Professional voice actors")


if __name__ == "__main__":
    try:
        generate_reference_audio()
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
