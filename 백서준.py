# streamlit_gemini_chatbot.py
import streamlit as st
import requests
import json

# Streamlit secrets에서 API 키 가져오기
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_API_URL = "https://api.generative.google.com/v1beta2/models/gemini-2.5-flash:generateContent"

# 세션 상태 초기화
if "history" not in st.session_state:
    st.session_state.history = []

st.title("💬 Gemini Chatbot")

# 사용자 입력
user_input = st.text_input("메시지를 입력하세요:", key="input")

def generate_response(user_message):
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_message}]
            }
        ],
        "temperature": 0.7,
        "candidate_count": 1,
    }

    try:
        # 스트리밍 방식 시도
        with requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), stream=True) as r:
            r.raise_for_status()
            response_text = ""
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    # 여기서 실제 응답 부분을 파싱해야 함
                    response_text += decoded_line
            return response_text
    except Exception as e:
        st.error(f"스트리밍 실패: {e}\n일반 요청으로 시도합니다.")
        # 스트리밍 불가 시 일반 요청
        r = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
        r.raise_for_status()
        resp_json = r.json()
        # 모델 응답 파싱 (모델 구조에 따라 수정 필요)
        return resp_json.get("candidates", [{}])[0].get("content", [{}])[0].get("text", "")

# 메시지 전송 처리
if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    bot_response = generate_response(user_input)
    st.session_state.history.append({"role": "assistant", "content": bot_response})
    st.experimental_rerun()

# 이전 대화 표시
for chat in st.session_state.history:
    if chat["role"] == "user":
        st.markdown(f"**You:** {chat['content']}")
    else:
        st.markdown(f"**Bot:** {chat['content']}")
