"""Pydantic schemas and validation for Slate-backed articles."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.user.schemas import UserResponse


MAX_CONTENT_NODES = 1000
MAX_TEXT_LENGTH = 100_000
MAX_SUMMARY_LENGTH = 2_000


def _validate_slate_nodes(nodes: Any, path: str = "content") -> list[dict[str, Any]]:
    if not isinstance(nodes, list):
        raise ValueError(f"{path} must be a list of Slate nodes")
    if len(nodes) > MAX_CONTENT_NODES:
        raise ValueError(f"{path} contains too many nodes")

    validated_nodes = []
    for index, node in enumerate(nodes):
        node_path = f"{path}[{index}]"
        if not isinstance(node, dict):
            raise ValueError(f"{node_path} must be an object")

        text = node.get("text")
        children = node.get("children")
        if text is None and children is None:
            raise ValueError(f"{node_path} must contain text or children")
        if text is not None and not isinstance(text, str):
            raise ValueError(f"{node_path}.text must be a string")
        if text is not None and len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"{node_path}.text is too long")
        if children is not None:
            _validate_slate_nodes(children, f"{node_path}.children")
        if "url" in node:
            url = node["url"]
            if not isinstance(url, str) or url.strip().lower().startswith(("javascript:", "data:", "vbscript:")):
                raise ValueError(f"{node_path}.url must use a safe URL scheme")

        validated_nodes.append(node)
    return validated_nodes


def _slate_node_text(node: dict[str, Any]) -> str:
    if isinstance(node.get("text"), str):
        return node["text"]
    children = node.get("children")
    if isinstance(children, list):
        return "".join(_slate_node_text(child) for child in children)
    return ""


def _default_summary(content: list[dict[str, Any]]) -> str:
    lines = [_slate_node_text(node).strip() for node in content if _slate_node_text(node).strip()]
    return "\n".join(lines[:3])[:MAX_SUMMARY_LENGTH]


class ArticleBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: list[dict[str, Any]]
    summary: str | None = Field(default=None, max_length=MAX_SUMMARY_LENGTH)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title cannot be empty")
        return normalized

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return _validate_slate_nodes(value)

    @model_validator(mode="after")
    def set_summary(self):
        if self.summary is None or not self.summary.strip():
            self.summary = _default_summary(self.content)
        else:
            self.summary = self.summary.strip()
        return self


class ArticleCreate(ArticleBase):
    """Payload for creating an article."""


class ArticleUpdate(BaseModel):
    """Payload for partially updating an article."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: list[dict[str, Any]] | None = None
    summary: str | None = Field(default=None, max_length=MAX_SUMMARY_LENGTH)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title cannot be empty")
        return normalized

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return _validate_slate_nodes(value)

    @field_validator("summary")
    @classmethod
    def normalize_summary(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class ArticleResponse(ArticleBase):
    """Article returned by the API."""

    id: UUID
    creator_id: UUID
    creator: UserResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
