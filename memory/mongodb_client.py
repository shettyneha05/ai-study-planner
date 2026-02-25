"""
MongoDB Client - Connection utility for the AI Study Planner

This module handles:
1. Loading the MONGODB_URI from .env
2. Creating a MongoClient connection
3. Providing access to the database and collections

MongoDB Hierarchy:
    Cluster → Database → Collection → Document
    (server)   (folder)   (table)      (row/JSON object)

Our structure:
    Cluster → ai_study_planner (database)
        ├── chat_history  (collection) - stores conversation messages
        └── study_plans   (collection) - stores generated study plans
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Load environment variables
load_dotenv()

# ============================================================
# MongoDB Configuration Constants
# ============================================================
DATABASE_NAME = "ai_study_planner"
CHAT_HISTORY_COLLECTION = "chat_history"
STUDY_PLANS_COLLECTION = "study_plans"


# ============================================================
# Connection: Create MongoClient
# ============================================================
def get_mongo_client() -> MongoClient:
    """
    Creates and returns a MongoClient instance.
    
    MongoClient is the entry point for all MongoDB operations.
    Think of it as: "Open a connection to my MongoDB server"
    
    Returns:
        MongoClient: A connected MongoDB client
    
    Raises:
        ValueError: If MONGODB_URI is not found in .env
    """
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError(
            "MONGODB_URI not found in environment variables. "
            "Add it to your .env file like:\n"
            "MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/"
        )

    # Create the client with SSL certificate bundle for Atlas
    client = MongoClient(mongodb_uri)
    return client #returning a client for this uri , a python class directly communicationg with the mongodb server, we can use this client to access databases and collections


# ============================================================
# Database: Get the main database
# ============================================================
def get_database():
    """
    Returns the 'ai_study_planner' database.
    
    A database is a container for collections (like a folder for tables).
    If the database doesn't exist yet, MongoDB creates it automatically
    when you first insert data.
    
    Returns:
        Database: The ai_study_planner database object
    """
    client = get_mongo_client()
    return client[DATABASE_NAME]


# ============================================================
# Collections: Get specific collections
# ============================================================
def get_chat_history_collection():
    """
    Returns the 'chat_history' collection.
    
    This collection stores conversation messages (human & AI)
    so the LLM can remember past interactions.
    
    Document structure:
        {
            "session_id": "user_abc_1708000000",
            "role": "human" | "ai",
            "content": "I want to learn Python",
            "timestamp": datetime
        }
    """
    db = get_database() #get this database
    return db[CHAT_HISTORY_COLLECTION] #get this collection from the database


def get_study_plans_collection():
    """
    Returns the 'study_plans' collection.
    
    This collection stores generated study plans
    so users can retrieve/update them later.
    
    Document structure:
        {
            "user_id": "user_abc",
            "goal": "Learn Python",
            "plan": { ... full study plan dict ... },
            "created_at": datetime
        }
    """
    db = get_database()
    return db[STUDY_PLANS_COLLECTION]