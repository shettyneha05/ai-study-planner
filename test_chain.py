"""
Test the complete Study Chain
This tests the full flow: Prompt → LLM → JSON Output
"""

from chains.study_chain import generate_study_plan
import json


def test_study_chain():
    print("🚀 Testing Study Planner Chain...")
    print("=" * 50)
    
    # Test inputs
    goal = "Master UPSC Exam"
    skills = "Basic geography, politics and history"
    time = "8 hours a day"
    
    print(f"📌 Goal: {goal}")
    print(f"📚 Skills: {skills}")
    print(f"⏰ Time: {time}")
    print("=" * 50)
    
    print("\n⏳ Generating study plan...\n")
    
    # Generate the plan
    result = generate_study_plan(goal, skills, time)
    
    # Pretty print the JSON result
    print("✅ Study Plan Generated!")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    
    # Validate the structure
    print("\n" + "=" * 50)
    print("🔍 Validating Output Structure:")
    
    required_keys = ["goal", "total_weeks", "weekly_plan", "tips"]
    for key in required_keys:
        if key in result:
            print(f"  ✅ '{key}' present")
        else:
            print(f"  ❌ '{key}' missing")
    
    # Check if it's actually a dict (parsed JSON)
    print(f"\n📦 Output Type: {type(result)}")
    print(f"✅ Successfully parsed to Python dict: {isinstance(result, dict)}")


if __name__ == "__main__":
    test_study_chain()
