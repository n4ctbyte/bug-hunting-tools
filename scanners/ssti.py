import requests
import html
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin

# Payload SSTI dan output yang diharapkan
SSTI_PAYLOADS = [
    ("{{1330*876}}", "1165080"),
    ("{{233*7}}", "1631"),
    ("{{111*2}}", "222"),
    # ("{{5**3}}", "125"),
]

def build_test_url(original_url, param_name, payload):
    parsed = urlparse(original_url)
    query = parse_qs(parsed.query)
    query[param_name] = [payload]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def detect_ssti(url, session, payload, expected_output):
    try:
        headers = {"User-Agent": "BugHunterPro-SSTI-Scanner"}
        session.headers.update(headers)

        # Ambil baseline response
        baseline_resp = session.get(url, timeout=10)
        baseline_text = html.unescape(baseline_resp.text)
        baseline_headers = html.unescape(str(baseline_resp.headers))

        # Uji parameter di URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        for param in params:
            test_url = build_test_url(url, param, payload)
            resp = session.get(test_url, timeout=10)

            body = html.unescape(resp.text)
            headers = html.unescape(str(resp.headers))

            if expected_output in body and expected_output not in baseline_text:
                print(f"[+] SSTI via query param: {param} -> {test_url}")
                return True

            if expected_output in headers and expected_output not in baseline_headers:
                print(f"[+] SSTI reflected in header via param: {param} -> {test_url}")
                return True

            if payload in body:
                if expected_output not in body:
                    print(f"[?] Payload reflected but NOT evaluated: {param} -> {test_url}")
                    snippet = body[:500].replace('\n', '')  # preview 500 char max
                    print(f"    ↳ Snippet: {snippet}")
                else:
                    print(f"[!] ⚠ Payload and expected output both in response — possible bypass")
                    return True

        # Tes juga refleksi di PATH
        test_path_url = urljoin(url, payload)
        resp = session.get(test_path_url, timeout=10)
        body = html.unescape(resp.text)
        if expected_output in body and expected_output not in baseline_text:
            print(f"[+] SSTI via path: {test_path_url}")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[!] Request error: {e}")
    return False

def scan_ssti(url, session=None):
    session = session or requests.Session()
    print(f"\n🔍 Scanning for SSTI in: {url}")

    for payload, expected in SSTI_PAYLOADS:
        print(f"  → Testing payload: {payload}")
        if detect_ssti(url, session, payload, expected):
            print(f"[✔] SSTI Detected using: {payload}")
            return True
    print("[-] No SSTI found.")
    return False