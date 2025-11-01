import requests
import json
import time


def test_endpoint(url, method="GET", data=None, description=""):
    """Test a single endpoint"""
    print(f"\n🔍 Testing {description}: {method} {url}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(
                url, json=data, headers={"Content-Type": "application/json"}, timeout=10
            )
        else:
            print(f"❌ Unsupported method: {method}")
            return False

        print(f"📊 Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print(f"✅ Success")
            if response.content:
                try:
                    result = response.json()
                    print(
                        f"📄 Response: {json.dumps(result, indent=2, ensure_ascii=False)}"
                    )
                except:
                    print(f"📄 Response: {response.text}")
            return True
        elif response.status_code == 404:
            print(f"❌ Not Found - Endpoint doesn't exist")
            return False
        elif response.status_code == 500:
            print(f"❌ Internal Server Error")
            print(f"Error: {response.text}")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_all_endpoints():
    """Test all endpoints"""
    base_url = "http://localhost:8000"

    print("🚀 Testing All Endpoints")
    print("=" * 60)

    # Test root endpoint
    test_endpoint(f"{base_url}/", "GET", description="Root endpoint")

    # Test API documentation
    test_endpoint(f"{base_url}/docs", "GET", description="API Documentation")

    # Test extract-info endpoint
    extract_data = {
        "messages": [
            {"id": "1", "text": "سلام می‌خوام به تهران سفر کنم", "sender": "CLIENT"},
            {"id": "2", "text": "تاریخ سفر؟", "sender": "AVATAR"},
            {"id": "3", "text": "۱۵ فروردین", "sender": "CLIENT"},
        ]
    }
    test_endpoint(
        f"{base_url}/api/v1/extract-info", "POST", extract_data, "Extract Info"
    )

    # Test trips endpoint
    trip_data = {
        "airportName": "فرودگاه امام خمینی",
        "travelDate": "۲۸ مرداد ۱۴۰۴",
        "flightNumber": "IR123",
        "passengers": [
            {"fullName": "علی رضایی", "nationalId": "1234567890", "luggageCount": 2}
        ],
    }
    test_endpoint(f"{base_url}/api/v1/trips", "POST", trip_data, "Create Trip")

    # Test messages endpoint
    message_data = {"id": "test123", "text": "تست پیام", "sender": "CLIENT"}
    test_endpoint(f"{base_url}/api/v1/messages", "POST", message_data, "Create Message")

    # Test passport endpoint
    test_endpoint(f"{base_url}/api/v1/passport/upload", "POST", {}, "Passport Upload")

    # Test responses endpoint
    test_endpoint(f"{base_url}/api/v1/responses", "GET", description="Get Responses")

    # Test assistant endpoint
    test_endpoint(
        f"{base_url}/api/v1/aiassistant/chat",
        "POST",
        {"message": "سلام"},
        "AI Assistant",
    )


def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server with:")
        print("python -m uvicorn api.app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Airport AI Bot - Endpoint Testing")
    print("=" * 60)

    # Check if server is running
    if not check_server_status():
        exit(1)

    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)

    # Test all endpoints
    test_all_endpoints()

    print("\n" + "=" * 60)
    print("🏁 Endpoint testing completed!")
