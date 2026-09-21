from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.observability.request_id import get_request_id

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


def response_with_meta(data: T) -> ApiResponse[T]:
    return ApiResponse(data=data, meta=ResponseMeta(request_id=get_request_id()))


class TimestampFields(BaseModel):
    created_at: datetime
    updated_at: datetime
