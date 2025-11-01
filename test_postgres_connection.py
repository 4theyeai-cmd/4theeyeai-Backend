import os
from dotenv import load_dotenv
from api.database.database import engine, get_db
from sqlalchemy import text

# Load environment variables
load_dotenv()


def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        # Test engine connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL connection successful!")
            print(f"📊 Database version: {version[0]}")

        # Test session
        db = next(get_db())
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        print(f"✅ Session test successful: {test_result[0]}")

        return True

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing PostgreSQL connection...")
    success = test_postgres_connection()

    if success:
        print("\n🎉 PostgreSQL is ready to use!")
    else:
        print(
            "\n⚠️  Please check your PostgreSQL configuration and environment variables."
        )
