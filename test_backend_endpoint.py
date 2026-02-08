import requests
import json

def test_backend():
    url = "http://localhost:8000/research"
    payload = {
        "included_industries": ["Tech"],
        "required_keywords": ["AI"],
        "target_countries": ["US"],
        "min_employees": 10
    }
    
    print(f"Testing {url}...")
    try:
        # We use stream=True because it's a streaming endpoint
        with requests.post(url, json=payload, stream=True) as r:
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print("Success! Backend is reachable.")
                # Read a bit of the stream
                for line in r.iter_lines():
                    if line:
                        print(f"Received: {line.decode('utf-8')[:100]}")
                        break
            else:
                print(f"Failed with status: {r.status_code}")
                print(f"Response: {r.text}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_backend()
