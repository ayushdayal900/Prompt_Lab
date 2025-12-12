import requests

try:
    response = requests.post(
        "http://localhost:8000/api/test-prompt",
        json={
            "system_prompt": "test",
            "user_prompt": "test",
            "model": "gpt-4o-mini",
            "secret": "test-secret"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
