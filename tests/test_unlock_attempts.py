import requests

def test_unlock_attempts():
    base_url = "http://localhost:5000/unlock_item"
    csrf_token = "<your_csrf_token_here>"  # Replace with a valid CSRF token
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token
    }

    # Simulate 3 unlock attempts
    for i in range(1, 5):
        response = requests.post(base_url, json={
            "itemType": "message",
            "itemId": 102,
            "faceImage": None if i < 4 else "dummy_face_image"
        }, headers=headers)

        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Attempt {i}: Status Code: {response.status_code}, Raw Response: {response.text}")
            continue

        print(f"Attempt {i}: Status Code: {response.status_code}, Response: {response_json}")

        if response.status_code == 403 and "permanently deleted" in response_json.get("message", ""):
            print("Message is permanently deleted after 3 attempts.")
            break

if __name__ == "__main__":
    test_unlock_attempts()
