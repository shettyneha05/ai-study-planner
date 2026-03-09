"""
Progress Store - Track completion of study plan days

This module lets users mark individual days as "done" in their study plans
and calculates overall progress (% completed).

How it works:
    - Each day in the plan gets a "completed" field (True/False)
    - When a user marks a day done, we update that specific day in MongoDB
    - Progress = (completed days / total days) * 100

Functions:
    initialize_progress(plan)              → Add completed=False to all days
    mark_day_completed(plan_id, week, day) → Set a specific day to completed=True
    calculate_progress(plan)               → Returns {"completed": X, "total": Y, "percentage": Z}
    get_progress_bar(percentage)           → Returns visual bar like ████░░░░ 50%

MongoDB Update Strategy:
    We use plan_store.update_study_plan() to replace the entire plan dict
    after modifying the "completed" field on the target day.
    This keeps things simple — one collection, one update function.
"""

from memory.plan_store import get_study_plan, update_study_plan


# ============================================================
# Initialize — Add "completed: False" to every day in a plan
# ============================================================
def initialize_progress(plan: dict) -> dict:
    """
    Adds a 'completed' field (set to False) to every day in the plan.

    Call this BEFORE saving the plan to MongoDB, so every day
    starts as not-completed.

    Args:
        plan: The study plan dict from Gemini

    Returns:
        dict: The same plan with 'completed' fields added

    Example:
        plan = generate_study_plan(...)
        plan = initialize_progress(plan)  # Now every day has completed=False
        save_study_plan(..., plan=plan)
    """
    weekly_plan = plan.get("weekly_plan", [])

    for week in weekly_plan:
        for day in week.get("days", []):
            if "completed" not in day:
                day["completed"] = False

    return plan


# ============================================================
# Mark Day Completed — Set a specific day to done
# ============================================================
def mark_day_completed(plan_id: str, week_number: int, day_name: str) -> bool:
    """
    Marks a specific day in a plan as completed.

    How it works:
        1. Fetches the full plan document from MongoDB
        2. Finds the matching week and day
        3. Sets completed=True on that day
        4. Saves the updated plan back to MongoDB

    Args:
        plan_id:     The MongoDB _id of the plan
        week_number: Which week (1, 2, etc.)
        day_name:    Which day ("Monday", "Tuesday", etc.)

    Returns:
        bool: True if the day was found and marked, False otherwise

    Example:
        success = mark_day_completed("65f1a2b3...", week_number=1, day_name="Monday")
        print(success)  # True
    """
    # Step 1: Fetch the plan from MongoDB
    doc = get_study_plan(plan_id)
    if not doc:
        print(f"❌ Plan not found: {plan_id}")
        return False

    plan = doc["plan"]

    # Step 2: Find the matching week and day
    found = False
    for week in plan.get("weekly_plan", []):
        if week.get("week") == week_number:
            for day in week.get("days", []):
                if day.get("day", "").lower() == day_name.lower():
                    day["completed"] = True
                    found = True
                    break
            break  # Found the week, no need to keep looking

    if not found:
        print(f"❌ Could not find Week {week_number}, {day_name} in this plan.")
        return False

    # Step 3: Save the updated plan back to MongoDB
    success = update_study_plan(plan_id, plan)
    return success


# ============================================================
# Calculate Progress — How much of the plan is done?
# ============================================================
def calculate_progress(plan: dict) -> dict:
    """
    Calculates completion statistics for a study plan.

    Args:
        plan: The study plan dict (from the "plan" field in MongoDB)

    Returns:
        dict with:
            - completed: Number of days marked as done
            - total:     Total number of days in the plan
            - percentage: Float 0-100

    Example:
        stats = calculate_progress(plan)
        print(f"{stats['completed']}/{stats['total']} days done ({stats['percentage']:.0f}%)")
        # "3/10 days done (30%)"
    """
    total_days = 0
    completed_days = 0

    for week in plan.get("weekly_plan", []):
        for day in week.get("days", []):
            total_days += 1
            if day.get("completed", False):
                completed_days += 1

    percentage = (completed_days / total_days * 100) if total_days > 0 else 0

    return {
        "completed": completed_days,
        "total": total_days,
        "percentage": percentage,
    }


# ============================================================
# Progress Bar — Visual representation of completion
# ============================================================
def get_progress_bar(percentage: float, width: int = 20) -> str:
    """
    Generates a text-based progress bar.

    Args:
        percentage: 0-100
        width:      Number of characters for the bar (default 20)

    Returns:
        str: Visual progress bar

    Examples:
        get_progress_bar(0)    → "░░░░░░░░░░░░░░░░░░░░   0%"
        get_progress_bar(50)   → "██████████░░░░░░░░░░  50%"
        get_progress_bar(100)  → "████████████████████ 100%"
    """
    filled = int(width * percentage / 100)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"{bar} {percentage:5.1f}%"


# ============================================================
# Get Progress for a Plan — Combines fetch + calculate
# ============================================================
def get_plan_progress(plan_id: str) -> dict | None:
    """
    Fetches a plan from MongoDB and returns its progress stats.

    Args:
        plan_id: The MongoDB _id of the plan

    Returns:
        dict with keys: completed, total, percentage, bar
        None if plan not found

    Example:
        progress = get_plan_progress("65f1a2b3...")
        print(progress["bar"])  # "██████████░░░░░░░░░░  50.0%"
    """
    doc = get_study_plan(plan_id)
    if not doc:
        return None

    plan = doc["plan"]
    stats = calculate_progress(plan)
    stats["bar"] = get_progress_bar(stats["percentage"])

    return stats
