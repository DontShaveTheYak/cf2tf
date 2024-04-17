"""Defines classes and methods for creating and interacting with HCL syntax."""

import logging
from typing import Any, Dict, List, Optional

from cf2tf.terraform.hcl2._block import Block

log = logging.getLogger("cf2tf")


class Variable(Block):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name

        valid_arguments = ["description", "type", "default"]
        super().__init__("variable", (self.name,), arguments, valid_arguments, [])

    def write(self):
        # Type will be quoted, so we have to unquote it.
        self.arguments["type"] = self.arguments["type"].strip('"')

        return super().write()

    def base_ref(self):
        ref = super().base_ref()

        return ref.replace("variable", "var")


class Locals(Block):
    def __init__(self, arguments: Dict[str, Any]) -> None:
        name = "locals"
        super().__init__(name, (), arguments, [], [])


class Data(Block):
    def __init__(
        self,
        name: str,
        type: str,
        arguments: Optional[Dict[str, Any]] = None,
        valid_arguments: Optional[List[str]] = None,
        valid_attributes: Optional[List[str]] = None,
    ) -> None:
        self.name = f'"{name}"'
        self.type = f'"{type}"'

        super().__init__(
            "data",
            (
                self.type,
                self.name,
            ),
            arguments,
            valid_arguments,
            valid_attributes,
        )


class Resource(Block):
    def __init__(
        self,
        name: str,
        type: str,
        arguments: Dict[str, Any],
        valid_arguments: List[str],
        valid_attributes: List[str],
    ) -> None:
        self.name = f'"{name}"'
        self.type = f'"{type}"'
        super().__init__(
            "resource",
            (self.type, self.name),
            arguments,
            valid_arguments,
            valid_attributes,
        )


class Output(Block):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = f'"{name}"'

        valid_arguments = ["description", "value"]
        super().__init__("output", (self.name,), arguments, valid_arguments, [])
