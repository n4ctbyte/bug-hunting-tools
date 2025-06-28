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
    parser.add_argument("--url", help="Target URL")
    parser.add_argument("--target_host", help="Target host for port scan and subdomain enumeration (e.g., example.com)")

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
    parser.add_argument("--recon", action="store_true", help="Run all recon tools (subdomain, port scan, dir brute)")
    parser.add_argument("--portscan", action="store_true", help="Run port scanner only")
    parser.add_argument("--subdomain", action="store_true", help="Run subdomain enumeration only")

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

    config = load_config()

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
        visited_urls, found_parameters = scan_sqli_with_discovery(args.url, session)
        results["crawled_urls"] = visited_urls
        results["found_parameters"] = list(found_parameters)

        if args.all or args.xss:
            results["xss_findings"] = scan_xss(args.url, session, config["payloads"]["xss"])
        if args.all or args.sqli:
            sqli_findings = []
            for test_url in visited_urls:
                if scan_sqli(test_url, session, config["payloads"]["sqli"]):
                    sqli_findings.append(test_url)
            results["sqli_findings"] = sqli_findings
        if args.all or args.lfi:
            results["lfi_findings"] = scan_lfi(args.url, session, config["payloads"]["lfi"])
        if args.all or args.idor:
            results["idor_findings"] = scan_idor(args.url, session, config["payloads"]["idor"])
        if args.all or args.ssti:
            results["ssti_findings"] = scan_ssti(args.url, session, config["payloads"]["ssti"])
        if args.all or args.rce:
            results["rce_findings"] = scan_rce(args.url, session, config["payloads"]["rce"])
        if args.all or args.csrf:
            results["csrf_findings"] = scan_csrf(args.url, session, config["payloads"]["csrf"])
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
            results["subdomains"] = enumerate_subdomains(args.target_host, session, config["wordlists"]["subdomains"])

    # Save report
    generate_report(results, args.output, args.output_file)

if __name__ == "__main__":
    main()