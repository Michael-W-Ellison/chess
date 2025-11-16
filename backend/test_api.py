"""
Test API Endpoints
Simple script to verify all API endpoints are working correctly
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response):
    """Print formatted response"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")


def test_health_endpoints():
    """Test basic health check endpoints"""
    print("\n" + "=" * 60)
    print("TESTING HEALTH ENDPOINTS")
    print("=" * 60)

    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print_response("GET /", response)

    # Test health endpoint
    response = requests.get(f"{BASE_URL}/health")
    print_response("GET /health", response)


def test_conversation_flow():
    """Test complete conversation flow"""
    print("\n" + "=" * 60)
    print("TESTING CONVERSATION FLOW")
    print("=" * 60)

    # 1. Start conversation
    response = requests.post(f"{BASE_URL}/api/conversation/start", params={"user_id": 1})
    print_response("POST /api/conversation/start", response)

    if response.status_code != 200:
        print("❌ Failed to start conversation, skipping rest of flow")
        return

    conversation_id = response.json()["conversation_id"]

    # 2. Send a message
    message_data = {
        "user_message": "Hi! My name is Alex and I'm 12 years old. I love playing video games!",
        "conversation_id": conversation_id,
        "user_id": 1
    }
    response = requests.post(f"{BASE_URL}/api/message", json=message_data)
    print_response("POST /api/message (first message)", response)

    # 3. Send another message
    message_data["user_message"] = "What's your favorite color?"
    response = requests.post(f"{BASE_URL}/api/message", json=message_data)
    print_response("POST /api/message (second message)", response)

    # 4. Get conversation details
    response = requests.get(f"{BASE_URL}/api/conversation/{conversation_id}")
    print_response(f"GET /api/conversation/{conversation_id}", response)

    # 5. End conversation
    response = requests.post(f"{BASE_URL}/api/conversation/end/{conversation_id}")
    print_response("POST /api/conversation/end", response)


def test_personality_endpoints():
    """Test personality endpoints"""
    print("\n" + "=" * 60)
    print("TESTING PERSONALITY ENDPOINTS")
    print("=" * 60)

    # Get personality
    response = requests.get(f"{BASE_URL}/api/personality", params={"user_id": 1})
    print_response("GET /api/personality", response)

    # Get personality description
    response = requests.get(f"{BASE_URL}/api/personality/description", params={"user_id": 1})
    print_response("GET /api/personality/description", response)


def test_profile_endpoints():
    """Test profile endpoints"""
    print("\n" + "=" * 60)
    print("TESTING PROFILE ENDPOINTS")
    print("=" * 60)

    # Get profile
    response = requests.get(f"{BASE_URL}/api/profile", params={"user_id": 1})
    print_response("GET /api/profile", response)

    # Get memories
    response = requests.get(f"{BASE_URL}/api/profile/memories", params={"user_id": 1})
    print_response("GET /api/profile/memories", response)

    # Update profile
    update_data = {
        "user_id": 1,
        "name": "Alex",
        "age": 12,
        "grade": 7
    }
    response = requests.put(f"{BASE_URL}/api/profile/update", json=update_data)
    print_response("PUT /api/profile/update", response)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CHATBOT BACKEND API TESTS")
    print("=" * 60)
    print("\nMake sure the backend server is running:")
    print("  cd backend && python main.py")
    print("\nStarting tests in 3 seconds...")

    import time
    time.sleep(3)

    try:
        # Test endpoints in order
        test_health_endpoints()
        test_personality_endpoints()
        test_profile_endpoints()
        test_conversation_flow()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        print("\nCheck the output above for any errors.")
        print("Note: LLM responses will be fallback messages if model is not loaded.")

    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 60)
        print("❌ ERROR: Could not connect to backend server")
        print("=" * 60)
        print("\nMake sure the server is running:")
        print("  cd backend")
        print("  python main.py")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
