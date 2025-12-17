"""
Streamlit Workout AI — Dark Gym Theme
Premium fitness UI with neon accents
Integrates:
- Advanced AI Workout Agent (agent.py)
- Persistent sessions & memory
- Dark-mode gym aesthetic
- Exercise visuals
"""

import streamlit as st
import uuid
import time
import streamlit.components.v1 as components
from agent import create_agent, chat as agent_chat

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="🏋️‍♂️ Workout AI Coach",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# DARK GYM THEME CSS
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0E0E10;
    color: #EAEAEA;
    font-family: 'Inter', sans-serif;
}

#chatbox {
    border-radius: 18px;
    padding: 22px;
    background: rgba(26,26,29,0.9);
    backdrop-filter: blur(12px);
    max-height: 65vh;
    overflow-y: auto;
    box-shadow: 0 0 40px rgba(255,106,0,0.2);
    border: 1px solid rgba(255,255,255,0.05);
}

.msg-user {
    margin-left: auto;
    margin-bottom: 14px;
    padding: 14px 18px;
    border-radius: 16px;
    background: #2A2A2E;
    max-width: 75%;
}

.msg-assistant {
    margin-right: auto;
    margin-bottom: 14px;
    padding: 16px 20px;
    border-radius: 16px;
    background: linear-gradient(135deg,#FF6A00,#FF3C00);
    max-width: 75%;
    box-shadow: 0 0 20px rgba(255,106,0,0.35);
}

.meta {
    font-size: 11px;
    opacity: 0.7;
    margin-top: 6px;
}

section[data-testid="stSidebar"] {
    background: #121214;
}

.sidebar-header {
    font-size: 18px;
    font-weight: 700;
    color: #FF6A00;
}

button {
    background: linear-gradient(135deg,#FF6A00,#FF3C00) !important;
    color: white !important;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 600 !important;
}

textarea {
    background: #1A1A1D !important;
    color: #EAEAEA !important;
    border-radius: 14px !important;
}

.exercise-img {
    max-width: 100%;
    border-radius: 14px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Agent Initialization
# =========================
@st.cache_resource(show_spinner=False)
def get_agent():
    return create_agent()

if "agent" not in st.session_state:
    st.session_state.agent = get_agent()

# =========================
# Session State
# =========================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# Sidebar
# =========================
st.sidebar.markdown('<div class="sidebar-header">📊 Session Stats</div>', unsafe_allow_html=True)
st.sidebar.metric("Messages", len(st.session_state.messages)//2)
st.sidebar.metric("Session", st.session_state.session_id.split('-')[0])

with st.sidebar.expander("Quick Actions"):
    if st.button("🔥 Weekly Plan"):
        st.session_state.messages.append({"role":"user","content":"Generate a weekly workout plan","ts":time.time()})
    if st.button("♻ Reset Session"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.experimental_rerun()

# =========================
# Header
# =========================
st.markdown("""
<h2 style="color:#FF6A00; font-weight:800;">🏋️‍♂️ AI Workout Coach</h2>
<p style="color:#BBBBBB;">Train smarter. Build consistency. Stay strong.</p>
""", unsafe_allow_html=True)

# =========================
# Chat Rendering
# =========================
exercise_visuals = {
    "push-ups": "https://i.imgur.com/Qr0VGZ7.gif",
    "squats": "https://i.imgur.com/0V7XKZd.gif",
    "plank": "https://i.imgur.com/9j2FqUE.gif",
    "bicep": "https://i.imgur.com/3fZsxv7.gif",
    "lunges": "https://i.imgur.com/D5hO6cD.gif",
}


def render_chat(messages):
    html = ["<div id='chatbox'>"]
    for m in messages:
        content = m["content"].replace("\n", "<br>")
        for key, img in exercise_visuals.items():
            if key in content.lower():
                content += f"<br><img class='exercise-img' src='{img}'/>"
        ts = time.strftime('%H:%M', time.localtime(m['ts']))
        if m["role"] == "user":
            html.append(f"<div style='display:flex;justify-content:flex-end;'><div class='msg-user'>{content}<div class='meta'>You • {ts}</div></div></div>")
        else:
            html.append(f"<div style='display:flex;justify-content:flex-start;'><div class='msg-assistant'>{content}<div class='meta'>Coach • {ts}</div></div></div>")
    html.append("</div>")
    return "\n".join(html)

chat_placeholder = st.empty()
chat_placeholder.markdown(render_chat(st.session_state.messages), unsafe_allow_html=True)

# =========================
# Input Form
# =========================
with st.form("chat_form", clear_on_submit=True):
    user_text = st.text_area("Your message", height=120, placeholder="E.g. Build muscle, 4 days/week...")
    send = st.form_submit_button("Send 💪")

if send and user_text.strip():
    st.session_state.messages.append({"role":"user","content":user_text.strip(),"ts":time.time()})
    st.session_state.messages.append({"role":"assistant","content":"Thinking...","ts":time.time()})

    chat_placeholder.markdown(render_chat(st.session_state.messages), unsafe_allow_html=True)

    response = agent_chat(user_text, st.session_state.agent, st.session_state.session_id)

    st.session_state.messages[-1]["content"] = response
    st.session_state.messages[-1]["ts"] = time.time()

    chat_placeholder.markdown(render_chat(st.session_state.messages), unsafe_allow_html=True)
    components.html("<script>var cb=document.getElementById('chatbox'); if(cb){cb.scrollTop=cb.scrollHeight;}</script>", height=0)
