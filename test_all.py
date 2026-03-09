"""
AI Study Planner — Master Test Suite
=====================================

Runs ALL tests in order: fast (no LLM) first, then slow (LLM calls).

Usage:
    python test_all.py          → Run only FAST tests (no LLM, ~10 seconds)
    python test_all.py --all    → Run ALL tests including LLM calls (~2 minutes)

Test Categories:
    FAST (no API calls):
        1. MongoDB Connection     — Can we ping the cluster?
        2. Chat History           — Save/load/clear messages in MongoDB
        3. Plan Store CRUD        — Create/Read/Update/Delete study plans
        4. Prompt Template        — Does the template format correctly?
    
    SLOW (calls Gemini API):
        5. LLM Basic Response     — Does Gemini respond at all?
        6. Study Chain            — Prompt → LLM → JSON parse working?
        7. Memory Chain           — Does the LLM use past context?
"""

import sys
import json
import traceback


# ============================================================
# Test tracking
# ============================================================
results = []  # List of (test_name, passed: bool, detail: str)


def record(name: str, passed: bool, detail: str = ""):
    """Record a test result."""
    results.append((name, passed, detail))
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} — {name}")
    if detail and not passed:
        print(f"         {detail}")


# ============================================================
# TEST 1: MongoDB Connection
# ============================================================
def test_mongodb_connection():
    """
    Tests: Can we connect to MongoDB and ping it?
    What it proves: Your MONGODB_URI is correct and the cluster is reachable.
    """
    print("\n🔌 Test 1: MongoDB Connection")
    print("─" * 40)

    try:
        from memory.mongodb_client import get_mongo_client, get_database

        # Test 1a: Can we create a client and ping?
        client = get_mongo_client()
        client.admin.command("ping")
        record("MongoDB ping", True)

        # Test 1b: Can we access the database?
        db = get_database()
        assert db.name == "ai_study_planner"
        record("Database access", True)

        # Test 1c: Can we list collections?
        client.list_database_names()
        record("List databases", True)

    except Exception as e:
        record("MongoDB connection", False, str(e))


# ============================================================
# TEST 2: Chat History (save/load/clear)
# ============================================================
def test_chat_history():
    """
    Tests: Can we save messages to MongoDB and read them back?
    What it proves: MongoDBChatMessageHistory is working correctly.
    """
    print("\n🧠 Test 2: Chat History (Save/Load/Clear)")
    print("─" * 40)

    session_id = "__test_chat_history__"

    try:
        from memory.chat_memory import get_chat_history, get_memory, clear_chat_history

        # Clean slate
        clear_chat_history(session_id)

        # Test 2a: Add messages
        chat = get_chat_history(session_id)
        chat.add_user_message("Test human message")
        chat.add_ai_message("Test AI response")
        messages = chat.messages
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        record("Save & load messages", True)

        # Test 2b: Verify message types
        assert messages[0].type == "human"
        assert messages[1].type == "ai"
        record("Message types correct", True)

        # Test 2c: Verify content
        assert messages[0].content == "Test human message"
        assert messages[1].content == "Test AI response"
        record("Message content correct", True)

        # Test 2d: ConversationBufferMemory wrapper
        memory = get_memory(session_id)
        memory_vars = memory.load_memory_variables({})
        assert "chat_history" in memory_vars
        assert len(memory_vars["chat_history"]) == 2
        record("ConversationBufferMemory wrapper", True)

        # Test 2e: Clear history
        clear_chat_history(session_id)
        chat_after = get_chat_history(session_id)
        assert len(chat_after.messages) == 0, "Messages not cleared"
        record("Clear chat history", True)

    except Exception as e:
        record("Chat history", False, str(e))
        # Clean up even on failure
        try:
            clear_chat_history(session_id)
        except:
            pass


