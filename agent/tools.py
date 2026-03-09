"""
Agent Tools — Custom tools the AI Agent can use

What is a Tool?
    A tool is a Python function that the Agent can CALL ON ITS OWN.
    You define what the tool does, and the Agent decides WHEN to use it
    based on the user's question.

    The @tool decorator turns a regular function into a LangChain Tool.
    The docstring becomes the tool's "description" — the Agent reads this
    to decide if the tool is relevant.

Tools in this file:
    1. search_web      — searches the internet via Tavily API
    2. get_user_plans  — fetches saved plans from MongoDB
    3. get_progress    — checks completion % on a plan
"""

import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from memory.plan_store import get_plans_by_user
from memory.progress_store import calculate_progress, get_progress_bar

load_dotenv()


# ============================================================
# Tool 1: Web Search (via Tavily)
# ============================================================
def get_search_tool():
    """
    Returns a Tavily web search tool.

    Tavily is a search API built specifically for AI agents.
    It returns clean, summarized results (not raw HTML).

    The Agent will call this when the user asks for:
    - "Find me React tutorials"
    - "What's the best Python book in 2026?"
    - "Latest resources for machine learning"
    """
    return TavilySearchResults(
        max_results=3,
        name="search_web",
        description="Search the internet for study resources, tutorials, courses, and learning materials. Use this when the user asks for recommendations or wants to find something online.",
    )


# ============================================================
# Tool 2: Get User's Plans from MongoDB
# ============================================================
@tool
def get_user_plans_tool(user_id: str) -> str:
    """
    Retrieve all saved study plans for a user from MongoDB.
    Use this when the user asks about their existing plans,
    what they've been studying, or wants a summary of their plans.

    Args:
        user_id: The user's ID (lowercase name, e.g. "neha")

    Returns:
        A text summary of all the user's plans
    """
    plans = get_plans_by_user(user_id)

    if not plans:
        return "No saved study plans found for this user."

    result_lines = [f"Found {len(plans)} study plan(s):\n"]

    for i, p in enumerate(plans, 1):
        goal = p.get("goal", "Unknown")
        skills = p.get("skills", "N/A")
        time_available = p.get("time", "N/A")
        created = str(p.get("created_at", "N/A"))

        # Calculate progress
        plan_data = p.get("plan", {})
        stats = calculate_progress(plan_data)
        bar = get_progress_bar(stats["percentage"], width=10)

        result_lines.append(f"Plan {i}: {goal}")
        result_lines.append(f"  Skills: {skills}")
        result_lines.append(f"  Time: {time_available}")
        result_lines.append(f"  Progress: {bar} ({stats['completed']}/{stats['total']} days)")
        result_lines.append(f"  Created: {created}")
        result_lines.append("")

    return "\n".join(result_lines)


# ============================================================
# Tool 3: Get Progress on a Specific Plan
# ============================================================
@tool
def get_progress_tool(user_id: str) -> str:
    """
    Check progress on all study plans for a user.
    Use this when the user asks how they're doing, their completion percentage,
    or how much of their study plan they've finished.

    Args:
        user_id: The user's ID (lowercase name, e.g. "neha")

    Returns:
        A text summary of progress across all plans
    """
    plans = get_plans_by_user(user_id)

    if not plans:
        return "No study plans found. The user hasn't created any plans yet."

    result_lines = [f"Progress report for {len(plans)} plan(s):\n"]

    for i, p in enumerate(plans, 1):
        goal = p.get("goal", "Unknown")
        plan_data = p.get("plan", {})
        stats = calculate_progress(plan_data)
        bar = get_progress_bar(stats["percentage"], width=15)

        result_lines.append(f"Plan {i}: {goal}")
        result_lines.append(f"  {bar}  ({stats['completed']}/{stats['total']} days completed)")

        # Show which days are done/pending per week
        for week in plan_data.get("weekly_plan", []):
            week_num = week.get("week", "?")
            days = week.get("days", [])
            done_days = [d["day"] for d in days if d.get("completed", False)]
            pending_days = [d["day"] for d in days if not d.get("completed", False)]

            if done_days:
                result_lines.append(f"  Week {week_num} done: {', '.join(done_days)}")
            if pending_days:
                result_lines.append(f"  Week {week_num} pending: {', '.join(pending_days)}")

        result_lines.append("")

    return "\n".join(result_lines)


# ============================================================
# Collect all tools into a list
# ============================================================
def get_all_tools():
    """
    Returns a list of all tools the agent can use.
    Called by study_agent.py when building the agent.
    """
    return [
        get_search_tool(),
        get_user_plans_tool,
        get_progress_tool,
    ]
