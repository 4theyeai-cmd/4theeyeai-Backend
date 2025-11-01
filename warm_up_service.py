#!/usr/bin/env python3
"""
Vercel Service Warm-up
گرم کردن سرویس Vercel برای جلوگیری از Cold Start
"""

import requests
import time
import os
from dotenv import load_dotenv


def warm_up_vercel_service():
    """Warm up the Vercel service to prevent cold starts"""
    print("🔥 Warming up Vercel service...")
    print("=" * 50)

    load_dotenv()
    chat_url = os.getenv("EXTERNAL_CHAT_SERVICE_URL")

    if not chat_url:
        print("❌ EXTERNAL_CHAT_SERVICE_URL not set")
        return False

    # Simple warm-up payload
    warm_up_payload = {
        "message": "warm up",
        "session_id": "warm_up_session",
        "language": "en",
    }

    print(f"URL: {chat_url}")
    print("Sending warm-up request...")

    try:
        # Send warm-up request with longer timeout
        response = requests.post(
            chat_url,
            json=warm_up_payload,
            timeout=120,  # 2 minutes for cold start
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        if response.status_code == 200:
            print("✅ Service warmed up successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Service returned status {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("⏰ Warm-up timeout - service may be very cold")
        return False
    except Exception as e:
        print(f"❌ Warm-up error: {e}")
        return False


def test_after_warm_up():
    """Test the service after warm-up"""
    print("\n🧪 Testing service after warm-up...")
    print("=" * 50)

    load_dotenv()
    chat_url = os.getenv("EXTERNAL_CHAT_SERVICE_URL")

    test_payload = {
        "message": "hello who you are",
        "session_id": "test_session",
        "language": "en",
    }

    try:
        start_time = time.time()
        response = requests.post(
            chat_url,
            json=test_payload,
            timeout=30,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
            print(f"✅ Test successful! Duration: {duration:.2f}s")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Test returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Vercel Service Warm-up Tool")
    print("=" * 50)

    # Warm up the service
    warm_up_success = warm_up_vercel_service()

    if warm_up_success:
        # Test after warm-up
        test_success = test_after_warm_up()

        if test_success:
            print("\n🎉 Service is ready for use!")
        else:
            print("\n⚠️  Service warmed up but test failed")
    else:
        print("\n💥 Warm-up failed - service may be down")
