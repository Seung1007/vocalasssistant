import streamlit as st
import google.generativeai as genai
import json
import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from gtts import gTTS

# 페이지 설정
st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

# 아카이브 파일 설정
ARCHIVE_FILE = Path("archive.json")

# CSS 스타일 (카드 UI용)
st.markdown("""<style>
    .line-card { background: #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid #e4e4f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .line-title { font-weight: 800; color: #4a4a8a; margin-bottom: 10px; font-size: 1.2rem; }
    .original-value { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .ipa-value { font-family: monospace; color: #3a3a7a; background: #ededfa; padding: 2px 8px; border-radius: 5px; font-size: 0.95rem; }
    .label { font-weight: 700; color: #8888bb; font-size: 0.8rem; margin-top: 15px; text-transform: uppercase; }
    .vocab-block { background: #f9f9fb; padding: 10px; border-radius: 8px; margin-top: 5px; }
</style>""", unsafe_allow_html=True)

# API 설정 함수
def get_api_key():
    if "sidebar_api_key" in st.session_state and st.session_state["sidebar_api_key"]:
        return st.session_state["sidebar_api_key"]
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

# 모델 초기화
def get_model():
    api_key = get_api_key()
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    # 모델명 자동 감지
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    flash_model = next((m for m in models if 'flash' in m), 'gemini-1.5-flash')
    return genai.GenerativeModel(flash_model)

# UI 및 로직
st.title("🎼 Vocal Diction Assistant")

if "lyrics_input" not in st.session_state: st.session_state.lyrics_input = ""
if "analysis" not in st.session_state: st.session_state.analysis = None

lyrics_input = st.text_area("가사를 입력하세요", value=st.session_state.lyrics_input, height=150)
st.session_state.lyrics_input = lyrics_input

if st.button("🎵 분석 시작"):
    if lyrics_input.strip():
        model = get_model()
        if not model:
            st.error("API 키가 설정되지 않았습니다.")
        else:
            with st.spinner("AI가 딕션을 분석 중입니다..."):
                prompt = f"다음 가사를 분석해서 JSON 형식(line_number, original, ipa, meaning, vocabulary[{word, meaning}])으로 출력해줘: {lyrics_input}"
                try:
                    response = model.generate_content(prompt)
                    # JSON 부분만 추출
                    clean_text = re.sub(r'```json|```', '', response.text).strip()
                    st.session_state.analysis = json.loads(clean_text)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

# 결과 출력 (카드 UI)
if st.session_state.analysis:
    st.subheader("📘 분석 결과")
    for item in st.session_state.analysis:
        st.markdown(f"""
        <div class="line-card">
            <div class="line-title">Line {item.get('line_number')}</div>
            <div class="original-value">{item.get('original')}</div>
            <div><span class="ipa-value">IPA: {item.get('ipa')}</span></div>
            <div class="label">의미</div>
            <div>{item.get('meaning')}</div>
        """, unsafe_allow_html=True)
        
        if item.get("vocabulary"):
            st.markdown('<div class="label">핵심 단어</div><div class="vocab-block">', unsafe_allow_html=True)
            for v in item["vocabulary"]:
                st.write(f"• **{v['word']}**: {v['meaning']}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### 🔑 설정")
    user_key = st.text_input("API Key 입력", type="password")
    if user_key: st.session_state["sidebar_api_key"] = user_key