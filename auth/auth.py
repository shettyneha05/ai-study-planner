"""
Auth — Authentication logic (register, login, verify)

This module handles the SECURITY LAYER for authentication.
It uses bcrypt for password hashing and user_store.py for database access.

Why bcrypt?
    - One-way hashing: password → hash (cannot reverse hash → password)
    - Built-in salt: gensalt() adds random bytes so identical passwords
      produce different hashes (prevents rainbow table attacks)
    - Slow by design: ~100ms per hash, making brute-force attacks impractical
    - Industry standard: used by GitHub, Dropbox, etc.

How password hashing works:
    REGISTER:
        "mypass123"  → bcrypt.hashpw()  → "$2b$12$xK9z..."
        (raw input)     (one-way hash)     (stored in MongoDB)

    LOGIN:
        "mypass123"  → bcrypt.checkpw(input, stored_hash) → True ✅
        "wrongpass"  → bcrypt.checkpw(input, stored_hash) → False ❌

Functions:
    register_user(username, password)  → Creates a new account
    login_user(username, password)     → Verifies credentials
    hash_password(password)            → Hashes a raw password
    verify_password(password, hash)    → Compares raw password with hash
"""

import bcrypt
from auth.user_store import create_user, find_user, username_exists


# ============================================================
# Password Hashing — Core security functions
# ============================================================
def hash_password(password: str) -> str:
    """
    Hashes a raw password using bcrypt.

    How it works:
        1. password.encode()  → converts string to bytes (bcrypt needs bytes)
        2. bcrypt.gensalt()   → generates a random salt (e.g., "$2b$12$xK...")
        3. bcrypt.hashpw()    → combines password + salt → produces hash

    The salt is embedded in the hash itself, so you don't need to store it separately.

    Args:
        password: The raw password string (e.g., "mypass123")

    Returns:
        str: The bcrypt hash string (e.g., "$2b$12$xK9z...")

    Example:
        hashed = hash_password("mypass123")
        # "$2b$12$LJ3m5..." — different every time because of random salt
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")  # Convert bytes back to string for MongoDB storage


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a raw password against a stored bcrypt hash.

    How it works:
        1. Encodes both the input password and stored hash to bytes
        2. bcrypt.checkpw() extracts the salt from the hash
        3. Hashes the input password with the SAME salt
        4. Compares the two hashes — if they match, password is correct

    Args:
        password:      The raw password the user typed (e.g., "mypass123")
        password_hash: The stored bcrypt hash from MongoDB

    Returns:
        bool: True if password matches, False if not

    Example:
        verify_password("mypass123", "$2b$12$LJ3m5...")  # True
        verify_password("wrongone", "$2b$12$LJ3m5...")   # False
    """
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


# ============================================================
# Register — Create a new user account
# ============================================================
def register_user(username: str, password: str) -> dict:
    """
    Registers a new user account.

    Flow:
        1. Normalize username (lowercase, strip spaces)
        2. Validate: username not empty, password not too short
        3. Check if username is already taken
        4. Hash the password with bcrypt
        5. Save to MongoDB via user_store.create_user()
        6. Return success with user_id

    Args:
        username: Desired username
        password: Desired password (will be hashed before storage)

    Returns:
        dict: {"success": True/False, "message": "...", "user_id": "..."}

    Examples:
        register_user("Neha", "mypass123")
        # {"success": True, "message": "Account created!", "user_id": "neha"}

        register_user("Neha", "mypass123")  # again
        # {"success": False, "message": "Username already taken"}
    """
    # Step 1: Normalize
    username = username.lower().strip()

    # Step 2: Validate
    if not username:
        return {"success": False, "message": "Username cannot be empty.", "user_id": None}

    if len(password) < 4:
        return {"success": False, "message": "Password must be at least 4 characters.", "user_id": None}

    # Step 3: Check for duplicates
    if username_exists(username):
        return {"success": False, "message": "Username already taken.", "user_id": None}

    # Step 4: Hash the password
    password_hash = hash_password(password)

    # Step 5: Save to MongoDB
    create_user(username, password_hash)

    # Step 6: Return success
    return {"success": True, "message": "Account created successfully!", "user_id": username}


# ============================================================
# Login — Verify credentials
# ============================================================
def login_user(username: str, password: str) -> dict:
    """
    Authenticates a user with username + password.

    Flow:
        1. Normalize username
        2. Look up user in MongoDB
        3. Not found → return failure
        4. Found → verify password with bcrypt
        5. Wrong password → return failure
        6. Correct → return success with user_id

    Args:
        username: The username
        password: The raw password to verify

    Returns:
        dict: {"success": True/False, "message": "...", "user_id": "..."}

    Security note:
        We return the SAME error message for "user not found" and "wrong password"
        to prevent username enumeration attacks (attacker can't tell if a username exists).
    """
    # Step 1: Normalize
    username = username.lower().strip()

    # Step 2: Look up user
    user = find_user(username)

    # Step 3-4: Verify (same message for both failures — security best practice)
    if not user:
        return {"success": False, "message": "Invalid username or password.", "user_id": None}

    if not verify_password(password, user["password_hash"]):
        return {"success": False, "message": "Invalid username or password.", "user_id": None}

    # Step 5: Success!
    return {"success": True, "message": f"Welcome back, {username}!", "user_id": username}
