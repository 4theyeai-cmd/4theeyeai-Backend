import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["POSTGRES_PASSWORD", "OPENAI_API_KEY", "KNOWLEDGE_SHEET_ID"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables:")
        print(
            """
# Example .env file:
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=airport_bot
OPENAI_API_KEY=your_openai_key_here
KNOWLEDGE_SHEET_ID=your_sheet_id_here
        """
        )
        return False

    print("✅ All required environment variables are set")
    return True


def setup_database():
    """Setup database and run migrations"""
    try:
        print("🔧 Setting up PostgreSQL database...")

        # Test connection first
        from test_postgres_connection import test_postgres_connection

        if not test_postgres_connection():
            print(
                "❌ Database connection failed. Please check your PostgreSQL configuration."
            )
            return False

        # Run Alembic migrations
        print("📦 Running database migrations...")
        os.system("alembic revision --autogenerate -m 'Initial migration'")
        os.system("alembic upgrade head")

        print("✅ Database setup completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def main():
    print("🚀 PostgreSQL Setup for Airport AI Bot")
    print("=" * 50)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Setup database
    if not setup_database():
        sys.exit(1)

    print("\n🎉 Setup completed successfully!")
    print("You can now run your application with:")
    print("python -m uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
