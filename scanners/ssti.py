import requests
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin

def detect_ssti(session, url, payload):
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
            if "49" in response.text: # For {{7*7}} payload
                return True

        # Test in path (simple case)
        test_url_path = urljoin(url, payload)
        response = session.get(test_url_path, timeout=10)
        if "49" in response.text and payload not in response.text and urllib.parse.quote(payload) not in response.text:
            return True

    except requests.exceptions.RequestException as e:
        print(f"Error during SSTI detection: {e}")
    return False

def scan_ssti(url, session, ssti_payloads):
    print(f"Scanning SSTI for {url}")

    found_ssti = False
    for payload in ssti_payloads:
        if detect_ssti(session, url, payload):
            print(f"[+] SSTI vulnerability found with payload: {payload}")
            found_ssti = True
            break
    if not found_ssti:
        print("[-] No SSTI vulnerabilities found.")
    return found_ssti


