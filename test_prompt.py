from prompts.planner_prompt import study_planner_template

formatted_prompt=study_planner_template.format(
    goal="Master UPSC Exam",
    skills="Basic geography,politics and history",
    time="8 hours a day"
)

print("-----FORMATTED PROMPT-----")
print(formatted_prompt)