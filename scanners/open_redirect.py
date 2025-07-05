import requests
from urllib.parse import urlparse


def scan_open_redirect(
    url, session, open_redirect_payloads=None, redirect_params=None, follow_redirects=False
):
    """
    Mendeteksi celah Open Redirect.
    - url: target base URL
    - session: objek requests.Session()
    - open_redirect_payloads: list payload redirect
    - redirect_params: list parameter redirect yang umum
    - follow_redirects: aktifkan pengecekan redirect sungguhan
    """
    if open_redirect_payloads is None:
        open_redirect_payloads = [
            "https://evil.com",
            "//evil.com",
            "%2F%2Fevil.com",
            "/%2Fevil.com",
            "///evil.com"
        ]

    if redirect_params is None:
        redirect_params = ["redirect", "url", "next", "continue", "jumpUrl"]

    session.headers.update({"X-HackerOne-Research": "n4ctbyte"})

    parsed_target = urlparse(url)
    base_host = parsed_target.netloc

    print(f"\n[~] Mulai scan Open Redirect: {url}\n")

    for param in redirect_params:
        for payload in open_redirect_payloads:
            test_url = f"{url}?{param}={payload}"

            try:
                resp = session.get(test_url, allow_redirects=False, timeout=10)
                location = resp.headers.get("Location", "")

                print(f"[{resp.status_code}] {test_url}")
                if location:
                    print(f"    ↳ Location header: {location}")

                # Jika server mengarahkan langsung ke domain luar
                if resp.status_code in (301, 302, 303, 307, 308):
                    loc_host = urlparse(location).netloc
                    if location.lower().startswith(payload.lower()) and loc_host and loc_host != base_host:
                        print(f"\n[+] VULNERABLE! Open Redirect ditemukan:")
                        print(f"    Parameter : {param}")
                        print(f"    Payload   : {payload}")
                        print(f"    Redirect  : {location}\n")
                        return True

                # Tambahan validasi: follow redirect sampai akhir (jika diaktifkan)
                if follow_redirects:
                    final_resp = session.get(test_url, allow_redirects=True, timeout=10)
                    final_url = final_resp.url
                    final_host = urlparse(final_url).netloc
                    if final_host and final_host != base_host and "evil.com" in final_host:
                        print(f"\n[+] Confirmed external redirect after following:")
                        print(f"    Final URL: {final_url}")
                        return True

            except requests.exceptions.RequestException as e:
                print(f"[!] Error saat request: {e}")

    print("\n[-] Tidak ditemukan celah Open Redirect.\n")
    return False