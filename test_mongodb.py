"""
Test MongoDB Connection
Run this to verify your MongoDB connection is working properly.

What this test does:
1. Connects to MongoDB using your URI
2. Pings the server (like saying "hello, are you there?")
3. Lists existing databases
4. Verifies we can access our collections
"""

from memory.mongodb_client import (
    get_mongo_client,
    get_database,
    get_chat_history_collection,
    get_study_plans_collection,
    DATABASE_NAME
)


def test_connection():
    print("🔌 Testing MongoDB Connection...")
    print("=" * 50)

    # Step 1: Test basic connection with a ping
    try:
        client = get_mongo_client()
        client.admin.command("ping")  # Sends a ping to the server
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Step 2: List databases on the cluster
    print("\n📂 Databases on your cluster:")
    for db_name in client.list_database_names():
        print(f"   - {db_name}")

    # Step 3: Access our database
    db = get_database()
    print(f"\n🗄️  Using database: '{DATABASE_NAME}'")

    # Step 4: Access collections
    chat_col = get_chat_history_collection()
    plans_col = get_study_plans_collection()
    print(f"📋 Chat history collection: '{chat_col.name}'")
    print(f"📋 Study plans collection: '{plans_col.name}'")

    # Step 5: Quick write/read test
    print("\n🧪 Quick write/read test...")
    test_doc = {"test": True, "message": "Hello from AI Study Planner!"}
    
    # Insert a test document
    result = chat_col.insert_one(test_doc)
    print(f"   ✅ Inserted test document (ID: {result.inserted_id})")

    # Read it back
    found = chat_col.find_one({"_id": result.inserted_id})
    print(f"   ✅ Read back: {found['message']}")

    # Clean up - delete the test document
    chat_col.delete_one({"_id": result.inserted_id})
    print(f"   ✅ Cleaned up test document")

    print("\n" + "=" * 50)
    print("🎉 All tests passed! MongoDB is ready to use.")


if __name__ == "__main__":
    test_connection()