# ============================================================
# TEST 3: Plan Store CRUD
# ============================================================
def test_plan_store():
    """
    Tests: Can we Create, Read, Update, Delete study plans?
    What it proves: All pymongo CRUD operations work correctly.
    """
    print("\n📚 Test 3: Plan Store (CRUD)")
    print("─" * 40)

    plan_id = None

    try:
        from memory.plan_store import (
            save_study_plan, get_study_plan, get_plans_by_user,
            update_study_plan, delete_study_plan
        )

        fake_plan = {
            "goal": "Test Goal",
            "total_weeks": 1,
            "weekly_plan": [{"week": 1, "theme": "Test Week"}],
            "tips": ["Test tip"]
        }

        # Test 3a: CREATE
        plan_id = save_study_plan(
            user_id="__test_user__",
            session_id="__test_session__",
            goal="Test Goal",
            skills="Test Skills",
            time="1 hour",
            plan=fake_plan
        )
        assert plan_id is not None
        record("CREATE (save plan)", True)

        # Test 3b: READ single
        plan = get_study_plan(plan_id)
        assert plan is not None
        assert plan["goal"] == "Test Goal"
        assert plan["plan"]["total_weeks"] == 1
        record("READ (get by ID)", True)

        # Test 3c: READ list
        plans = get_plans_by_user("__test_user__")
        assert len(plans) >= 1
        assert any(p["_id"] == plan_id for p in plans)
        record("READ (list by user)", True)

        # Test 3d: UPDATE
        updated = fake_plan.copy()
        updated["total_weeks"] = 3
        success = update_study_plan(plan_id, updated)
        assert success is True
        plan_after = get_study_plan(plan_id)
        assert plan_after["plan"]["total_weeks"] == 3
        record("UPDATE (modify plan)", True)

        # Test 3e: DELETE
        deleted = delete_study_plan(plan_id)
        assert deleted is True
        gone = get_study_plan(plan_id)
        assert gone is None
        record("DELETE (remove plan)", True)
        plan_id = None  # Already cleaned up

    except Exception as e:
        record("Plan store CRUD", False, str(e))
    finally:
        # Clean up if test failed mid-way
        if plan_id:
            try:
                from memory.plan_store import delete_study_plan
                delete_study_plan(plan_id)
            except:
                pass


# ============================================================
# TEST 4: Prompt Template
# ============================================================
def test_prompt_template():
    """
    Tests: Do both prompt templates format correctly with variables?
    What it proves: No missing variables, no formatting errors.
    """
    print("\n📝 Test 4: Prompt Template Formatting")
    print("─" * 40)

    try:
        from prompts.planner_prompt import study_planner_template, study_planner_memory_template

        # Test 4a: Original template
        result = study_planner_template.format(
            goal="Learn Python",
            skills="No experience",
            time="2 hours"
        )
        assert "Learn Python" in result
        assert "No experience" in result
        assert "2 hours" in result
        record("Original template formats correctly", True)

        # Test 4b: Memory template
        result_mem = study_planner_memory_template.format(
            chat_history="Human: I like math\nAI: Noted!",
            goal="Learn Calculus",
            skills="Algebra",
            time="3 hours"
        )
        assert "I like math" in result_mem
        assert "Learn Calculus" in result_mem
        assert "chat_history" not in result_mem  # Variable should be replaced
        record("Memory template formats correctly", True)

        # Test 4c: JSON structure markers present
        assert '"goal"' in result
        assert '"weekly_plan"' in result
        assert '"tips"' in result
        record("JSON structure in template", True)

    except Exception as e:
        record("Prompt template", False, str(e))


# ============================================================
# TEST 5: LLM Basic Response (SLOW — calls Gemini)
# ============================================================
def test_llm_response():
    """
    Tests: Does Gemini respond to a simple prompt?
    What it proves: API key works, model is reachable.
    """
    print("\n🤖 Test 5: LLM Basic Response (calls Gemini)")
    print("─" * 40)

    try:
        from llm.gemini_llm import get_gemini_llm

        llm = get_gemini_llm()
        response = llm.invoke("Say 'hello' and nothing else.")
        assert response is not None
        assert len(response.content) > 0
        record("LLM responds", True)

    except Exception as e:
        record("LLM response", False, str(e))


