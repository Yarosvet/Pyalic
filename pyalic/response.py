"""Responses environment and managing responses"""
from . import exceptions
from .types import LicenseInfoResponse, OperationResponse, SessionResponse


def process_key_info(status_code: int, content: dict) -> LicenseInfoResponse:
    """Process response for checking key"""
    if status_code == 200:
        return LicenseInfoResponse(request_code=status_code,
                                   content=content,
                                   ends=content['ends'],
                                   activated=content['activated'],
                                   install_limit=content['install_limit'],
                                   sessions_limit=content['sessions_limit'],
                                   additional_content_signature=content['additional_content_signature'],
                                   additional_content_product=content['additional_content_product'])
    error = content.get('error', None) or content.get('detail', None) or content  # If no error found, set it to content
    if error == exceptions.InvalidKeyException.message:
        raise exceptions.InvalidKeyException(response=OperationResponse(status_code, content))
    raise exceptions.CheckLicenseException(error, response=OperationResponse(status_code, content))


def process_start_session(status_code: int, content: dict) -> SessionResponse:
    """Process response for checking key"""
    if status_code == 200:
        return SessionResponse(request_code=status_code,
                               content=content,
                               session_id=content['session_id'])
    error = content.get('error', None) or content.get('detail', None) or content  # If no error found, set it to content
    if error == exceptions.InvalidKeyException.message:
        raise exceptions.InvalidKeyException(response=OperationResponse(status_code, content))
    if error == exceptions.LicenseExpiredException.message:
        raise exceptions.LicenseExpiredException(response=OperationResponse(status_code, content))
    if error == exceptions.SessionsLimitException.message:
        raise exceptions.SessionsLimitException(response=OperationResponse(status_code, content))
    if error == exceptions.InstallationsLimitException.message:
        raise exceptions.InstallationsLimitException(response=OperationResponse(status_code, content))
    raise exceptions.CheckLicenseException(error, response=OperationResponse(status_code, content))


def process_keepalive(status_code: int, content: dict) -> None:
    """Process response for keepalive and raise exceptions if it's failed"""
    if status_code == 200 and 'success' in content and content['success']:
        return
    error = content.get('error', None) or content.get('detail', None) or content  # If no error found, set it to content
    raise exceptions.KeepaliveException(error, response=OperationResponse(status_code, content))


def process_end_session(status_code: int, content: dict) -> None:
    """Process response for ending session and raise exceptions if it's failed"""
    if status_code == 200 and 'success' in content and content['success']:
        return
    error = content.get('error', None) or content.get('detail', None) or content  # If no error found, set it to content
    raise exceptions.EndSessionException(error, response=OperationResponse(status_code, content))
