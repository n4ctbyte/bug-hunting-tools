import requests

domain = "https://photos.adobe.io"

endpoints = [
    "/", "/admin", "/panel", "/upload", "/login", "/backup",
    "/test", "/dev", "/api/user", "/user_info", "/config",
    "/dashboard", "/status", "/monitor", "/data", "/info"
]

headers = {
    "Origin": "https://evil.com"
}

def test_cors_endpoints(domain, endpoints):
    print(f"\n🛡️  Starting CORS Scan on: {domain}\n")
    for endpoint in endpoints:
        url = domain + endpoint
        try:
            response = requests.get(url, headers=headers, timeout=10)
            origin = response.headers.get("Access-Control-Allow-Origin")
            creds = response.headers.get("Access-Control-Allow-Credentials")
            print(f"🔍 Testing {url}")
            
            if origin == "https://evil.com" and creds == "true":
                print(f"  🔥 VULNERABLE! Origin reflected + Credentials allowed")
            elif origin:
                print(f"  ⚠️  CORS header found: {origin} | Creds: {creds} | Status: {response.status_code}")
            else:
                print(f"  ❌ No CORS | Status: {response.status_code}")
        
        except requests.RequestException as e:
            print(f"  ⚠️ Error accessing {url} => {e}")

test_cors_endpoints(domain, endpoints)