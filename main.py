#!/usr/bin/env python3

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
from utils.config import get_session


def main():
    parser = argparse.ArgumentParser(description="""BugHunterPro - Advanced Bug Hunting Toolkit""")
    parser.add_argument("--url", help="Target URL")
    parser.add_argument("--target_host", help="Target Host for Port Scan and Subdomain Enumeration (e.g., example.com)")
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
    parser.add_argument("--recon", action="store_true", help="Run reconnaissance tools (subdomain, port scan, directory brute)")
    parser.add_argument("--user_agent", help="Set custom User-Agent")
    parser.add_argument("--cookies", help="Set custom cookies (JSON string)")
    parser.add_argument("--proxy", help="Set proxy (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--output", default="txt", choices=["txt", "json", "csv"], help="Output format (txt, json, csv)")
    parser.add_argument("--output_file", default="report", help="Output filename (without extension)")

    args = parser.parse_args()

    if not args.url and not args.target_host:
        parser.error("--url or --target_host is required")

    session = get_session(
        args.user_agent,
        json.loads(args.cookies) if args.cookies else None,
        {"http": args.proxy, "https": args.proxy} if args.proxy else None
    )

    results = {}

    # CRAWLING & PARAMETER ENUMERATION
    if args.url:
        print(f"Target URL: {args.url}")
        visited_urls, found_parameters = scan_sqli_with_discovery(args.url)
        results["crawled_urls"] = visited_urls
        results["found_parameters"] = list(found_parameters)

        # XSS Scanner
        if args.all or args.xss:
            xss_findings = scan_xss(args.url)
            results["xss_findings"] = xss_findings

        # SQLi Scanner
        if args.all or args.sqli:
            sqli_findings = scan_sqli(args.url)
            results["sqli_findings"] = sqli_findings

        # LFI Scanner
        if args.all or args.lfi:
            lfi_findings = scan_lfi(args.url)
            results["lfi_findings"] = lfi_findings

        # IDOR Scanner
        if args.all or args.idor:
            idor_findings = scan_idor(args.url)
            results["idor_findings"] = idor_findings

        # SSTI Scanner
        if args.all or args.ssti:
            ssti_findings = scan_ssti(args.url)
            results["ssti_findings"] = ssti_findings

        # RCE Scanner
        if args.all or args.rce:
            rce_findings = scan_rce(args.url)
            results["rce_findings"] = rce_findings

        # CSRF Scanner
        if args.all or args.csrf:
            csrf_findings = scan_csrf(args.url)
            results["csrf_findings"] = csrf_findings

        # CORS Scanner
        if args.all or args.cors:
            cors_findings = scan_cors(args.url)
            results["cors_findings"] = cors_findings

        # Open Redirect Scanner
        if args.all or args.open_redirect:
            redirect_findings = scan_open_redirect(args.url)
            results["open_redirect_findings"] = redirect_findings

        # Directory Bruteforce (Recon)
        if args.all or args.recon:
            dir_findings = brute_directories(args.url)
            results["dir_bruteforce"] = dir_findings

    # PORT SCAN & SUBDOMAIN ENUMERATION
    if args.target_host:
        print(f"Target Host: {args.target_host}")
        if args.all or args.recon:
            open_ports = scan_ports(args.target_host)
            results["open_ports"] = open_ports

            subdomains = enumerate_subdomains(args.target_host)
            results["subdomains"] = subdomains

    # GENERATE FINAL REPORT
    generate_report(results, args.output, args.output_file)


if __name__ == "__main__":
    main()
