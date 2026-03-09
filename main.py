"""
AI Study Planner - Main Entry Point

This is the CLI (Command Line Interface) for the AI Study Planner.
It ties together ALL the components we've built:

    LLM (Gemini)  →  Prompt  →  Chain  →  Memory (MongoDB)  →  Plan Store (MongoDB)

How it works:
    1. User enters their name → creates a session_id
    2. User provides goal, skills, time → chain generates a plan
    3. Plan + conversation saved to MongoDB
    4. User can generate more plans, view past plans, or exit
    5. Memory persists — close the app, reopen, history is still there
"""

import json
import time as time_module
from chains.study_chain import generate_study_plan_with_memory
from memory.chat_memory import clear_chat_history, get_message_count, get_last_goals
from memory.plan_store import get_plans_by_user, get_study_plan
from memory.progress_store import (
    mark_day_completed,
    calculate_progress,
    get_progress_bar,
    get_plan_progress,
)
from agent.study_agent import create_study_agent, chat_with_agent
from auth.auth import register_user, login_user


# ============================================================
# Helper: Pretty print a study plan
# ============================================================
def display_plan(plan: dict):
    """
    Displays a study plan in a readable format with progress tracking.
    """
    print(f"\n📌 Goal: {plan.get('goal', 'N/A')}")
    print(f"📅 Total Weeks: {plan.get('total_weeks', 'N/A')}")

    # Show progress bar if any days have the 'completed' field
    stats = calculate_progress(plan)
    if stats["total"] > 0:
        bar = get_progress_bar(stats["percentage"])
        print(f"📊 Progress: {bar}  ({stats['completed']}/{stats['total']} days)")

    weekly_plan = plan.get("weekly_plan", [])
    for week in weekly_plan:
        print(f"\n{'─' * 40}")
        print(f"📖 Week {week.get('week', '?')}: {week.get('theme', '')}")
        print(f"{'─' * 40}")

        for day in week.get("days", []):
            # Show ✅ for completed days, ⬜ for incomplete
            done = day.get("completed", False)
            status_icon = "✅" if done else "⬜"
            print(f"  {status_icon} {day.get('day', '?')}")
            print(f"     Topic: {day.get('topic', 'N/A')}")
            print(f"     Duration: {day.get('duration_hours', '?')} hours")

            resources = day.get("resources", [])
            if resources:
                print(f"     Resources: {', '.join(resources)}")

            tasks = day.get("tasks", [])
            if tasks:
                for task in tasks:
                    print(f"     • {task}")

    tips = plan.get("tips", [])
    if tips:
        print(f"\n💡 Tips:")
        for tip in tips:
            print(f"   • {tip}")


