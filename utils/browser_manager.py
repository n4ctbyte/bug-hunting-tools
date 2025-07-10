from playwright_stealth import Stealth
print(f"DEBUG: Using Stealth class from: {Stealth.__module__}")
import asyncio
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import random
import time

class BrowserManager:
    def __init__(self):
        self.playwright_browser = None
        self.playwright_context = None
        self.playwright_page = None
        self.selenium_driver = None
        self.uc_driver = None

    async def init_playwright(self, proxy=None):
        if not self.playwright_browser:
            p = await async_playwright().start()
            args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-zygote',
                '--single-process',
                '--incognito',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
            launch_options = {
                'headless': True,
                'args': args
            }
            if proxy:
                launch_options['proxy'] = {'server': proxy}

            self.playwright_browser = await p.chromium.launch(**launch_options)
            self.playwright_context = await self.playwright_browser.new_context(
                user_agent=self.generate_user_agent(),
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                    "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"Windows"'
                }
            )
            self.playwright_page = await self.playwright_context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(self.playwright_page)
        return self.playwright_page

    def generate_user_agent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/126.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
        ]
        return random.choice(user_agents)

    async def simulate_human_behavior_playwright(self, page):
        await page.evaluate("window.scrollTo(0, Math.floor(Math.random() * document.body.scrollHeight));")
        await asyncio.sleep(random.uniform(0.5, 1.5))

        try:
            viewport_size = page.viewport_size
            if viewport_size:
                width, height = viewport_size['width'], viewport_size['height']
                for _ in range(random.randint(1, 3)):
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.5))
        except Exception as e:
            print(f"Error simulating mouse movement in Playwright: {e}")

        if random.random() < 0.5:
            keys = ['a', 's', 'd', 'f', 'q', 'w', 'e', 'r', '1', '2', '3', '4', 'Tab', 'Enter']
            for _ in range(random.randint(1, 3)):
                await page.keyboard.press(random.choice(keys))
                await asyncio.sleep(random.uniform(0.1, 0.3))

        if random.random() < 0.2:
            try:
                elements = await page.query_selector_all('a, button, input[type="submit"]')
                if elements:
                    target_element = random.choice(elements)
                    await target_element.click(timeout=3000)
                    await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"Error simulating click in Playwright: {e}")

    async def solve_js_challenge_playwright(self, page):
        print("[!] Attempting to solve JavaScript challenge with Playwright...")
        await page.wait_for_load_state('networkidle', timeout=10000)
        await asyncio.sleep(random.uniform(2, 5))

        if await page.locator('div#cf-wrapper').is_visible():
            print("[!] Cloudflare challenge detected. Trying to click 'Verify you are human'...")
            try:
                await page.locator('input[type="checkbox"]').click(timeout=5000)
                await asyncio.sleep(random.uniform(3, 7))
            except Exception as e:
                print(f"Error clicking Cloudflare checkbox: {e}")
        
        print("[!] Generic wait for Akamai challenge resolution...")
        await asyncio.sleep(random.uniform(5, 10))

        if await page.evaluate("typeof Akamai !== 'undefined' && typeof Akamai.bmak !== 'undefined'"):
            print("[!] Akamai bmak.js detected. Attempting to execute...")
            try:
                sensor_data = await page.evaluate("Akamai.bmak.get_sensor_data()")
                print(f"[+] Akamai sensor_data: {sensor_data}")
            except Exception as e:
                print(f"Error getting Akamai sensor_data: {e}")
        
        current_url = page.url
        if "/cdn-cgi/" in current_url or "/akam/" in current_url:
            print("[!] JavaScript challenge might not be fully resolved. Still on challenge page.")
            return False
        return True

    async def fetch_playwright(self, url, headers=None, proxy=None):
        page = await self.init_playwright(proxy=proxy)
        try:
            if headers:
                await page.set_extra_http_headers(headers)
            
            await self.simulate_human_behavior_playwright(page)

            response = await page.goto(url, wait_until='domcontentloaded')
            html = await page.content()
            status_code = response.status

            if status_code in [403, 429] or "cloudflare" in html.lower() or "akamai" in html.lower():
                print("[!] WAF detected during initial fetch. Attempting to solve JS challenge...")
                if await self.solve_js_challenge_playwright(page):
                    print("[+] JavaScript challenge likely solved. Re-fetching content.")
                    response = await page.goto(url, wait_until='domcontentloaded')
                    html = await page.content()
                    status_code = response.status
                else:
                    print("[-] Failed to solve JavaScript challenge.")

            return html, status_code
        except Exception as e:
            print(f"Playwright fetch error: {e}")
            return "", 0

    def init_selenium(self, proxy=None):
        if not self.selenium_driver:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')

            self.selenium_driver = webdriver.Chrome(options=options)
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });")
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });")
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });")
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")
            self.selenium_driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                    "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"Windows"'
                }
            })
        return self.selenium_driver

    def simulate_human_behavior_selenium(self, driver):
        driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * document.body.scrollHeight));")
        time.sleep(random.uniform(0.5, 1.5))

        try:
            size = driver.get_window_size()
            width, height = size['width'], size['height']
            for _ in range(random.randint(1, 3)):
                x = random.randint(0, width)
                y = random.randint(0, height)
        except Exception as e:
            print(f"Error simulating mouse movement in Selenium: {e}")

        if random.random() < 0.5:
            keys = ['a', 's', 'd', 'f', 'q', 'w', 'e', 'r', '1', '2', '3', '4', webdriver.common.keys.Keys.TAB, webdriver.common.keys.Keys.ENTER]
            for _ in range(random.randint(1, 3)):
                driver.find_element(by=webdriver.common.by.By.TAG_NAME, value='body').send_keys(random.choice(keys))
                time.sleep(random.uniform(0.1, 0.3))

        if random.random() < 0.2:
            try:
                elements = driver.find_elements(by=webdriver.common.by.By.CSS_SELECTOR, value='a, button, input[type="submit"]')
                visible_elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                if visible_elements:
                    target_element = random.choice(visible_elements)
                    target_element.click()
                    time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"Error simulating click in Selenium: {e}")

    def solve_js_challenge_selenium(self, driver):
        print("[!] Attempting to solve JavaScript challenge with Selenium...")
        time.sleep(random.uniform(2, 5))

        try:
            checkbox = driver.find_element(by=webdriver.common.by.By.CSS_SELECTOR, value='input[type="checkbox"]')
            if checkbox.is_displayed():
                print("[!] Cloudflare challenge detected. Trying to click 'Verify you are human'...")
                checkbox.click()
                time.sleep(random.uniform(3, 7))
        except Exception as e:
            print(f"Error clicking Cloudflare checkbox: {e}")
        
        print("[!] Generic wait for Akamai challenge resolution...")
        time.sleep(random.uniform(5, 10))

        if driver.execute_script("return typeof Akamai !== 'undefined' && typeof Akamai.bmak !== 'undefined'"):
            print("[!] Akamai bmak.js detected. Attempting to execute...")
            try:
                sensor_data = driver.execute_script("return Akamai.bmak.get_sensor_data()")
                print(f"[+] Akamai sensor_data: {sensor_data}")
            except Exception as e:
                print(f"Error getting Akamai sensor_data: {e}")

        current_url = driver.current_url
        if "/cdn-cgi/" in current_url or "/akam/" in current_url:
            print("[!] JavaScript challenge might not be fully resolved. Still on challenge page.")
            return False
        return True

    def fetch_selenium(self, url, headers=None, proxy=None):
        driver = self.init_selenium(proxy=proxy)
        try:
            if headers:
                if 'User-Agent' in headers:
                    driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': headers['User-Agent']})
            
            self.simulate_human_behavior_selenium(driver)

            driver.get(url)
            html = driver.page_source
            status_code = 200
            try:
                status_code = driver.execute_script('return window.performance.getEntriesByType("resource")[0].responseStatus')
            except Exception:
                pass
            
            if status_code in [403, 429] or "cloudflare" in html.lower() or "akamai" in html.lower():
                print("[!] WAF detected during initial fetch. Attempting to solve JS challenge...")
                if self.solve_js_challenge_selenium(driver):
                    print("[+] JavaScript challenge likely solved. Re-fetching content.")
                    html = driver.page_source
                else:
                    print("[-] Failed to solve JavaScript challenge.")

            return html, status_code
        except Exception as e:
            print(f"Selenium fetch error: {e}")
            return "", 0

    def init_uc(self, proxy=None):
        if not self.uc_driver:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')
            self.uc_driver = uc.Chrome(options=options)
            self.uc_driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                    "Sec-CH-UA": '"Not_A Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"Windows"'
                }
            })
        return self.uc_driver

    def simulate_human_behavior_uc(self, driver):
        driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * document.body.scrollHeight));")
        time.sleep(random.uniform(0.5, 1.5))

        try:
            size = driver.get_window_size()
            width, height = size['width'], size['height']
            for _ in range(random.randint(1, 3)):
                x = random.randint(0, width)
                y = random.randint(0, height)
        except Exception as e:
            print(f"Error simulating mouse movement in Undetected-Chromedriver: {e}")

        if random.random() < 0.5:
            keys = ['a', 's', 'd', 'f', 'q', 'w', 'e', 'r', '1', '2', '3', '4', webdriver.common.keys.Keys.TAB, webdriver.common.keys.Keys.ENTER]
            for _ in range(random.randint(1, 3)):
                driver.find_element(by=webdriver.common.by.By.TAG_NAME, value='body').send_keys(random.choice(keys))
                time.sleep(random.uniform(0.1, 0.3))

        if random.random() < 0.2:
            try:
                elements = driver.find_elements(by=webdriver.common.by.By.CSS_SELECTOR, value='a, button, input[type="submit"]')
                visible_elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                if visible_elements:
                    target_element = random.choice(visible_elements)
                    target_element.click()
                    time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"Error simulating click in Undetected-Chromedriver: {e}")

    def solve_js_challenge_uc(self, driver):
        print("[!] Attempting to solve JavaScript challenge with Undetected-Chromedriver...")
        time.sleep(random.uniform(2, 5))

        try:
            checkbox = driver.find_element(by=webdriver.common.by.By.CSS_SELECTOR, value='input[type="checkbox"]')
            if checkbox.is_displayed():
                print("[!] Cloudflare challenge detected. Trying to click 'Verify you are human'...")
                checkbox.click()
                time.sleep(random.uniform(3, 7))
        except Exception as e:
            print(f"Error clicking Cloudflare checkbox: {e}")
        
        print("[!] Generic wait for Akamai challenge resolution...")
        time.sleep(random.uniform(5, 10))

        if driver.execute_script("return typeof Akamai !== 'undefined' && typeof Akamai.bmak !== 'undefined'"):
            print("[!] Akamai bmak.js detected. Attempting to execute...")
            try:
                sensor_data = driver.execute_script("return Akamai.bmak.get_sensor_data()")
                print(f"[+] Akamai sensor_data: {sensor_data}")
            except Exception as e:
                print(f"Error getting Akamai sensor_data: {e}")

        current_url = driver.current_url
        if "/cdn-cgi/" in current_url or "/akam/" in current_url:
            print("[!] JavaScript challenge might not be fully resolved. Still on challenge page.")
            return False
        return True

    def fetch_uc(self, url, headers=None, proxy=None):
        driver = self.init_uc(proxy=proxy)
        try:
            if headers:
                if 'User-Agent' in headers:
                    driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': headers['User-Agent']})
            
            self.simulate_human_behavior_uc(driver)

            driver.get(url)
            html = driver.page_source
            status_code = 200
            try:
                status_code = driver.execute_script('return window.performance.getEntriesByType("resource")[0].responseStatus')
            except Exception:
                pass
            
            if status_code in [403, 429] or "cloudflare" in html.lower() or "akamai" in html.lower():
                print("[!] WAF detected during initial fetch. Attempting to solve JS challenge...")
                if self.solve_js_challenge_uc(driver):
                    print("[+] JavaScript challenge likely solved. Re-fetching content.")
                    html = driver.page_source
                else:
                    print("[-] Failed to solve JavaScript challenge.")

            return html, status_code
        except Exception as e:
            print(f"Undetected-Chromedriver fetch error: {e}")
            return "", 0

    async def close_all(self):
        if self.playwright_page:
            await self.playwright_page.close()
        if self.playwright_context:
            await self.playwright_context.close()
        if self.playwright_browser:
            await self.playwright_browser.close()
        if self.selenium_driver:
            self.selenium_driver.quit()
        if self.uc_driver:
            self.uc_driver.quit()

async def main():
    manager = BrowserManager()
    try:
        print("Testing Playwright...")
        html_pw, status_pw = await manager.fetch_playwright("http://httpbin.org/headers", headers={'User-Agent': 'PlaywrightTestAgent'})
        print(f"Playwright Status: {status_pw}, HTML length: {len(html_pw)}")

        print("Testing Selenium...")
        html_sel, status_sel = manager.fetch_selenium("http://httpbin.org/headers", headers={'User-Agent': 'SeleniumTestAgent'})
        print(f"Selenium Status: {status_sel}, HTML length: {len(html_sel)}")

        print("Testing Undetected-Chromedriver...")
        html_uc, status_uc = manager.fetch_uc("http://httpbin.org/headers", headers={'User-Agent': 'UCTestAgent'})
        print(f"UC Status: {status_uc}, HTML length: {len(html_uc)}")

    finally:
        await manager.close_all()

if __name__ == "__main__":
    asyncio.run(main())