"""Data model base classes."""

import string
from collections.abc import ItemsView, ValuesView
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module
from pydantic.generics import GenericModel


class NamedModel(BaseModel):  # pylint: disable=too-few-public-methods
    """Extend the Pydantic base model with a name."""

    name: str = Field(..., regex=r"[^\.]+")  # Disallow dots so names can be used as key


class DescribedModel(NamedModel):  # pylint: disable=too-few-public-methods
    """Extend the named model with a description."""

    description: str = Field(..., regex=r".+")

    @validator("description")
    def set_description(cls, description):  # pylint: disable=no-self-argument
        """Add a dot if needed."""
        return description if description.endswith(tuple(string.punctuation)) else description + "."


ValueT = TypeVar("ValueT")


class MappedModel(GenericModel, Generic[ValueT]):
    """Extend the Pydantic base model with a mapping."""

    __root__: dict[str, ValueT]

    def __getitem__(self, key: str) -> ValueT:
        """Return the model with the specified key."""
        return self.__root__[key]  # pragma: no cover-behave

    def get(self, key: str) -> ValueT | None:
        """Return the model with the specified key or None if the key does not exist."""
        return self.__root__.get(key)  # pragma: no cover-behave

    def items(self) -> ItemsView:
        """Return all keys and values."""
        return self.__root__.items()  # pragma: no cover-behave

    def values(self) -> ValuesView:
        """Return all values."""
        return self.__root__.values()  # pragma: no cover-behave
