"""Test responses processing"""
import pytest

from ..pyalic import response
from ..pyalic import exceptions

# pylint: disable=missing-function-docstring

_wrong_request_content = {
    "detail": [
        {
            "type": "json_invalid",
            "loc": [
                "body",
                30
            ],
            "msg": "JSON decode error",
            "input": {},
            "ctx": {
                "error": "Expecting property name enclosed in double quotes"
            }
        }
    ]
}


def test_valid_key():
    content = {"success": True,
               "session_id": "123",
               "additional_content_product": "test_product",
               "additional_content_signature": "test_signature"}
    r = response.process_start_session(200, content)
    assert r.session_id == "123"
    assert r.request_code == 200
    assert r.content == content
    assert r.error is None


def test_wrong_key_error():
    content = {"success": False,
               "error": "Invalid license key"}
    with pytest.raises(exceptions.InvalidKeyException):
        response.process_start_session(400, content)


def test_check_key_wrong_request():
    content = _wrong_request_content
    with pytest.raises(exceptions.CheckLicenseException):
        response.process_start_session(422, content)


def test_keepalive_success():
    content = {"success": True}
    response.process_keepalive(200, content)


def test_keepalive_fail():
    content = {"detail": "Session not found"}
    with pytest.raises(exceptions.KeepaliveException):
        response.process_keepalive(404, content)


def test_keepalive_wrong_request():
    content = _wrong_request_content
    with pytest.raises(exceptions.KeepaliveException):
        response.process_keepalive(422, content)


def test_end_session_success():
    content = {"success": True}
    response.process_end_session(200, content)


def test_end_session_fail():
    content = {"success": False,
               "error": "Session not found"}
    with pytest.raises(exceptions.EndSessionException):
        response.process_end_session(404, content)


def test_end_session_wrong_request():
    content = _wrong_request_content
    with pytest.raises(exceptions.EndSessionException):
        response.process_end_session(422, content)
