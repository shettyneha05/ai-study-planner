from langchain_core.prompts import PromptTemplate

study_planner_template = PromptTemplate(
    input_variables=["goal","skills","time"],
    template="""
You are an AI study planner. Given the user's learning goal, current skills, and available time, create a detailed weekly study plan.
📌Goal: {goal}
📚Current Skills: {skills}
⏰Available Time (hours per week): {time}
IMPORTANT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no extra text.

Use this EXACT JSON structure:
{{
    "goal": "the user's goal",
    "total_weeks": <number>,
    "weekly_plan": [
        {{
            "week": 1,
            "theme": "Week theme",
            "days": [
                {{
                    "day": "Monday",
                    "topic": "Topic to study",
                    "duration_hours": <number>,
                    "resources": ["resource1", "resource2"],
                    "tasks": ["task1", "task2"]
                }}
            ]
        }}
    ],
    "tips": ["tip1", "tip2"]
}}
IMPORTANT: Keep the plan to a maximum of 2 weeks. Only include 5 days per week (Monday to Friday).
Respond with ONLY the JSON object. No other text before or after.
"""
)
