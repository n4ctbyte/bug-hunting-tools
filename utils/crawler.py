import sys
import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

class ParameterDiscovery:
    def __init__(self, session, max_depth=2, skip_exts=None, priority_params=None):
        self.session = session
        self.max_depth = max_depth
        self.skip_exts = skip_exts or [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.eot', '.ttf', '.css', '.js', '.mp4'
        ]
        self.priority_params = priority_params or ['id', 'q', 'query', 'token', 'form', 'origin', 'redirect']

    def find_urls_with_parameters(self, base_url):
        raw_urls = self._crawl(base_url)
        return self._filter_and_dedup(raw_urls)

    def _crawl(self, base_url):
        found = []
        visited = set()
        queue = [(base_url.split('#')[0], 0)]

        while queue:
            url, depth = queue.pop(0)
            # Normalize URL by stripping fragment
            url = url.split('#')[0]
            if depth > self.max_depth or url in visited:
                continue
            visited.add(url)
            print(f"Crawling: {url} (depth={depth})")

            try:
                resp = self.session.get(url, timeout=10)
                if not self._is_html(resp):
                    continue
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Extract <a>, <iframe>, <form>
                for tag in soup.find_all(['a', 'iframe', 'form']):
                    link = self._get_link_from_tag(url, tag)
                    if not link:
                        continue
                    link = link.split('#')[0]
                    if link in visited or not self._is_same_domain(base_url, link):
                        continue
                    if self._has_params(link):
                        found.append(link)
                    queue.append((link, depth+1))

                # Extract JS embedded URLs
                for js_url in self._extract_js_urls(resp.text, url):
                    js_url = js_url.split('#')[0]
                    if js_url in visited or not self._is_same_domain(base_url, js_url):
                        continue
                    if self._has_params(js_url):
                        found.append(js_url)
                    queue.append((js_url, depth+1))

            except Exception as e:
                print(f"Error crawling {url}: {e}")
        return found

    def _filter_and_dedup(self, urls):
        seen = set()
        filtered = []
        for url in urls:
            parsed = urlparse(url)
            key = (parsed.path, tuple(sorted(parse_qs(parsed.query).keys())))
            if key in seen:
                continue
            seen.add(key)
            filtered.append(url)

        # Prioritize URLs with priority_params
        high = [u for u in filtered if any(p + '=' in u for p in self.priority_params)]
        low = [u for u in filtered if u not in high]
        return high + low

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
            except:
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
        b = urlparse(base).netloc
        c = urlparse(url).netloc
        return c == b or c.endswith('.' + b)

    def _get_link_from_tag(self, base, tag):
        if tag.name == 'a' and tag.has_attr('href'):
            return urljoin(base, tag['href'])
        if tag.name == 'iframe' and tag.has_attr('src'):
            return urljoin(base, tag['src'])
        if tag.name == 'form' and tag.has_attr('action'):
            action = urljoin(base, tag['action'])
            if tag.get('method', '').lower() == 'get':
                params = [f"{inp.get('name')}=test" for inp in tag.find_all(['input', 'select', 'textarea']) if inp.get('name')]
                if params:
                    return f"{action}?{'&'.join(params)}"
        return None

    def _extract_js_urls(self, text, base):
        pattern = re.compile(r'["\']((?:https?:)?//[^"\']+\?.+?)["\']')
        matches = pattern.findall(text)
        urls = set(urljoin(base, m) for m in matches)
        return [u for u in urls if self._is_same_domain(base, u)]


def scan_sqli_with_discovery(base_url, session):
    pd = ParameterDiscovery(session)
    raw = pd.find_urls_with_parameters(base_url)
    common = pd.discover_common_endpoints(base_url)
    all_urls = pd._filter_and_dedup(raw + common)
    print(f"Total filtered URLs: {len(all_urls)}")
    params = sorted({k for u in all_urls for k in parse_qs(urlparse(u).query)})
    print(f"Parameters found: {params}")
    return all_urls, params

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python crawler.py <base_url>")
        sys.exit(1)
    base = sys.argv[1]
    sess = requests.Session()
    urls, params = scan_sqli_with_discovery(base, sess)
    for u in urls:
        print(u)