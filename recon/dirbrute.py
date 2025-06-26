
# Path: BugHunterPro/recon/dirbrute.py

def brute_directories(url):
    print(f"Bruteforcing directories for {url}")
    # Directory bruteforcing logic here
    pass




import requests

def brute_directories(url, wordlist_path="/home/ubuntu/BugHunterPro/payloads/common_dirs.txt"):
    print(f"Bruteforcing directories for {url}")
    found_dirs = []
    try:
        with open(wordlist_path, "r") as f:
            wordlist = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: Wordlist not found at {wordlist_path}")
        return []

    for directory in wordlist:
        target_url = f"{url}/{directory}"
        try:
            response = requests.get(target_url, timeout=2)
            if response.status_code == 200:
                print(f"[+] Found directory: {target_url}")
                found_dirs.append(target_url)
        except requests.exceptions.RequestException:
            pass
    if not found_dirs:
        print("[-] No directories found.")
    return found_dirs


