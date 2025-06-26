import requests

def enumerate_subdomains(target, session, wordlist_path):
    print(f"Enumerating subdomains for {target}")
    subdomains = []
    try:
        with open(wordlist_path, "r") as f:
            wordlist = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: Wordlist not found at {wordlist_path}")
        return False

    for sub in wordlist:
        try:
            url = f"http://{sub}.{target}"
            response = session.get(url, timeout=2)
            if response.status_code < 400:
                print(f"[+] Found subdomain: {url}")
                subdomains.append(url)
        except requests.exceptions.RequestException:
            pass
    if not subdomains:
        print("[-] No subdomains found.")
    return len(subdomains) > 0


