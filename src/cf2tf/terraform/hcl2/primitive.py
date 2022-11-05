from abc import abstractclassmethod
from typing import Any, Union

try:
    from typing import Protocol
except ImportError:
    # Python 3.6 and 3.7
    from typing_extensions import Protocol  # type: ignore

import logging

log = logging.getLogger("cf2tf")


class TerraformType(Protocol):
    """A Terraform value of some type."""

    value: Any

    def __str__(self) -> str:
        return self.render()

    @abstractclassmethod
    def render(self, indent: int) -> str:
        raise NotImplementedError


class StringType(str, TerraformType):
    """A sequence of Unicode characters representing some text, like "hello"."""

    def __init__(self, value: str) -> None:
        """Default constructor

        Args:
            value (str): The value for this Terraform type.
        """
        super().__init__()

        self.value = value

    def __str__(self) -> str:
        return self.render()

    def render(self, _=0):

        return f'"{self.value}"'


class NumberType(int, TerraformType):
    """A numeric value. The number type can represent both whole numbers like 15 and fractional values like 6.283185."""

    def __init__(self, value: Union[int, float]) -> None:
        """Default constructor

        Args:
            value (str): The value for this Terraform type.
        """
        super().__init__()

        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def render(self, _=0):
        return self.value


class NullType(int, TerraformType):
    """A value that represents absence or omission. If you set an argument of a resource to null, Terraform behaves as though you had completely omitted it."""

    def __init__(self) -> None:
        """Default constructor

        Args:
            value (str): The value for this Terraform type.
        """
        super().__init__()

        self.value: str = "null"

    def __str__(self) -> str:
        return self.render()

    def render(self, _=0):
        return self.value

    # Needed for unit testing
    def __eq__(self, __x: object) -> bool:
        return __x == self.value


PrimitiveTypes = Union[StringType, NumberType, NullType]
