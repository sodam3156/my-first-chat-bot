# streamlit_gemini_chatbot.py
# Streamlit chatbot that calls Google Gemini (gemini-2.5-flash).
# - Uses Streamlit secrets for the GEMINI_API_KEY (do NOT hardcode keys).
# - Attempts SSE streaming via the Gemini streamGenerateContent endpoint.
# - Falls back to a single-response generateContent if streaming isn't available.
# Requirements:
#   pip install streamlit requests

import streamlit as st
import requests
import json
from typing import Generator

st.set_page_config(page_title="Gemini Chat (gemini-2.5-flash)", layout="wide")
st.title("Gemini Chat — gemini-2.5-flash (Streamlit)")

# Load API key from Streamlit secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Streamlit secret 'GEMINI_API_KEY' not found. Put your Gemini API key in .streamlit/secrets.toml")
    st.stop()

API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash"

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state.history = []  # list of (role, text)

# UI layout: left column for chat, right column for controls/history
col1, col2 = st.columns([3, 1])

with col1:
    # Display conversation
    chat_container = st.container()
    with chat_container:
        for role, text in st.session_state.history:
            if role == "user":
                st.markdown(f"**You:** {text}")
            else:
                st.markdown(f"**Assistant:** {text}")

    # Input area
    prompt = st.text_input("Enter a message and press Enter", key="prompt_input")

    if prompt:
        # Add user message
        st.session_state.history.append(("user", prompt))

        # Rerender messages including new user message
        chat_container.empty()
        with chat_container:
            for role, text in st.session_state.history:
                if role == "user":
                    st.markdown(f"**You:** {text}")
                else:
                    st.markdown(f"**Assistant:** {text}")

        # Prepare assistant placeholder
        assistant_placeholder = st.empty()
        assistant_text = ""
        assistant_placeholder.markdown("**Assistant:** _thinking..._")

        # Try streaming first
        try:
            for chunk in stream_gemini_sse(prompt, api_key=API_KEY, model=MODEL):
                assistant_text += chunk
                assistant_placeholder.markdown(f"**Assistant:** {assistant_text}")
            st.session_state.history.append(("assistant", assistant_text))
        except Exception as e:
            assistant_placeholder.markdown(f"**Assistant:** _stream failed, falling back..._\n\n`{e}`")
            try:
                text = generate_gemini_once(prompt, api_key=API_KEY, model=MODEL)
                st.session_state.history.append(("assistant", text))
                assistant_placeholder.markdown(f"**Assistant:** {text}")
            except Exception as e2:
                assistant_placeholder.markdown(f"**Assistant:** _error: {e2}_")

        # Clear prompt input
        st.session_state.prompt_input = ""

with col2:
    st.header("Conversation history")
    if st.button("Clear conversation"):
        st.session_state.history = []
        st.experimental_rerun()
    for role, text in st.session_state.history[::-1]:
        st.write(f"{role}: {text[:120]}{'...' if len(text)>120 else ''}")


# ----------------------
# Helper functions
# ----------------------

def stream_gemini_sse(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> Generator[str, None, None]:
    """Call the Gemini streamGenerateContent SSE endpoint and yield text chunks."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    obj = json.loads(data_str)
                except Exception:
                    continue
                chunk_text = ""
                for cand in obj.get("candidates", []):
                    content = cand.get("content") or {}
                    parts = content.get("parts") if isinstance(content, dict) else None
                    if parts:
                        for p in parts:
                            t = p.get("text")
                            if t:
                                chunk_text += t
                if not chunk_text:
                    try:
                        chunk_text = obj.get('candidates', [])[0].get('content', {}).get('parts', [])[0].get('text', '')
                    except Exception:
                        chunk_text = ""
                if chunk_text:
                    yield chunk_text


def generate_gemini_once(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    """Non-streaming generateContent call."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    j = resp.json()
    try:
        return j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        txt = j.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
        if txt:
            return txt
        return json.dumps(j)
my-first-chat-bot/
 ├─ chatbot_minimal.py
 └─ .streamlit/
     └─ secrets.toml
GEMINI_API_KEY = "AIzaSyAYKx91V10uejbYvPBubodXJwnNQYnYJ9M"


