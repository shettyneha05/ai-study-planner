"""
Session Store — Persistent session tokens in MongoDB

When a user logs in, we generate a random token, store it in MongoDB,
and set it as a browser cookie. On page refresh, the cookie is read
and validated against MongoDB to restore the session.

Flow:
    LOGIN   → create_session("neha") → token → MongoDB + cookie
    REFRESH → read cookie → validate_session(token) → returns "neha"
    LOGOUT  → delete_session(token) → removed from MongoDB + cookie
"""

import secrets
from datetime import datetime, timezone, timedelta
from memory.mongodb_client import get_database

SESSIONS_COLLECTION = "sessions"
SESSION_EXPIRY_DAYS = 30


def _get_sessions_collection():
    db = get_database()
    return db[SESSIONS_COLLECTION]


def create_session(user_id: str) -> str:
    """
    Creates a new session token for a user and stores it in MongoDB.

    Returns:
        str: A random 64-character hex token
    """
    collection = _get_sessions_collection()
    token = secrets.token_hex(32)

    collection.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS),
    })

    return token


def validate_session(token: str) -> str | None:
    """
    Validates a session token against MongoDB.

    Returns:
        str: user_id if token is valid and not expired, None otherwise
    """
    if not token:
        return None

    collection = _get_sessions_collection()
    session = collection.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })

    return session["user_id"] if session else None


def delete_session(token: str):
    """Deletes a session token from MongoDB (logout)."""
    if not token:
        return
    collection = _get_sessions_collection()
    collection.delete_one({"token": token})
