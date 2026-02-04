import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env
load_dotenv()

def get_gemini_llm():
    """
    Initializes and returns a Gemini LLM using LangChain.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    print(api_key)

    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )

    return llm
