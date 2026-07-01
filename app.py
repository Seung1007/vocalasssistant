import streamlit as st
import google.generativeai as genai  # 이 줄을 수정하세요!
import json
import re

st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

st.markdown("""<style>
    .line-card { background: #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid #e4e4f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .line-title { font-weight: 800; color: #4a4a8a; margin-bottom: 10px; font-size: 1.2rem; }
    .original-value { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .ipa-value { font-family: monospace; color: #3a3a7a; background: #ededfa; padding: 2px 8px; border-radius: 5px; font-size: 0.95rem; }
    .label { font-weight: 700; color: #8888bb; font-size: 0.8rem; margin-top: 15px; text-transform: uppercase; }
    .vocab-block { background: #f9f9fb; padding: 10px; border-radius: 8px; margin-top: 5px; }
</style>""", unsafe_allow_html=True)

def clean_json(text):
    text = re.sub(r"^```(?:json)?\n", "", text).replace("```", "")
    match = re.search(r"\{.*\}", text, flags=re.S)
    return match.group(0) if match else text

# STREAMING_CHUNK:교체할 call_model_cached 함수
@st.cache_data(show_spinner=False, max_entries=512)
def call_model_cached(lines_tuple: tuple, api_key: str) -> dict:
    if not api_key:
        raise RuntimeError("구글 API 키가 설정되지 않았습니다. 사이드바에 직접 입력하거나 Secrets에서 설정해 주세요.")

    # 핵심 수정: genai.configure 방식을 사용합니다
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    inner_attempts = 3
    last_exc = None
    for inner in range(inner_attempts):
        try:
            prompt = build_prompt(list(lines_tuple))
            if inner > 0:
                prompt += "\n다시 한 번 강조합니다: 각 줄의 'line_ipa'와 'diction'을 반드시 빈칸 없이 채워 한국어로 작성하고, 다른 텍스트 없이 오직 JSON 객체만 출력하세요."

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                }
            )
            raw = getattr(response, "text", "") or ""

            payload = None
            try:
                payload = json.loads(clean_json_text(raw))
            except Exception:
                payload = parse_model_response(raw, list(lines_tuple))

            if not isinstance(payload, dict):
                last_exc = RuntimeError("모델 응답을 파싱하지 못했습니다.")
                continue

            if validate_payload(payload, list(lines_tuple)):
                return payload
            last_exc = RuntimeError("모델이 일부 항목의 IPA/딕션을 누락했습니다.")

        except Exception as exc:
            last_exc = exc
            if is_rate_limit_error(exc):
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("모델 호출에 실패했습니다.")

st.title("🎼 Vocal Diction Assistant")

if "lyrics_input" not in st.session_state: st.session_state.lyrics_input = ""
lyrics_input = st.text_area("가사를 입력하세요", value=st.session_state.lyrics_input, height=150)
st.session_state.lyrics_input = lyrics_input

if st.button("🎵 초고속 분석 시작", type="primary"):
    api_key = st.session_state.get("sidebar_api_key") or st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("API 키를 확인해주세요.")
    else:
        with st.spinner("AI가 빠르게 분석 중입니다..."):
            try:
                results = call_model(lyrics_input, api_key)
                st.session_state.analysis_results = results
                st.success("분석 완료!")
            except Exception as e:
                st.error(f"분석 오류: {e}")

if "analysis_results" in st.session_state:
    st.subheader("📘 분석 결과")
    for item in st.session_state.analysis_results:
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

with st.sidebar:
    st.markdown("### 🔑 설정")
    user_key = st.text_input("API Key 입력", type="password")
    if user_key: st.session_state["sidebar_api_key"] = user_key