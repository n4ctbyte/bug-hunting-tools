import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin

def detect_rce(session, url, payload):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        # Test in query parameters
        for param, values in query_params.items():
            test_params = query_params.copy()
            test_params[param] = [payload]
            test_url = urlunparse((
                parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                parsed_url.params, urlencode(test_params, doseq=True), parsed_url.fragment
            ))
            response = session.get(test_url, timeout=10)
            if "root:x:0:0:root" in response.text or "Windows" in response.text: # For `cat /etc/passwd` or `dir`
                return True

        # Test in path (simple case)
        test_url_path = urljoin(url, payload)
        response = session.get(test_url_path, timeout=10)
        if "root:x:0:0:root" in response.text or "Windows" in response.text:
            return True

    except requests.exceptions.RequestException as e:
        print(f"Error during RCE detection: {e}")
    return False

def scan_rce(url, session, rce_payloads):
    print(f"Scanning RCE for {url}")

    found_rce = False
    for payload in rce_payloads:
        if detect_rce(session, url, payload):
            print(f"[+] RCE vulnerability found with payload: {payload}")
            found_rce = True
            break
    if not found_rce:
        print("[-] No RCE vulnerabilities found.")
    return found_rce


