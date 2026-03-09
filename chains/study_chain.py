"""
Study Chain - Connects Prompt Template with LLM, Memory, and Output Parser

LangChain Concepts Used:
1. LLMChain (or LCEL) - Chains prompt → LLM → parser
2. JsonOutputParser - Parses LLM output into Python dict
3. RunnableSequence - Modern way to chain components
4. ConversationBufferMemory - MongoDB-backed conversation memory

Two modes:
    - create_study_chain()          → Original chain (no memory, for quick tests)
    - create_study_chain_with_memory() → Memory-aware chain (uses MongoDB)
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.planner_prompt import study_planner_template, study_planner_memory_template
from llm.gemini_llm import get_gemini_llm
from memory.chat_memory import get_memory, get_chat_history
from memory.plan_store import save_study_plan
from memory.progress_store import initialize_progress


# ============================================================
# Original chain (no memory) — still works for quick tests (have still kept it for comparison)
# ============================================================
def create_study_chain():
    """
    Creates a simple chain WITHOUT memory.
    Good for quick tests where you don't need conversation history.
    
    Flow: prompt → LLM → JSON parser
    """
    llm = get_gemini_llm()
    json_parser = JsonOutputParser()
    chain = study_planner_template | llm | json_parser
    return chain


def generate_study_plan(goal: str, skills: str, time: str) -> dict:
    """
    Generates a study plan WITHOUT memory (original behavior).
    """
    chain = create_study_chain()
    result = chain.invoke({
        "goal": goal,
        "skills": skills,
        "time": time
    })
    return result


# ============================================================
# Memory-aware chain — uses MongoDB for conversation history
# ============================================================
def create_study_chain_with_memory():
    """
    Creates a chain WITH memory support.
    
    Flow: prompt (with chat_history) → LLM → JSON parser
    
    Note: Memory is NOT embedded in the chain itself.
    Instead, we manually load/save memory in generate_study_plan_with_memory().
    This gives us more control over what gets saved.
    
    Why manual instead of automatic?
        - We need to parse JSON AFTER getting the LLM response
        - We want to save the plan to study_plans collection too
        - Automatic memory would save raw text, but we want structured data
    """
    llm = get_gemini_llm()
    json_parser = JsonOutputParser()
    
    # Same LCEL pipe, but using the memory-aware template
    chain = study_planner_memory_template | llm | json_parser
    return chain


def generate_study_plan_with_memory(
    goal: str,
    skills: str,
    time: str,
    session_id: str,
    user_id: str = "default_user"
) -> dict:
    """
    Generates a study plan WITH memory and saves it to MongoDB.
    
    This function does 4 things:
        1. LOAD past messages from MongoDB (via session_id)
        2. GENERATE a study plan (with past context in the prompt)
        3. SAVE the conversation (human + AI messages) to MongoDB
        4. SAVE the generated plan to study_plans collection
    
    Args:
        goal:       Learning goal ("Learn Python basics")
        skills:     Current skills ("No experience")
        time:       Available time ("2 hours a day")
        session_id: Conversation thread ID ("neha_session_1")
        user_id:    Who this belongs to ("neha")
    
    Returns:
        dict: The generated study plan
    
    Example:
        plan = generate_study_plan_with_memory(
            goal="Learn Python",
            skills="No experience",
            time="2 hours a day",
            session_id="neha_session_1",
            user_id="neha"
        )
    """
    # ---- Step 1: LOAD past messages from MongoDB ----
    memory = get_memory(session_id)
    memory_vars = memory.load_memory_variables({}) #stores the pas conversation recording ai and human msgs
    
    # Convert message objects to a readable string for the prompt
    # e.g., "Human: I want to learn Python\nAI: Here's your plan..."
    chat_history = memory_vars.get("chat_history", [])
    if chat_history:
        history_text = "\n".join(
            f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}"
            for msg in chat_history
        )
    else:
        history_text = "No previous conversation."
    
    # ---- Step 2: GENERATE study plan with context ----
    chain = create_study_chain_with_memory()
    
    result = chain.invoke({
        "chat_history": history_text,
        "goal": goal,
        "skills": skills,
        "time": time
    })
    
    # ---- Step 3: SAVE conversation to MongoDB ----
    # Save the human message (what the user asked for)
    chat_history_store = get_chat_history(session_id)
    chat_history_store.add_user_message(
        f"Goal: {goal}, Skills: {skills}, Time: {time}"
    )
    # Save the AI response (summary of what was generated)
    chat_history_store.add_ai_message(
        f"Generated a {result.get('total_weeks', '?')}-week study plan for: {goal}"
    )
    
    # ---- Step 4: INITIALIZE progress tracking on every day ----
    # Adds "completed": false to each day before saving
    initialize_progress(result)

    # ---- Step 5: SAVE the plan to study_plans collection ----
    plan_id = save_study_plan(
        user_id=user_id,
        session_id=session_id,
        goal=goal,
        skills=skills,
        time=time,
        plan=result
    )
    
    # Attach the plan_id to the result so the caller can reference it
    result["plan_id"] = plan_id
    
    return result
