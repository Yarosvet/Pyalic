"""Synchronous LicenseManager's environment module"""
from threading import Thread
import time
from typing import Any
from collections.abc import Callable

from .fingerprint import get_fingerprint
from .exceptions import RequestFailed, KeepaliveException, PyalicException
from . import response
from .wrappers import SecureApiWrapper
from .types import LicenseInfoResponse, SessionResponse


class AutoKeepaliveSender:
    """Automatic keep-alive packets sender"""

    interval = 2  # pylint: disable=duplicate-code

    alive = False
    _stop_flag = False
    _t = None
    _event = None

    def __init__(self, lm: 'LicenseManager'):
        self.lm = lm

    def start(self):
        """
        Start sending keepalive packets in a new thread (if not started)
        """
        if self.alive:
            return
        self._t = Thread(target=self._keepalive_cycle, name="LicenseAutoKeepAlive", daemon=True)
        self._t.start()

    def _keepalive_cycle(self):
        self.alive = True
        try:
            # Keepalive
            last_sent = time.time()
            self.lm.keep_alive()
            while not self._stop_flag:
                # Keep interval between requests
                time_past = time.time() - last_sent
                time.sleep(self.interval - time_past if self.interval > time_past else 0)
                # Keepalive
                last_sent = time.time()
                self.lm.keep_alive()
        except (RequestFailed, KeepaliveException) as exc:
            # Call event if request failed
            self._call_event_bad_keepalive(exc=exc)
        finally:
            self.alive = False

    def set_event_bad_keepalive(self, func: Callable[[PyalicException], Any]) -> None:
        """
        Set function-event will be called when keep-alive request goes wrong.

        Function must expect an argument (exception)
        """
        self._event = func

    def _call_event_bad_keepalive(self, exc: PyalicException = None) -> None:
        if self._event is not None:
            self._event(exc)

    def stop(self):
        """Stop sending keepalive packets"""
        self._stop_flag = True


class LicenseManager:
    """Synchronous License Manager"""
    enable_auto_keepalive = True

    def __init__(self, root_url: str, ssl_public_key: str | None = None):
        """
        Synchronous License Manager
        :param root_url: Root URL of Pyalic_server Server
        :param ssl_public_key: Path to SSL cert, or **None** to cancel SSL verifying
        """
        self.session_id = None
        self.last_valid_key = None

        self.auto_keepalive_sender = AutoKeepaliveSender(lm=self)
        self.api = SecureApiWrapper(url=root_url, ssl_cert=False if ssl_public_key is None else ssl_public_key)

    def key_info(self, key: str) -> LicenseInfoResponse:
        """
        Check license key with specified Pyalic Server and get information about it
        :param key: License key
        :return: `response.LicenseResponse`
        """
        r = self.api.key_info(key)
        processed_resp = response.process_key_info(r.status_code, r.json())
        # Save key
        self.last_valid_key = key
        return processed_resp

    def start_session(self, key: str) -> SessionResponse:
        """
        Start new license session with specified key
        :param key: License key
        :return: `response.SessionResponse`
        """
        fingerprint = get_fingerprint()
        r = self.api.start_session(key, fingerprint)
        processed_resp = response.process_start_session(r.status_code, r.json())
        # Save session id
        self.session_id = processed_resp.session_id
        # Start sending keepalive packets if needed
        if self.enable_auto_keepalive:
            self.auto_keepalive_sender.start()
        return processed_resp

    def keep_alive(self):
        """
        Send keep-alive packet to license server
        (LicenseManager can do it automatically)
        """
        r = self.api.keepalive(self.session_id)
        response.process_keepalive(r.status_code, r.json())

    def end_session(self):
        """
        End current license session
        """
        self.auto_keepalive_sender.stop()
        r = self.api.end_session(self.session_id)
        response.process_end_session(r.status_code, r.json())
