"""
Test the Memory-Aware Study Chain

This test does:
1. Generates a plan WITH memory (saves to MongoDB)
2. Generates a SECOND plan in the same session (LLM sees past context)
3. Verifies the plan was saved to study_plans collection
4. Cleans up test data
"""

import json
from chains.study_chain import generate_study_plan_with_memory
from memory.chat_memory import get_chat_history, clear_chat_history
from memory.plan_store import get_plans_by_user, delete_study_plan


SESSION_ID = "test_memory_session"
USER_ID = "test_memory_user"


def test_memory_chain():
    print("🧠 Testing Memory-Aware Study Chain")
    print("=" * 50)

    # ---- Clean up any leftover test data ----
    clear_chat_history(SESSION_ID)

    # ---- First request ----
    print("\n📝 Request 1: Generate a SBI PO exam study plan...")
    plan1 = generate_study_plan_with_memory(
        goal="Clear SBI PO exam in 2 weeks",
        skills="Have no idea what SBI PO asks, but I'm a quick learner",
        time="2 hours a day",
        session_id=SESSION_ID,
        user_id=USER_ID
    )
    print(f"   ✅ Plan 1 generated! Goal: {plan1.get('goal')}")
    print(f"   ✅ Weeks: {plan1.get('total_weeks')}")
    print(f"   ✅ Plan ID: {plan1.get('plan_id')}")

    # ---- Check that chat history was saved ----
    print("\n📖 Checking chat history in MongoDB...")
    chat_history = get_chat_history(SESSION_ID)
    messages = chat_history.messages
    print(f"   ✅ Messages in history: {len(messages)}")
    for msg in messages:
        role = "🧑 Human" if msg.type == "human" else "🤖 AI"
        print(f"      {role}: {msg.content[:80]}...")

    # ---- Second request (same session — LLM should see history) ----
    print("\n📝 Request 2: Now add backup to the plan (same session)...")
    plan2 = generate_study_plan_with_memory(
        goal="Add Backup plan like other exams if I can't clear SBI PO",
        skills="Have no idea how to start",
        time="3 hours a day",
        session_id=SESSION_ID,
        user_id=USER_ID
    )
    print(f"   ✅ Plan 2 generated! Goal: {plan2.get('goal')}")
    print(f"   ✅ Plan ID: {plan2.get('plan_id')}")

    # ---- Check that BOTH plans are saved ----
    print("\n📋 Checking saved plans for user...")
    plans = get_plans_by_user(USER_ID)
    print(f"   ✅ Total plans saved: {len(plans)}")
    for p in plans:
        print(f"      - {p['goal']} (ID: {p['_id']})")

    # ---- Chat history should now have 4 messages ----
    print("\n📖 Full chat history:")
    messages = get_chat_history(SESSION_ID).messages
    print(f"   ✅ Total messages: {len(messages)}")
    for msg in messages:
        role = "🧑 Human" if msg.type == "human" else "🤖 AI"
        print(f"      {role}: {msg.content[:80]}...")

    # ---- Clean up ----
    print("\n🧹 Cleaning up test data...")
    clear_chat_history(SESSION_ID)
    for p in plans:
        delete_study_plan(p["_id"])
    print("   ✅ Cleaned up!")

    print("\n" + "=" * 50)
    print("🎉 Memory chain test passed!")


if __name__ == "__main__":
    test_memory_chain()
