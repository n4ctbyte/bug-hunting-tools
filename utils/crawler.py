import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

class ParameterDiscovery:
    def __init__(self, session):
        self.session = session
        
    def find_urls_with_parameters(self, base_url, max_depth=2):
        """Find URLs with parameters for SQLi testing"""
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
                
                # 1. Find links with parameters
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    if self.has_parameters(full_url):
                        found_urls.add(full_url)
                        print(f"[+] Found URL with parameters: {full_url}")
                    
                    # Add to crawl queue
                    if depth < max_depth and self.is_same_domain(base_url, full_url):
                        to_visit.append((full_url, depth + 1))
                
                # 2. Find form actions
                for form in soup.find_all('form'):
                    action = form.get('action', '')
                    method = form.get('method', 'get').lower()
                    
                    if method == 'get':
                        form_url = urljoin(current_url, action)
                        
                        # Extract input names to create test URL
                        inputs = form.find_all(['input', 'select', 'textarea'])
                        if inputs:
                            test_params = []
                            for input_tag in inputs[:3]:  # Limit to first 3 inputs
                                name = input_tag.get('name')
                                if name and input_tag.get('type', '').lower() not in ['submit', 'button']:
                                    test_params.append(f"{name}=test")
                            
                            if test_params:
                                test_url = f"{form_url}?{'&'.join(test_params)}"
                                found_urls.add(test_url)
                                print(f"[+] Found form URL: {test_url}")
                
                # 3. Find JavaScript URLs (basic extraction)
                js_urls = self.extract_js_urls(response.text, current_url)
                for js_url in js_urls:
                    if self.has_parameters(js_url):
                        found_urls.add(js_url)
                        print(f"[+] Found JS URL with parameters: {js_url}")
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
                continue
        
        return list(found_urls)
    
    def has_parameters(self, url):
        """Check if URL has query parameters"""
        parsed = urlparse(url)
        return bool(parsed.query)
    
    def is_same_domain(self, base_url, check_url):
        """Check if URLs are from same domain"""
        base_domain = urlparse(base_url).netloc
        check_domain = urlparse(check_url).netloc
        return base_domain == check_domain
    
    def extract_js_urls(self, html_content, base_url):
        """Extract URLs from JavaScript (basic patterns)"""
        js_urls = set()
        
        # Common JavaScript URL patterns
        patterns = [
            r'["\\]([^"\\]*\\?[^"\\]*)["\\]',  # URLs with query strings
            r'url\\s*[:=]\\s*["\\]([^"\\]*\\?[^"\\]*)["\\]',
            r'ajax\\s*\\(\\s*["\\]([^"\\]*\\?[^"\\]*)["\\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                full_url = urljoin(base_url, match)
                if self.is_same_domain(base_url, full_url):
                    js_urls.add(full_url)
        
        return js_urls

    def discover_common_endpoints(self, base_url):
        """Try common endpoint patterns"""
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
            except:
                continue
        
        return found_endpoints

# Enhanced scan function
def scan_sqli_with_discovery(url, session):
    """Scan SQLi with parameter discovery"""
    print(f"Starting parameter discovery for {url}")
    
    # Discover URLs with parameters
    discovery = ParameterDiscovery(session)
    
    # Method 1: Crawl for URLs with parameters
    param_urls = discovery.find_urls_with_parameters(url, max_depth=2)
    
    # Method 2: Try common endpoints
    endpoint_urls = discovery.discover_common_endpoints(url)
    
    # Combine results
    all_urls = list(set(param_urls + endpoint_urls))
    
    if not all_urls:
        print("[-] No URLs with parameters found")
        return [], []
    
    print(f"\n[+] Found {len(all_urls)} URLs with parameters to test:")
    for test_url in all_urls:
        print(f"    {test_url}")
    
    # For now, we return all found URLs and a dummy list of parameters
    # The actual parameter extraction for SQLi will happen within the SQLi scanner
    return all_urls, ["dummy_param"] # Returning a dummy parameter for now