# ============================================================
# TEST 6: Study Chain — Prompt → LLM → JSON Parse (SLOW)
# ============================================================
def test_study_chain():
    """
    Tests: Does the full chain produce a valid parsed JSON study plan?
    What it proves: Prompt formatting + LLM generation + JSON parsing all work.
    """
    print("\n🔗 Test 6: Study Chain (Prompt → LLM → JSON)")
    print("─" * 40)

    try:
        from chains.study_chain import generate_study_plan

        result = generate_study_plan(
            goal="Learn basic HTML",
            skills="No experience",
            time="1 hour a day"
        )

        # Test 6a: Result is a dict (JSON was parsed)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        record("Output is a parsed dict", True)

        # Test 6b: Required keys present
        required_keys = ["goal", "total_weeks", "weekly_plan", "tips"]
        missing = [k for k in required_keys if k not in result]
        assert not missing, f"Missing keys: {missing}"
        record("All required keys present", True)

        # Test 6c: weekly_plan is a list
        assert isinstance(result["weekly_plan"], list)
        assert len(result["weekly_plan"]) > 0
        record("weekly_plan is non-empty list", True)

    except Exception as e:
        record("Study chain", False, str(e))


# ============================================================
# TEST 7: Memory Chain — Context Carryover (SLOW)
# ============================================================
def test_memory_chain():
    """
    Tests: Does the LLM receive past conversation context?
    What it proves: Memory loads → injected into prompt → plan saved to MongoDB.
    """
    print("\n🧠 Test 7: Memory Chain (Context Carryover)")
    print("─" * 40)

    session_id = "__test_memory_chain__"
    user_id = "__test_memory_user__"

    try:
        from chains.study_chain import generate_study_plan_with_memory
        from memory.chat_memory import get_chat_history, clear_chat_history
        from memory.plan_store import get_plans_by_user, delete_study_plan

        # Clean slate
        clear_chat_history(session_id)

        # Test 7a: First plan
        plan1 = generate_study_plan_with_memory(
            goal="Learn CSS basics",
            skills="Knows HTML",
            time="1 hour a day",
            session_id=session_id,
            user_id=user_id
        )
        assert isinstance(plan1, dict)
        assert "plan_id" in plan1
        record("First plan generated & saved", True)

        # Test 7b: Chat history saved
        messages = get_chat_history(session_id).messages
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        record("Chat history saved (2 messages)", True)

        # Test 7c: Second plan with context
        plan2 = generate_study_plan_with_memory(
            goal="Now add JavaScript",
            skills="Knows HTML and CSS",
            time="2 hours a day",
            session_id=session_id,
            user_id=user_id
        )
        assert isinstance(plan2, dict)
        assert "plan_id" in plan2
        record("Second plan with context generated", True)

        # Test 7d: Both plans saved in MongoDB
        plans = get_plans_by_user(user_id)
        assert len(plans) >= 2, f"Expected >= 2 plans, got {len(plans)}"
        record("Both plans saved to study_plans", True)

        # Test 7e: Chat history now has 4 messages
        messages_after = get_chat_history(session_id).messages
        assert len(messages_after) == 4, f"Expected 4 messages, got {len(messages_after)}"
        record("Chat history has 4 messages", True)

        # Clean up
        clear_chat_history(session_id)
        for p in plans:
            delete_study_plan(p["_id"])

    except Exception as e:
        record("Memory chain", False, str(e))
        # Clean up on failure
        try:
            from memory.chat_memory import clear_chat_history
            from memory.plan_store import get_plans_by_user, delete_study_plan
            clear_chat_history(session_id)
            for p in get_plans_by_user(user_id):
                delete_study_plan(p["_id"])
        except:
            pass


# ============================================================
# MAIN — Run the tests
# ============================================================
def main():
    run_all = "--all" in sys.argv

    print("=" * 50)
    print("🧪 AI Study Planner — Test Suite")
    print("=" * 50)

    if run_all:
        print("Mode: FULL (fast + slow tests)")
    else:
        print("Mode: FAST only (no LLM calls)")
        print("Tip:  Run with --all to include LLM tests")

    # ---- FAST TESTS (no LLM calls) ----
    print("\n" + "=" * 50)
    print("🏃 FAST TESTS")
    print("=" * 50)

    test_mongodb_connection()
    test_chat_history()
    test_plan_store()
    test_prompt_template()

    # ---- SLOW TESTS (LLM calls) ----
    if run_all:
        print("\n" + "=" * 50)
        print("🐢 SLOW TESTS (calling Gemini API...)")
        print("=" * 50)

        test_llm_response()
        test_study_chain()
        test_memory_chain()

    # ---- SUMMARY ----
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    for name, p, detail in results:
        status = "✅" if p else "❌"
        print(f"  {status} {name}")

    print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check details above.")

    # Return exit code (0 = all passed, 1 = some failed)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
