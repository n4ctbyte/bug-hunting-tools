import requests

def brute_directories(url, session, wordlist_path):
    print(f"Bruteforcing directories for {url}")
    found_dirs = []
    try:
        with open(wordlist_path, "r") as f:
            wordlist = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: Wordlist not found at {wordlist_path}")
        return False

    for directory in wordlist:
        target_url = f"{url}/{directory}"
        try:
            response = session.get(target_url, timeout=2)
            if response.status_code == 200:
                print(f"[+] Found directory: {target_url}")
                found_dirs.append(target_url)
        except requests.exceptions.RequestException:
            pass
    if not found_dirs:
        print("[-] No directories found.")
    return len(found_dirs) > 0


