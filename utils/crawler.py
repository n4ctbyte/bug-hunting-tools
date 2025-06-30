import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

class ParameterDiscovery:
    def __init__(self, session, max_depth=2, skip_exts=None):
        self.session = session
        self.max_depth = max_depth
        # Skip static resource extensions
        self.skip_exts = skip_exts or [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.eot', '.ttf', '.css', '.js'
        ]

    def find_urls_with_parameters(self, base_url):
        found = set()
        visited = set()
        queue = [(base_url, 0)]

        while queue:
            url, depth = queue.pop(0)
            if depth > self.max_depth or url in visited:
                continue
            visited.add(url)
            print(f"Crawling: {url} (depth={depth})")

            try:
                resp = self.session.get(url, timeout=10)
                if not self._is_html(resp):
                    continue
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Extract links, iframes, form actions
                for tag in soup.find_all(['a', 'iframe', 'form']):
                    link = self._get_link_from_tag(url, tag)
                    if not link or link in visited:
                        continue
                    if self._is_same_domain(base_url, link):
                        if self._has_params(link):
                            found.add(link)
                            print(f"[+] Parameter URL: {link}")
                        queue.append((link, depth+1))

                # Extract JS-embedded URLs
                for js_url in self._extract_js_urls(resp.text, url):
                    if js_url not in visited:
                        if self._has_params(js_url):
                            found.add(js_url)
                            print(f"[+] JS Parameter URL: {js_url}")
                        queue.append((js_url, depth+1))

            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue

        return list(found)

    def discover_common_endpoints(self, base_url):
        paths = [
            '/search?q=test', '/api/search?query=test', '/product?id=1',
            '/user?id=1', '/page?id=1', '/category?cat=1',
            '/news?id=1', '/article?id=1'
        ]
        domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        found = []
        print(f"Testing common endpoints on {domain}")
        for p in paths:
            u = domain + p
            try:
                r = self.session.get(u, timeout=5)
                if r.status_code == 200 and self._is_html(r):
                    found.append(u)
                    print(f"[+] Found endpoint: {u}")
            except Exception:
                continue
        return found

    def _is_html(self, response):
        ct = response.headers.get('Content-Type', '')
        path = urlparse(response.url).path.lower()
        if any(path.endswith(ext) for ext in self.skip_exts):
            return False
        return 'html' in ct.lower()

    def _has_params(self, url):
        return bool(urlparse(url).query)

    def _is_same_domain(self, base, url):
        base_net = urlparse(base).netloc
        check_net = urlparse(url).netloc
        return check_net == base_net or check_net.endswith('.' + base_net)

    def _get_link_from_tag(self, base, tag):
        if tag.name == 'a' and tag.has_attr('href'):
            return urljoin(base, tag['href'])
        if tag.name == 'iframe' and tag.has_attr('src'):
            return urljoin(base, tag['src'])
        if tag.name == 'form' and tag.has_attr('action'):
            action = urljoin(base, tag['action'])
            if tag.get('method', '').lower() == 'get':
                params = []
                for inp in tag.find_all(['input', 'select', 'textarea']):
                    name = inp.get('name')
                    if name:
                        params.append(f"{name}=test")
                if params:
                    return f"{action}?{'&'.join(params)}"
        return None

    def _extract_js_urls(self, text, base):
        # Match URLs with query parameters inside JS strings
        pattern = re.compile(r'["\']((?:https?:)?//[^"\']+\?.+?)["\']')
        matches = pattern.findall(text)
        js_urls = set(urljoin(base, m) for m in matches)
        return [u for u in js_urls if self._is_same_domain(base, u)]


def scan_sqli_with_discovery(base_url, session):
    print(f"Starting discovery for {base_url}")
    pd = ParameterDiscovery(session)
    param_urls = pd.find_urls_with_parameters(base_url)
    common = pd.discover_common_endpoints(base_url)
    all_urls = list(set(param_urls + common))
    print(f"Total URLs with parameters: {len(all_urls)}")
    return all_urls, list({k for u in all_urls for k in parse_qs(urlparse(u).query)})