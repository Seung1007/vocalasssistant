import streamlit as st
import google.generativeai as genai
import json
import os
import re
import uuid
from datetime import datetime
from io import BytesIO
from gtts import gTTS

LANG_TTS_MAP = {"de": "de", "it": "it", "fr": "fr", "en": "en", "es": "es", "ru": "ru"}

st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

# =========================================================
# 기존 함수 (변경 없음)
# =========================================================

def get_api_key():
    return st.session_state.get("sidebar_api_key") or st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))


def generate_audio(text, lang_code):
    try:
        buffer = BytesIO()
        lang = lang_code.split('-')[0] if '-' in lang_code else lang_code
        tts = gTTS(text=text, lang=LANG_TTS_MAP.get(lang, "en"), slow=False)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except:
        return None


def call_model(lines: list, api_key: str) -> list:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = (f"다음 가사를 분석해줘. JSON 리스트 형태로 답해줘. "
              f"각 아이템은 다음 키를 가져야 해: line_number, original, lang_code, ipa, literal_translation, poetic_translation, vocabulary(word, meaning). "
              f"모든 응답은 한국어로 작성해. 가사: {lines}")
    response = model.generate_content(prompt)
    clean_text = re.sub(r'```json|```', '', response.text).strip()
    return json.loads(clean_text)


# =========================================================
# 새로 추가: 레퍼토리 저장/불러오기 (로컬 JSON 파일 기반)
#
# ⚠️ 주의: Streamlit Community Cloud는 앱이 재시작되거나
# 재배포될 때 파일 시스템이 초기화돼서 repertoire.json이
# 날아갈 수 있어요. 지금은 "저장 기능이 있으면 사람들이
# 실제로 쓰는지"를 검증하는 용도로만 쓰고, 검증되면
# Supabase 같은 진짜 DB로 옮기는 걸 추천해요.
# =========================================================

REPERTOIRE_FILE = "repertoire.json"


def load_repertoire():
    if not os.path.exists(REPERTOIRE_FILE):
        return []
    try:
        with open(REPERTOIRE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_repertoire(data):
    with open(REPERTOIRE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_repertoire(lyrics_input, analysis_results):
    repertoire = load_repertoire()
    # 원문 첫 줄을 제목으로 임시 사용 (나중에 유저가 직접 제목 입력하게 바꿀 수 있음)
    title_guess = analysis_results[0].get("original", "제목 없음") if analysis_results else "제목 없음"
    new_entry = {
        "id": str(uuid.uuid4()),
        "title": title_guess,
        "lyrics_input": lyrics_input,
        "analysis_results": analysis_results,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    repertoire.append(new_entry)
    save_repertoire(repertoire)
    return new_entry


def delete_from_repertoire(entry_id):
    repertoire = load_repertoire()
    repertoire = [item for item in repertoire if item["id"] != entry_id]
    save_repertoire(repertoire)


# =========================================================
# 화면 구성
# =========================================================

st.title("🎼 Vocal Diction Assistant")

with st.sidebar:
    user_key = st.text_input("Gemini API Key 직접 입력", type="password")
    if user_key:
        st.session_state["sidebar_api_key"] = user_key

    st.markdown("---")

    # ----- 새로 추가: 사이드바 "내 레퍼토리" 목록 -----
    st.subheader("📚 내 레퍼토리")
    repertoire = load_repertoire()

    if not repertoire:
        st.caption("아직 저장된 곡이 없어요.")
    else:
        for entry in reversed(repertoire):  # 최근 저장한 곡이 위로 오게
            with st.expander(f"🎵 {entry['title'][:20]}"):
                st.caption(f"저장일: {entry['saved_at']}")
                col1, col2 = st.columns(2)
                if col1.button("불러오기", key=f"load_{entry['id']}"):
                    st.session_state.analysis_results = entry["analysis_results"]
                    st.session_state.loaded_lyrics = entry["lyrics_input"]
                    st.rerun()
                if col2.button("삭제", key=f"delete_{entry['id']}"):
                    delete_from_repertoire(entry["id"])
                    st.rerun()

# 레퍼토리에서 불러온 가사가 있으면 입력창에 자동으로 채워주기
default_lyrics = st.session_state.get("loaded_lyrics", "")
lyrics_input = st.text_area("가사를 입력하세요", value=default_lyrics, height=200)

if st.button("🎵 분석 실행"):
    api_key = get_api_key()
    if not api_key:
        st.error("API 키를 사이드바에 입력해주세요.")
    else:
        try:
            with st.spinner("AI 분석 중..."):
                results = call_model([lyrics_input], api_key)
                st.session_state.analysis_results = results
        except Exception as e:
            st.error(f"분석 오류: {str(e)}")

if "analysis_results" in st.session_state and isinstance(st.session_state.analysis_results, list):
    st.subheader("📘 분석 결과")

    # ----- 새로 추가: 레퍼토리 저장 버튼 -----
    if st.button("📁 레퍼토리에 저장"):
        add_to_repertoire(lyrics_input, st.session_state.analysis_results)
        st.success("레퍼토리에 저장했어요!")
        st.rerun()

    for item in st.session_state.analysis_results:
        if not isinstance(item, dict):
            continue
        st.markdown("---")
        c1, c2 = st.columns([0.8, 0.2])
        c1.markdown(f"### {item.get('original', '')}")
        audio_bytes = generate_audio(item.get('original', ''), item.get('lang_code', 'en'))
        if audio_bytes:
            c2.audio(audio_bytes, format="audio/mp3")
        st.write(f"**IPA:** {item.get('ipa', '')}")
        st.write(f"**직역:** {item.get('literal_translation', '')}")
        st.write(f"**의역:** {item.get('poetic_translation', '')}")
        vocab = item.get('vocabulary', [])
        if vocab:
            st.write("**핵심 단어:**")
            for v in vocab:
                st.write(f"- {v.get('word', '')}: {v.get('meaning', '')}")