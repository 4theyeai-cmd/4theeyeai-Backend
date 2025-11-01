import requests
import socket
import subprocess
import sys
import time
import os


def check_port(host, port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ Error checking port {port}: {e}")
        return False


def check_server_endpoints():
    """Check if server endpoints are responding"""
    base_url = "http://localhost:4000"
    endpoints = ["/", "/docs", "/openapi.json", "/api/v1/extract-info"]

    print("🔍 Checking server endpoints...")

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused")
        except requests.exceptions.Timeout:
            print(f"⚠️  {endpoint}: Timeout")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")


def check_processes():
    """Check if uvicorn processes are running"""
    print("🔍 Checking for uvicorn processes...")

    try:
        # On Windows
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                capture_output=True,
                text=True,
            )
            if "uvicorn" in result.stdout or "api.app" in result.stdout:
                print("✅ Uvicorn process found")
                return True
        else:
            # On Unix/Linux
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if "uvicorn" in result.stdout:
                print("✅ Uvicorn process found")
                return True

        print("❌ No uvicorn process found")
        return False

    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False


def start_server():
    """Start the server"""
    print("🚀 Starting server...")

    try:
        # Check if .env file exists
        if not os.path.exists(".env"):
            print("⚠️  .env file not found. Creating example...")
            with open(".env", "w") as f:
                f.write(
                    """# Example .env file
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=airport_bot
OPENAI_API_KEY=your_openai_key_here
KNOWLEDGE_SHEET_ID=your_sheet_id_here
EXTERNAL_EXTRACTINFO_SERVICE_URL=your_external_service_url_here
ENVIRONMENT=development
"""
                )
            print("📝 Please edit .env file with your actual values")
            return False

        # Start server
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

        process = subprocess.Popen(cmd)
        print(f"✅ Server started with PID: {process.pid}")

        # Wait a moment for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)

        return True

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def main():
    print("🔍 Server Status Check")
    print("=" * 50)

    # Check if port 4000 is open
    print("🔍 Checking port 4000...")
    if check_port("localhost", 4000):
        print("✅ Port 4000 is open")
        check_server_endpoints()
    else:
        print("❌ Port 4000 is not open")

        # Check for running processes
        if check_processes():
            print("⚠️  Server process found but port not responding")
        else:
            print("❌ No server process found")

            # Ask to start server
            response = input("🚀 Would you like to start the server? (y/N): ")
            if response.lower() == "y":
                start_server()

                # Check again after starting
                print("\n⏳ Checking server status after start...")
                time.sleep(3)
                if check_port("localhost", 4000):
                    print("✅ Server is now running!")
                    check_server_endpoints()
                else:
                    print("❌ Server failed to start properly")

    print("\n" + "=" * 50)
    print("🏁 Status check completed!")


if __name__ == "__main__":
    main()
