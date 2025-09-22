# streamlit_gemini_chatbot.py
# Streamlit chatbot that calls Google Gemini (gemini-2.5-flash).
# - Uses Streamlit secrets for the GEMINI_API_KEY (do NOT hardcode keys).
# - Attempts SSE streaming via the Gemini streamGenerateContent endpoint.
# - Falls back to a single-response generateContent if streaming isn't available.
# Requirements:
# pip install streamlit requests
# Optional (if you prefer advanced SSE parsing): pip install sseclient-py


import streamlit as st
import requests
import json
import time
from typing import Generator, Optional


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
st.session_state.history = [] # list of (role, text)


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
# Re-render messages quickly (user message)
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
# update placeholder with partial content
assistant_placeholder.markdown(f"**Assistant:** {assistant_text}")
# streaming finished
st.session_state.history.append(("assistant", assistant_text))
except Exception as e:
# Streaming failed -> fallback to normal generate
assistant_placeholder.markdown(f"**Assistant:** _stream failed, falling back..._\n\n`{e}`")
try:
text = generate_gemini_once(prompt, api_key=API_KEY, model=MODEL)
st.session_state.history.append(("assistant", text))
assistant_placeholder.markdown(f"**Assistant:** {text}")
except Exception as e2:
assistant_placeholder.markdown(f"**Assistant:** _error: {e2}_")


# clear prompt input
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