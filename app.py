import streamlit as st
import os
import io
import json
import uuid
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# ── API 설정 (자동 감지 모드) ─────────────────────────────────────────────────
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 사용 가능한 모델 목록을 조회해서 첫 번째 flash 모델을 자동으로 가져옵니다.
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # 'flash'가 포함된 모델을 찾거나, 없으면 기본값으로 1.5-flash 사용
    flash_model = next((m for m in available_models if 'flash' in m), 'gemini-1.5-flash')
    
    model = genai.GenerativeModel(flash_model)
    st.sidebar.caption(f"연결된 모델: {flash_model}") 
except Exception as e:
    st.error(f"API 설정 오류: {e}")
    st.stop()

# ── CSS 디자인 (기존 코드 그대로) ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f7f7fb; }
    .main .block-container { padding-top: 2rem; max-width: 1100px; }
    .line-card { background: #ffffff; border: 1px solid #e4e4f0; border-radius: 16px; padding: 22px 28px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(80,80,160,0.06); }
    .line-title { font-size: 1.0rem; font-weight: 800; color: #3a3a6a; margin-bottom: 12px; text-transform: uppercase; }
    .label { font-weight: 700; color: #8888bb; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 3px; margin-top: 10px; }
    .value { color: #1a1a2e; font-size: 1.0rem; line-height: 1.65; margin-bottom: 4px; }
    .original-value { color: #1a1a2e; font-size: 1.1rem; font-weight: 600; line-height: 1.5; margin-bottom: 4px; }
    .ipa-value { font-family: 'Courier New', monospace; background: #ededfa; padding: 4px 12px; border-radius: 8px; display: inline-block; color: #3a3a7a; font-size: 1.02rem; margin-bottom: 4px; }
    .vocab-block { background: #f8f8fd; border-radius: 10px; padding: 10px 14px; margin-top: 4px; }
    .vocab-item { margin-bottom: 4px; color: #2a2a4a; font-size: 0.93rem; }
    .vocab-item .word { font-weight: 700; color: #5252a0; }
    .section-header { font-size: 1.05rem; font-weight: 800; color: #3a3a6a; margin: 1.6rem 0 0.7rem 0; padding-bottom: 6px; border-bottom: 2.5px solid #e4e4f0; }
    .archive-card { background: #fff; border: 1px solid #e4e4f0; border-radius: 14px; padding: 18px 22px; margin-bottom: 14px; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 및 아카이브 함수 ──────────────────────────────────────────────────
if "analysis_results" not in st.session_state: st.session_state.analysis_results = []
if "tts_cache" not in st.session_state: st.session_state.tts_cache = {}
if "page" not in st.session_state: st.session_state.page = "analysis"

def load_archive():
    return json.loads(ARCHIVE_PATH.read_text(encoding="utf-8")) if ARCHIVE_PATH.exists() else []

def save_archive(data):
    ARCHIVE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def archive_add(title, composer, lyrics, results):
    data = load_archive()
    entry = {"id": str(uuid.uuid4()), "title": title, "composer": composer, "lyrics": lyrics, "results": results, "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    data.append(entry)
    save_archive(data)
    return "added"

# ── Gemini용 분석 로직 (OpenAI에서 교체) ───────────────────────────────────────
def build_prompt(lines):
    joined = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))
    return f"""You are a world-class vocal diction coach. Analyze the lyrics line by line in the format:
LINE_NUMBER: <number>
ORIGINAL: <text>
IPA: <IPA>
MEANING: <Korean>
VOCABULARY:
- <word>: <meaning>
---
Lyrics: {joined}"""

# ── 분석 결과를 카드 형태로 예쁘게 출력하는 함수 (app.py에 추가/수정) ──────────
def display_results(results):
    for item in results:
        with st.container():
            st.markdown(f'<div class="line-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="line-title">Line {item["line_number"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="original-value">{item["original"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ipa-value">{item["ipa"]}</div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="label">의미</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="value">{item["meaning"]}</div>', unsafe_allow_html=True)
            
            if item.get("vocabulary"):
                st.markdown(f'<div class="label">단어장</div>', unsafe_allow_html=True)
                st.markdown('<div class="vocab-block">', unsafe_allow_html=True)
                for vocab in item["vocabulary"]:
                    st.markdown(f'<div class="vocab-item"><span class="word">{vocab["word"]}</span>: {vocab["meaning"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# ── 메인 화면 출력 로직 (버튼 밑에 추가) ──────────────────────────────────────────
if st.session_state.analysis_results:
    display_results(st.session_state.analysis_results)
    if st.button("💾 이 분석 결과 저장하기"):
        archive_add("오페라 분석", "Unknown", lyrics_input, st.session_state.analysis_results)
        st.success("보관함에 저장되었습니다!")