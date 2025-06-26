
# Path: BugHunterPro/utils/config.py

import requests

def get_session(user_agent=None, cookies=None, proxy=None):
    session = requests.Session()
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    if cookies:
        # cookies should be a dictionary
        session.cookies.update(cookies)
    if proxy:
        # proxy should be a dictionary like {"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}
        session.proxies.update(proxy)
    return session


