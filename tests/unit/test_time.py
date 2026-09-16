from __future__ import annotations

import datetime

import pytest

from bitbucket._time import format_instant  # ruff: ignore[import-private-name]
from bitbucket._time import parse_instant  # ruff: ignore[import-private-name]
from bitbucket.errors import ValidationError


def test_parse_instant_normalizes_to_utc() -> None:
    # Arrange
    value = "2024-01-01T10:00:00-05:00"
    # Act
    parsed = parse_instant(value)
    # Assert
    assert parsed == datetime.datetime(2024, 1, 1, 15, 0, tzinfo=datetime.UTC)


def test_parse_instant_treats_naive_value_as_utc() -> None:
    # Arrange
    value = "2024-01-01T10:00:00"
    # Act
    parsed = parse_instant(value)
    # Assert
    assert parsed == datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC)


def test_parse_instant_rejects_non_string() -> None:
    # Arrange
    invalid_value = 123
    # Act
    # Assert
    with pytest.raises(ValidationError):
        parse_instant(invalid_value)  # type: ignore[arg-type]


def test_parse_instant_rejects_malformed_string() -> None:
    # Arrange
    invalid_value = "not-a-date"
    # Act
    # Assert
    with pytest.raises(ValidationError):
        parse_instant(invalid_value)


def test_format_instant_round_trips_through_parse() -> None:
    # Arrange
    original = datetime.datetime(2024, 6, 15, 12, 30, 45, tzinfo=datetime.UTC)
    # Act
    formatted = format_instant(original)
    # Assert
    assert parse_instant(formatted) == original


def test_format_instant_naive_datetime_is_treated_as_utc() -> None:
    # Arrange
    naive = datetime.datetime(2024, 6, 15, 12, 30, 45)  # ruff: ignore[call-datetime-without-tzinfo]
    # Act
    formatted = format_instant(naive)
    # Assert
    assert formatted == "2024-06-15T12:30:45+00:00"


def test_format_instant_rejects_non_datetime() -> None:
    # Arrange
    invalid_value = "2024-01-01"
    # Act
    # Assert
    with pytest.raises(ValidationError):
        format_instant(invalid_value)  # type: ignore[arg-type]
