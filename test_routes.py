import requests

def test_routes():
    base_url = "http://localhost:8000"
    
    # Test Root
    try:
        r = requests.get(f"{base_url}/")
        print(f"GET / : Status {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"GET / failed: {e}")

    # Test Docs
    try:
        r = requests.get(f"{base_url}/docs")
        print(f"GET /docs : Status {r.status_code}")
    except Exception as e:
        print(f"GET /docs failed: {e}")

    # Test Research
    try:
        r = requests.post(f"{base_url}/research", json={})
        print(f"POST /research : Status {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"POST /research failed: {e}")

if __name__ == "__main__":
    test_routes()
