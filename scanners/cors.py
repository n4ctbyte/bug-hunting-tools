
import requests

def scan_cors(url):
    print(f"Scanning CORS Misconfiguration for {url}")
    headers = {
        "Origin": "https://evil.com"
    }
    try:
        response = requests.get(url, headers=headers)
        if "Access-Control-Allow-Origin" in response.headers:
            if response.headers["Access-Control-Allow-Origin"] == "*" or \
               response.headers["Access-Control-Allow-Origin"] == "https://evil.com":
                print(f"[+] CORS Misconfiguration found: Access-Control-Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
            else:
                print("[-] No CORS misconfiguration found.")
        else:
            print("[-] No Access-Control-Allow-Origin header found.")
    except requests.exceptions.RequestException as e:
        print(f"Error during CORS detection: {e}")