# ============================================================
# Helper: View past plans for a user
# ============================================================
def view_past_plans(user_id: str):
    """
    Retrieves and displays all saved plans for a user.
    """
    plans = get_plans_by_user(user_id)

    if not plans:
        print("\n📭 No saved plans found.")
        return

    print(f"\n📋 Your Saved Plans ({len(plans)} total):")
    print("=" * 50)

    for i, p in enumerate(plans, 1):
        print(f"\n  [{i}] {p['goal']}")
        print(f"      Skills: {p.get('skills', 'N/A')}")
        print(f"      Time: {p.get('time', 'N/A')}")
        print(f"      Created: {p.get('created_at', 'N/A')}")
        print(f"      Plan ID: {p['_id']}")

    # Ask if they want to view a specific plan's details
    print()
    choice = input(f"Enter a number [1-{len(plans)}] to view full details (or press Enter to go back): ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(plans):
            display_plan(plans[idx]["plan"])
        else:
            print("❌ Invalid plan number.")


# ============================================================
# Helper: Update progress on a plan (interactive flow)
# ============================================================
def update_progress(user_id: str):
    """
    Interactive flow: pick a plan → pick a week → pick a day → mark done.
    """
    plans = get_plans_by_user(user_id)

    if not plans:
        print("\n📭 No saved plans found. Generate a plan first!")
        return

    # ---- Step 1: Pick a plan ----
    print(f"\n📋 Your Plans ({len(plans)} total):")
    print("=" * 50)
    for i, p in enumerate(plans, 1):
        progress = calculate_progress(p["plan"])
        bar = get_progress_bar(progress["percentage"], width=10)
        print(f"  [{i}] {p['goal']}  {bar}")

    print()
    plan_choice = input(f"Pick a plan [1-{len(plans)}] (or press Enter to go back): ").strip()
    if not plan_choice.isdigit():
        return
    plan_idx = int(plan_choice) - 1
    if plan_idx < 0 or plan_idx >= len(plans):
        print("❌ Invalid plan number.")
        return

    selected_plan = plans[plan_idx]
    plan_id = selected_plan["_id"]
    plan = selected_plan["plan"]

    # ---- Step 2: Pick a week ----
    weekly_plan = plan.get("weekly_plan", [])
    if not weekly_plan:
        print("❌ This plan has no weekly schedule.")
        return

    print(f"\n📖 Weeks in \"{selected_plan['goal']}\":")
    for week in weekly_plan:
        week_num = week.get("week", "?")
        theme = week.get("theme", "")
        # Count completed days in this week
        days = week.get("days", [])
        done = sum(1 for d in days if d.get("completed", False))
        total = len(days)
        print(f"  [Week {week_num}] {theme}  ({done}/{total} days done)")

    print()
    week_choice = input(f"Pick a week [1-{len(weekly_plan)}] (or press Enter to go back): ").strip()
    if not week_choice.isdigit():
        return
    week_idx = int(week_choice) - 1
    if week_idx < 0 or week_idx >= len(weekly_plan):
        print("❌ Invalid week number.")
        return

    selected_week = weekly_plan[week_idx]
    week_number = selected_week.get("week", week_idx + 1)

    # ---- Step 3: Pick a day ----
    days = selected_week.get("days", [])
    if not days:
        print("❌ This week has no days.")
        return

    print(f"\n📅 Days in Week {week_number}:")
    for j, day in enumerate(days, 1):
        done = day.get("completed", False)
        icon = "✅" if done else "⬜"
        print(f"  [{j}] {icon} {day.get('day', '?')} — {day.get('topic', 'N/A')}")

    print()
    day_choice = input(f"Pick a day to mark as done [1-{len(days)}] (or press Enter to go back): ").strip()
    if not day_choice.isdigit():
        return
    day_idx = int(day_choice) - 1
    if day_idx < 0 or day_idx >= len(days):
        print("❌ Invalid day number.")
        return

    selected_day = days[day_idx]
    day_name = selected_day.get("day", "")

    if selected_day.get("completed", False):
        print(f"\n✅ {day_name} is already marked as completed!")
        return

    # ---- Step 4: Mark the day as done ----
    success = mark_day_completed(plan_id, week_number, day_name)

    if success:
        print(f"\n🎉 Marked Week {week_number}, {day_name} as DONE!")

        # Show updated progress
        progress = get_plan_progress(plan_id)
        if progress:
            print(f"📊 Overall Progress: {progress['bar']}  ({progress['completed']}/{progress['total']} days)")
    else:
        print(f"\n❌ Failed to update progress.")


# ============================================================
# Main conversation loop
# ============================================================
def main():
    print("=" * 50)
    print("🤖 AI Study Planner")
    print("   Powered by LangChain + Gemini + MongoDB")
    print("=" * 50)

    # ---- Authentication: Login or Register ----
    user_id = None

    while not user_id:
        print("\n🔐 Login or Register")
        print("  [L] Login")
        print("  [R] Register")
        print("  [Q] Quit")

        auth_choice = input("Your choice (L/R/Q): ").strip().upper()

        if auth_choice == "Q":
            print("👋 Goodbye!")
            return

        elif auth_choice == "R":
            print()
            username = input("Choose a username: ").strip()
            password = input("Choose a password: ").strip()

            result = register_user(username, password)
            if result["success"]:
                print(f"\n✅ {result['message']}")
                user_id = result["user_id"]
            else:
                print(f"\n❌ {result['message']}")

        elif auth_choice == "L":
            print()
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            result = login_user(username, password)
            if result["success"]:
                print(f"\n✅ {result['message']}")
                user_id = result["user_id"]
            else:
                print(f"\n❌ {result['message']}")

        else:
            print("❌ Invalid choice. Enter L, R, or Q.")

    # ---- Session setup (same as before, but user_id is now verified) ----
    session_id = user_id

    # ---- Check for existing session in MongoDB ----
    message_count = get_message_count(session_id)

    if message_count > 0:
        # Returning user — show what we remember
        print(f"\n👋 Welcome back, {user_id}!")
        print(f"📎 Session: {session_id}")
        print(f"💬 You have {message_count} past messages in this session.")

        # Show their recent goals
        past_goals = get_last_goals(session_id)
        if past_goals:
            print(f"📌 Last time you were learning: {', '.join(past_goals)}")

        # Ask: continue or start fresh?
        print(f"\nWould you like to:")
        print(f"  [C] Continue this session (keep memory)")
        print(f"  [N] Start a new session (clear memory)")

        session_choice = input("Your choice (C/N): ").strip().upper()

        if session_choice == "N":
            clear_chat_history(session_id)
            print("✨ Fresh session started! Memory cleared.")
        else:
            print("✅ Continuing with existing memory...")
    else:
        # First-time user
        print(f"\n👋 Welcome, {user_id}!")
        print(f"📎 Session: {session_id}")
        print(f"   (Your conversation history will be saved to MongoDB)")

    print()

    while True:
        print("─" * 50)
        print("What would you like to do?")
        print("  [1] 📝 Generate a new study plan")
        print("  [2] 📋 View my past plans")
        print("  [3] 📊 Update progress on a plan")
        print("  [4] 🤖 Chat with AI agent")
        print("  [5] 🗑️  Clear this session's chat history")
        print("  [6] 🚪 Exit")
        print("─" * 50)

        choice = input("Your choice (1-6): ").strip()

        # ---- Option 1: Generate a study plan ----
        if choice == "1":
            print()
            goal = input("📌 What's your learning goal? ").strip()
            if not goal:
                print("❌ Goal cannot be empty.")
                continue

            skills = input("📚 What are your current skills? ").strip()
            if not skills:
                skills = "No prior experience"

            available_time = input("⏰ How much time do you have per day? ").strip()
            if not available_time:
                available_time = "2 hours a day"

            print("\n⏳ Generating your study plan... (this may take 20-40 seconds)")

            try:
                plan = generate_study_plan_with_memory(
                    goal=goal,
                    skills=skills,
                    time=available_time,
                    session_id=session_id,
                    user_id=user_id,
                )

                print("\n✅ Study plan generated and saved!")
                print(f"💾 Plan ID: {plan.get('plan_id', 'N/A')}")
                display_plan(plan)

            except Exception as e:
                print(f"\n❌ Error generating plan: {e}")

        # ---- Option 2: View past plans ----
        elif choice == "2":
            view_past_plans(user_id)

        # ---- Option 3: Update progress ----
        elif choice == "3":
            update_progress(user_id)

        # ---- Option 4: Chat with AI agent ----
        elif choice == "4":
            print("\n\U0001f916 AI Agent Chat (type 'back' to return to menu)")
            print("   Ask me anything — I can search the web, check your plans,")
            print("   and give you personalized study advice!\n")

            # Create agent once for this chat session
            agent = create_study_agent(user_id)

            while True:
                user_input = input("You: ").strip()
                if not user_input or user_input.lower() == "back":
                    print("\u2190 Returning to menu...")
                    break

                print("\u23f3 Thinking...")
                try:
                    response = chat_with_agent(agent, user_input, session_id)
                    print(f"\n\U0001f916 Agent: {response}\n")
                except Exception as e:
                    print(f"\n\u274c Agent error: {e}\n")

        # ---- Option 5: Clear chat history ----
        elif choice == "5":
            confirm = input("Are you sure? This clears conversation memory. (y/n): ").strip().lower()
            if confirm == "y":
                clear_chat_history(session_id)
            else:
                print("Cancelled.")

        # ---- Option 6: Exit ----
        elif choice == "6":
            print(f"\n👋 Goodbye, {user_id}! Your plans are saved in MongoDB.")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

        print()


if __name__ == "__main__":
    main()
