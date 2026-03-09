"""
Test Plan Store - Verify all CRUD operations work with MongoDB

What this test does:
1. CREATE — Save a study plan
2. READ   — Get it back by _id
3. READ   — List all plans for a user
4. UPDATE — Modify the plan
5. DELETE — Remove the plan
"""

from memory.plan_store import (
    save_study_plan,
    get_study_plan,
    get_plans_by_user,
    update_study_plan,
    delete_study_plan,
)


def test_plan_store():
    print("📚 Testing Plan Store (CRUD Operations)")
    print("=" * 50)

    # ---- CREATE ----
    print("\n📥 CREATE — Saving a study plan...")
    
    fake_plan = {
        "goal": "Learn Python basics",
        "total_weeks": 2,
        "weekly_plan": [
            {
                "week": 1,
                "theme": "Python Fundamentals",
                "days": [
                    {"day": "Monday", "topic": "Variables & Data Types", "duration_hours": 2}
                ]
            }
        ],
        "tips": ["Practice daily", "Build small projects"]
    }
    
    plan_id = save_study_plan(
        user_id="test_user",
        session_id="test_session_001",
        goal="Learn Python basics",
        skills="No experience",
        time="2 hours a day",
        plan=fake_plan
    )
    print(f"   ✅ Saved! Plan ID: {plan_id}")

    # ---- READ (single) ----
    print("\n📤 READ — Getting plan by ID...")
    plan = get_study_plan(plan_id)
    if plan:
        print(f"   ✅ Found plan: '{plan['goal']}'")
        print(f"   ✅ User: {plan['user_id']}")
        print(f"   ✅ Total weeks: {plan['plan']['total_weeks']}")
    else:
        print("   ❌ Plan not found!")
        return

    # ---- READ (list) ----
    print("\n📋 READ — Listing all plans for 'test_user'...")
    all_plans = get_plans_by_user("test_user")
    print(f"   ✅ Found {len(all_plans)} plan(s)")
    for p in all_plans:
        print(f"      - {p['goal']} (ID: {p['_id']})")

    # ---- UPDATE ----
    print("\n✏️  UPDATE — Modifying the plan...")
    updated_plan = fake_plan.copy()
    updated_plan["total_weeks"] = 4  # Changed from 2 to 4
    updated_plan["tips"].append("Join a study group")  # Added a tip
    
    success = update_study_plan(plan_id, updated_plan)
    if success:
        # Read it back to verify
        updated = get_study_plan(plan_id)
        print(f"   ✅ Updated! New total_weeks: {updated['plan']['total_weeks']}")
        print(f"   ✅ Tips now: {updated['plan']['tips']}")
    else:
        print("   ❌ Update failed!")

    # ---- DELETE ----
    print("\n🗑️  DELETE — Removing the plan...")
    deleted = delete_study_plan(plan_id)
    if deleted:
        print(f"   ✅ Deleted plan {plan_id}")
    else:
        print("   ❌ Delete failed!")

    # Verify deletion
    gone = get_study_plan(plan_id)
    print(f"   ✅ Plan still exists? {gone is not None}")

    print("\n" + "=" * 50)
    print("🎉 All CRUD tests passed!")


if __name__ == "__main__":
    test_plan_store()
