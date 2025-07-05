import requests

# Ganti dengan target domain kamu
domain = "https://www.opposhop.cn"

# Endpoint umum yang ingin diuji
endpoints = [
    "/", "/admin", "/panel", "/upload", "/login", "/backup",
    "/test", "/dev", "/api/user", "/user_info", "/config",
    "/dashboard", "/status", "/monitor", "/data", "/info"
]

# Header untuk simulasi permintaan dari domain asing
headers = {
    "Origin": "https://evil.com"
}

# Fungsi untuk uji CORS pada semua endpoint
def test_cors_endpoints(domain, endpoints):
    for endpoint in endpoints:
        url = domain + endpoint
        try:
            response = requests.get(url, headers=headers, timeout=10)
            cors = response.headers.get("Access-Control-Allow-Origin")
            print(f"🔍 Testing {url}")
            if cors == "*":
                print(f"  ✅ CORS open: {cors} | Status: {response.status_code}")
            else:
                print(f"  ❌ Not vulnerable | CORS: {cors} | Status: {response.status_code}")
        except requests.RequestException as e:
            print(f"  ⚠️ Error accessing {url} => {e}")

# Jalankan scanner
test_cors_endpoints(domain, endpoints)