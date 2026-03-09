"""
Study Agent — AI Agent that reasons, uses tools, and makes decisions

What is an Agent?
    An Agent is an LLM with a REASONING LOOP. Instead of just generating text,
    it can:
        1. THINK about what to do
        2. PICK a tool to use
        3. Call the tool and READ the result
        4. THINK again — does it need more info?
        5. Repeat until it has a final answer

    This is called the ReAct pattern (Reason + Act).

How it works here:
    - We use langgraph's create_react_agent() to build the agent
    - The agent gets 3 tools: search_web, get_user_plans, get_progress
    - It has a system prompt explaining who it is
    - It uses the same Gemini LLM we already have
    - Chat history is passed in so the agent remembers past messages

Example conversation:
    User: "Find me the best React tutorials"
    Agent thinks: I should search the web for this.
    Agent calls: search_web("best React tutorials 2026")
    Agent reads the results
    Agent responds: "Here are the top React tutorials I found: ..."
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from llm.gemini_llm import get_gemini_llm
from agent.tools import get_all_tools
from memory.chat_memory import get_chat_history


# ============================================================
# System prompt for the agent
# ============================================================
AGENT_SYSTEM_PROMPT = """You are an AI Study Planner Assistant. You help users plan their learning journey.

You have access to these tools:
- search_web: Search the internet for study resources, tutorials, and courses
- get_user_plans_tool: Look up a user's saved study plans from the database
- get_progress_tool: Check how much of a user's study plan they've completed

Guidelines:
- Be helpful, encouraging, and concise
- When the user asks for resources, use search_web to find current ones
- When the user asks about their plans, use get_user_plans_tool
- When the user asks about their progress, use get_progress_tool
- Always pass the user_id when calling get_user_plans_tool or get_progress_tool
- If you're not sure which tool to use, just answer with your knowledge
- Keep responses focused and actionable
- The current user's user_id is: {user_id}
"""


# ============================================================
# Create the agent
# ============================================================
def create_study_agent(user_id: str):
    """
    Creates a ReAct agent with tools and a system prompt.

    Args:
        user_id: The current user's ID (passed to tools that query MongoDB)

    Returns:
        A compiled langgraph agent ready to invoke
    """
    llm = get_gemini_llm()
    tools = get_all_tools()

    # Build system prompt with user_id injected
    system_prompt = AGENT_SYSTEM_PROMPT.format(user_id=user_id)

    # create_react_agent builds a ReAct loop:
    #   User message → LLM thinks → calls tool (maybe) → thinks again → responds
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent


# ============================================================
# Chat with the agent (single turn)
# ============================================================
def chat_with_agent(
    agent,
    user_message: str,
    session_id: str,
) -> str:
    """
    Sends a message to the agent and returns the response.
    Also saves the conversation to MongoDB for persistence.

    Args:
        agent:        The compiled langgraph agent
        user_message: What the user typed
        session_id:   For saving chat history to MongoDB

    Returns:
        str: The agent's text response
    """
    # Load past messages from MongoDB
    chat_history_store = get_chat_history(session_id)
    past_messages = chat_history_store.messages

    # Build the message list: past history + new user message
    messages = list(past_messages) + [HumanMessage(content=user_message)]

    # Invoke the agent — it will reason + use tools as needed
    result = agent.invoke({"messages": messages})

    # Extract the final AI response from the result
    # The agent returns a list of messages; the last one is the AI's answer
    ai_messages = result.get("messages", [])
    if ai_messages:
        final_message = ai_messages[-1]
        response_text = final_message.content
    else:
        response_text = "I couldn't generate a response. Please try again."

    # Save to MongoDB for memory persistence
    chat_history_store.add_user_message(user_message)
    chat_history_store.add_ai_message(response_text)

    return response_text
