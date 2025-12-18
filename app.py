"""
Streamlit Workout AI — PRODUCTION READY
Premium Dark Gym Theme with Enhanced UX
Features:
- Advanced AI Workout Agent (agent.py)
- Persistent chat across refreshes
- XSS protection with HTML escaping
- Beautiful animations and transitions
- Mobile-optimized responsive design
- Exercise visuals with fallbacks
- Quick action buttons with suggestions
- Progress tracking and stats
"""

import streamlit as st
import uuid
import time
import html
import re
from datetime import datetime
from agent import create_agent, chat as agent_chat, load_user_profiles

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
# ENHANCED DARK GYM THEME CSS
# =========================
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* Global Styles */
html, body, [class*="css"] {
    background: linear-gradient(135deg, #0E0E10 0%, #1a1a1d 100%);
    color: #EAEAEA;
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main Container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Chat Container */
#chatbox {
    border-radius: 20px;
    padding: 24px;
    background: rgba(26,26,29,0.95);
    backdrop-filter: blur(16px);
    min-height: 60vh;
    max-height: 65vh;
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(255,106,0,0.15), 0 0 60px rgba(255,106,0,0.08);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 24px;
    scroll-behavior: smooth;
}

/* Custom Scrollbar */
#chatbox::-webkit-scrollbar {
    width: 8px;
}

#chatbox::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}

#chatbox::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #FF6A00, #FF3C00);
    border-radius: 10px;
}

#chatbox::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #FF7A10, #FF4C10);
}

/* Messages */
.msg-user {
    margin-left: auto;
    margin-bottom: 16px;
    padding: 16px 20px;
    border-radius: 18px 18px 4px 18px;
    background: linear-gradient(135deg, #2A2A2E 0%, #35353a 100%);
    max-width: 75%;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255,255,255,0.05);
}

.msg-assistant {
    margin-right: auto;
    margin-bottom: 16px;
    padding: 18px 22px;
    border-radius: 18px 18px 18px 4px;
    background: linear-gradient(135deg, #FF6A00 0%, #FF3C00 100%);
    max-width: 75%;
    box-shadow: 0 8px 24px rgba(255,106,0,0.4);
    animation: slideInLeft 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255,255,255,0.1);
}

.msg-thinking {
    margin-right: auto;
    margin-bottom: 16px;
    padding: 18px 22px;
    border-radius: 18px 18px 18px 4px;
    background: rgba(255,106,0,0.15);
    border: 2px dashed rgba(255,106,0,0.4);
    max-width: 75%;
    animation: pulse 1.5s ease-in-out infinite;
}

/* Animations */
@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 0.5;
        transform: scale(0.98);
    }
    50% {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Message Meta Info */
.meta {
    font-size: 11px;
    opacity: 0.7;
    margin-top: 8px;
    font-weight: 500;
}

/* Welcome Card */
.welcome-card {
    background: linear-gradient(135deg, rgba(255,106,0,0.08) 0%, rgba(255,60,0,0.12) 100%);
    border: 2px solid rgba(255,106,0,0.25);
    border-radius: 20px;
    padding: 32px;
    margin: 20px 0;
    text-align: center;
    animation: fadeIn 0.5s ease;
}

.welcome-card h3 {
    color: #FF6A00;
    margin-bottom: 16px;
    font-size: 24px;
    font-weight: 800;
}

.welcome-card p {
    color: #BBBBBB;
    line-height: 1.6;
    margin: 12px 0;
}

/* Quick Prompts */
.quick-prompts-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 20px;
}

.quick-prompt {
    display: inline-block;
    background: rgba(255,106,0,0.12);
    border: 1px solid rgba(255,106,0,0.35);
    padding: 10px 18px;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 14px;
    font-weight: 600;
    color: #FF8C42;
}

.quick-prompt:hover {
    background: rgba(255,106,0,0.25);
    border-color: rgba(255,106,0,0.6);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255,106,0,0.3);
    color: #FFB584;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #121214 0%, #0E0E10 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

.sidebar-header {
    font-size: 20px;
    font-weight: 800;
    color: #FF6A00;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,106,0,0.08);
    padding: 12px;
    border-radius: 12px;
    border: 1px solid rgba(255,106,0,0.2);
}

[data-testid="stMetricLabel"] {
    color: #BBBBBB !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #FF6A00 !important;
    font-weight: 800;
}

/* Buttons */
button[kind="primary"], button[kind="secondary"] {
    background: linear-gradient(135deg, #FF6A00 0%, #FF3C00 100%) !important;
    color: white !important;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 700 !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(255,106,0,0.3) !important;
}

button[kind="primary"]:hover, button[kind="secondary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(255,106,0,0.5) !important;
}

button[kind="primary"]:disabled, button[kind="secondary"]:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
}

