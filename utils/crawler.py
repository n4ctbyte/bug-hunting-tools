import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

class ParameterDiscovery:
    def __init__(self, session):
        self.session = session

    def find_urls_with_parameters(self, base_url, max_depth=2):
        found_urls = set()
        visited = set()
        to_visit = [(base_url, 0)]

        while to_visit:
            current_url, depth = to_visit.pop(0)

            if depth > max_depth or current_url in visited:
                continue

            visited.add(current_url)
            print(f"Crawling: {current_url} (depth: {depth})")

            try:
                response = self.session.get(current_url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find <a> tags with href
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)

                    if self.has_parameters(full_url) and self.is_valid_target_url(full_url):
                        found_urls.add(full_url)
                        print(f"[+] Found URL with parameters: {full_url}")

                    if depth < max_depth and self.is_same_domain(base_url, full_url) and self.is_valid_target_url(full_url):
                        to_visit.append((full_url, depth + 1))

                # Find forms with GET method
                for form in soup.find_all('form'):
                    action = form.get('action', '')
                    method = form.get('method', 'get').lower()

                    if method == 'get':
                        form_url = urljoin(current_url, action)
                        inputs = form.find_all(['input', 'select', 'textarea'])
                        test_params = []

                        for input_tag in inputs[:3]:
                            name = input_tag.get('name')
                            if name and input_tag.get('type', '').lower() not in ['submit', 'button']:
                                test_params.append(f"{name}=test")

                        if test_params:
                            test_url = f"{form_url}?{'&'.join(test_params)}"
                            if self.is_valid_target_url(test_url):
                                found_urls.add(test_url)
                                print(f"[+] Found form URL: {test_url}")

                # Additional tag parsing (script, iframe, link)
                for tag in soup.find_all(['script', 'iframe', 'link']):
                    src = tag.get('src') or tag.get('href')
                    if src:
                        full_url = urljoin(current_url, src)
                        if self.is_same_domain(base_url, full_url) and self.is_valid_target_url(full_url):
                            to_visit.append((full_url, depth + 1))

                # JavaScript URLs from raw text
                js_urls = self.extract_js_urls(response.text, current_url)
                for js_url in js_urls:
                    if self.has_parameters(js_url) and self.is_valid_target_url(js_url):
                        found_urls.add(js_url)
                        print(f"[+] Found JS URL with parameters: {js_url}")

            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
                continue

        return list(found_urls)

    def has_parameters(self, url):
        parsed = urlparse(url)
        return bool(parsed.query)

    def is_same_domain(self, base_url, check_url):
        base = urlparse(base_url).netloc
        check = urlparse(check_url).netloc
        return check == base or check.endswith('.' + base)

    def is_valid_target_url(self, url):
        skip_keywords = ['fonts.', 'google.com', 'gstatic.com', 'youtube.com', 'doubleclick.net',
                         'googletagmanager.com', 'analytics.']
        return not any(keyword in url for keyword in skip_keywords)

    def extract_js_urls(self, html_content, base_url):
        """Extract only real URLs with query‑string from inline JS"""
        js_urls = set()

        # cari pola "https://…?…" atau "/…?…"
        url_pattern = re.compile(r'''["']((?:https?:)?//[^"']+\?.+?|/[^"'<> ]+\?.+?)["']''')
        matches = url_pattern.findall(html_content)

        for raw in matches:
            full = urljoin(base_url, raw)
            if self.is_same_domain(base_url, full):
                js_urls.add(full)

        return js_urls

    def discover_common_endpoints(self, base_url):
        common_endpoints = [
            '/search?q=test',
            '/api/search?query=test',
            '/product?id=1',
            '/user?id=1',
            '/page?id=1',
            '/category?cat=1',
            '/news?id=1',
            '/article?id=1',
            '/item?id=1',
            '/view?id=1',
            '/detail?id=1',
            '/show?id=1'
        ]

        found_endpoints = []
        base_parsed = urlparse(base_url)
        base_domain = f"{base_parsed.scheme}://{base_parsed.netloc}"

        print(f"Testing common endpoints on {base_domain}...")

        for endpoint in common_endpoints:
            test_url = base_domain + endpoint
            try:
                response = self.session.get(test_url, timeout=5)
                if response.status_code == 200:
                    found_endpoints.append(test_url)
                    print(f"[+] Found endpoint: {test_url}")
                else:
                    print(f"[-] {test_url} returned status {response.status_code}")
            except:
                continue

        return found_endpoints


def scan_sqli_with_discovery(url, session):
    print(f"Starting parameter discovery for {url}")
    discovery = ParameterDiscovery(session)
    param_urls = discovery.find_urls_with_parameters(url, max_depth=2)
    endpoint_urls = discovery.discover_common_endpoints(url)

    all_urls = list(set(param_urls + endpoint_urls))

    if not all_urls:
        print("[-] No URLs with parameters found")
        return [], []

    print(f"\n[+] Found {len(all_urls)} URLs with parameters to test:")
    for test_url in all_urls:
        print(f"    {test_url}")

    # Ekstraksi semua parameter unik dari URL yang ditemukan
    found_parameters = set()
    for test_url in all_urls:
        parsed = urlparse(test_url)
        params = parse_qs(parsed.query)
        for param in params:
            found_parameters.add(param)

    return all_urls, list(found_parameters)