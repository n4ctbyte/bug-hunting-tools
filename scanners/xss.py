
import requests
from urllib.parse import urljoin

def detect_xss(url, payload):
    try:
        # Assuming the payload is meant to be injected into a parameter, not directly appended to the base URL
        # For a more robust XSS scanner, we would need to identify parameters first.
        # For now, let\'s simulate a simple reflection by adding a query parameter.
        test_url = f"{url}?q={payload}"
        response = requests.get(test_url)
        if payload in response.text:
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error during XSS detection: {e}")
    return False

def scan_xss(url):
    print(f"Scanning XSS for {url}")
    xss_payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "\";!--\"<XSS>=&{()}"
    ]

    found_xss = False
    for payload in xss_payloads:
        if detect_xss(url, payload):
            print(f"[+] XSS vulnerability found with payload: {payload}")
            found_xss = True
            break
    if not found_xss:
        print("[-] No XSS vulnerabilities found.")


