import requests
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

def scan_idor(url, session, idor_payloads):
    print(f"Scanning IDOR for {url}")
    found_idor = False

    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)

    for param, values in query_params.items():
        try:
            original_value = int(values[0])
            for payload_offset in idor_payloads:
                test_value = original_value + int(payload_offset)
                test_params = query_params.copy()
                test_params[param] = [str(test_value)]
                test_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, urlencode(test_params, doseq=True), parsed_url.fragment
                ))

                print(f"Testing IDOR with: {test_url}")
                response = session.get(test_url, timeout=10)

                # Simple check: if the response is 200 OK and content is similar to original
                # This is a very basic check and needs refinement for real-world scenarios
                if response.status_code == 200 and len(response.text) > 0:
                    print(f"[+] Potential IDOR vulnerability found with URL: {test_url}")
                    found_idor = True
                    # In a real scenario, you\'d compare content, check for sensitive data, etc.
                    # For now, we\'ll just report potential access.
                    break # Found one, move to next parameter or stop
            if found_idor: # If IDOR found for this parameter, move to next parameter
                break
        except ValueError:
            # Parameter is not an integer, skip for simple IDOR test
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error during IDOR detection for {test_url}: {e}")
            continue

    if not found_idor:
        print("[-] No IDOR vulnerabilities found (basic check).")
    return found_idor


