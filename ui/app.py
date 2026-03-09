"""
AI Study Planner — Streamlit Web UI

Pages:
    1. Login / Register
    2. Dashboard (plans overview + progress)
    3. Generate Plan (form → result)
    4. Plan Detail (expand plan, mark days, resources)
    5. Agent Chat (conversational AI assistant)
"""

import sys
import os

# Add project root to path so imports work when running from ui/ folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth.auth import register_user, login_user
from chains.study_chain import generate_study_plan_with_memory
from memory.plan_store import get_plans_by_user, get_study_plan, delete_study_plan
from memory.chat_memory import clear_chat_history, get_message_count, get_last_goals
from memory.progress_store import (
    mark_day_completed,
    calculate_progress,
    get_plan_progress,
)
from agent.study_agent import create_study_agent, chat_with_agent


# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="AI Study Planner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Custom CSS — Dark theme styling
# ============================================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* Cards */
    .plan-card {
        background: rgba(30, 30, 60, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: border-color 0.3s;
    }
    .plan-card:hover {
        border-color: rgba(99, 102, 241, 0.7);
    }

    /* Progress bar container */
    .progress-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
        height: 12px;
        margin: 0.5rem 0;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        transition: width 0.5s ease;
    }

    /* Day card */
    .day-card {
        background: rgba(30, 30, 60, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .day-card.completed {
        border-color: rgba(34, 197, 94, 0.5);
        background: rgba(34, 197, 94, 0.08);
    }

    /* Status badge */
    .badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-done {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }
    .badge-pending {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
    }

    /* Chat bubbles */
    .chat-user {
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px 12px 4px 12px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        margin-left: 20%;
    }
    .chat-ai {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px 12px 12px 4px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        margin-right: 20%;
    }

    /* Auth container */
    .auth-container {
        max-width: 420px;
        margin: 4rem auto;
        padding: 2rem;
        background: rgba(30, 30, 60, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
    }

    /* Metric styling */
    .metric-card {
        background: rgba(30, 30, 60, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #a855f7;
    }
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.25rem;
    }

    /* Subtle divider */
    .divider {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin: 1.5rem 0;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# Session State Defaults
# ============================================================
def init_session_state():
    defaults = {
        "user_id": None,
        "session_id": None,
        "page": "auth",
        "agent": None,
        "chat_messages": [],
        "selected_plan_id": None,
        "generating": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ============================================================
# Auth Page — Login / Register
# ============================================================
def render_auth_page():
    st.markdown("<div style='text-align:center; margin-top:2rem;'>", unsafe_allow_html=True)
    st.markdown("# 🎓 AI Study Planner")
    st.markdown("*Your personal AI-powered learning companion*")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    else:
                        result = login_user(username, password)
                        if result["success"]:
                            st.session_state.user_id = result["user_id"]
                            st.session_state.session_id = result["user_id"]
                            st.session_state.page = "dashboard"
                            st.rerun()
                        else:
                            st.error(result["message"])

        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Pick a username")
                new_password = st.text_input("Choose a password", type="password", placeholder="Min 4 characters")
                confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    if not new_username or not new_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        result = register_user(new_username, new_password)
                        if result["success"]:
                            st.session_state.user_id = result["user_id"]
                            st.session_state.session_id = result["user_id"]
                            st.session_state.page = "dashboard"
                            st.rerun()
                        else:
                            st.error(result["message"])


# ============================================================
# Sidebar — Navigation
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎓 AI Study Planner")
        st.markdown(f"**👤 {st.session_state.user_id}**")
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        if st.button("📊  Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.selected_plan_id = None
            st.rerun()

        if st.button("📝  Generate Plan", use_container_width=True):
            st.session_state.page = "generate"
            st.rerun()

        if st.button("🤖  AI Agent Chat", use_container_width=True):
            st.session_state.page = "agent_chat"
            st.rerun()

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # Session info
        msg_count = get_message_count(st.session_state.session_id)
        st.caption(f"💬 {msg_count} messages in memory")

        if st.button("🗑️  Clear Chat History", use_container_width=True):
            clear_chat_history(st.session_state.session_id)
            st.session_state.chat_messages = []
            st.session_state.agent = None
            st.toast("Chat history cleared!", icon="🗑️")
            st.rerun()

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        if st.button("🚪  Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ============================================================
# Dashboard Page
# ============================================================
def render_dashboard():
    st.markdown("## 📊 Dashboard")

    plans = get_plans_by_user(st.session_state.user_id)

    # Metrics row
    total_plans = len(plans)
    total_days = 0
    completed_days = 0
    for p in plans:
        stats = calculate_progress(p.get("plan", {}))
        total_days += stats["total"]
        completed_days += stats["completed"]

    overall_pct = (completed_days / total_days * 100) if total_days > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_plans}</div>
            <div class="metric-label">Study Plans</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{completed_days}/{total_days}</div>
            <div class="metric-label">Days Completed</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{overall_pct:.0f}%</div>
            <div class="metric-label">Overall Progress</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent goals
    past_goals = get_last_goals(st.session_state.session_id)
    if past_goals:
        st.markdown("**🎯 Recent Goals:** " + " · ".join(f"`{g}`" for g in past_goals))
        st.markdown("<br>", unsafe_allow_html=True)

    # Plans list
    if not plans:
        st.info("No study plans yet! Click **Generate Plan** in the sidebar to create your first one.")
        return

    st.markdown("### 📋 Your Study Plans")

    for p in plans:
        plan_data = p.get("plan", {})
        stats = calculate_progress(plan_data)
        pct = stats["percentage"]

        col_info, col_action = st.columns([4, 1])
        with col_info:
            st.markdown(f"""
            <div class="plan-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="font-size:1.1rem;">📌 {p.get('goal', 'N/A')}</strong><br>
                        <span style="color:rgba(255,255,255,0.5); font-size:0.85rem;">
                            {plan_data.get('total_weeks', '?')} weeks · {stats['total']} days · Skills: {p.get('skills', 'N/A')}
                        </span>
                    </div>
                    <div style="text-align:right; min-width:80px;">
                        <span style="font-size:1.3rem; font-weight:700; color:#a855f7;">{pct:.0f}%</span>
                    </div>
                </div>
                <div class="progress-container" style="margin-top:0.6rem;">
                    <div class="progress-fill" style="width:{pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_action:
            st.markdown("<div style='padding-top:1rem;'>", unsafe_allow_html=True)
            if st.button("View →", key=f"view_{p['_id']}", use_container_width=True):
                st.session_state.selected_plan_id = p["_id"]
                st.session_state.page = "plan_detail"
                st.rerun()
            if st.button("🗑️", key=f"del_{p['_id']}"):
                delete_study_plan(p["_id"])
                st.toast("Plan deleted!", icon="🗑️")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# Generate Plan Page
# ============================================================
def render_generate_plan():
    st.markdown("## 📝 Generate a Study Plan")
    st.markdown("*Tell us what you want to learn and we'll create a personalized plan.*")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("generate_form"):
            goal = st.text_input(
                "🎯 What do you want to learn?",
                placeholder="e.g., Learn React.js, Master Machine Learning",
            )
            skills = st.text_area(
                "📚 What are your current skills?",
                placeholder="e.g., I know basic HTML/CSS, some Python experience",
                height=100,
            )
            time_available = st.text_input(
                "⏰ How many hours per week can you study?",
                placeholder="e.g., 10 hours per week, 14 hours per week",
            )
            submitted = st.form_submit_button("🚀 Generate Plan", use_container_width=True)

        if submitted:
            if not goal:
                st.error("Please enter a learning goal.")
            else:
                skills = skills or "No prior experience"
                time_available = time_available or "2 hours a day"

                with st.spinner("✨ Generating your personalized study plan... (20-40 seconds)"):
                    try:
                        plan = generate_study_plan_with_memory(
                            goal=goal,
                            skills=skills,
                            time=time_available,
                            session_id=st.session_state.session_id,
                            user_id=st.session_state.user_id,
                        )
                        st.success(f"Study plan generated! Plan ID: `{plan.get('plan_id', 'N/A')}`")
                        st.session_state.selected_plan_id = plan.get("plan_id")
                        st.session_state.page = "plan_detail"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating plan: {e}")

    with col2:
        st.markdown("""
        <div class="plan-card">
            <strong>💡 Tips for better plans</strong><br><br>
            <span style="color:rgba(255,255,255,0.7); font-size:0.9rem;">
            • Be specific about your goal<br>
            • Mention your current level<br>
            • Specify realistic daily time<br>
            • Plans cover up to 2 weeks<br>
            • Mon-Fri schedule (weekdays)
            </span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# Plan Detail Page
# ============================================================
def render_plan_detail():
    plan_id = st.session_state.selected_plan_id
    if not plan_id:
        st.warning("No plan selected.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    doc = get_study_plan(plan_id)
    if not doc:
        st.error("Plan not found. It may have been deleted.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    plan = doc["plan"]
    stats = calculate_progress(plan)

    # Header
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.session_state.selected_plan_id = None
            st.rerun()
    with col_title:
        st.markdown(f"## 📌 {plan.get('goal', doc.get('goal', 'Study Plan'))}")

    # Progress overview
    pct = stats["percentage"]
    st.markdown(f"""
    <div class="plan-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.95rem;">📊 Progress: <strong>{stats['completed']}/{stats['total']}</strong> days completed</span>
            <span style="font-size:1.5rem; font-weight:700; color:#a855f7;">{pct:.0f}%</span>
        </div>
        <div class="progress-container" style="margin-top:0.5rem;">
            <div class="progress-fill" style="width:{pct}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex; gap:1rem; margin:0.8rem 0;">
        <span style="color:rgba(255,255,255,0.6);">📅 {plan.get('total_weeks', '?')} weeks</span>
        <span style="color:rgba(255,255,255,0.6);">📚 Skills: {doc.get('skills', 'N/A')}</span>
        <span style="color:rgba(255,255,255,0.6);">⏰ Time: {doc.get('time', 'N/A')}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Weekly plan
    weekly_plan = plan.get("weekly_plan", [])
    for week in weekly_plan:
        week_num = week.get("week", "?")
        theme = week.get("theme", "")
        days = week.get("days", [])
        week_done = sum(1 for d in days if d.get("completed", False))
        week_total = len(days)

        with st.expander(f"📖 Week {week_num}: {theme}  ({week_done}/{week_total} done)", expanded=True):
            for day in days:
                is_done = day.get("completed", False)
                day_name = day.get("day", "?")
                topic = day.get("topic", "N/A")
                duration = day.get("duration_hours", "?")
                resources = day.get("resources", [])
                tasks = day.get("tasks", [])

                card_class = "day-card completed" if is_done else "day-card"
                status_badge = '<span class="badge badge-done">✅ Done</span>' if is_done else '<span class="badge badge-pending">⬜ Pending</span>'

                # Day header + info
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{day_name}</strong>
                        {status_badge}
                    </div>
                    <div style="margin-top:0.4rem; color:rgba(255,255,255,0.8);">
                        📝 <strong>{topic}</strong> · ⏱️ {duration}h
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Resources & tasks
                detail_col, action_col = st.columns([4, 1])
                with detail_col:
                    if resources:
                        st.markdown("**📎 Resources:** " + " · ".join(f"`{r}`" for r in resources))
                    if tasks:
                        for task in tasks:
                            st.markdown(f"  - {task}")
                with action_col:
                    if not is_done:
                        if st.button("Mark Done ✓", key=f"done_{plan_id}_{week_num}_{day_name}"):
                            mark_day_completed(plan_id, week_num, day_name)
                            st.toast(f"✅ {day_name} marked as done!", icon="🎉")
                            st.rerun()

                st.markdown("---")

    # Tips
    tips = plan.get("tips", [])
    if tips:
        st.markdown("### 💡 Tips")
        for tip in tips:
            st.markdown(f"- {tip}")


# ============================================================
# Agent Chat Page
# ============================================================
def render_agent_chat():
    st.markdown("## 🤖 AI Agent Chat")
    st.markdown("*Ask anything — I can search the web, check your plans, and give study advice.*")
    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize agent if needed
    if st.session_state.agent is None:
        with st.spinner("Initializing AI agent..."):
            st.session_state.agent = create_study_agent(st.session_state.user_id)

    # Chat display area
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="chat-ai">
                👋 Hi! I'm your AI study assistant. I can:<br>
                • 🔍 Search the web for learning resources<br>
                • 📋 Check your study plans and progress<br>
                • 💡 Give personalized study advice<br><br>
                What would you like to know?
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Type your message...")

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        # Get agent response
        with st.spinner("🤔 Thinking..."):
            try:
                response = chat_with_agent(
                    st.session_state.agent,
                    user_input,
                    st.session_state.session_id,
                )
            except Exception as e:
                response = f"Sorry, an error occurred: {e}"

        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()


# ============================================================
# Main Router
# ============================================================
def main():
    if st.session_state.user_id is None:
        render_auth_page()
    else:
        render_sidebar()

        page = st.session_state.page
        if page == "dashboard":
            render_dashboard()
        elif page == "generate":
            render_generate_plan()
        elif page == "plan_detail":
            render_plan_detail()
        elif page == "agent_chat":
            render_agent_chat()
        else:
            render_dashboard()


if __name__ == "__main__":
    main()
