"""
User Store — MongoDB collection for user accounts

This module handles the DATABASE LAYER for authentication.
It talks directly to MongoDB's "users" collection.

What it does:
    - Create a new user document
    - Find a user by username
    - Check if a username is already taken

What it does NOT do:
    - Password hashing    → that's auth.py's job
    - Login validation    → that's auth.py's job
    - CLI interaction     → that's main.py's job

This separation keeps things clean:
    user_store.py = "talk to the database"
    auth.py       = "handle security logic"
    main.py       = "handle user interaction"

MongoDB Document Structure:
    {
        "_id": ObjectId("..."),
        "username": "neha",                      # unique, always lowercase
        "password_hash": "$2b$12$xK9z...",       # bcrypt hash, NEVER raw password
        "created_at": "2026-03-09T10:30:00+00:00"
    }
"""

from datetime import datetime, timezone
from memory.mongodb_client import get_database


# ============================================================
# Constants
# ============================================================
USERS_COLLECTION = "users"


# ============================================================
# Get the users collection
# ============================================================
def get_users_collection():
    """
    Returns the MongoDB 'users' collection.
    Creates the collection automatically if it doesn't exist
    (MongoDB creates collections on first insert).
    """
    db = get_database()
    return db[USERS_COLLECTION]


# ============================================================
# Create a new user document
# ============================================================
def create_user(username: str, password_hash: str) -> str:
    """
    Inserts a new user into the 'users' collection.

    Args:
        username:      The username (already lowercased by auth.py)
        password_hash: The bcrypt hash of their password (NOT the raw password)

    Returns:
        str: The MongoDB _id of the new user document

    Note:
        This function does NOT check for duplicates — auth.py does that
        before calling this function.
    """
    collection = get_users_collection()

    document = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
    }

    result = collection.insert_one(document)
    return str(result.inserted_id)


# ============================================================
# Find a user by username
# ============================================================
def find_user(username: str) -> dict | None:
    """
    Looks up a user by their username.

    Args:
        username: The username to search for (lowercase)

    Returns:
        dict: The user document if found, None if not found

    Example:
        user = find_user("neha")
        if user:
            print(user["password_hash"])  # "$2b$12$..."
        else:
            print("User not found")
    """
    collection = get_users_collection()
    document = collection.find_one({"username": username})

    if document:
        document["_id"] = str(document["_id"])

    return document


# ============================================================
# Check if a username already exists
# ============================================================
def username_exists(username: str) -> bool:
    """
    Returns True if the username is already taken.

    Used during registration to prevent duplicate accounts.

    Args:
        username: The username to check (lowercase)

    Returns:
        bool: True if taken, False if available
    """
    return find_user(username) is not None