/* Text Area */
textarea {
    background: rgba(26,26,29,0.8) !important;
    color: #EAEAEA !important;
    border-radius: 16px !important;
    border: 2px solid rgba(255,106,0,0.25) !important;
    padding: 16px !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
}

textarea:focus {
    border-color: rgba(255,106,0,0.6) !important;
    box-shadow: 0 0 20px rgba(255,106,0,0.2) !important;
}

/* Exercise Images */
.exercise-img {
    max-width: 100%;
    max-height: 280px;
    border-radius: 16px;
    margin-top: 12px;
    object-fit: cover;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    border: 2px solid rgba(255,255,255,0.1);
}

.exercise-img-error {
    background: rgba(255,59,48,0.1);
    border: 2px dashed rgba(255,59,48,0.3);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: #FF6B6B;
    margin-top: 12px;
}

/* Error Messages */
.error-message {
    background: rgba(255,59,48,0.12);
    border: 1px solid rgba(255,59,48,0.4);
    padding: 16px;
    border-radius: 14px;
    margin: 12px 0;
    color: #FF6B6B;
    font-weight: 600;
    animation: fadeIn 0.3s ease;
}

/* Success Messages */
.success-message {
    background: rgba(52,199,89,0.12);
    border: 1px solid rgba(52,199,89,0.4);
    padding: 16px;
    border-radius: 14px;
    margin: 12px 0;
    color: #34C759;
    font-weight: 600;
}

/* Info Badges */
.info-badge {
    display: inline-block;
    background: rgba(100,210,255,0.15);
    border: 1px solid rgba(100,210,255,0.3);
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    color: #64D2FF;
    margin: 4px;
}

/* Header */
.app-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: rgba(255,106,0,0.05);
    border-radius: 20px;
    border: 1px solid rgba(255,106,0,0.15);
}

.app-header h1 {
    color: #FF6A00;
    font-weight: 900;
    font-size: 42px;
    margin-bottom: 8px;
    text-shadow: 0 0 30px rgba(255,106,0,0.3);
}

.app-header p {
    color: #BBBBBB;
    font-size: 16px;
    margin-top: 8px;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    #chatbox {
        max-height: 50vh;
        padding: 16px;
    }
    
    .msg-user, .msg-assistant {
        max-width: 85%;
        padding: 14px 16px;
    }
    
    .app-header h1 {
        font-size: 32px;
    }
    
    .quick-prompt {
        font-size: 12px;
        padding: 8px 14px;
    }
}

/* Loading Spinner */
.spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,106,0,0.3);
    border-radius: 50%;
    border-top-color: #FF6A00;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

# =========================
# Session State Initialization
# =========================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    # Try to load from persistent storage
    try:
        from agent import load_memory
        saved_memory = load_memory()
        if st.session_state.session_id in saved_memory:
            # Convert to Streamlit message format
            st.session_state.messages = []
            for role, content in saved_memory[st.session_state.session_id]:
                st.session_state.messages.append({
                    "role": role if role == "user" else "assistant",
                    "content": content,
                    "ts": time.time()
                })
        else:
            st.session_state.messages = []
    except:
        st.session_state.messages = []

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "agent" not in st.session_state:
    st.session_state.agent = None

if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = len(st.session_state.messages) == 0

# =========================
# Agent Initialization
# =========================

@st.cache_resource(show_spinner=False)
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return create_agent()
    except Exception as e:
        st.error(f"❌ Failed to initialize AI agent: {str(e)}")
        return None

if st.session_state.agent is None:
    with st.spinner("🔥 Initializing AI Coach..."):
        st.session_state.agent = get_agent()

# =========================
# Helper Functions
# =========================

def generate_session_name(session_id: str) -> str:
    """Generate a friendly session name."""
    return f"#{session_id[:8].upper()}"


def sanitize_html(text: str) -> str:
    """Sanitize user input to prevent XSS attacks."""
    return html.escape(text)


def fuzzy_match_exercise(content: str) -> list:
    """Find exercise keywords with fuzzy matching."""
    exercise_keywords = {
        "push": "push-ups",
        "squat": "squats",
        "plank": "plank",
        "bicep": "bicep",
        "curl": "bicep",
        "lunge": "lunges",
        "chest": "push-ups",
        "deadlift": "squats",
        "pull": "pull-ups",
    }
    
    content_lower = content.lower()
    matched = []
    
    for keyword, exercise in exercise_keywords.items():
        if keyword in content_lower:
            matched.append(exercise)
    
    return list(set(matched))


def get_exercise_visual(exercise: str) -> str:
    """Get visual URL for exercise."""
    exercise_visuals = {
        "push-ups": "https://i.imgur.com/Qr0VGZ7.gif",
        "squats": "https://i.imgur.com/0V7XKZd.gif",
        "plank": "https://i.imgur.com/9j2FqUE.gif",
        "bicep": "https://i.imgur.com/3fZsxv7.gif",
        "lunges": "https://i.imgur.com/D5hO6cD.gif",
    }
    return exercise_visuals.get(exercise, "")


