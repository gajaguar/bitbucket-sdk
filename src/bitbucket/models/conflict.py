from __future__ import annotations

from enum import StrEnum

from bitbucket.models.base import BitbucketModel


class FileConflictScenario(StrEnum):
    DELETE_MODIFY = "delete_modify"
    MODIFY_DELETE = "modify_delete"
    CONTENT = "content"
    BINARY = "binary"
    FLAGS = "flags"
    MODE = "mode"
    TYPE = "type"
    SYMLINK = "symlink"
    DIRECTORY_FILE = "directory_file"
    FILE_DIRECTORY = "file_directory"
    ADD_RENAME = "add_rename"
    RENAME_ADD = "rename_add"
    DELETE_RENAME = "delete_rename"
    RENAME_DELETE = "rename_delete"
    RENAME = "rename"
    SUBREPO = "subrepo"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> FileConflictScenario:
        del value
        return cls.UNKNOWN


class FileConflict(BitbucketModel):
    path: str | None = None
    type: str | None = None
    scenario: FileConflictScenario | None = None
    message: str | None = None
