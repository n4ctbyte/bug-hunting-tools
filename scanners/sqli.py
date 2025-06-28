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
        """Get baseline response for comparison"""
        try:
            response = self.session.get(url, timeout=10)
            return {
                "status_code": response.status_code,
                "text": response.text,
                "length": len(response.text),
                "headers": dict(response.headers)
            }
        except Exception as e:
            print(f"Error getting baseline: {e}")
            return None

    def detect_sqli_advanced(self, base_url, payload, param_name, baseline):
        """Advanced SQLi detection with baseline comparison"""
        try:
            parsed_url = urlparse(base_url)
            
            if parsed_url.query:
                params = parse_qs(parsed_url.query, keep_blank_values=True)
                if param_name not in params:
                    return False
                params[param_name] = [payload]
                new_query = urlencode(params, doseq=True)
                test_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, new_query, parsed_url.fragment
                ))
            else:
                return False
            
            time.sleep(random.uniform(0.5, 1.0))
            
            response = self.session.get(test_url, timeout=10)
            
            if baseline:
                return self.analyze_response_difference(
                    baseline, response, payload, test_url
                )
            
            return False
            
        except Exception as e:
            return False

    def analyze_response_difference(self, baseline, response, payload, test_url):
        """Analyze differences between baseline and test response"""
        
        if self.check_database_errors(response.text):
            print(f"[+] Database error detected: {test_url}")
            return True
        
        # 2. Check for significant status code changes
        if baseline["status_code"] == 200 and response.status_code == 500:
            print(f"[+] Status code change (200->500): {test_url}")
            return True
        
        # 3. Check for significant content length changes
        length_diff = abs(len(response.text) - baseline["length"])
        if length_diff > 1000:  # Significant change
            print(f"[+] Significant content length change: {test_url}")
            return True
        
        # 4. Boolean-based detection (for specific payloads)
        if self.is_boolean_payload(payload):
            return self.detect_boolean_sqli(baseline, response, test_url)
        
        # 5. Time-based detection
        if self.is_time_payload(payload):
            return self.detect_time_based_sqli(test_url, payload)
        
        return False

    def check_database_errors(self, response_text):
        """Check for actual database error messages"""
        error_patterns = [
            "mysql_fetch_array()",
            "You have an error in your SQL syntax",
            "PostgreSQL query failed",
            "ORA-00933:",
            "Microsoft OLE DB Provider",
            "Unclosed quotation mark",
            "sqlite3.OperationalError",
        ]
        
        response_lower = response_text.lower()
        for pattern in error_patterns:
            if pattern.lower() in response_lower:
                return True
        return False

    def is_boolean_payload(self, payload):
        """Check if payload is boolean-based"""
        boolean_patterns = ["1=1", "1=2", "'1'='1", "'1'='2"]
        return any(pattern in payload for pattern in boolean_patterns)

    def is_time_payload(self, payload):
        """Check if payload is time-based"""
        time_patterns = ["SLEEP", "WAITFOR", "DELAY"]
        return any(pattern.upper() in payload.upper() for pattern in time_patterns)

    def detect_boolean_sqli(self, baseline, response, test_url):
        """Detect boolean-based SQLi by comparing response similarity"""
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, baseline["text"], response.text).ratio()
        
        # If responses are too similar, it's likely not vulnerable
        if similarity > 0.95:
            return False
        
        # If responses are completely different, it might be vulnerable
        if similarity < 0.5:
            print(f"[+] Boolean-based SQLi detected (similarity: {similarity:.2f}): {test_url}")
            return True
        
        return False

    def detect_time_based_sqli(self, test_url, payload):
        """Detect time-based SQLi by measuring response time"""
        
        try:
            start_time = time.time()
            response = self.session.get(test_url, timeout=30)
            response_time = time.time() - start_time
            
            # If response takes longer than expected, might be time-based SQLi
            if response_time > 4:  # Expecting 5 second delay
                print(f"[+] Time-based SQLi detected (response time: {response_time:.2f}s): {test_url}")
                return True
        except requests.exceptions.Timeout:
            print(f"[+] Time-based SQLi detected (timeout): {test_url}")
            return True
        except Exception:
            pass
        
        return False

    def extract_parameters_from_url(self, url):
        """Extract actual parameters from URL"""
        parsed_url = urlparse(url)
        if parsed_url.query:
            return list(parse_qs(parsed_url.query).keys())
        return []

    def scan_sqli_improved(self, url, sqli_payloads):
        """Improved SQL Injection scanning"""
        print(f"Scanning SQLi for {url}")
        
        # Get baseline response
        baseline = self.get_baseline_response(url)
        if not baseline:
            print("[-] Could not get baseline response")
            return False
        
        # Extract actual parameters
        actual_params = self.extract_parameters_from_url(url)
        if not actual_params:
            print("[-] No parameters found in URL")
            print("[*] Suggestion: Try URLs with parameters like:")
            print("    - https://find.yun.oppo.com/search?q=test")
            print("    - https://find.yun.oppo.com/api/endpoint?id=123")
            print("[*] Or use crawler to find URLs with parameters")
            return False
        
        print(f"Found parameters: {actual_params}")
        
        found_sqli = False
        vulnerability_count = 0
        
        print(f"Testing {len(sqli_payloads)} payloads on {len(actual_params)} parameters...")
        
        for param in actual_params:
            print(f"\nTesting parameter: {param}")
            
            for i, payload in enumerate(sqli_payloads, 1):
                print(f"[{i}/{len(sqli_payloads)}] Testing payload: {payload}")
                
                if self.detect_sqli_advanced(url, payload, param, baseline):
                    print(f"[+] SQL Injection vulnerability found in parameter '{param}' with payload: {payload}")
                    found_sqli = True
                    vulnerability_count += 1
        
        if found_sqli:
            print(f"\n[+] Total SQL Injection vulnerabilities found: {vulnerability_count}")
        else:
            print("\n[-] No SQL Injection vulnerabilities found.")
        
        return url if found_sqli else None

# Usage function
def scan_sqli(url, session, sqli_payloads):
    scanner = SQLiScanner(session)
    result = scanner.scan_sqli_improved(url, sqli_payloads)
    return result

