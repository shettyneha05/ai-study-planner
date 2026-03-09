"""
Chat Memory - MongoDB-backed conversation memory for the AI Study Planner

This module provides long-term memory for conversations using MongoDB.

How it works:
    1. MongoDBChatMessageHistory → saves/loads messages to/from MongoDB
    2. ConversationBufferMemory  → wraps it so LangChain chains can use it
    3. session_id                → groups messages by conversation or seperates user

Flow:
    User says something
        → message saved to MongoDB (chat_history collection)
    LLM responds
        → response saved to MongoDB (chat_history collection)
    Next time user talks (same session_id)
        → past messages loaded from MongoDB
        → injected into prompt as context
        → LLM "remembers" the conversation

Key Concepts:
    - MongoDBChatMessageHistory: The STORAGE layer (where messages live)
    - ConversationBufferMemory: The INTERFACE layer (how LangChain uses them)
    - session_id: The GROUPING key (which conversation thread)
"""

import os
from dotenv import load_dotenv
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_classic.memory import ConversationBufferMemory

load_dotenv()

# ============================================================
# Constants
# ============================================================
DATABASE_NAME = "ai_study_planner"
COLLECTION_NAME = "chat_history"


# ============================================================
# Get MongoDB Connection String
# ============================================================
def _get_connection_string() -> str:
    """
    Returns the MongoDB URI from environment variables.
    
    We keep this as a helper because MongoDBChatMessageHistory
    needs the raw connection string (not a MongoClient object).
    """
    connection_string = os.getenv("MONGODB_URI")
    if not connection_string:
        raise ValueError("MONGODB_URI not found in .env")
    return connection_string


# ============================================================
# Component 1: MongoDBChatMessageHistory
# ============================================================
def get_chat_history(session_id: str) -> MongoDBChatMessageHistory:
    """
    Creates a MongoDBChatMessageHistory for a specific session.
    
    This is the STORAGE layer — it handles:
    - Saving human messages to MongoDB
    - Saving AI messages to MongoDB  
    - Loading all past messages for this session_id
    
    Args:
        session_id: Unique identifier for the conversation.
                    Example: "neha_session_1"
                    All messages with this ID belong to the same thread.
    
    Returns:
        MongoDBChatMessageHistory: An object that reads/writes messages to MongoDB
    
    What gets stored in MongoDB (chat_history collection):
        {
            "SessionId": "neha_session_1",
            "History": [
                {"type": "human", "content": "I want to learn Python"},
                {"type": "ai", "content": "Here's your study plan..."}
            ]
        }
    """
    return MongoDBChatMessageHistory(
        connection_string=_get_connection_string(),
        database_name=DATABASE_NAME,
        collection_name=COLLECTION_NAME,
        session_id=session_id,
    )


# ============================================================
# Component 2: ConversationBufferMemory (wraps Component 1)
# ============================================================
def get_memory(session_id: str) -> ConversationBufferMemory:
    """
    Creates a ConversationBufferMemory backed by MongoDB.
    
    This is the INTERFACE layer — it:
    - Uses MongoDBChatMessageHistory as its backend
    - Exposes a 'chat_history' variable for your prompt template
    - Automatically loads past messages when the chain runs
    
    Args:
        session_id: Unique conversation thread identifier
    
    Returns:
        ConversationBufferMemory: Memory object ready to plug into a chain
    
    How it connects to your chain:
        memory = get_memory("neha_session_1")
        
        # The memory provides a variable called "chat_history"
        # which contains all past messages for this session.
        # Your prompt template can use {chat_history} to include them.
    """
    # Get the MongoDB-backed chat history
    chat_history = get_chat_history(session_id)
    
    # Wrap it in ConversationBufferMemory
    memory = ConversationBufferMemory(
        memory_key="chat_history",          # Variable name used in prompt template
        chat_memory=chat_history,           # Backend storage (MongoDB)
        return_messages=True,               # Return as Message objects (not raw text)
        output_key="output"                 # Which chain output to save as AI message
    )
    
    return memory


# ============================================================
# Utility: Clear a session's history
# ============================================================
def get_message_count(session_id: str) -> int:
    """
    Returns the number of messages stored for a session.

    Useful for checking if a session has existing history
    (e.g., on startup: "Welcome back! You have 4 past messages").

    Args:
        session_id: The session to check

    Returns:
        int: Number of messages (0 if no history exists)
    """
    chat_history = get_chat_history(session_id)
    return len(chat_history.messages)


def get_last_goals(session_id: str, max_goals: int = 3) -> list[str]:
    """
    Extracts the most recent learning goals from past human messages.

    Scans messages for "Goal: ..." patterns (how we save them in the chain).
    Returns up to max_goals most recent ones.

    Args:
        session_id: The session to check
        max_goals:  Maximum number of goals to return

    Returns:
        list[str]: List of goal strings, most recent first
    """
    chat_history = get_chat_history(session_id)
    goals = []

    for msg in reversed(chat_history.messages):
        if msg.type == "human" and "Goal:" in msg.content:
            # Extract goal from "Goal: Learn Python, Skills: ..., Time: ..."
            content = msg.content
            goal_part = content.split("Goal:")[-1].split(",")[0].strip()
            if goal_part and goal_part not in goals:
                goals.append(goal_part)
            if len(goals) >= max_goals:
                break

    return goals


def clear_chat_history(session_id: str):
    """
    Deletes all messages for a specific session.
    
    Useful for:
    - Starting a fresh conversation
    - Testing/debugging
    - User requests to "forget" past conversations
    
    Args:
        session_id: The session whose history to clear
    """
    chat_history = get_chat_history(session_id)
    chat_history.clear()
    print(f"🗑️ Cleared chat history for session: {session_id}")
