import streamlit as st
from google import genai
import json
import os
import re

# 페이지 설정
st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

# CSS 스타일 (카드 UI용)
st.markdown("""<style>
    .line-card { background: #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid #e4e4f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .line-title { font-weight: 800; color: #4a4a8a; margin-bottom: 10px; font-size: 1.2rem; }
    .original-value { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .ipa-value { font-family: monospace; color: #3a3a7a; background: #ededfa; padding: 2px 8px; border-radius: 5px; font-size: 0.95rem; }
    .label { font-weight: 700; color: #8888bb; font-size: 0.8rem; margin-top: 15px; text-transform: uppercase; }
    .vocab-block { background: #f9f9fb; padding: 10px; border-radius: 8px; margin-top: 5px; }
</style>""", unsafe_allow_html=True)

# 1. API 설정 및 모델 함수
def get_api_key():
    return st.session_state.get("sidebar_api_key") or st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

@st.cache_data(show_spinner=False, max_entries=512)
def call_model_cached(lines_tuple: tuple, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"다음 가사를 분석해서 JSON 형식으로 출력해줘: {lines_tuple}. 필수 필드: line_number, original, ipa, literal_translation, poetic_translation, vocabulary(word, meaning). 모든 뜻은 한국어로 작성해."
    
    response = model.generate_content(prompt)
    clean_text = re.sub(r'
```json|```', '', response.text).strip()
    return json.loads(clean_text)

def call_model(lines: list, api_key: str) -> dict:
    return call_model_cached(tuple(lines), api_key)

def analyze_text(text):
    api_key = get_api_key()
    if not api_key:
        st.error("API 키가 설정되지 않았습니다.")
        return
    
    with st.spinner("AI가 분석 중입니다..."):
        try:
            st.session_state.analysis = call_model([text], api_key)
        except Exception as e:
            st.error(f"분석 오류: {e}")

# 2. 메인 UI (여기서 들여쓰기 0으로 시작!)
st.title("🎼 Vocal Diction Assistant")

if "lyrics_input" not in st.session_state: st.session_state.lyrics_input = ""
lyrics_input = st.text_area("가사를 입력하세요", value=st.session_state.lyrics_input, height=150)
st.session_state.lyrics_input = lyrics_input

if st.button("🎵 분석 시작"):
    if lyrics_input.strip():
        analyze_text(lyrics_input)

# 3. 결과 출력
if "analysis" in st.session_state and st.session_state.analysis:
    st.subheader("📘 분석 결과")
    for item in st.session_state.analysis:
        st.markdown(f"""
        <div class="line-card">
            <div class="line-title">Line {item.get('line_number')}</div>
            <div class="original-value">{item.get('original')}</div>
            <div><span class="ipa-value">IPA: {item.get('ipa')}</span></div>
            <div class="label">직역</div>
            <div>{item.get('literal_translation')}</div>
            <div class="label">의역 (성악적 해석)</div>
            <div>{item.get('poetic_translation')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if item.get("vocabulary"):
            st.markdown('<div class="label">핵심 단어</div><div class="vocab-block">', unsafe_allow_html=True)
            for v in item["vocabulary"]:
                st.write(f"• **{v.get('word')}**: {v.get('meaning')}")
            st.markdown('</div>', unsafe_allow_html=True)

# 4. 사이드바
with st.sidebar:
    st.markdown("### 🔑 설정")
    user_key = st.text_input("API Key 입력", type="password")
    if user_key: st.session_state["sidebar_api_key"] = user_key