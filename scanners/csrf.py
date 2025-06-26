
# Path: BugHunterPro/scanners/csrf.py

def scan_csrf(url):
    print(f"Scanning CSRF for {url}")
    # CSRF scanning logic here
    pass




import requests
from bs4 import BeautifulSoup

def scan_csrf(url):
    print(f"Scanning CSRF for {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')

        if not forms:
            print("[-] No forms found on the page, likely no CSRF vulnerability related to forms.")
            return

        for form in forms:
            # Check for CSRF tokens in hidden fields
            csrf_token_found = False
            for input_tag in form.find_all('input', type='hidden'):
                if 'csrf' in input_tag.get('name', '').lower() or \
                   'token' in input_tag.get('name', '').lower():
                    csrf_token_found = True
                    break
            
            if not csrf_token_found:
                print(f"[+] Potential CSRF vulnerability: No CSRF token found in form: {form.get('action') or url}")
            else:
                print(f"[-] CSRF token found in form: {form.get('action') or url}")

    except requests.exceptions.RequestException as e:
        print(f"Error during CSRF detection: {e}")


