import requests
import json


def test_trips_endpoint():
    """Test the trips endpoint"""

    # Test data for creating a trip
    test_trip_data = {
        "airportName": "فرودگاه امام خمینی",
        "travelDate": "۲۸ مرداد ۱۴۰۴",
        "flightNumber": "IR123",
        "passengers": [
            {"fullName": "علی رضایی", "nationalId": "1234567890", "luggageCount": 2},
            {"fullName": "فاطمه احمدی", "nationalId": "0987654321", "luggageCount": 1},
        ],
    }

    print("🔍 Testing trips endpoint...")
    print(
        f"📤 Sending trip data: {json.dumps(test_trip_data, indent=2, ensure_ascii=False)}"
    )

    try:
        # Test POST /api/v1/trips
        response = requests.post(
            "http://localhost:4000/api/v1/trips",
            json=test_trip_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"📊 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ Trip created successfully: {json.dumps(result, indent=2, ensure_ascii=False)}"
            )

            # Test GET /api/v1/trips/{trip_id}
            trip_id = result.get("id")
            if trip_id:
                print(f"\n🔍 Testing GET trip with ID: {trip_id}")
                get_response = requests.get(
                    f"http://localhost:4000/api/v1/trips/{trip_id}", timeout=30
                )

                print(f"📊 GET Response status: {get_response.status_code}")

                if get_response.status_code == 200:
                    get_result = get_response.json()
                    print(
                        f"✅ Trip retrieved successfully: {json.dumps(get_result, indent=2, ensure_ascii=False)}"
                    )
                    return True
                else:
                    print(f"❌ GET trip failed: {get_response.text}")
                    return False
            else:
                print("⚠️  No trip ID returned from creation")
                return False
        else:
            print(f"❌ Create trip failed: {response.status_code}")
            print(f"Error response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Trips Endpoint")
    print("=" * 50)

    success = test_trips_endpoint()

    if success:
        print("\n🎉 Trips endpoint is working correctly!")
    else:
        print("\n⚠️  Trips endpoint test failed. Please check your configuration.")
