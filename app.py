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
                # 문제 해결: 중괄호 중복을 피하기 위해 프롬프트 수정
                prompt = (f"다음 가사를 분석해서 JSON 형식으로 출력해줘. "
                          f"필수 필드: line_number, original, ipa, meaning, vocabulary(word와 meaning 포함). "
                          f"**중요: 'meaning'과 vocabulary의 'meaning'은 반드시 한국어로 번역해서 작성해줘.** "
                          f"가사: {lyrics_input}")
                try:
                    response = model.generate_content(prompt)
                    clean_text = re.sub(r'```json|```', '', response.text).strip()
                    st.session_state.analysis = json.loads(clean_text)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

# 결과 출력 (카드 UI 수정본)
if st.session_state.analysis:
    st.subheader("📘 분석 결과")
    
    # 데이터가 딕셔너리라면 리스트로 변환 시도
    analysis_data = st.session_state.analysis
    if isinstance(analysis_data, dict):
        # 만약 dict 안에 'lines'라는 키가 있다면 그것을 사용
        analysis_data = analysis_data.get('lines', [analysis_data])
    
    # 이제 반드시 리스트 형태일 것이므로 안전하게 루프 실행
    for item in analysis_data:
        # 데이터가 None일 경우를 대비해 기본값 처리
        line_num = item.get('line_number', '1')
        original = item.get('original', '가사 없음')
        ipa = item.get('ipa', '정보 없음')
        meaning = item.get('meaning', '번역 없음')
        
        st.markdown(f"""
        <div class="line-card">
            <div class="line-title">Line {line_num}</div>
            <div class="original-value">{original}</div>
            <div><span class="ipa-value">IPA: {ipa}</span></div>
            <div class="label">의미</div>
            <div>{meaning}</div>
        </div>
        """, unsafe_allow_html=True)
        
        vocab = item.get("vocabulary")
        if vocab and isinstance(vocab, list):
            st.markdown('<div class="label">핵심 단어</div><div class="vocab-block">', unsafe_allow_html=True)
            for v in vocab:
                st.write(f"• **{v.get('word', '')}**: {v.get('meaning', '')}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### 🔑 설정")
    user_key = st.text_input("API Key 입력", type="password")
    if user_key: st.session_state["sidebar_api_key"] = user_key