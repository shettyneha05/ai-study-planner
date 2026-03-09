"""
Plan Store - CRUD operations for study plans in MongoDB

This module handles saving, retrieving, updating, and deleting
study plans in the 'study_plans' collection.

Unlike chat_memory.py (which uses LangChain's built-in classes),
this is a CUSTOM layer using plain pymongo — you control everything.

CRUD Operations:
    C - Create  → save_study_plan()      → insert_one()
    R - Read    → get_study_plan()       → find_one()
                  get_plans_by_user()    → find()
    U - Update  → update_study_plan()    → update_one()
    D - Delete  → delete_study_plan()    → delete_one()

Document Structure in MongoDB:
    {
        "_id": ObjectId("..."),           # Auto-generated unique ID
        "user_id": "neha",                # Who this plan belongs to
        "session_id": "neha_1709308800",  # Which conversation created it
        "goal": "Learn Python",           # Original user input
        "skills": "No experience",        # Original user input
        "time": "2 hours a day",          # Original user input
        "plan": { ... },                  # The full study plan dict from Gemini
        "created_at": datetime,           # When the plan was first created
        "updated_at": datetime            # When the plan was last modified
    }
"""

from datetime import datetime, timezone
from bson import ObjectId
from memory.mongodb_client import get_study_plans_collection


# ============================================================
# CREATE — Save a new study plan
# ============================================================
def save_study_plan(user_id: str, session_id: str, goal: str, skills: str, time: str, plan: dict) -> str:
    """
    Saves a generated study plan to MongoDB.
    
    How it works:
        1. Builds a document (Python dict) with all the plan data
        2. Adds timestamps (created_at, updated_at)
        3. Calls insert_one() to save it to MongoDB
        4. Returns the _id of the new document (as a string)
    
    Args:
        user_id:    Who this plan belongs to ("neha")
        session_id: Which conversation created it ("neha_1709308800")
        goal:       The learning goal ("Learn Python basics")
        skills:     Current skills ("No experience")
        time:       Available time ("2 hours a day")
        plan:       The full study plan dict returned by Gemini
    
    Returns:
        str: The MongoDB _id of the saved document
    
    Example:
        plan_id = save_study_plan(
            user_id="neha",
            session_id="neha_session_1",
            goal="Learn Python",
            skills="No experience",
            time="2 hours a day",
            plan={"goal": "Learn Python", "total_weeks": 2, ...}
        )
        print(plan_id)  # "65f1a2b3c4d5e6f7a8b9c0d1"
    """
    collection = get_study_plans_collection() #study plans collection in mongodb
    
    # Build the document to insert
    document = {
        "user_id": user_id,
        "session_id": session_id,
        "goal": goal,
        "skills": skills,
        "time": time,
        "plan": plan,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    # insert_one() saves the document and returns an InsertOneResult
    # .inserted_id gives us the auto-generated _id (ObjectId)
    result = collection.insert_one(document)
    
    # Convert ObjectId to string for easy use in Python
    return str(result.inserted_id)


# ============================================================
# READ — Get a single plan by its _id
# ============================================================
def get_study_plan(plan_id: str) -> dict | None:
    """
    Retrieves a single study plan by its MongoDB _id.
    
    How it works:
        1. Converts the string plan_id to an ObjectId
        2. Calls find_one() to search by _id
        3. Returns the document as a Python dict (or None if not found)
    
    Args:
        plan_id: The _id string returned by save_study_plan()
    
    Returns:
        dict: The plan document, or None if not found
    
    Example:
        plan = get_study_plan("65f1a2b3c4d5e6f7a8b9c0d1")
        print(plan["goal"])        # "Learn Python"
        print(plan["plan"])        # The full study plan dict
    """
    collection = get_study_plans_collection()
    
    # find_one() returns the first document matching the filter
    # We use _id (the unique identifier) to find an exact plan
    document = collection.find_one({"_id": ObjectId(plan_id)})
    
    if document:
        # Convert ObjectId to string so it's JSON-serializable
        document["_id"] = str(document["_id"])
    
    return document


# ============================================================
# READ — Get all plans for a specific user
# ============================================================
def get_plans_by_user(user_id: str) -> list[dict]:
    """
    Retrieves ALL study plans belonging to a user.
    
    How it works:
        1. Calls find() with a filter on user_id
        2. Sorts by created_at (newest first)
        3. Returns a list of plan documents
    
    Args:
        user_id: The user whose plans to retrieve
    
    Returns:
        list[dict]: List of plan documents (empty list if none found)
    
    Example:
        plans = get_plans_by_user("neha")
        print(f"Neha has {len(plans)} study plans")
        for plan in plans:
            print(f"  - {plan['goal']} (created {plan['created_at']})")
    """
    collection = get_study_plans_collection()
    
    # find() returns a Cursor — like a lazy list of matching documents
    # .sort() orders them: -1 = descending (newest first)
    cursor = collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1)
    
    # Convert cursor to list, and make _id a string in each document
    plans = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        plans.append(doc)
    
    return plans


# ============================================================
# UPDATE — Modify an existing plan
# ============================================================
def update_study_plan(plan_id: str, updated_plan: dict) -> bool:
    """
    Updates the study plan content for an existing document.
    
    How it works:
        1. Uses update_one() with the $set operator
        2. $set replaces only the specified fields (doesn't touch others)
        3. Also updates the updated_at timestamp
        4. Returns True if a document was modified, False if not found
    
    Args:
        plan_id:      The _id of the plan to update
        updated_plan: The new plan dict (replaces the old one)
    
    Returns:
        bool: True if plan was found and updated, False otherwise
    
    Example:
        # User asks to regenerate their plan
        new_plan = generate_study_plan("Learn Python", "Knows basics", "3 hours")
        success = update_study_plan("65f1a2b3c4d5e6f7a8b9c0d1", new_plan)
        print(success)  # True
    """
    collection = get_study_plans_collection()
    
    # update_one() takes:
    #   - filter: which document to update (by _id)
    #   - update: what to change ($set replaces specific fields)
    result = collection.update_one(
        {"_id": ObjectId(plan_id)},         # Filter: find this document
        {
            "$set": {                        # $set: only change these fields
                "plan": updated_plan,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # modified_count = 1 if something was changed, 0 if not found
    return result.modified_count > 0


# ============================================================
# DELETE — Remove a plan
# ============================================================
def delete_study_plan(plan_id: str) -> bool:
    """
    Deletes a study plan from MongoDB.
    
    How it works:
        1. Calls delete_one() with a filter on _id
        2. Returns True if a document was deleted, False if not found
    
    Args:
        plan_id: The _id of the plan to delete
    
    Returns:
        bool: True if plan was found and deleted, False otherwise
    
    Example:
        success = delete_study_plan("65f1a2b3c4d5e6f7a8b9c0d1")
        print(success)  # True
    """
    collection = get_study_plans_collection()
    
    result = collection.delete_one({"_id": ObjectId(plan_id)})
    
    # deleted_count = 1 if something was removed, 0 if not found
    return result.deleted_count > 0
