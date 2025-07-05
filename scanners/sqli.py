import requests
import urllib.parse
import time
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from difflib import SequenceMatcher

class SQLiScanner:
    def __init__(self, session):
        self.session = session

    def get_baseline_response(self, url):
        try:
            response = self.session.get(url, timeout=10)
            return {
                "status_code": response.status_code,
                "text": response.text,
                "length": len(response.text),
                "headers": dict(response.headers),
                "time": response.elapsed.total_seconds()
            }
        except Exception as e:
            print(f"Error getting baseline: {e}")
            return None

    def detect_sqli_advanced(self, base_url, payload_true, payload_false, param_name, baseline):
        try:
            parsed_url = urlparse(base_url)
            params = parse_qs(parsed_url.query, keep_blank_values=True)
            if param_name not in params:
                return False

            # Boolean-based comparison
            if self.is_boolean_payload(payload_true):
                url_true = self.build_test_url(parsed_url, param_name, payload_true)
                url_false = self.build_test_url(parsed_url, param_name, payload_false)
                return self.detect_boolean_sqli(url_true, url_false)

            # Time-based
            if self.is_time_payload(payload_true):
                url_test = self.build_test_url(parsed_url, param_name, payload_true)
                return self.detect_time_based_sqli(url_test, baseline)

            # Error-based or status diff
            url_test = self.build_test_url(parsed_url, param_name, payload_true)
            response = self.session.get(url_test, timeout=10)
            return self.analyze_response_difference(baseline, response, url_test)

        except Exception:
            return False

    def build_test_url(self, parsed_url, param, payload):
        params = parse_qs(parsed_url.query, keep_blank_values=True)
        params[param] = [payload]
        new_query = urlencode(params, doseq=True)
        return urlunparse((
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, new_query, parsed_url.fragment
        ))

    def analyze_response_difference(self, baseline, response, test_url):
        if self.check_database_errors(response.text):
            print(f"[+] Database error detected: {test_url}")
            return True
        if baseline["status_code"] == 200 and response.status_code == 500:
            print(f"[+] Status code change (200->500): {test_url}")
            return True
        return False

    def check_database_errors(self, response_text):
        error_patterns = [
            "mysql_fetch_array()", "You have an error in your SQL syntax",
            "PostgreSQL query failed", "ORA-00933:", "Microsoft OLE DB Provider",
            "Unclosed quotation mark", "sqlite3.OperationalError",
            "SQLSTATE", "Syntax error in string", "Microsoft SQL Native Client"
        ]
        response_lower = response_text.lower()
        return any(pattern.lower() in response_lower for pattern in error_patterns)

    def is_boolean_payload(self, payload):
        boolean_patterns = ["1=1", "1=2", "'1'='1", "'1'='2"]
        return any(pattern in payload for pattern in boolean_patterns)

    def is_time_payload(self, payload):
        time_patterns = ["SLEEP", "WAITFOR", "DELAY"]
        return any(pattern.upper() in payload.upper() for pattern in time_patterns)

    def detect_boolean_sqli(self, url_true, url_false):
        try:
            resp_true = self.session.get(url_true, timeout=10)
            resp_false = self.session.get(url_false, timeout=10)
            sim = SequenceMatcher(None, resp_true.text, resp_false.text).ratio()
            if sim < 0.85:
                print(f"[+] Boolean-based SQLi detected (similarity: {sim:.2f}): {url_true}")
                return True
        except Exception:
            pass
        return False

    def detect_time_based_sqli(self, url, baseline):
        try:
            start = time.time()
            self.session.get(url, timeout=30)
            elapsed = time.time() - start
            baseline_time = baseline.get("time", 0)
            if elapsed - baseline_time > 4:
                print(f"[+] Time-based SQLi detected (delay: {elapsed:.2f}s): {url}")
                return True
        except requests.exceptions.Timeout:
            print(f"[+] Time-based SQLi detected (timeout): {url}")
            return True
        return False

    def extract_parameters_from_url(self, url):
        parsed_url = urlparse(url)
        return list(parse_qs(parsed_url.query).keys()) if parsed_url.query else []

    def scan_sqli_improved(self, url, sqli_payload_pairs):
        print(f"Scanning SQLi for {url}")
        baseline = self.get_baseline_response(url)
        if not baseline:
            print("[-] Could not get baseline response")
            return False

        actual_params = self.extract_parameters_from_url(url)
        if not actual_params:
            print("[-] No parameters found in URL")
            return False

        print(f"Found parameters: {actual_params}")
        found_sqli = False
        print(f"Testing payloads on {len(actual_params)} parameters...")

        for param in actual_params:
            print(f"\nTesting parameter: {param}")
            for i, (true_payload, false_payload) in enumerate(sqli_payload_pairs, 1):
                print(f"[{i}/{len(sqli_payload_pairs)}] Payloads: TRUE='{true_payload}', FALSE='{false_payload}'")
                if self.detect_sqli_advanced(url, true_payload, false_payload, param, baseline):
                    print(f"[+] SQLi detected in '{param}' with TRUE: {true_payload}")
                    found_sqli = True

        print("\n[+] Done" if found_sqli else "\n[-] No SQLi vulnerabilities found.")
        return url if found_sqli else None

def scan_sqli(urls, session, sqli_payload_pairs):
    scanner = SQLiScanner(session)
    if isinstance(urls, str):
        urls = [urls]
    findings = []
    for url in urls:
        result = scanner.scan_sqli_improved(url, sqli_payload_pairs)
        if result:
            findings.append(result)
    return findings if findings else False