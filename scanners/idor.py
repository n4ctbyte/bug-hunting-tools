import requests
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
import difflib
import hashlib
import time


def hash_response_content(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def is_significantly_different(text1, text2, threshold=0.9):
    seq = difflib.SequenceMatcher(None, text1, text2)
    return seq.quick_ratio() < threshold


def scan_idor(url, session, idor_payloads, auth_headers=None):
    print(f"[+] Scanning IDOR for {url}")
    found_idor = False

    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    
    # Get original response
    try:
        original_response = session.get(url, headers=auth_headers, timeout=10)
        original_hash = hash_response_content(original_response.text)
    except Exception as e:
        print(f"[-] Failed to get original response: {e}")
        return False

    for param, values in query_params.items():
        try:
            original_value = int(values[0])
            for offset in idor_payloads:
                test_value = original_value + int(offset)
                test_params = query_params.copy()
                test_params[param] = [str(test_value)]
                test_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, urlencode(test_params, doseq=True), parsed_url.fragment
                ))

                print(f"  [*] Testing with: {test_url}")
                try:
                    test_response = session.get(test_url, headers=auth_headers, timeout=10)

                    if test_response.status_code == 200:
                        if is_significantly_different(original_response.text, test_response.text):
                            print(f"  [+] Potential IDOR found! Changed content at: {test_url}")
                            found_idor = True
                            break
                        else:
                            print("     [-] Response too similar, skipping.")
                    else:
                        print(f"     [-] Status code: {test_response.status_code}, probably protected.")

                except requests.RequestException as e:
                    print(f"     [-] Error accessing {test_url}: {e}")
                    continue

            if found_idor:
                break

        except ValueError:
            print(f"[-] Parameter '{param}' is not an integer, skipping.")
            continue

    if not found_idor:
        print("[-] No IDOR vulnerabilities found (advanced check).")
    return found_idor


if __name__ == "__main__":
    session = requests.Session()
    url = "http://example.com/view?id=1"
    payloads = [-2, -1, 1, 2, 10, 100]
    scan_idor(url, session, payloads)