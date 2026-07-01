import streamlit as st
import google.generativeai as genai
from google import genai as genai_v2
import json
import os
import re
from io import BytesIO
from gtts import gTTS

# 페이지 설정
st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

# CSS 스타일
st.markdown("""<style>
    .line-card { background: #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid #e4e4f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .line-title { font-weight: 800; color: #4a4a8a; margin-bottom: 10px; font-size: 1.2rem; }
    .original-value { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .ipa-value { font-family: monospace; color: #3a3a7a; background: #ededfa; padding: 2px 8px; border-radius: 5px; font-size: 0.95rem; }
    .label { font-weight: 700; color: #8888bb; font-size: 0.8rem; margin-top: 15px; text-transform: uppercase; }
</style>""", unsafe_allow_html=True)

def get_api_key():
    return st.session_state.get("sidebar_api_key") or st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def call_model(lines: list, api_key: str) -> dict:
    # 안정적인 호출을 위해 configure 방식 사용
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = (f"다음 가사를 분석해서 JSON 형식으로만 출력해줘. "
              f"필수 필드: line_number, original, ipa, literal_translation, poetic_translation, vocabulary(word, meaning). "
              f"가사: {lines}")
    
    response = model.generate_content(prompt)
    raw_text = response.text
    # 깔끔하게 정리
    clean_text = re.sub(r'```json|```', '', raw_text).strip()
    return json.loads(clean_text)

st.title("🎼 Vocal Diction Assistant")

# 사이드바 설정
with st.sidebar:
    st.markdown("### 🔑 API 설정")
    user_key = st.text_input("Gemini API Key 직접 입력", type="password")
    if user_key:
        st.session_state["sidebar_api_key"] = user_key

# 메인 입력
if "lyrics_input" not in st.session_state: st.session_state.lyrics_input = ""
lyrics_input = st.text_area("가사를 입력하세요", value=st.session_state.lyrics_input, height=200)
st.session_state.lyrics_input = lyrics_input

if st.button("🎵 분석 실행", type="primary"):
    api_key = get_api_key()
    if not api_key:
        st.error("API 키가 없습니다. 사이드바에 입력해주세요.")
    else:
        try:
            with st.spinner("분석 중..."):
                results = call_model([lyrics_input], api_key)
                st.session_state.analysis_results = results
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

# 결과 출력
if "analysis_results" in st.session_state and st.session_state.analysis_results:
    st.subheader("📘 분석 결과")
    for item in st.session_state.analysis_results:
        st.markdown(f"""
        <div class="line-card">
            <div class="line-title">Line {item.get('line_number')}</div>
            <div class="original-value">{item.get('original')}</div>
            <div><span class="ipa-value">IPA: {item.get('ipa')}</span></div>
            <div class="label">직역</div>
            <div>{item.get('literal_translation')}</div>
            <div class="label">의역</div>
            <div>{item.get('poetic_translation')}</div>
        </div>
        """, unsafe_allow_html=True)