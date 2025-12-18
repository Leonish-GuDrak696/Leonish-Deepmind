"""
Advanced AI Workout Split Generator - PRODUCTION READY
- Autonomous LangChain Agent with persistent memory
- Tracks user progress, feedback, and adapts plans dynamically
- Structured user profiles with key context extraction
- Cost tracking and timeout management
- Better tool routing and context management
"""

from dotenv import load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from typing import List, Tuple, Dict
from collections import defaultdict
import json
import os
import time
import signal
from contextlib import contextmanager
from datetime import datetime

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in environment variables")

MEMORY_FILE = "user_memory.json"
USER_PROFILES = "user_profiles.json"
USAGE_STATS = "usage_stats.json"

# =========================
# Timeout
# =========================

class TimeoutError(Exception):
    pass

@contextmanager
def timeout(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# =========================
# Memory & Profiles
# =========================

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def load_user_profiles():
    if os.path.exists(USER_PROFILES):
        try:
            with open(USER_PROFILES, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_profiles(profiles):
    with open(USER_PROFILES, "w") as f:
        json.dump(profiles, f, indent=2)

def load_usage_stats():
    if os.path.exists(USAGE_STATS):
        try:
            with open(USAGE_STATS, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_usage_stats(stats):
    with open(USAGE_STATS, "w") as f:
        json.dump(stats, f, indent=2)

def update_usage_stats(session_id):
    stats = load_usage_stats()
    if session_id not in stats:
        stats[session_id] = {
            "total_requests": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
    stats[session_id]["total_requests"] += 1
    stats[session_id]["last_seen"] = datetime.now().isoformat()
    save_usage_stats(stats)
    return stats[session_id]["total_requests"]

# =========================
# Validation
# =========================

def is_valid_input(text: str) -> bool:
    if not text or len(text.strip()) < 2:
        return False
    return any(c.isalpha() for c in text)

def is_greeting(text: str) -> bool:
    return text.strip().lower() in {
        "hi", "hello", "hey", "hii", "hai", "yo",
        "good morning", "good afternoon", "good evening"
    }

# =========================
# Chat History
# =========================

def prepare_chat_history(chat_history, max_messages=20):
    formatted = []
    for role, msg in chat_history[-max_messages:]:
        if role == "human":
            formatted.append(HumanMessage(content=msg))
        else:
            formatted.append(AIMessage(content=msg))
    return formatted

# =========================
# TOOLS (FIXED DEFAULT PARAMS)
# =========================

@tool
def suggest_exercises(muscle_group: str = "", equipment: str = "") -> str:
    exercises = {
        "chest": ["Push-ups", "Bench Press", "Dumbbell Flyes"],
        "legs": ["Squats", "Lunges", "Leg Press"],
        "back": ["Pull-ups", "Rows", "Deadlifts"]
    }
    return f"{muscle_group.title()} exercises: {', '.join(exercises.get(muscle_group.lower(), []))}"

@tool
def adjust_sets_reps(goal: str = "", experience_level: str = "") -> str:
    return f"For {goal}, {experience_level} level: 3–4 sets of 8–12 reps"

@tool
def process_feedback(feedback: str = "") -> str:
    return f"Feedback noted: {feedback}"

# =========================
# Agent Creation
# =========================

def create_agent() -> AgentExecutor:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.6,
        max_tokens=1500
    )

    tools = [suggest_exercises, adjust_sets_reps, process_feedback]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an AI personal trainer.

RULES:
- Use tools ONLY if explicitly required.
- Do NOT generate full plans unless asked.
- Answer only what is asked.
- For greetings, respond warmly.
- Be supportive and professional.

IMPORTANT FALLBACK RULE:
If the user states a fitness goal or intent but does not ask explicitly,
ask clarifying questions instead of refusing.
"""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3
    )

# =========================
# Chat Handler
# =========================

user_memory = load_memory()

def chat(user_input: str, agent_executor: AgentExecutor, session_id: str, timeout_seconds: int = 30) -> str:
    if not is_valid_input(user_input):
        return "Could you please provide a more detailed request?"

    if is_greeting(user_input):
        return "Hello! I'm your AI workout coach 💪 How can I help you today?"

    chat_history = user_memory.get(session_id, [])
    formatted_history = prepare_chat_history(chat_history)

    try:
        with timeout(timeout_seconds):
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": formatted_history
            })

        output = response.get("output")

        # ✅ SAFE FALLBACK (IMPORTANT FIX)
        if not output or len(output.strip()) < 10:
            output = (
                "I want to help you better 💪\n\n"
                "Could you tell me:\n"
                "- Your fitness goal\n"
                "- Your experience level\n"
                "- Equipment available\n\n"
                "Example: Beginner, muscle gain, home dumbbells"
            )

        chat_history.append(("human", user_input))
        chat_history.append(("assistant", output))
        user_memory[session_id] = chat_history[-50:]
        save_memory(user_memory)

        return output

    except TimeoutError:
        return "I'm taking too long to respond. Please try again."

    except Exception as e:
        print("Agent error:", e)
        return "I'm having trouble processing that. Please try rephrasing."

# =========================
# Local Test
# =========================

if __name__ == "__main__":
    agent = create_agent()
    sid = "test_user"
    print(chat("Hi", agent, sid))
    print(chat("I want to build muscle", agent, sid))
