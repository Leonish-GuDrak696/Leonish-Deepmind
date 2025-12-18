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
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import json
import os
import time
import signal
from contextlib import contextmanager
from datetime import datetime

load_dotenv()

# Validate API key
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in environment variables. Please add it to your .env file")

# =========================
# Persistent Storage Files
# =========================

MEMORY_FILE = "user_memory.json"
USER_PROFILES = "user_profiles.json"
USAGE_STATS = "usage_stats.json"

# =========================
# Timeout Context Manager
# =========================

class TimeoutError(Exception):
    pass

@contextmanager
def timeout(seconds: int):
    """Context manager for function timeout."""
    def handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# =========================
# Memory & Profile Management
# =========================

def load_memory() -> Dict[str, List[Tuple[str, str]]]:
    """Load conversation history from file."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {MEMORY_FILE}, starting fresh")
            return {}
    return {}


def save_memory(memory: Dict[str, List[Tuple[str, str]]]):
    """Save conversation history to file."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")


def load_user_profiles() -> Dict[str, Dict]:
    """Load user profiles (goals, experience, preferences, limitations)."""
    if os.path.exists(USER_PROFILES):
        try:
            with open(USER_PROFILES, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {USER_PROFILES}, starting fresh")
            return {}
    return {}


def save_user_profiles(profiles: Dict[str, Dict]):
    """Save user profiles to file."""
    try:
        with open(USER_PROFILES, "w") as f:
            json.dump(profiles, f, indent=2)
    except Exception as e:
        print(f"Error saving profiles: {e}")


def load_usage_stats() -> Dict[str, Dict]:
    """Load usage statistics for cost tracking."""
    if os.path.exists(USAGE_STATS):
        try:
            with open(USAGE_STATS, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_usage_stats(stats: Dict[str, Dict]):
    """Save usage statistics."""
    try:
        with open(USAGE_STATS, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving usage stats: {e}")


def update_usage_stats(session_id: str):
    """Track API usage per session."""
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


def extract_user_context(session_id: str, chat_history: List[Tuple[str, str]]) -> Dict:
    """
    Extract key user context from conversation history.
    This preserves important info even if conversation exceeds 50 messages.
    """
    profiles = load_user_profiles()
    
    if session_id not in profiles:
        profiles[session_id] = {
            "goals": [],
            "experience_level": "unknown",
            "equipment": [],
            "limitations": [],
            "preferences": [],
            "last_updated": datetime.now().isoformat()
        }
    
    profile = profiles[session_id]
    
    # Simple keyword extraction from recent messages
    recent_messages = chat_history[-10:] if len(chat_history) > 10 else chat_history
    all_text = " ".join([msg for role, msg in recent_messages if role == "human"]).lower()
    
    # Extract goals
    goal_keywords = {
        "muscle": "muscle gain",
        "strength": "strength",
        "lose weight": "fat loss",
        "fat loss": "fat loss",
        "endurance": "endurance",
        "cardio": "cardio"
    }
    for keyword, goal in goal_keywords.items():
        if keyword in all_text and goal not in profile["goals"]:
            profile["goals"].append(goal)
    
    # Extract experience level
    experience_keywords = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
        "new to": "beginner",
        "just started": "beginner"
    }
    for keyword, level in experience_keywords.items():
        if keyword in all_text:
            profile["experience_level"] = level
            break
    
    # Extract equipment
    equipment_keywords = ["dumbbells", "barbell", "kettlebell", "resistance bands", 
                         "gym", "home", "bodyweight", "machines"]
    for equipment in equipment_keywords:
        if equipment in all_text and equipment not in profile["equipment"]:
            profile["equipment"].append(equipment)
    
    # Extract limitations/injuries
    limitation_keywords = ["injury", "pain", "hurt", "sore", "bad knee", 
                          "back pain", "shoulder", "can't do"]
    for keyword in limitation_keywords:
        if keyword in all_text:
            # Extract the sentence containing the limitation
            for role, msg in recent_messages:
                if role == "human" and keyword in msg.lower():
                    if msg not in profile["limitations"]:
                        profile["limitations"].append(msg)
                        break
    
    profile["last_updated"] = datetime.now().isoformat()
    profiles[session_id] = profile
    save_user_profiles(profiles)
    
    return profile


user_memory = load_memory()
user_profiles = load_user_profiles()

# =========================
# Rate Limiting (Persistent)
# =========================

request_times = defaultdict(list)
RATE_LIMIT_FILE = "rate_limits.json"

def load_rate_limits() -> Dict:
    """Load persistent rate limits."""
    if os.path.exists(RATE_LIMIT_FILE):
        try:
            with open(RATE_LIMIT_FILE, "r") as f:
                data = json.load(f)
                # Convert timestamps back to floats
                return {k: [float(t) for t in v] for k, v in data.items()}
        except:
            return {}
    return {}

def save_rate_limits():
    """Save rate limits to disk."""
    try:
        with open(RATE_LIMIT_FILE, "w") as f:
            json.dump(request_times, f)
    except Exception as e:
        print(f"Error saving rate limits: {e}")

# Load existing rate limits on startup
request_times.update(load_rate_limits())

def check_rate_limit(session_id: str, max_requests: int = 20, window: int = 60) -> Tuple[bool, str]:
    """
    Prevent abuse by limiting requests per user.
    Returns (is_allowed, message)
    """
    now = time.time()
    request_times[session_id] = [t for t in request_times[session_id] if now - t < window]
    
    if len(request_times[session_id]) >= max_requests:
        wait_time = int(window - (now - request_times[session_id][0]))
        return False, f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
    
    request_times[session_id].append(now)
    save_rate_limits()
    return True, ""


# =========================
# Smart Tool Routing
# =========================

def should_use_exercises_tool(user_input: str) -> bool:
    """Check if user is asking for exercise suggestions."""
    keywords = ["exercise", "workout", "suggest", "recommend", "what should i do", 
                "chest day", "leg day", "back day", "arm", "shoulder"]
    return any(kw in user_input.lower() for kw in keywords)

def should_use_sets_reps_tool(user_input: str) -> bool:
    """Check if user is asking about training volume."""
    keywords = ["sets", "reps", "repetitions", "how many", "volume", 
                "intensity", "how much"]
    return any(kw in user_input.lower() for kw in keywords)

def should_use_feedback_tool(user_input: str) -> bool:
    """Check if user is giving feedback."""
    keywords = ["pain", "hurt", "sore", "too hard", "too easy", "difficult",
                "can't do", "injury", "feel", "struggled"]
    return any(kw in user_input.lower() for kw in keywords)


# =========================
# Tools (STRICTLY CONTROLLED)
# =========================

@tool
def suggest_exercises(muscle_group: str, equipment: str) -> str:
    """
    Suggest exercises ONLY when the user explicitly asks
    for exercises or workouts for a muscle group.
    """
    exercises = {
        "chest": ["Push-ups", "Bench Press", "Dumbbell Flyes", "Cable Crossovers", "Incline Press"],
        "back": ["Pull-ups", "Lat Pulldown", "Seated Rows", "Deadlifts", "T-Bar Rows"],
        "legs": ["Squats", "Lunges", "Leg Press", "Glute Bridges", "Romanian Deadlifts", "Leg Curls"],
        "shoulders": ["Overhead Press", "Lateral Raises", "Front Raises", "Face Pulls", "Arnold Press"],
        "arms": ["Bicep Curls", "Tricep Dips", "Hammer Curls", "Skull Crushers", "Cable Curls"],
        "core": ["Plank", "Bicycle Crunches", "Leg Raises", "Russian Twists", "Dead Bug"],
        "full body": ["Burpees", "Mountain Climbers", "Thrusters", "Clean and Press"]
    }

    chosen = exercises.get(muscle_group.lower(), ["Bodyweight exercises"])
    return f"Suggested {muscle_group} exercises using {equipment}: {', '.join(chosen)}"


@tool
def adjust_sets_reps(goal: str, experience_level: str) -> str:
    """
    Calculate sets and reps ONLY when the user asks
    about training volume, reps, or intensity.
    """
    mapping = {
        "muscle gain": {"beginner": "3x10-12", "intermediate": "4x8-10", "advanced": "5x6-8"},
        "strength": {"beginner": "3x5", "intermediate": "4x3-5", "advanced": "5x1-3"},
        "fat loss": {"beginner": "2-3x12-15", "intermediate": "3x12-15", "advanced": "4x15-20"},
        "endurance": {"beginner": "2x15-20", "intermediate": "3x15-20", "advanced": "4x20+"},
        "general fitness": {"beginner": "2-3x10-12", "intermediate": "3x10-12", "advanced": "4x8-12"},
    }

    sets_reps = mapping.get(goal.lower(), mapping["general fitness"]).get(
        experience_level.lower(), "3x10"
    )
    return f"For {goal} at {experience_level} level: {sets_reps} (sets x reps)"


@tool
def process_feedback(feedback: str) -> str:
    """
    Process feedback ONLY when the user gives
    progress updates, pain, or preferences.
    """
    return f"Feedback noted: {feedback}. I'll adjust recommendations accordingly."

# =========================
# Input Validation
# =========================

def is_valid_input(text: str) -> bool:
    """Check if input is meaningful text."""
    if not text or len(text.strip()) < 2:
        return False
    
    has_letters = any(c.isalpha() for c in text)
    has_content = len(text.strip()) >= 2
    
    return has_letters and has_content


def is_greeting(text: str) -> bool:
    """Check if input is a simple greeting."""
    greetings = {
        "hi", "hello", "hey", "hii", "hai", "yo",
        "good morning", "good afternoon", "good evening"
    }
    return text.strip().lower() in greetings


# =========================
# Context Window Management
# =========================

def prepare_chat_history(chat_history: List[Tuple[str, str]], max_messages: int = 20) -> List:
    """
    Prepare chat history with sliding window to manage context length.
    Keeps most recent messages + summarizes older ones.
    """
    if len(chat_history) <= max_messages:
        formatted_history = []
        for role, msg in chat_history:
            if role == "human":
                formatted_history.append(HumanMessage(content=msg))
            else:
                formatted_history.append(AIMessage(content=msg))
        return formatted_history
    
    # Keep recent messages
    recent = chat_history[-max_messages:]
    formatted_history = []
    
    # Add summary of older messages
    older_count = len(chat_history) - max_messages
    summary = f"[Earlier in conversation: {older_count} messages exchanged about workout planning]"
    formatted_history.append(AIMessage(content=summary))
    
    # Add recent messages
    for role, msg in recent:
        if role == "human":
            formatted_history.append(HumanMessage(content=msg))
        else:
            formatted_history.append(AIMessage(content=msg))
    
    return formatted_history


# =========================
# Agent Creation
# =========================

def create_agent() -> AgentExecutor:
    """Create the LangChain agent with tools."""
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.6,
        max_tokens=1500
    )

    tools = [
        suggest_exercises,
        adjust_sets_reps,
        process_feedback
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an AI personal trainer agent.

You have access to tools and MUST use them selectively.

TOOLS & RULES:

1. suggest_exercises:
   - Use ONLY if the user explicitly asks for exercises or workouts.

2. adjust_sets_reps:
   - Use ONLY if the user asks about reps, sets, intensity, or volume.

3. process_feedback:
   - Use ONLY when the user gives feedback, pain, difficulty, or preferences.

STRICT RULES:
- Do NOT use tools unless clearly required.
- Do NOT generate full workout plans unless explicitly asked.
- If input is unclear or incomplete, ask for clarification.
- For greetings or acknowledgements, respond in plain text warmly.
- Answer ONLY what is asked. Do not over-explain.
- Be motivational, supportive, and professional.
- If user mentions pain or injury, prioritize their safety and suggest consulting a professional.
"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
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
# Chat Handler (TOP-LEVEL INPUT GUARD)
# =========================

def chat(user_input: str, agent_executor: AgentExecutor, session_id: str, timeout_seconds: int = 30) -> str:
    """
    Main chat interface with validation, memory management, and timeout.
    
    Args:
        user_input: User's message
        agent_executor: The LangChain agent
        session_id: Unique session identifier
        timeout_seconds: Maximum time to wait for response
    
    Returns:
        Agent's response or error message
    """
    global user_memory

    # Rate limiting check
    is_allowed, message = check_rate_limit(session_id)
    if not is_allowed:
        return message

    # Validate input
    if not is_valid_input(user_input):
        return "Could you please provide a more detailed request?"

    # Handle simple greetings
    if is_greeting(user_input):
        return "Hello! I'm your AI personal trainer. How can I help you with your workout today? I can suggest exercises, create workout plans, adjust training volume, and track your progress!"

    # Update usage stats
    total_requests = update_usage_stats(session_id)
    
    # Load conversation history
    chat_history = user_memory.get(session_id, [])
    
    # Extract and update user profile context
    user_profile = extract_user_context(session_id, chat_history)
    
    # Add user profile context to input if relevant
    enhanced_input = user_input
    if user_profile.get("limitations"):
        enhanced_input = f"{user_input}\n[User has mentioned: {', '.join(user_profile['limitations'][:2])}]"

    # Prepare chat history with context window management
    formatted_history = prepare_chat_history(chat_history, max_messages=20)

    try:
        # Execute agent with timeout
        with timeout(timeout_seconds):
            response = agent_executor.invoke({
                "input": enhanced_input,
                "chat_history": formatted_history
            })

        output = response.get("output", "I'm not sure how to respond to that. Could you rephrase?")

        # Update memory (keep last 50 messages for raw history)
        chat_history.append(("human", user_input))
        chat_history.append(("assistant", output))
        user_memory[session_id] = chat_history[-50:]

        save_memory(user_memory)
        
        print(f"[{session_id[:8]}] Request #{total_requests} completed successfully")
        
        return output

    except TimeoutError as e:
        print(f"Timeout Error [{session_id}]: {str(e)}")
        return "I'm taking too long to process that. Could you try asking a simpler question or breaking it into parts?"
    
    except Exception as e:
        # Log error internally but give user-friendly message
        print(f"Agent Error [{session_id}]: {str(e)}")
        return "I'm having trouble processing that request. Could you rephrase it or try asking something else?"


# =========================
# Run Example
# =========================

if __name__ == "__main__":
    agent_executor = create_agent()
    session_id = "user_001"

    print("=== Testing Greeting ===")
    print(chat("Hi", agent_executor, session_id))
    
    print("\n=== Testing Invalid Input ===")
    print(chat("Bu", agent_executor, session_id))
    
    print("\n=== Testing Valid Request ===")
    print(chat("I want a chest workout", agent_executor, session_id))
    
    print("\n=== Testing Sets/Reps Query ===")
    print(chat("What sets and reps for muscle gain as a beginner?", agent_executor, session_id))
    
    print("\n=== Testing Context Extraction ===")
    print(chat("I'm a beginner with dumbbells at home, bad knee", agent_executor, session_id))
    profiles = load_user_profiles()
    print(f"Extracted Profile: {json.dumps(profiles.get(session_id, {}), indent=2)}")
    
    print("\n=== Testing Rate Limit ===")
    for i in range(22):
        result = chat(f"test {i}", agent_executor, session_id)
        if "Rate limit" in result:
            print(f"Rate limit triggered at request {i+1}")
            break