def render_welcome_card():
    """Render the welcome card with quick prompts."""
    return """
    <div class='welcome-card'>
        <h3>💪 Welcome to Your AI Workout Coach!</h3>
        <p>I'm here to help you achieve your fitness goals with personalized workout plans and expert guidance.</p>
        <p style='margin-top: 20px;'><strong>I can help you with:</strong></p>
        <div class='quick-prompts-container'>
            <span class='quick-prompt'>🏋️ Custom Workout Plans</span>
            <span class='quick-prompt'>💪 Exercise Recommendations</span>
            <span class='quick-prompt'>📊 Training Volume Advice</span>
            <span class='quick-prompt'>🎯 Goal Setting & Tracking</span>
            <span class='quick-prompt'>🔄 Progress Adjustments</span>
            <span class='quick-prompt'>🩹 Injury Modifications</span>
        </div>
        <p style='margin-top: 24px; color: #FF8C42; font-size: 15px; font-weight: 600;'>
            👇 Start by telling me your fitness goals or try a quick action below!
        </p>
    </div>
    """


def render_chat(messages):
    """Render chat messages with visuals and XSS protection."""
    if not messages:
        return render_welcome_card()
    
    html_parts = ["<div id='chatbox'>"]
    
    for m in messages:
        # Sanitize content to prevent XSS
        content = sanitize_html(m["content"])
        content = content.replace("\n", "<br>")
        
        # Add exercise visuals with error handling
        matched_exercises = fuzzy_match_exercise(m["content"])
        for exercise in matched_exercises:
            visual_url = get_exercise_visual(exercise)
            if visual_url:
                content += f"<br><img class='exercise-img' src='{visual_url}' alt='{exercise}' onerror='this.style.display=\"none\"'/>"
        
        ts = time.strftime('%H:%M', time.localtime(m.get('ts', time.time())))
        
        if m["role"] == "user":
            html_parts.append(
                f"<div style='display:flex;justify-content:flex-end;'>"
                f"<div class='msg-user'>{content}<div class='meta'>You • {ts}</div></div>"
                f"</div>"
            )
        elif m.get("thinking", False):
            html_parts.append(
                f"<div style='display:flex;justify-content:flex-start;'>"
                f"<div class='msg-thinking'>"
                f"<div class='spinner'></div> {content}"
                f"<div class='meta'>Coach • {ts}</div>"
                f"</div></div>"
            )
        else:
            html_parts.append(
                f"<div style='display:flex;justify-content:flex-start;'>"
                f"<div class='msg-assistant'>{content}<div class='meta'>Coach • {ts}</div></div>"
                f"</div>"
            )
    
    html_parts.append("</div>")
    
    # Auto-scroll JavaScript
    html_parts.append("""
    <script>
        setTimeout(function() {
            var chatbox = document.getElementById('chatbox');
            if (chatbox) {
                chatbox.scrollTop = chatbox.scrollHeight;
            }
        }, 150);
    </script>
    """)
    
    return "\n".join(html_parts)


def process_user_message(user_text: str):
    """Process user message and get agent response."""
    if st.session_state.agent is None:
        st.error("❌ AI Coach is not initialized. Please refresh the page.")
        return False
    
    try:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_text.strip(),
            "ts": time.time()
        })
        
        # Hide welcome card
        st.session_state.show_welcome = False
        
        # Add thinking placeholder
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Analyzing your request...",
            "ts": time.time(),
            "thinking": True
        })
        
        st.session_state.is_processing = True
        
        # Get agent response with timeout handling
        response = agent_chat(
            user_text,
            st.session_state.agent,
            st.session_state.session_id,
            timeout_seconds=30
        )
        
        # Update with actual response
        st.session_state.messages[-1] = {
            "role": "assistant",
            "content": response,
            "ts": time.time(),
            "thinking": False
        }
        
        st.session_state.is_processing = False
        return True
        
    except Exception as e:
        # Remove thinking message
        if st.session_state.messages and st.session_state.messages[-1].get("thinking"):
            st.session_state.messages.pop()
        
        # Add error message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ I encountered an error processing your request. Please try again or rephrase your question.",
            "ts": time.time()
        })
        
        st.session_state.is_processing = False
        print(f"❌ Agent Error: {str(e)}")
        return False


def get_user_stats(session_id: str) -> dict:
    """Get user statistics from profile."""
    try:
        profiles = load_user_profiles()
        if session_id in profiles:
            profile = profiles[session_id]
            return {
                "goals": len(profile.get("goals", [])),
                "equipment": len(profile.get("equipment", [])),
                "experience": profile.get("experience_level", "unknown").title()
            }
    except:
        pass
    return {"goals": 0, "equipment": 0, "experience": "Unknown"}

