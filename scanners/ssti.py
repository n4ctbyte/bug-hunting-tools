
# Path: BugHunterPro/scanners/ssti.py

def scan_ssti(url):
    print(f"Scanning SSTI for {url}")
    # SSTI scanning logic here
    pass




import requests

def detect_ssti(url, payload):
    try:
        response = requests.get(url + payload)
        if "49" in response.text: # For {{7*7}} payload
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error during SSTI detection: {e}")
    return False

def scan_ssti(url):
    print(f"Scanning SSTI for {url}")
    ssti_payloads = [
        "{{7*7}}",
        "${{7*7}}",
        "<%= 7*7 %>",
        "#{7*7}"
    ]

    found_ssti = False
    for payload in ssti_payloads:
        if detect_ssti(url, payload):
            print(f"[+] SSTI vulnerability found with payload: {payload}")
            found_ssti = True
            break
    if not found_ssti:
        print("[-] No SSTI vulnerabilities found.")


