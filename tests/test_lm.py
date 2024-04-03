"""Test License Manager module"""
import time
import pytest
from ..pyalic.lm import LicenseManager
from ..pyalic.fingerprint import get_fingerprint
from ..pyalic.types import LicenseInfoResponse, SessionResponse
from ..pyalic import exceptions
from . import SERVER_PORT, rand_str, CERT_FILE
from .server_http import HTTPRequest, CommonResponses


# pylint: disable=duplicate-code

def test_key_info_valid(ssl_server):
    """Test checking valid key"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.enable_auto_keepalive = False
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/key_info",
                    request_data={"license_key": key}),
        CommonResponses.valid_key_info_response()
    )
    assert isinstance(lm.key_info(key), LicenseInfoResponse)


def test_key_info_invalid(ssl_server):
    """Test checking invalid key"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.enable_auto_keepalive = False
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/key_info",
                    request_data={"license_key": key}),
        CommonResponses.invalid_key_info_response()
    )
    with pytest.raises(exceptions.InvalidKeyException):
        lm.key_info(key)


def test_keepalive(ssl_server):
    """Test sending keepalive packet"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session/keepalive",
                    request_data={"session_id": lm.session_id}),
        CommonResponses.valid_keepalive_response()
    )
    lm.keep_alive()


def test_keepalive_invalid(ssl_server):
    """Test sending keepalive packet with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session/keepalive",
                    request_data={"session_id": lm.session_id}),
        CommonResponses.invalid_keepalive_response()
    )
    with pytest.raises(exceptions.KeepaliveException):
        lm.keep_alive()


def test_end_session(ssl_server):
    """Test ending session"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="DELETE",
                    url="/session",
                    request_data={"session_id": lm.session_id}),
        CommonResponses.valid_end_session_response()
    )
    lm.end_session()


def test_end_session_invalid(ssl_server):
    """Test ending session with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="DELETE",
                    url="/session",
                    request_data={"session_id": lm.session_id}),
        CommonResponses.invalid_end_session_response()
    )
    with pytest.raises(exceptions.EndSessionException):
        lm.end_session()


def test_auto_keepalive(ssl_server):
    """Test auto-sending keepalive packets mechanism"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.enable_auto_keepalive = True
    lm.auto_keepalive_sender.interval = 0.5
    key = rand_str(16)
    session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        CommonResponses.valid_start_session_response(session_id=session_id)
    )

    keepalive_count = 0

    def got_keepalive():
        nonlocal keepalive_count
        keepalive_count += 1

    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session/keepalive",
                    request_data={"session_id": session_id}),
        CommonResponses.valid_keepalive_response(),
        event=got_keepalive
    )
    assert isinstance(lm.start_session(key), SessionResponse)
    assert lm.auto_keepalive_sender.alive
    time.sleep(2)
    assert keepalive_count >= 4
    lm.auto_keepalive_sender.stop()
    time.sleep(lm.auto_keepalive_sender.interval)
    assert not lm.auto_keepalive_sender.alive


def test_auto_keepalive_fail_event(ssl_server):
    """Test auto-sending keepalive packets mechanism with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.enable_auto_keepalive = True
    lm.auto_keepalive_sender.interval = 0.5
    bad_flag = False

    def got_bad_keepalive(exc: exceptions.PyalicException):  # pylint: disable=unused-argument
        nonlocal bad_flag
        bad_flag = True

    # When got bad keepalive, set bad_flag to True
    lm.auto_keepalive_sender.set_event_bad_keepalive(got_bad_keepalive)
    key = rand_str(16)
    session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        CommonResponses.valid_start_session_response(session_id=session_id)
    )
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/session/keepalive",
                    request_data={"session_id": session_id}),
        CommonResponses.invalid_keepalive_response()
    )
    assert isinstance(lm.start_session(key), SessionResponse)
    time.sleep(lm.auto_keepalive_sender.interval)
    assert not lm.auto_keepalive_sender.alive
    assert bad_flag
