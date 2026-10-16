from __future__ import annotations

import datetime as dt
from typing import Annotated

from pydantic import BeforeValidator
from pydantic import PlainSerializer

from bitbucket.errors import ErrorBody
from bitbucket.errors import ValidationError


def _invalid(value: object) -> ValidationError:
    message = f"Invalid Bitbucket instant: {value!r}"
    return ValidationError(body=ErrorBody(message=message))


def parse_instant(value: str) -> dt.datetime:
    if not isinstance(value, str):
        raise _invalid(value)
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise _invalid(value) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def format_instant(value: dt.datetime) -> str:
    if not isinstance(value, dt.datetime):
        raise _invalid(value)
    moment = value.replace(tzinfo=dt.UTC) if value.tzinfo is None else value.astimezone(dt.UTC)
    base = moment.strftime("%Y-%m-%dT%H:%M:%S")
    suffix = f".{moment.microsecond:06d}+00:00" if moment.microsecond else "+00:00"
    return base + suffix


def _validate_instant(value: object) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return parse_instant(format_instant(value))
    if isinstance(value, str):
        return parse_instant(value)
    raise _invalid(value)


type BitbucketInstant = Annotated[  # pylint: disable=gajaguar-module-const-naming
    dt.datetime,
    BeforeValidator(_validate_instant),
    PlainSerializer(format_instant, return_type=str, when_used="json"),
]
