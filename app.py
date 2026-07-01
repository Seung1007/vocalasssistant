import streamlit as st
import google.generativeai as genai
import json
import os
import re

# 페이지 설정
st.set_page_config(page_title="Vocal Diction Assistant", page_icon="🎼", layout="wide")

def get_api_key():
    return st.session_state.get("sidebar_api_key") or st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def call_model(lines: list, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 단어 뜻(vocabulary) 필드를 다시 복구하고 한국어 출력을 강화했습니다.
    prompt = (f"다음 가사를 성악 딕션 분석가처럼 분석해줘. "
              f"모든 응답(직역, 의역, 단어 의미)은 반드시 한국어로 작성해. "
              f"결과는 JSON 형식으로 출력할 것. "
              f"필수 필드: line_number, original, ipa, literal_translation(한국어 직역), poetic_translation(한국어 의역), vocabulary(word와 meaning 포함). "
              f"가사: {lines}")
    
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
            with st.spinner("AI 코치가 가사와 단어 뜻을 분석 중입니다..."):
                results = call_model([lyrics_input], api_key)
                st.session_state.analysis_results = results
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

if "analysis_results" in st.session_state:
    st.subheader("📘 분석 결과")
    for item in st.session_state.analysis_results:
        st.markdown(f"""
        <div style='background:#f9f9fb; padding:20px; border-radius:10px; margin-bottom:15px;'>
            <h4>{item.get('original')}</h4>
            <p><b>IPA:</b> {item.get('ipa')}</p>
            <p><b>직역:</b> {item.get('literal_translation')}</p>
            <p><b>의역:</b> {item.get('poetic_translation')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 단어 뜻(vocabulary) 부분 복구 출력
        vocab_list = item.get('vocabulary', [])
        if vocab_list:
            st.markdown("<b>핵심 단어 뜻:</b>", unsafe_allow_html=True)
            for v in vocab_list:
                st.write(f"• **{v.get('word')}**: {v.get('meaning')}")