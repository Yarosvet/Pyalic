"""Types of responses"""
from dataclasses import dataclass
from collections import ChainMap


@dataclass
class OperationResponse:
    """Response from server for some operation"""
    request_code: int
    content: dict
    error: str = None

    @classmethod
    def _get_annotations(cls):
        """Get annotations from all parent classes including current class"""
        return ChainMap(*(c.__annotations__ for c in cls.__mro__ if '__annotations__' in c.__dict__))

    def __post_init__(self):
        for (name, field_type) in self.__class__._get_annotations().items():  # pylint: disable=protected-access
            if not isinstance(getattr(self, name), field_type) and getattr(self, name) is not None:
                setattr(self, name, field_type(getattr(self, name)))


@dataclass
class LicenseInfoResponse(OperationResponse):
    """Response from server for checking license"""
    ends: int | None = None
    activated: int | None = None
    install_limit: int | None = None
    sessions_limit: int | None = None
    additional_content_signature: str = ""
    additional_content_product: str = ""


@dataclass
class SessionResponse(OperationResponse):
    """Response from server for session operations"""
    session_id: str = None
