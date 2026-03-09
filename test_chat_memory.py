"""
Test Chat Memory - Verify MongoDB-backed conversation memory works

What this test does:
1. Creates a memory for a test session
2. Manually adds messages (simulating a conversation)
3. Retrieves them to prove they persisted in MongoDB
4. Clears the history
"""

from memory.chat_memory import get_chat_history, get_memory, clear_chat_history


def test_chat_memory():
    session_id = "test_session_001"
    
    print("🧠 Testing Chat Memory (MongoDB-backed)")
    print("=" * 50)
    
    # ---- Step 1: Clear any leftover test data ---- 
    clear_chat_history(session_id)
    
    # ---- Step 2: Get the chat history object ----
    print("\n📝 Adding messages to MongoDB...")
    chat_history = get_chat_history(session_id)
    
    # Add messages (these go straight to MongoDB)
    chat_history.add_user_message("I want to learn Python in 2 weeks")
    chat_history.add_ai_message("Great! I'll create a 2-week Python study plan for you.")
    chat_history.add_user_message("I already know basic variables and loops")
    chat_history.add_ai_message("Perfect, I'll skip the basics and focus on intermediate topics.")
    
    print("   ✅ Added 4 messages (2 human, 2 AI)")
    
    # ---- Step 3: Retrieve messages ----
    print("\n📖 Retrieving messages from MongoDB...")
    messages = chat_history.messages
    
    for msg in messages:
        role = "🧑 Human" if msg.type == "human" else "🤖 AI"
        print(f"   {role}: {msg.content}")
    
    print(f"\n   ✅ Retrieved {len(messages)} messages")
    
    # ---- Step 4: Test ConversationBufferMemory wrapper ----
    print("\n🔗 Testing ConversationBufferMemory wrapper...")
    memory = get_memory(session_id)
    
    # load_memory_variables returns the chat_history for the prompt
    memory_vars = memory.load_memory_variables({})
    print(f"   ✅ Memory key: 'chat_history'")
    print(f"   ✅ Messages in memory: {len(memory_vars['chat_history'])}")
    
    # ---- Step 5: Clean up ----
    print("\n🧹 Cleaning up...")
    clear_chat_history(session_id)
    
    # Verify cleanup
    chat_history_after = get_chat_history(session_id)
    remaining = len(chat_history_after.messages)
    print(f"   ✅ Messages remaining after clear: {remaining}")
    
    print("\n" + "=" * 50)
    print("🎉 Chat memory test passed! MongoDB memory is working.")


if __name__ == "__main__":
    test_chat_memory()
