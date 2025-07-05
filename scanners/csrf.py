import requests
from bs4 import BeautifulSoup

def scan_csrf(url, session, csrf_payloads=None):
    print(f"Scanning CSRF for {url}")
    found_csrf = False
    csrf_payloads = csrf_payloads or []

    try:
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')

        if not forms:
            print("[-] No forms found on the page, likely no CSRF vulnerability related to forms.")
            return found_csrf

        for form in forms:
            action = form.get('action') or url
            method = form.get('method', 'get').lower()
            csrf_token_found = False
            data = {}

            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if not name:
                    continue
                if input_tag.get('type') == 'hidden' and ('csrf' in name.lower() or 'token' in name.lower()):
                    csrf_token_found = True
                data[name] = value

            if csrf_token_found:
                print(f"[-] CSRF token found in form: {action}")
                continue

            print(f"[+] Potential CSRF vulnerability: No CSRF token found in form: {action}")
            found_csrf = True

            # Kirim payload simulasi tanpa token
            for payload in csrf_payloads:
                if payload.strip().startswith("<img"):
                    print(f"[>] Test GET-based CSRF payload (img tag): {payload}")
                    # Kita bisa parse URL dari tag img src
                    soup_payload = BeautifulSoup(payload, 'html.parser')
                    img_tag = soup_payload.find('img')
                    if img_tag and img_tag.get('src'):
                        test_url = img_tag['src']
                        try:
                            r = session.get(test_url)
                            print(f"[!] Payload sent to {test_url} — Status: {r.status_code}")
                        except Exception as e:
                            print(f"[X] Error testing img CSRF payload: {e}")

                elif payload.strip().startswith("<form"):
                    print(f"[>] Found simulated POST-based CSRF payload (form auto-submit)")
                    # Hanya tampilkan payload karena menjalankan form submit JS butuh browser
                    print("[!] This form payload would be auto-submitted in browser context.")
                    print(payload[:100] + "...")  # Show snippet

    except requests.exceptions.RequestException as e:
        print(f"Error during CSRF detection: {e}")
    return found_csrf