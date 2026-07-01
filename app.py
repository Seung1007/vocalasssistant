import streamlit as st
import google.generativeai as genai
import json
import os
import re
from io import BytesIO
from gtts import gTTS

LANG_TTS_MAP = {"de": "de", "it": "it", "fr": "fr", "en": "en", "es": "es", "ru": "ru"}

st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

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

st.title("🎼 Vocal Diction Assistant")

with st.sidebar:
    user_key = st.text_input("Gemini API Key 직접 입력", type="password")
    if user_key: st.session_state["sidebar_api_key"] = user_key

lyrics_input = st.text_area("가사를 입력하세요", height=200)

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
    for item in st.session_state.analysis_results:
        if not isinstance(item, dict): continue
        
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