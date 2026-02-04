"""
Study Chain - Connects Prompt Template with LLM and Output Parser

LangChain Concepts Used:
1. LLMChain (or LCEL) - Chains prompt → LLM → parser
2. JsonOutputParser - Parses LLM output into Python dict
3. RunnableSequence - Modern way to chain components
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.planner_prompt import study_planner_template
from llm.gemini_llm import get_gemini_llm


def create_study_chain():
    """
    Creates a chain that:
    1. Takes user input (goal, skills, time)
    2. Formats it into our prompt template
    3. Sends to Gemini LLM
    4. Parses the JSON response
    
    Returns:
        RunnableSequence: A chain that can be invoked with input variables
    """
    
    # Get the LLM
    llm = get_gemini_llm()
    
    # Create JSON output parser for clean structured output
    json_parser = JsonOutputParser()
    
    # Create the chain using LCEL (LangChain Expression Language)
    # This is the modern way: prompt | llm | parser
    chain = study_planner_template | llm | json_parser
    
    return chain


def generate_study_plan(goal: str, skills: str, time: str) -> dict:
    """
    High-level function to generate a study plan.
    
    Args:
        goal: The learning goal (e.g., "Master UPSC Exam")
        skills: Current skills (e.g., "Basic geography, politics and history")
        time: Available time (e.g., "8 hours a day")
    
    Returns:
        dict: Structured study plan as a Python dictionary
    """
    
    # Create the chain
    chain = create_study_chain()
    
    # Invoke the chain with our input variables
    result = chain.invoke({
        "goal": goal,
        "skills": skills,
        "time": time
    })
    
    return result
