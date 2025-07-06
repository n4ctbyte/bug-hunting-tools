import yaml
import requests

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_session(user_agent=None, cookies=None, proxy=None):
    session = requests.Session()
    if user_agent:
        session.headers.update({'User-Agent': user_agent})
    if cookies:
        session.cookies.update(cookies)
    if proxy:
        session.proxies.update(proxy)
    
    session.verify = False
    return session

config = load_config()

