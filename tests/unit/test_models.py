from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from bitbucket.models.account import UserType
from bitbucket.models.branch import MergeStrategy
from bitbucket.models.comment import CommentInline
from bitbucket.models.link import Links
from bitbucket.models.pull_request import BranchSpec
from bitbucket.models.pull_request import EndpointSpec
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.repository import Repository


def test_links_self_field_uses_reserved_word_alias() -> None:
    # Arrange
    payload = {"self": {"href": "https://x"}}
    # Act
    links = Links.model_validate(payload)
    # Assert
    assert links.self_ is not None
    assert links.self_.href == "https://x"


def test_links_self_field_can_be_constructed_by_python_name() -> None:
    # Arrange
    self_payload = {"href": "https://x"}
    # Act
    links = Links(self_=self_payload)
    # Assert
    assert links.model_dump(mode="json", by_alias=True)["self"] == {"href": "https://x", "name": None}


def test_comment_inline_from_field_uses_reserved_word_alias() -> None:
    # Arrange
    payload = {"path": "a.py", "from": 3, "to": 4}
    # Act
    inline = CommentInline.model_validate(payload)
    # Assert
    assert inline.from_ == 3
    assert inline.to == 4


def test_extra_fields_are_preserved() -> None:
    # Arrange
    payload = {"name": "repo", "brand_new_field": "value"}
    # Act
    repository = Repository.model_validate(payload)
    # Assert
    assert repository.model_extra == {"brand_new_field": "value"}


def test_read_models_are_frozen() -> None:
    # Arrange
    repository = Repository.model_validate({"name": "repo"})
    # Act
    # Assert
    with pytest.raises(PydanticValidationError):
        repository.name = "renamed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("value", "expected"),
    [("user", UserType.USER), ("team", UserType.TEAM), ("something-new", UserType.UNKNOWN)],
)
def test_user_type_falls_back_to_unknown_for_unrecognized_values(value: str, expected: UserType) -> None:
    # Arrange
    # Act
    # Assert
    assert UserType(value) is expected


def test_merge_strategy_falls_back_to_unknown() -> None:
    # Arrange
    raw_value = "something-new"
    # Act
    # Assert
    assert MergeStrategy(raw_value) is MergeStrategy.UNKNOWN


def test_write_model_dump_excludes_unset_fields() -> None:
    # Arrange
    payload = PullRequestCreate(title="New PR", source=EndpointSpec(branch=BranchSpec(name="feature")))
    # Act
    body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
    # Assert
    assert body == {"title": "New PR", "source": {"branch": {"name": "feature"}}}
    assert "description" not in body
    assert "close_source_branch" not in body
