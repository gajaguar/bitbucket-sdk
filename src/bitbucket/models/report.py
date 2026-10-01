from __future__ import annotations

from enum import StrEnum
from typing import Any

from bitbucket._time import BitbucketInstant
from bitbucket.ids import Uuid
from bitbucket.models.base import BitbucketModel


class ReportType(StrEnum):
    SECURITY = "SECURITY"
    COVERAGE = "COVERAGE"
    TEST = "TEST"
    BUG = "BUG"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> ReportType:
        del value
        return cls.UNKNOWN


class ReportResult(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> ReportResult:
        del value
        return cls.UNKNOWN


class ReportDataType(StrEnum):
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DURATION = "DURATION"
    LINK = "LINK"
    NUMBER = "NUMBER"
    PERCENTAGE = "PERCENTAGE"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> ReportDataType:
        del value
        return cls.UNKNOWN


class AnnotationType(StrEnum):
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"
    BUG = "BUG"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> AnnotationType:
        del value
        return cls.UNKNOWN


class AnnotationResult(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    IGNORED = "IGNORED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> AnnotationResult:
        del value
        return cls.UNKNOWN


class AnnotationSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> AnnotationSeverity:
        del value
        return cls.UNKNOWN


class ReportData(BitbucketModel):
    # The spec types `value` as `object`, but its description says a number,
    # string, boolean or a `{text, href}` object, depending on `type`.
    type: ReportDataType | None = None
    title: str | None = None
    value: Any = None


class Report(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    title: str | None = None
    details: str | None = None
    external_id: str | None = None
    reporter: str | None = None
    link: str | None = None
    remote_link_enabled: bool | None = None
    logo_url: str | None = None
    report_type: ReportType | None = None
    result: ReportResult | None = None
    data: list[ReportData] | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None


class ReportWrite(BitbucketModel):
    # No `type`: the spec's sample request omits it.
    title: str | None = None
    details: str | None = None
    external_id: str | None = None
    reporter: str | None = None
    link: str | None = None
    remote_link_enabled: bool | None = None
    logo_url: str | None = None
    report_type: ReportType | None = None
    result: ReportResult | None = None
    data: list[ReportData] | None = None


class ReportAnnotation(BitbucketModel):
    type: str | None = None
    uuid: Uuid | None = None
    external_id: str | None = None
    title: str | None = None
    annotation_type: AnnotationType | None = None
    path: str | None = None
    line: int | None = None
    summary: str | None = None
    details: str | None = None
    result: AnnotationResult | None = None
    severity: AnnotationSeverity | None = None
    link: str | None = None
    created_on: BitbucketInstant | None = None
    updated_on: BitbucketInstant | None = None


class ReportAnnotationWrite(BitbucketModel):
    # `external_id` is what the bulk upload keys on; the spec's samples also
    # send `title`, which its schema omits.
    external_id: str | None = None
    title: str | None = None
    annotation_type: AnnotationType | None = None
    path: str | None = None
    line: int | None = None
    summary: str | None = None
    details: str | None = None
    result: AnnotationResult | None = None
    severity: AnnotationSeverity | None = None
    link: str | None = None
