import argparse
import os
import json

from scanners.xss import scan_xss
from scanners.sqli import scan_sqli
from scanners.lfi import scan_lfi
from scanners.idor import scan_idor
from scanners.portscan import scan_ports
from scanners.ssti import scan_ssti
from scanners.rce import scan_rce
from scanners.csrf import scan_csrf
from scanners.cors import scan_cors
from scanners.open_redirect import scan_open_redirect

from recon.subdomains import enumerate_subdomains
from recon.dirbrute import brute_directories

from utils.crawler import scan_sqli_with_discovery
from utils.reporter import generate_report
from utils.config import get_session, load_config

def main():
    parser = argparse.ArgumentParser(description="BugHunterPro - Advanced Bug Hunting Toolkit")

    # Target
    parser.add_argument("--url", help="Target URL, e.g., https://example.com/page?id=1")
    parser.add_argument("--target_host", help="Target host for port scan and subdomain enumeration (e.g., example.com)")

    # Recon arguments
    parser.add_argument("--recon", action="store_true", help="Run all recon tools (subdomain, port scan, dir brute)")
    parser.add_argument("--portscan", action="store_true", help="Run port scanner only")
    parser.add_argument("--subdomain", action="store_true", help="Run subdomain enumeration only")
    parser.add_argument("--wordlist", help="Path to subdomain wordlist (overrides config)")
    parser.add_argument("--timeout", type=int, default=3, help="Subdomain enumeration timeout")
    parser.add_argument("--threads", type=int, default=30, help="Subdomain enumeration threads")

    # Scan options
    parser.add_argument("--all", action="store_true", help="Run all scanners")
    parser.add_argument("--xss", action="store_true", help="Run XSS scanner")
    parser.add_argument("--sqli", action="store_true", help="Run SQL Injection scanner")
    parser.add_argument("--lfi", action="store_true", help="Run Local File Inclusion scanner")
    parser.add_argument("--idor", action="store_true", help="Run IDOR tester")
    parser.add_argument("--ssti", action="store_true", help="Run SSTI scanner")
    parser.add_argument("--rce", action="store_true", help="Run RCE scanner")
    parser.add_argument("--csrf", action="store_true", help="Run CSRF scanner")
    parser.add_argument("--cors", action="store_true", help="Run CORS Misconfiguration scanner")
    parser.add_argument("--open_redirect", action="store_true", help="Run Open Redirect scanner")

    # Custom headers
    parser.add_argument("--user_agent", help="Set custom User-Agent")
    parser.add_argument("--cookies", help="Set custom cookies (JSON string)")
    parser.add_argument("--proxy", help="Set proxy (e.g., http://127.0.0.1:8080)")

    # Output
    parser.add_argument("--output", default="txt", choices=["txt", "json", "csv"], help="Output format")
    parser.add_argument("--output_file", default="report", help="Output filename (without extension)")

    args = parser.parse_args()

    if not args.url and not args.target_host:
        parser.error("--url or --target_host is required")

    # Load config
    config = load_config()

    # Determine subdomain wordlist path
    wordlist_path = args.wordlist or config["wordlists"]["subdomains"]
    if (args.recon or args.subdomain) and not os.path.isfile(wordlist_path):
        print(f"[!] Wordlist file not found: {wordlist_path}")
        exit(1)

    # Session Setup
    user_agent = args.user_agent or config["settings"]["user_agent"]
    cookies = None
    if args.cookies:
        try:
            cookies = json.loads(args.cookies)
        except json.JSONDecodeError:
            print("[!] Invalid JSON format for cookies.")
            exit(1)

    proxy = {"http": args.proxy, "https": args.proxy} if args.proxy else config["settings"]["proxy"]
    session = get_session(user_agent, cookies, proxy)

    results = {}

    # Scanning by URL
    if args.url:
        print(f"Target URL: {args.url}")
        visited_urls, found_params = scan_sqli_with_discovery(args.url, session)
        results["crawled_urls"] = visited_urls
        results["found_parameters"] = list(found_params)

        if args.all or args.xss:
            results["xss_findings"] = scan_xss(visited_urls, session, config["payloads"]["xss"])
        if args.all or args.sqli:
            results["sqli_findings"] = scan_sqli(visited_urls, session, config["payloads"]["sqli"])
        if args.all or args.lfi:
            results["lfi_findings"] = scan_lfi(args.url, session, config["payloads"]["lfi"])
        if args.all or args.idor:
            results["idor_findings"] = scan_idor(args.url, session, config["payloads"]["idor"])
        if args.all or args.ssti:
            results["ssti_findings"] = scan_ssti(args.url, session)
        if args.all or args.rce:
            results["rce_findings"] = scan_rce(args.url, session, config["payloads"]["rce"])
        if args.all or args.csrf:
            csrf_vuln = scan_csrf(args.url, session)
            results["csrf_findings"] = {
                "vulnerable": csrf_vuln,
                "details": "Confirmed: Form accepted without CSRF token" if csrf_vuln else "No obvious CSRF detected"
            }
        if args.all or args.cors:
            results["cors_findings"] = scan_cors(args.url, session, config["payloads"]["cors"])
        if args.all or args.open_redirect:
            results["open_redirect_findings"] = scan_open_redirect(args.url, session, config["payloads"]["open_redirect"])
        if args.all or args.recon:
            results["dir_bruteforce"] = brute_directories(args.url, session, config["wordlists"]["common_dirs"])

    # Scanning by Host
    if args.target_host:
        print(f"Target Host: {args.target_host}")
        if args.all or args.recon or args.portscan:
            results["open_ports"] = scan_ports(args.target_host)
        if args.all or args.recon or args.subdomain:
            results["subdomains"] = enumerate_subdomains(
                args.target_host,
                wordlist_path,
                args.timeout,
                args.threads
            )

    # Save report
    generate_report(results, args.output, args.output_file)

if __name__ == "__main__":
    main()