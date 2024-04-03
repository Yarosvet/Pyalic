"""Wrapper for API"""
from functools import wraps
from json import JSONDecodeError
import httpx

from .exceptions import RequestFailed


class ApiWrapper:
    """Pyalic API wrapper"""

    TIMEOUT = 20

    def __init__(self, url: str, ssl_cert: str | bool = False):
        self.url = url
        self.ssl_cert = ssl_cert

    def key_info(self, key: str) -> httpx.Response:
        """Send **key info** request"""
        return httpx.request('POST', f"{self.url}/key_info",
                             verify=self.ssl_cert,
                             json={"license_key": key},
                             timeout=self.TIMEOUT)

    def start_session(self, key: str, fingerprint: str) -> httpx.Response:
        """Send **start session** request"""
        return httpx.request('POST', f"{self.url}/session",
                             verify=self.ssl_cert,
                             json={"license_key": key, "fingerprint": fingerprint},
                             timeout=self.TIMEOUT)

    def keepalive(self, session_id: str) -> httpx.Response:
        """Send **keepalive** request"""
        return httpx.request('POST', f"{self.url}/session/keepalive",
                             verify=self.ssl_cert,
                             json={"session_id": session_id},
                             timeout=self.TIMEOUT)

    def end_session(self, session_id: str) -> httpx.Response:
        """Send **end session** request"""
        return httpx.request('DELETE', f"{self.url}/session",
                             verify=self.ssl_cert,
                             json={"session_id": session_id},
                             timeout=self.TIMEOUT)


def request_attempts(attempts: int):
    """Decorator for methods which may cause RequestError or JSONDecodeError and must be re-attempted"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            attempted = 0
            while True:
                attempted += 1
                try:
                    return func(self, *args, **kwargs)
                except (httpx.RequestError, JSONDecodeError) as exc:
                    if attempted < attempts:
                        continue
                    raise RequestFailed from exc  # If attempts limit reached, raise exception

        return wrapper

    return decorator


class SecureApiWrapper(ApiWrapper):
    """Secure Pyalic API wrapper which attempts to get response several times"""

    ATTEMPTS = 3

    @request_attempts(ATTEMPTS)
    def key_info(self, key: str) -> httpx.Response:
        """Securely send **key info** request"""
        r = super().key_info(key=key)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    def start_session(self, key: str, fingerprint: str) -> httpx.Response:
        """Securely send **start session** request"""
        r = super().start_session(key=key, fingerprint=fingerprint)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    def keepalive(self, session_id: str) -> httpx.Response:
        """Securely send **keepalive** request"""
        r = super().keepalive(session_id)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    def end_session(self, session_id: str) -> httpx.Response:
        """Securely send **end session** request"""
        r = super().end_session(session_id)
        r.json()  # Ensure that response is JSON-encoded
        return r
