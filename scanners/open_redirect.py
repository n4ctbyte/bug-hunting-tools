
# Path: BugHunterPro/scanners/open_redirect.py

def scan_open_redirect(url):
    print(f"Scanning Open Redirect for {url}")
    # Open Redirect scanning logic here
    pass




import requests

def scan_open_redirect(url):
    print(f"Scanning Open Redirect for {url}")
    redirect_payloads = [
        "//google.com",
        "https://google.com",
        "//evil.com"
    ]

    found_redirect = False
    for payload in redirect_payloads:
        test_url = f"{url}?next={payload}" # Common parameter for redirects
        try:
            response = requests.get(test_url, allow_redirects=False)
            if response.status_code in [301, 302, 303, 307, 308] and payload in response.headers.get("Location", ""):
                print(f"[+] Open Redirect vulnerability found with payload: {payload}")
                found_redirect = True
                break
        except requests.exceptions.RequestException as e:
            print(f"Error during Open Redirect detection: {e}")
    if not found_redirect:
        print("[-] No Open Redirect vulnerabilities found.")


