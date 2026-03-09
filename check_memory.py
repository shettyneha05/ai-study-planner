"""
Quick check: what's stored in MongoDB chat_history for a given session?
Run this to see if your conversations are being saved.
"""

from memory.chat_memory import get_chat_history
from memory.mongodb_client import get_chat_history_collection


def check_all_sessions():
    """Shows all sessions stored in chat_history collection."""
    collection = get_chat_history_collection()
    
    # Find all unique session IDs
    sessions = collection.distinct("SessionId")
    
    if not sessions:
        print("📭 No chat history found in MongoDB.")
        return
    
    print(f"📋 Found {len(sessions)} session(s) in MongoDB:\n")
    
    for session_id in sessions:
        print(f"{'─' * 50}")
        print(f"📎 Session: {session_id}")
        print(f"{'─' * 50}")
        
        chat_history = get_chat_history(session_id)
        messages = chat_history.messages
        
        if not messages:
            print("   (no messages)")
        else:
            for msg in messages:
                role = "🧑 Human" if msg.type == "human" else "🤖 AI"
                # Truncate long messages
                content = msg.content[:120] + "..." if len(msg.content) > 120 else msg.content
                print(f"   {role}: {content}")
        
        print()


if __name__ == "__main__":
    check_all_sessions()
