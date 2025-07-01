import requests
import socket
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Improved Subdomain Enumerator
# - DNS resolution before HTTP request
# - HTTPS fallback
# - Concurrency with ThreadPoolExecutor
# - Customizable timeout and threads

def is_resolvable(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def check_subdomain(sub, target, timeout, use_https):
    protocol = 'https' if use_https else 'http'
    url = f"{protocol}://{sub}.{target}"
    # DNS resolution first
    if not is_resolvable(f"{sub}.{target}"):
        return None
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return url
    except requests.RequestException:
        # on failure, try alternate protocol
        if not use_https:
            return check_subdomain(sub, target, timeout, True)
    return None


def enumerate_subdomains(target, wordlist_path, timeout=3, threads=30):
    found = []
    with open(wordlist_path) as f:
        subs = [line.strip() for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(check_subdomain, sub, target, timeout, False): sub
            for sub in subs
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"[+] Found: {result}")
                found.append(result)

    if not found:
        print("[-] No valid subdomains found.")
    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Concurrent Subdomain Enumerator')
    parser.add_argument('target', help='e.g., example.com')
    parser.add_argument('wordlist', help='Path to subdomain wordlist')
    parser.add_argument('-t', '--timeout', type=int, default=3, help='Request timeout')
    parser.add_argument('-T', '--threads', type=int, default=30, help='Number of threads')
    args = parser.parse_args()

    print(f"Starting enumeration on {args.target} with {args.threads} threads...")
    results = enumerate_subdomains(args.target, args.wordlist, args.timeout, args.threads)
    print(f"\nEnumeration complete: {len(results)} subdomains found.")