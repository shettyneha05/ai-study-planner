"""
Test Auth — Tests for authentication (register, login, password hashing)

Tests:
    1. hash_password — produces a hash, not the original
    2. verify_password — correct password matches, wrong one doesn't
    3. register_user — creates account, prevents duplicates
    4. login_user — correct credentials pass, wrong ones fail
    5. MongoDB integration — full round-trip (register → login → verify)

Run:
    python test_auth.py          → Fast tests (no MongoDB)
    python test_auth.py --all    → All tests (includes MongoDB)
"""

import sys
from auth.auth import hash_password, verify_password, register_user, login_user
from auth.user_store import find_user, get_users_collection


# ============================================================
# Test 1: Password hashing
# ============================================================
def test_hash_password():
    """Hash should be different from the original password."""
    password = "testpass123"
    hashed = hash_password(password)

    assert hashed != password, "Hash should NOT equal raw password"
    assert hashed.startswith("$2b$"), "Should be a bcrypt hash (starts with $2b$)"
    assert len(hashed) == 60, "bcrypt hash is always 60 characters"

    # Hashing same password twice should produce different hashes (random salt)
    hashed2 = hash_password(password)
    assert hashed != hashed2, "Two hashes of same password should differ (random salt)"

    print("✅ hash_password — produces bcrypt hash, different each time")


# ============================================================
# Test 2: Password verification
# ============================================================
def test_verify_password():
    """Correct password should verify, wrong one should not."""
    password = "mypassword"
    hashed = hash_password(password)

    assert verify_password("mypassword", hashed) is True, "Correct password should verify"
    assert verify_password("wrongpass", hashed) is False, "Wrong password should fail"
    assert verify_password("", hashed) is False, "Empty password should fail"

    print("✅ verify_password — correct passes, wrong fails")


# ============================================================
# Test 3: Register + Login (MongoDB)
# ============================================================
def test_register_and_login():
    """Full round-trip: register a user, then login with correct/wrong credentials."""
    test_username = "__test_auth_user__"
    test_password = "testpass123"

    # Clean up any leftover test user
    collection = get_users_collection()
    collection.delete_many({"username": test_username})

    # ---- Register ----
    result = register_user(test_username, test_password)
    assert result["success"] is True, f"Registration should succeed: {result['message']}"
    assert result["user_id"] == test_username
    print(f"   Registered: {test_username}")

    # ---- Duplicate registration should fail ----
    result2 = register_user(test_username, test_password)
    assert result2["success"] is False, "Duplicate registration should fail"
    assert "already taken" in result2["message"].lower()
    print("   Duplicate blocked ✓")

    # ---- Login with correct password ----
    login_result = login_user(test_username, test_password)
    assert login_result["success"] is True, f"Login should succeed: {login_result['message']}"
    assert login_result["user_id"] == test_username
    print("   Login with correct password ✓")

    # ---- Login with wrong password ----
    wrong_result = login_user(test_username, "wrongpassword")
    assert wrong_result["success"] is False, "Wrong password should fail"
    print("   Wrong password rejected ✓")

    # ---- Login with non-existent user ----
    nouser_result = login_user("__nonexistent__", "anything")
    assert nouser_result["success"] is False, "Non-existent user should fail"
    print("   Non-existent user rejected ✓")

    # ---- Verify user exists in MongoDB ----
    user = find_user(test_username)
    assert user is not None, "User should exist in MongoDB"
    assert user["username"] == test_username
    assert user["password_hash"].startswith("$2b$"), "Stored hash should be bcrypt"
    print("   User verified in MongoDB ✓")

    # ---- Clean up ----
    collection.delete_many({"username": test_username})
    print("✅ register + login — full round-trip works")


# ============================================================
# Test 4: Validation
# ============================================================
def test_validation():
    """Registration should reject empty username and short passwords."""
    result1 = register_user("", "password")
    assert result1["success"] is False, "Empty username should fail"

    result2 = register_user("someuser", "ab")
    assert result2["success"] is False, "Short password should fail"

    print("✅ validation — empty username and short password rejected")


# ============================================================
# Run tests
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Authentication Tests")
    print("=" * 50)

    # Fast tests (no MongoDB)
    test_hash_password()
    test_verify_password()

    # MongoDB tests (only with --all)
    if "--all" in sys.argv:
        print("\n--- MongoDB Integration Tests ---")
        test_validation()
        test_register_and_login()
    else:
        print("\n⏩ Skipping MongoDB tests. Run with --all to include them.")

    print("\n" + "=" * 50)
    print("🎉 All auth tests PASSED!")
    print("=" * 50)