# =========================
# Header
# =========================

st.markdown("""
<div class='app-header'>
    <h1>🏋️‍♂️ AI WORKOUT COACH</h1>
    <p>Train Smarter • Build Consistency • Stay Strong</p>
</div>
""", unsafe_allow_html=True)

# =========================
# Sidebar
# =========================

with st.sidebar:
    st.markdown('<div class="sidebar-header">📊 YOUR STATS</div>', unsafe_allow_html=True)
    
    # Session stats
    message_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💬 Messages", message_count)
    with col2:
        st.metric("🆔 Session", generate_session_name(st.session_state.session_id))
    
    # User profile stats
    user_stats = get_user_stats(st.session_state.session_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Goals", user_stats["goals"])
    with col2:
        st.metric("🏋️ Equipment", user_stats["equipment"])
    with col3:
        st.metric("📈 Level", user_stats["experience"][:3])
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown('<div class="sidebar-header">⚡ QUICK ACTIONS</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Weekly Plan", use_container_width=True, disabled=st.session_state.is_processing, key="weekly_plan"):
            process_user_message("Create a comprehensive weekly workout plan for me based on my goals and experience level")
            st.rerun()
    
    with col2:
        if st.button("🔥 Quick Workout", use_container_width=True, disabled=st.session_state.is_processing, key="quick_workout"):
            process_user_message("Give me a quick 30-minute full body workout I can do right now")
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💪 Muscle Gain", use_container_width=True, disabled=st.session_state.is_processing, key="muscle_gain"):
            process_user_message("I want to build muscle. What's the best approach for sets, reps, and exercises?")
            st.rerun()
    
    with col2:
        if st.button("♻️ Reset Chat", use_container_width=True, key="reset_chat"):
            st.session_state.messages = []
            st.session_state.show_welcome = True
            st.session_state.is_processing = False
            st.rerun()
    
    st.markdown("---")
    
    # Example Prompts
    with st.expander("💡 EXAMPLE PROMPTS", expanded=False):
        st.markdown("""
        **Getting Started:**
        - "I'm a beginner, where should I start?"
        - "Create a 4-day workout split for muscle gain"
        
        **Specific Requests:**
        - "Suggest chest exercises with dumbbells"
        - "How many sets and reps for strength?"
        - "I have a bad knee, what exercises are safe?"
        
        **Progress Tracking:**
        - "I'm finding squats too easy now"
        - "My shoulder hurts after overhead press"
        - "I want to increase intensity"
        """)
    
    # Tips
    with st.expander("✨ PRO TIPS", expanded=False):
        st.markdown("""
        - 🎯 **Be specific** about your goals and limitations
        - 📊 **Mention** available equipment
        - ⏱️ **Include** time constraints if any
        - 💬 **Ask follow-up** questions for clarification
        - 🔄 **Update me** on your progress regularly
        """)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; padding: 20px; opacity: 0.6;'>
        <p style='font-size: 12px;'>💪 Powered by Advanced AI</p>
        <p style='font-size: 11px;'>Stay Consistent, Stay Strong</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# Main Chat Area
# =========================

# Show processing indicator at top
if st.session_state.is_processing:
    st.info("⏳ Processing your request... This may take a few moments.", icon="⏳")

# Render chat
chat_placeholder = st.empty()
chat_placeholder.markdown(render_chat(st.session_state.messages), unsafe_allow_html=True)

# =========================
# Input Form
# =========================

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_text = st.text_area(
            "💬 Your Message",
            height=100,
            placeholder="E.g., 'I want to build muscle with 4 workouts per week' or 'Suggest chest exercises with dumbbells'",
            disabled=st.session_state.is_processing,
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        send = st.form_submit_button(
            "Send 💪",
            use_container_width=True,
            disabled=st.session_state.is_processing or not user_text.strip()
        )

# Handle form submission
if send and user_text.strip():
    success = process_user_message(user_text)
    if success:
        chat_placeholder.markdown(render_chat(st.session_state.messages), unsafe_allow_html=True)
        st.rerun()

# =========================
# Footer Info
# =========================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='text-align: center;'>
        <p style='color: #FF6A00; font-weight: 700; font-size: 18px;'>🎯</p>
        <p style='font-size: 12px; color: #999;'>Personalized Plans</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='text-align: center;'>
        <p style='color: #FF6A00; font-weight: 700; font-size: 18px;'>🤖</p>
        <p style='font-size: 12px; color: #999;'>AI-Powered Coaching</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='text-align: center;'>
        <p style='color: #FF6A00; font-weight: 700; font-size: 18px;'>📈</p>
        <p style='font-size: 12px; color: #999;'>Progress Tracking</p>
    </div>
    """, unsafe_allow_html=True)
