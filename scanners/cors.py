import requests

def scan_cors(url, session, cors_payloads):
    print(f"Scanning CORS Misconfiguration for {url}")
    found_cors = False
    for evil_origin in cors_payloads:
        headers = {
            "Origin": evil_origin
        }
        try:
            response = session.get(url, headers=headers, timeout=10)
            if "Access-Control-Allow-Origin" in response.headers:
                if response.headers["Access-Control-Allow-Origin"] == "*" or \
                   response.headers["Access-Control-Allow-Origin"] == evil_origin:
                    print(f"[+] CORS Misconfiguration found: Access-Control-Allow-Origin: {response.headers["Access-Control-Allow-Origin"]} with Origin: {evil_origin}")
                    found_cors = True
                    break
            else:
                print("[-] No Access-Control-Allow-Origin header found.")
        except requests.exceptions.RequestException as e:
            print(f"Error during CORS detection: {e}")
    if not found_cors:
        print("[-] No CORS misconfiguration found.")
    return found_cors


