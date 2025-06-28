import requests


def scan_open_redirect(url, session, open_redirect_payloads=None, redirect_params=None):
    """
    Mencari celah Open Redirect pada berbagai parameter dan payload.
    - url: base URL target (misal "https://career.oppo.com")
    - session: objek requests.Session() yang sudah dikonfigurasi
    - open_redirect_payloads: list payload URL yang akan diuji
    - redirect_params: list nama parameter yang akan diuji
    """
    # Default payloads jika tidak diberikan
    if open_redirect_payloads is None:
        open_redirect_payloads = [
            "https://evil.com",
            "//evil.com",
            "%2F%2Fevil.com",
            "/%2Fevil.com",
            "///evil.com"
        ]
    # Default parameter jika tidak diberikan
    if redirect_params is None:
        redirect_params = ["jumpUrl", "redirect", "url", "next", "continue"]

    # Tambahkan header riset (untuk production sites seperti OPPO)
    session.headers.update({"X-HackerOne-Research": "n4ctbyte"})

    print(f"Mulai scan Open Redirect di {url}\n")
    found = False

    for param in redirect_params:
        for payload in open_redirect_payloads:
            test_url = f"{url}?{param}={payload}"
            try:
                resp = session.get(test_url, allow_redirects=False, timeout=10)
                loc = resp.headers.get("Location", "")
                print(f"[{resp.status_code}] {test_url} → Location: {loc}")

                # Cek status code redirect dan payload di header Location
                if resp.status_code in (301, 302, 303, 307, 308) \
                   and payload in loc \
                   and loc.startswith(("http://", "https://")):
                    print(f"\n[+] VULNERABLE! Open Redirect ditemukan:")
                    print(f"    Parameter : {param}")
                    print(f"    Payload   : {payload}")
                    print(f"    Redirect  : {loc}\n")
                    found = True
                    break

            except requests.exceptions.RequestException as e:
                print(f"    Error saat testing {test_url}: {e}")

        if found:
            break

    if not found:
        print("\n[-] Tidak ditemukan Open Redirect.\n")

    return found