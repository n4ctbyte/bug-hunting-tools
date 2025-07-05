import requests
from urllib.parse import urljoin

def brute_directories(url, session, wordlist_path):
    print(f"📂 Bruteforcing directories on: {url}")
    found_dirs = []

    try:
        with open(wordlist_path, "r") as f:
            wordlist = f.read().splitlines()
    except FileNotFoundError:
        print(f"[!] Wordlist not found: {wordlist_path}")
        return []

    if not url.endswith("/"):
        url += "/"

    for directory in wordlist:
        target_url = urljoin(url, directory)
        try:
            response = session.get(target_url, timeout=3, allow_redirects=True)

            # Status yang dianggap "menarik"
            if response.status_code in [200, 301, 302, 403, 401]:
                print(f"[+] Found: {target_url} (Status: {response.status_code})")
                found_dirs.append({
                    "url": target_url,
                    "status": response.status_code
                })

        except requests.exceptions.RequestException:
            pass

    if not found_dirs:
        print("[-] No accessible directories found.")
    return found_dirs