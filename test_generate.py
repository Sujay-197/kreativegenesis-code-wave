import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_generation():
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

    print("\n--- Testing App Generation (Mistral API) ---")
    payload = {
        "session_id": "test-session-123",
        "requirements_object": {
            "auth_and_users": "No specific authentication needed yet. Just the owner.",
            "data_and_storage": "Needs to store customer's name, order due date, cake flavor, and payment status (paid/unpaid).",
            "ui_complexity": "A clean, simple table view of orders with a form to add new ones. Mobile friendly.",
            "business_logic": "Needs to track payment for each order and sort by due date.",
            "integrations": "None yet."
        }
    }

    print("Sending generation request (this may take up to 20-30 seconds)...")
    response = requests.post(f"{BASE_URL}/api/generate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        app_id = data.get("app_id")
        print(f"Success! App generated with ID: {app_id}")
        
        print(f"\n--- Testing App Retrieval for ID {app_id} ---")
        retrieval_response = requests.get(f"{BASE_URL}/api/apps/{app_id}")
        if retrieval_response.status_code == 200:
            app_data = retrieval_response.json()
            print("Successfully retrieved from SQLite database!")
            print(f"HTML snippet: {app_data['html'][:150]}...\n")
            print(f"CSS snippet: {app_data['css'][:100]}...\n")
            print(f"JS snippet: {app_data['js'][:150]}...\n")
        else:
            print(f"Error retrieving app {retrieval_response.status_code}: {retrieval_response.text}")

    else:
        print(f"Error during generation {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_generation()
