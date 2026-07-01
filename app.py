import streamlit as st
import os
import io
import json
import uuid
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# ── 페이지 설정 및 API 초기화 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Vocal Diction & Opera Lyric Assistant",
    page_icon="🎼",
    layout="wide",
)

# Gemini API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
except Exception as e:
    st.error(f"API 설정 오류: {e}")
    st.stop()

ARCHIVE_PATH = Path("archive.json")

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

def parse_analysis(raw):
    # 기존 파싱 함수 그대로 사용
    results = []
    for block in raw.split("---"):
        if not block.strip(): continue
        entry = {"line_number": "", "original": "", "ipa": "", "meaning": "", "vocabulary": []}
        # ... (기존 파싱 로직 동일)
        results.append(entry)
    return results

# ── 메인 로직 ────────────────────────────────────────────────────────────────
st.title("🎼 Vocal Diction & Opera Lyric Assistant")
lyrics_input = st.text_area("가사를 입력하세요", height=200)

if st.button("🎵 분석 시작"):
    lines_raw = [l for l in lyrics_input.split("\n") if l.strip()]
    if lines_raw:
        with st.spinner("분석 중..."):
            try:
                response = model.generate_content(build_prompt(lines_raw))
                st.session_state.analysis_results = parse_analysis(response.text)
            except Exception as e:
                st.error(f"분석 오류: {e}")
