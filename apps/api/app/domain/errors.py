from dataclasses import dataclass
from http import HTTPStatus


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    message: str
    next_action: str
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
