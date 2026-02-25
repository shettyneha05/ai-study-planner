# 🤖 AI Study Planner - LangChain + Gemini

## 📌 Project Overview
This project is a beginner-friendly implementation of **LangChain** integrated with **Google Gemini**.
The goal is to build an **AI-powered Study Planner** that generates personalized weekly study plans.

### ✅ What's Implemented
- ✅ **Step 1**: LLM Setup with Gemini
- ✅ **Step 2**: Prompt Engineering with LangChain
  - Structured `PromptTemplate` with input variables
  - JSON output formatting for predictable responses
  - Study chain connecting Prompt → LLM → JSON Parser
- ✅ **Step 3**: MongoDB Long-Term Memory Setup
  - MongoDB Atlas connection with SSL support
  - Database & collection utilities for `chat_history` and `study_plans`

---

## 🛠 Tech Stack
- **Python 3.x**
- **LangChain** – LLM orchestration framework
- **Google Gemini** – Large Language Model (gemini-2.5-flash)
- **MongoDB Atlas** – Cloud database for long-term memory
- **pymongo** – Python MongoDB driver
- **python-dotenv** – Environment variable management
- **Git & GitHub** – Version control and collaboration

---

## 📂 Project Structure

```
ai-study-planner/
├── .env                    # API keys (NOT pushed to git)
├── .gitignore              # Files to ignore
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── llm/
│   └── gemini_llm.py       # Gemini LLM configuration
│
├── prompts/
│   └── planner_prompt.py   # PromptTemplate for study planning
│
├── chains/
│   └── study_chain.py      # Chain: Prompt → LLM → JSON Parser
│
├── memory/
│   └── mongodb_client.py   # MongoDB connection utility
├── agent/                  # (Coming soon) AI Agent logic
├── ui/                     # (Coming soon) User interface
│
└── tests/
    ├── test_llm.py         # Test LLM connection
    ├── test_prompt.py      # Test prompt formatting
    └── test_chain.py       # Test full chain
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/nehaaa-k/AI-Study-Planner.git
cd ai-study-planner
