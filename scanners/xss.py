import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from difflib import SequenceMatcher

def detect_xss(session, url, param_name, payload):
    """Inject payload into a single param and check if it's reflected"""
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query, keep_blank_values=True)

    if param_name not in params:
        return False

    # Inject payload
    params[param_name] = [payload]
    new_query = urlencode(params, doseq=True)
    test_url = urlunparse((
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, new_query, parsed_url.fragment
    ))

    try:
        response = session.get(test_url, timeout=10)
        # Simple reflection check
        if payload in response.text:
            print(f"[+] Reflected payload detected: {payload} in param '{param_name}' -> {test_url}")
            return True
    except requests.exceptions.RequestException:
        pass

    return False


def extract_parameters_from_url(url):
    parsed = urlparse(url)
    return list(parse_qs(parsed.query).keys())


def scan_xss(urls, session, xss_payloads):
    found_xss_urls = []

    for url in urls:
        print(f"\n[>] Scanning XSS for: {url}")
        param_names = extract_parameters_from_url(url)
        if not param_names:
            continue

        for param in param_names:
            for payload in xss_payloads:
                if detect_xss(session, url, param, payload):
                    found_xss_urls.append((url, param, payload))
                    break

    if found_xss_urls:
        print(f"\n[+] Total XSS found: {len(found_xss_urls)}")
        for url, param, payload in found_xss_urls:
            print(f"  - {url} param={param} payload={payload}")
        return found_xss_urls
    else:
        print("[-] No XSS vulnerabilities found.")
        return False