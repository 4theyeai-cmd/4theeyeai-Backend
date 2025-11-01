import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_external_service():
    """Test the external extract info service"""

    # Test data - exactly what you provided before
    test_data = {
        "messages": [
            {
                "id": "1755320084411",
                "text": "سلام می‌خوام به نیویورک سفر کنم",
                "sender": "CLIENT",
            },
            {"id": "1755320102152", "text": "فرودگاه امام خمینی", "sender": "CLIENT"},
            {"id": "1755320113088", "text": "خروجی از فرودگاه", "sender": "CLIENT"},
            {"id": "1755320124988", "text": "۲۸ مرداد ۱۴۰۴", "sender": "CLIENT"},
            {
                "id": "1755320129384",
                "text": "تعداد دقیق مسافران چند نفر است؟",
                "sender": "AVATAR",
            },
        ]
    }

    # Get the external service URL
    external_url = os.getenv("EXTERNAL_EXTRACTINFO_SERVICE_URL")

    if not external_url:
        print("❌ EXTERNAL_EXTRACTINFO_SERVICE_URL is not set")
        return False

    print(f"🔍 Testing external service: {external_url}")
    print(f"📤 Sending payload: {json.dumps(test_data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(
            external_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"📊 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ External service response: {json.dumps(result, indent=2, ensure_ascii=False)}"
            )

            # Validate response format
            expected_fields = [
                "airportName",
                "travelDate",
                "flightNumber",
                "passengers",
            ]
            missing_fields = [field for field in expected_fields if field not in result]

            if missing_fields:
                print(f"⚠️  Missing fields in response: {missing_fields}")
            else:
                print("✅ Response format is correct")

            return True
        else:
            print(f"❌ External service error: {response.status_code}")
            print(f"Error response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing External Extract Info Service")
    print("=" * 50)

    success = test_external_service()

    if success:
        print("\n🎉 External service is working correctly!")
    else:
        print("\n⚠️  External service test failed. Please check your configuration.")
