"""Asynchronous wrapper for API"""
import ssl
import json
import httpx

from ..exceptions import RequestFailed


class AsyncApiWrapper:
    """Pyalic API asynchronous wrapper"""
    TIMEOUT = 20

    def __init__(self, url: str, ssl_cert: str | bool):
        self.url = url
        if ssl_cert:
            self.ssl_context = ssl.create_default_context(cafile=ssl_cert)
        else:
            self.ssl_context = False

    async def start_session(self, key: str, fingerprint: str) -> httpx.Response:
        """Send **start session** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('GET',
                                        f"{self.url}/session",
                                        json={"license_key": key, "fingerprint": fingerprint})

    async def key_info(self, key: str) -> httpx.Response:
        """Send **key info** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('POST',
                                        f"{self.url}/key_info",
                                        json={"license_key": key})

    async def keepalive(self, client_id: str) -> httpx.Response:
        """Send **keepalive** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('POST',
                                        f"{self.url}/session/keepalive",
                                        json={"session_id": client_id})

    async def end_session(self, client_id: str) -> httpx.Response:
        """Send **end client** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('DELETE',
                                        f"{self.url}/session",
                                        json={"session_id": client_id})


def request_attempts(attempts: int):
    """Async decorator to repeat request several times"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            attempted = 0
            while True:
                attempted += 1
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, json.JSONDecodeError) as exc:
                    if attempted < attempts:
                        continue
                    raise RequestFailed from exc  # If attempts limit reached, raise exception

        return wrapper

    return decorator


class AsyncSecureApiWrapper(AsyncApiWrapper):
    """Secure Pyalic API asynchronous wrapper which attempts to get response several times"""
    ATTEMPTS = 3

    @request_attempts(ATTEMPTS)
    async def key_info(self, key: str) -> httpx.Response:
        """Securely send **key info** request"""
        r = await super().key_info(key=key)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    async def start_session(self, key: str, fingerprint: str) -> httpx.Response:
        """Securely send **start session** request"""
        r = await super().start_session(key=key, fingerprint=fingerprint)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    async def keepalive(self, client_id: str) -> httpx.Response:
        """Securely send **keepalive** request"""
        r = await super().keepalive(client_id)
        r.json()  # Ensure that response is JSON-encoded
        return r

    @request_attempts(ATTEMPTS)
    async def end_session(self, client_id: str) -> httpx.Response:
        """Securely send **end client** request"""
        r = await super().end_session(client_id)
        r.json()  # Ensure that response is JSON-encoded
        return r
