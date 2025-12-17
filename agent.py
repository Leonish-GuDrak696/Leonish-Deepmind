"""
Advanced AI Workout Split Generator
- Autonomous LangChain Agent with persistent memory
- Tracks user progress, feedback, and adapts plans dynamically
- Motivational and professional persona
"""

from dotenv import load_dotenv
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from typing import List, Tuple, Dict
import json
import os

load_dotenv()

# =========================
# Persistent Memory Storage
# =========================

MEMORY_FILE = "user_memory.json"


def load_memory() -> Dict[str, List[Tuple[str, str]]]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_memory(memory: Dict[str, List[Tuple[str, str]]]):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


user_memory = load_memory()

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
        "chest": ["Push-ups", "Bench Press", "Dumbbell Flyes"],
        "back": ["Pull-ups", "Lat Pulldown", "Seated Rows"],
        "legs": ["Squats", "Lunges", "Leg Press", "Glute Bridges"],
        "shoulders": ["Overhead Press", "Lateral Raises"],
        "arms": ["Bicep Curls", "Tricep Dips", "Hammer Curls"],
        "core": ["Plank", "Bicycle Crunches", "Leg Raises"]
    }

    chosen = exercises.get(muscle_group.lower(), ["Bodyweight exercise"])
    return f"Suggested {muscle_group} exercises using {equipment}: {', '.join(chosen)}"


@tool
def adjust_sets_reps(goal: str, experience_level: str) -> str:
    """
    Calculate sets and reps ONLY when the user asks
    about training volume, reps, or intensity.
    """
    mapping = {
        "muscle gain": {"beginner": "3x10", "intermediate": "4x10", "advanced": "5x8"},
        "strength": {"beginner": "3x5", "intermediate": "4x5", "advanced": "5x3"},
        "fat loss": {"beginner": "2x12", "intermediate": "3x12", "advanced": "4x15"},
        "general fitness": {"beginner": "2x10", "intermediate": "3x10", "advanced": "4x10"},
    }

    return mapping.get(goal.lower(), mapping["general fitness"]).get(
        experience_level.lower(), "3x10"
    )


@tool
def process_feedback(feedback: str) -> str:
    """
    Process feedback ONLY when the user gives
    progress updates, pain, or preferences.
    """
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
- For greetings or acknowledgements, respond in plain text.
- Answer ONLY what is asked. Do not over-explain.
"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)


    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3
    )

# =========================
# Chat Handler (TOPPER-LEVEL INPUT GUARD)
# =========================

def chat(user_input: str, agent_executor: AgentExecutor, session_id: str) -> str:
    global user_memory

    clean_input = user_input.strip().lower()

    greetings = {
        "hi", "hello", "hey", "hii", "hai",
        "ok", "okay", "yo", "yes", "no"
    }

    if not clean_input:
        return "Could you please clarify your request?"

    if not any(char.isalpha() for char in clean_input):
        return "Could you please clarify your request?"

    if len(clean_input) < 3 and clean_input not in greetings:
        return "Could you please clarify your request?"

    chat_history = user_memory.get(session_id, [])

    formatted_history = []
    for role, msg in chat_history:
        if role == "human":
            formatted_history.append(HumanMessage(content=msg))
        else:
            formatted_history.append(AIMessage(content=msg))

    try:
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": formatted_history
        })

        output = response.get("output", "")

        chat_history.append(("human", user_input))
        chat_history.append(("assistant", output))
        user_memory[session_id] = chat_history[-50:]

        save_memory(user_memory)
        return output

    except Exception as e:
        return f"I encountered an error: {str(e)}"


# =========================
# Run Example
# =========================

if __name__ == "__main__":
    agent_executor = create_agent()
    session_id = "user_001"

    print(chat("Hi", agent_executor, session_id))
    print(chat("Bu", agent_executor, session_id))

