import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup

def detect_xss(session, url, payload):
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
            if payload in response.text:
                return True

        # Test in path (simple case, more complex path injection would be needed)
        test_url_path = urljoin(url, payload)
        response = session.get(test_url_path, timeout=10)
        if payload in response.text:
            return True

        # Test in form fields (requires crawling and form submission logic)
        # This is a placeholder for future improvement

    except requests.exceptions.RequestException as e:
        print(f"Error during XSS detection: {e}")
    return False

def scan_xss(url, session, xss_payloads):
    print(f"Scanning XSS for {url}")

    found_xss = False
    for payload in xss_payloads:
        if detect_xss(session, url, payload):
            print(f"[+] XSS vulnerability found with payload: {payload}")
            found_xss = True
            # For now, we break after the first finding. In a real scenario, we might want to continue to find all.
            break
    if not found_xss:
        print("[-] No XSS vulnerabilities found.")
    return found_xss


