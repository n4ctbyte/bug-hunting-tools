import requests
import urllib.parse
from urllib.parse import urljoin, urlparse

def detect_lfi(session, base_url, payload, param_name="file"):
    """
    Detect LFI vulnerability by testing payload in URL parameter
    """
    try:
        # Parse the base URL to handle it properly
        parsed_url = urlparse(base_url)
        
        # Create test URLs with different approaches
        test_urls = []
        
        # Method 1: Add as query parameter
        if parsed_url.query:
            # If URL already has parameters, add our parameter
            test_url = f"{base_url}&{param_name}={urllib.parse.quote(payload)}"
        else:
            # If no parameters, add our parameter
            test_url = f"{base_url}?{param_name}={urllib.parse.quote(payload)}"
        test_urls.append(test_url)
        
        # Method 2: Test common parameter names
        common_params = ["file", "page", "include", "path", "document", "root", "pg", "style"]
        for param in common_params:
            if parsed_url.query:
                test_url = f"{base_url}&{param}={urllib.parse.quote(payload)}"
            else:
                test_url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            test_urls.append(test_url)
        
        # Method 3: Try direct path injection (for some APIs)
        if not base_url.endswith("/"):
            test_urls.append(f"{base_url}/{payload}")
        else:
            test_urls.append(f"{base_url}{payload}")
        
        # Test each URL
        for test_url in test_urls:
            try:
                response = session.get(test_url, timeout=10, verify=False)
                
                # Check for common LFI indicators
                if check_lfi_indicators(response.text):
                    print(f"[+] Potential LFI found: {test_url}")
                    return True
                    
            except requests.exceptions.RequestException as e:
                # Skip individual URL errors but continue testing
                continue
                
    except Exception as e:
        print(f"Error during LFI detection: {e}")
    
    return False

def check_lfi_indicators(response_text):
    """
    Check response for LFI indicators
    """
    # Linux/Unix indicators
    linux_indicators = [
        "root:x:0:0:root",
        "daemon:x:",
        "bin:x:",
        "sys:x:",
        "/bin/bash",
        "/bin/sh",
        "nobody:x:",
        "/etc/passwd"
    ]
    
    # Windows indicators
    windows_indicators = [
        "[boot loader]",
        "[operating systems]",
        "multi(0)disk(0)",
        "[fonts]",
        "[extensions]",
        "ECHO is on",
        "Volume in drive C",
        "[drivers]"
    ]
    
    # Check for indicators
    response_lower = response_text.lower()
    
    for indicator in linux_indicators + windows_indicators:
        if indicator.lower() in response_lower:
            return True
    
    return False

def scan_lfi(url, session, lfi_payloads):
    """
    Main LFI scanning function
    """
    print(f"Scanning LFI for {url}")
    
    found_lfi = False
    
    for payload in lfi_payloads:
        if detect_lfi(session, url, payload):
            print(f"[+] LFI vulnerability found with payload: {payload}")
            found_lfi = True
            # Don't break here, continue testing to find more vulnerabilities
    
    if not found_lfi:
        print("[-] No LFI vulnerabilities found.")
    
    return found_lfi


