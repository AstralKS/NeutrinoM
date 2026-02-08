import httpx
import sys

URL = "http://127.0.0.1:8001/analyze"
REPO = "https://github.com/fastapi/fastapi"

try:
    print(f"Triggering analysis for {REPO}...")
    response = httpx.post(URL, json={"repo_url": REPO}, timeout=60.0)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
