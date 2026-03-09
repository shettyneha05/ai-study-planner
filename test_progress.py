"""
Test Progress Store - Tests for progress tracking functions

Tests:
    1. initialize_progress — adds completed=False to all days
    2. calculate_progress — counts completed vs total
    3. get_progress_bar — visual progress bar
    4. mark_day_completed — marks a day in MongoDB (requires DB connection)
    5. get_plan_progress — fetch + calculate from MongoDB (requires DB connection)

Run:
    python test_progress.py          → Fast tests (no MongoDB)
    python test_progress.py --all    → All tests (includes MongoDB)
"""

import sys
from memory.progress_store import (
    initialize_progress,
    calculate_progress,
    get_progress_bar,
    mark_day_completed,
    get_plan_progress,
)


# ============================================================
# Sample plan for testing (mimics Gemini's output)
# ============================================================
SAMPLE_PLAN = {
    "goal": "Learn Python",
    "total_weeks": 1,
    "weekly_plan": [
        {
            "week": 1,
            "theme": "Python Basics",
            "days": [
                {"day": "Monday", "topic": "Variables", "duration_hours": 2, "resources": [], "tasks": ["Practice variables"]},
                {"day": "Tuesday", "topic": "Loops", "duration_hours": 2, "resources": [], "tasks": ["Write for loops"]},
                {"day": "Wednesday", "topic": "Functions", "duration_hours": 2, "resources": [], "tasks": ["Create functions"]},
                {"day": "Thursday", "topic": "Lists", "duration_hours": 2, "resources": [], "tasks": ["List exercises"]},
                {"day": "Friday", "topic": "Dicts", "duration_hours": 2, "resources": [], "tasks": ["Dict exercises"]},
            ],
        }
    ],
    "tips": ["Practice daily"],
}


def test_initialize_progress():
    """Test that initialize_progress adds completed=False to every day."""
    import copy
    plan = copy.deepcopy(SAMPLE_PLAN)

    # Before: no 'completed' fields
    for week in plan["weekly_plan"]:
        for day in week["days"]:
            assert "completed" not in day, "Day should NOT have 'completed' before init"

    # Initialize
    result = initialize_progress(plan)

    # After: every day has completed=False
    for week in result["weekly_plan"]:
        for day in week["days"]:
            assert "completed" in day, "Day should have 'completed' after init"
            assert day["completed"] is False, "Day should start as False"

    print("✅ initialize_progress — adds completed=False to all days")


def test_calculate_progress_zero():
    """Test progress calculation when nothing is completed."""
    import copy
    plan = copy.deepcopy(SAMPLE_PLAN)
    initialize_progress(plan)

    stats = calculate_progress(plan)
    assert stats["completed"] == 0
    assert stats["total"] == 5
    assert stats["percentage"] == 0.0

    print("✅ calculate_progress — 0/5 = 0%")


def test_calculate_progress_partial():
    """Test progress when some days are marked done."""
    import copy
    plan = copy.deepcopy(SAMPLE_PLAN)
    initialize_progress(plan)

    # Mark 2 days done
    plan["weekly_plan"][0]["days"][0]["completed"] = True
    plan["weekly_plan"][0]["days"][1]["completed"] = True

    stats = calculate_progress(plan)
    assert stats["completed"] == 2
    assert stats["total"] == 5
    assert stats["percentage"] == 40.0

    print("✅ calculate_progress — 2/5 = 40%")


def test_calculate_progress_full():
    """Test progress when all days are done."""
    import copy
    plan = copy.deepcopy(SAMPLE_PLAN)
    initialize_progress(plan)

    # Mark all days done
    for day in plan["weekly_plan"][0]["days"]:
        day["completed"] = True

    stats = calculate_progress(plan)
    assert stats["completed"] == 5
    assert stats["total"] == 5
    assert stats["percentage"] == 100.0

    print("✅ calculate_progress — 5/5 = 100%")


def test_progress_bar():
    """Test visual progress bar output."""
    bar_0 = get_progress_bar(0)
    assert "░" in bar_0
    assert "█" not in bar_0
    assert "0.0%" in bar_0

    bar_50 = get_progress_bar(50)
    assert "█" in bar_50
    assert "░" in bar_50
    assert "50.0%" in bar_50

    bar_100 = get_progress_bar(100)
    assert "█" in bar_100
    assert "░" not in bar_100
    assert "100.0%" in bar_100

    print("✅ get_progress_bar — 0%, 50%, 100% all correct")


def test_mark_day_in_mongodb():
    """
    Integration test: saves a plan to MongoDB, marks a day done, verifies.
    Only runs with --all flag.
    """
    import copy
    from memory.plan_store import save_study_plan, get_study_plan, delete_study_plan

    plan = copy.deepcopy(SAMPLE_PLAN)
    initialize_progress(plan)

    # Save to MongoDB
    plan_id = save_study_plan(
        user_id="test_progress_user",
        session_id="test_progress_session",
        goal="Learn Python",
        skills="None",
        time="2 hours",
        plan=plan,
    )
    print(f"   Saved test plan: {plan_id}")

    # Mark Monday as done
    success = mark_day_completed(plan_id, week_number=1, day_name="Monday")
    assert success is True, "mark_day_completed should return True"

    # Verify in MongoDB
    doc = get_study_plan(plan_id)
    monday = doc["plan"]["weekly_plan"][0]["days"][0]
    assert monday["completed"] is True, "Monday should be marked completed"

    # Check progress
    progress = get_plan_progress(plan_id)
    assert progress is not None
    assert progress["completed"] == 1
    assert progress["total"] == 5
    assert progress["percentage"] == 20.0
    print(f"   Progress after marking Monday: {progress['bar']}")

    # Clean up
    delete_study_plan(plan_id)
    print("✅ mark_day_completed + get_plan_progress — MongoDB integration works")


# ============================================================
# Run tests
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Progress Store Tests")
    print("=" * 50)

    # Fast tests (no MongoDB)
    test_initialize_progress()
    test_calculate_progress_zero()
    test_calculate_progress_partial()
    test_calculate_progress_full()
    test_progress_bar()

    # MongoDB test (only with --all flag)
    if "--all" in sys.argv:
        print("\n--- MongoDB Integration Tests ---")
        test_mark_day_in_mongodb()
    else:
        print("\n⏩ Skipping MongoDB tests. Run with --all to include them.")

    print("\n" + "=" * 50)
    print("🎉 All progress tests PASSED!")
    print("=" * 50)
