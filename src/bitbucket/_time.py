from __future__ import annotations

import datetime
from typing import Annotated

from pydantic import BeforeValidator
from pydantic import PlainSerializer

from bitbucket.errors import ErrorBody
from bitbucket.errors import ValidationError


def _invalid(value: object) -> ValidationError:
    message = f"Invalid Bitbucket instant: {value!r}"
    return ValidationError(body=ErrorBody(message=message))


def parse_instant(value: str) -> datetime.datetime:
    if not isinstance(value, str):
        raise _invalid(value)
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError as error:
        raise _invalid(value) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.UTC)
    return parsed.astimezone(datetime.UTC)


def format_instant(value: datetime.datetime) -> str:
    if not isinstance(value, datetime.datetime):
        raise _invalid(value)
    moment = value.replace(tzinfo=datetime.UTC) if value.tzinfo is None else value.astimezone(datetime.UTC)
    base = moment.strftime("%Y-%m-%dT%H:%M:%S")
    suffix = f".{moment.microsecond:06d}+00:00" if moment.microsecond else "+00:00"
    return base + suffix


def _validate_instant(value: object) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        return parse_instant(format_instant(value))
    if isinstance(value, str):
        return parse_instant(value)
    raise _invalid(value)


type BitbucketInstant = Annotated[  # pylint: disable=app-module-const-naming
    datetime.datetime,
    BeforeValidator(_validate_instant),
    PlainSerializer(format_instant, return_type=str, when_used="json"),
]
