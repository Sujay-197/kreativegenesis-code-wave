import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("Waiting for server to start...")
    # Wait for the server to be up
    for _ in range(10):
        try:
            r = requests.get(f"{BASE_URL}/api/health")
            if r.status_code == 200:
                print("Server is up!")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("Server did not start in time.")
        return

    print("\n--- Starting Conversation ---")
    session_id = None
    messages = [
        "Hi, I run a small local bakery and I'm really struggling to keep track of my custom cake orders. People message me on WhatsApp, Instagram, and SMS, and I keep messing up dates.",
        "Yes, exactly! I just need to record the customer's name, the date they need the cake, the flavor, and if they've paid yet or not."
    ]

    for msg in messages:
        print(f"\nUser: {msg}")
        payload = {
            "user_message": msg
        }
        if session_id:
            payload["session_id"] = session_id
        
        response = requests.post(f"{BASE_URL}/api/chat/simple", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"\nAssistant: {data.get('next_question')}")
            print(f"Confidence Score: {data.get('confidence_score')}")
            print("Requirements Object:")
            for k, v in data.get("requirements_object", {}).items():
                print(f"  - {k}: {v}")
        else:
            print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_api()
