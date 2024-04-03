"""Test SecureApiWrapper class"""
from ..pyalic.wrappers import SecureApiWrapper
from . import SERVER_PORT, rand_str, CERT_FILE
from .server_http import HTTPRequest, CommonResponses


# pylint: disable=duplicate-code

def test_key_info_secure(http_server):
    """Test checking key after one attempt failed"""
    key = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="POST",
                    url="/key_info",
                    request_data={"license_key": key}),
        CommonResponses.valid_key_info_response()
    )
    wrapper = SecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    assert wrapper.key_info(key).json()

def test_start_session_secure(http_server):
    """Test starting session after one attempt failed"""
    key = rand_str(16)
    fingerprint = rand_str(16)
    s_id = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="POST",
                    url="/session",
                    request_data={"license_key": key, "fingerprint": fingerprint}),
        CommonResponses.valid_start_session_response(session_id=s_id)
    )
    wrapper = SecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    assert wrapper.start_session(key, fingerprint).json()["session_id"] == s_id


def test_check_key_ssl_enabled(ssl_server):
    """Test checking key with SSL enabled"""
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/key_info",
                    request_data={"license_key": key}),
        CommonResponses.valid_key_info_response()
    )
    wrapper = SecureApiWrapper(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    assert wrapper.key_info(key).json()


def test_keepalive_secure(http_server):
    """Test sending keepalive packet after one attempt failed"""
    session_id = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="POST",
                    url="/session/keepalive",
                    request_data={"session_id": session_id}),
        CommonResponses.valid_keepalive_response()
    )
    wrapper = SecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    assert wrapper.keepalive(session_id).json()["success"]


def test_end_session_secure(http_server):
    """Test sending end session packet after one attempt failed"""
    session_id = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="DELETE",
                    url="/session",
                    request_data={"session_id": session_id}),
        CommonResponses.valid_end_session_response()
    )
    wrapper = SecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    assert wrapper.end_session(session_id).json()["success"]
