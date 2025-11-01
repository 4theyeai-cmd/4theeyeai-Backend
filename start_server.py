import os
import sys
import subprocess
import time
from dotenv import load_dotenv


def check_environment():
    """Check if environment is properly configured"""
    print("Checking environment...")

    # Load environment variables
    load_dotenv()

    # Check required environment variables
    required_vars = [
        "POSTGRES_PASSWORD",
        "OPENAI_API_KEY",
        "KNOWLEDGE_SHEET_ID",
        "EXTERNAL_EXTRACTINFO_SERVICE_URL",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables.")
        return False

    print("Environment variables are set")
    return True


def start_server():
    """Start the FastAPI server"""
    print("Starting FastAPI server...")

    try:
        # Command to start server
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "4000",
            "--reload",
        ]

        print(f"Running: {' '.join(cmd)}")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)

        # Start the server
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

    return True


def main():
    print("Airport AI Bot Server")
    print("=" * 50)

    # Check environment
    if not check_environment():
        print("\nEnvironment not properly configured")
        print("Please create a .env file with required variables")
        return

    # Start server
    start_server()


if __name__ == "__main__":
    main()
