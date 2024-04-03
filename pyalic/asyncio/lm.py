"""AsyncLicenseManager's environment module"""
import asyncio
from collections.abc import Callable
from typing import Any
import time

from .. import response
from ..exceptions import RequestFailed, KeepaliveException, PyalicException
from .wrappers import AsyncSecureApiWrapper
from ..fingerprint import get_fingerprint
from ..types import LicenseInfoResponse, SessionResponse


class AsyncAutoKeepaliveSender:
    """Asynchronous automatic keep-alive packets sender"""

    interval = 2

    alive = False
    _stop_flag = False
    _t = None
    _event = None

    def __init__(self, async_lm: 'AsyncLicenseManager'):
        self.lm = async_lm

    def start(self):
        """
        Start sending keepalive packets in a new thread.
        If already started, it will stop existing thread and start a new one
        """
        if self.alive:
            return
        asyncio.ensure_future(self._keepalive_cycle(), loop=asyncio.get_event_loop())

    async def _keepalive_cycle(self):
        self.alive = True
        try:
            # Keepalive
            last_sent = time.time()
            await self.lm.keep_alive()
            while not self._stop_flag:
                # Keep interval between requests
                time_past = time.time() - last_sent
                await asyncio.sleep(self.interval - time_past if self.interval > time_past else 0)
                # Keepalive
                last_sent = time.time()
                await self.lm.keep_alive()
        except (RequestFailed, KeepaliveException) as exc:
            # Call event if request failed
            await self._call_event_bad_keepalive(exc=exc)
        finally:
            self.alive = False

    def set_event_bad_keepalive(self, func: Callable[[PyalicException], Any]) -> None:
        """
        Set asynchronous function-event will be awaited when keep-alive request goes wrong.

        Function must expect argument (exception)
        """
        self._event = func

    async def _call_event_bad_keepalive(self, exc: PyalicException = None) -> None:
        if self._event is not None:
            await self._event(exc)

    def stop(self):
        """Stop sending keepalive packets"""
        self._stop_flag = True


class AsyncLicenseManager:
    """Asynchronous license manager"""

    enable_auto_keepalive = True

    def __init__(self, root_url: str, ssl_public_key: str | None = None):
        """
        Synchronous License Manager
        :param root_url: Root URL of Pyalic_server Server
        :param ssl_public_key: Path to SSL cert, or **None** to cancel SSL verifying
        """
        self.session_id = None
        self.last_valid_key = None

        self.auto_keepalive_sender = AsyncAutoKeepaliveSender(async_lm=self)
        self.api = AsyncSecureApiWrapper(url=root_url, ssl_cert=ssl_public_key)

    async def key_info(self, key: str) -> LicenseInfoResponse:
        """
        Check license key with specified Pyalic Server and get information about it
        :param key: License key
        :return: `LicenseResponse`
        """
        r = await self.api.key_info(key)
        processed_resp = response.process_key_info(r.status_code, r.json())
        # Save key
        self.last_valid_key = key
        return processed_resp

    async def start_session(self, key: str) -> SessionResponse:
        """
        Start new license session with specified key
        :param key: License key
        :return: `response.SessionResponse`
        """
        fingerprint = get_fingerprint()
        r = await self.api.start_session(key, fingerprint)
        processed_resp = response.process_start_session(r.status_code, r.json())
        # Save session id
        self.session_id = processed_resp.session_id
        # Start auto-keepalive sender
        if self.enable_auto_keepalive:
            self.auto_keepalive_sender.start()
        return processed_resp

    async def keep_alive(self):
        """
        Send keep-alive packet to license server
        (LicenseManager can do it automatically)
        """
        r = await self.api.keepalive(self.session_id)
        response.process_keepalive(r.status_code, r.json())

    async def end_session(self):
        """
        End current license session
        """
        self.auto_keepalive_sender.stop()
        r = await self.api.end_session(self.session_id)
        response.process_end_session(r.status_code, r.json())
