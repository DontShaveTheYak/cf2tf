"""Defines classes and methods for creating and interacting with HCL syntax."""


from typing import Any, Dict, List, Optional

import logging

log = logging.getLogger("cf2tf")


class Block:
    def __init__(
        self,
        block_type: str,
        labels: List[str],
        arguments: Optional[Dict[str, Any]] = None,
        valid_arguments: Optional[List[str]] = None,
        valid_attributes: Optional[List[str]] = None,
    ) -> None:
        self.block_type = block_type
        self.labels = labels
        self.arguments = arguments if arguments else {}
        self.valid_arguments = valid_arguments if valid_arguments else []
        self.valid_attributes = valid_attributes if valid_attributes else []

    def base_ref(self):
        return f"{self.block_type}.{'.'.join(self.labels)}"

    def __repr__(self) -> str:
        return self.base_ref()

    def ref(self, attribute_name: Optional[str] = None):
        if not attribute_name:
            return f"{self.base_ref()}.{self.valid_attributes[0]}"

        return f"{self.base_ref()}.{attribute_name}"

    def write(self):

        code_block = ""

        code_block += f"{self.block_type} {create_labels(self.labels)} {{\n"

        # code_block += (
        #     f"  // Converted from {self.cf_resource.logical_id} {self.cf_resource.type}"
        # )

        for name, value in self.arguments.items():

            if isinstance(value, dict):
                code_block = code_block + "\n\n" + create_subsection(name, value)
                continue
            code_block = code_block + f"  {name} = {value}\n"

        code_block += "}\n"

        return code_block


class Variable(Block):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name

        valid_arguments = ["description", "type", "default"]
        super().__init__("variable", [self.name], arguments, valid_arguments, [])

    def write(self):

        # Type will be quoted, so we have to unquote it.
        self.arguments["type"] = self.arguments["type"].strip('"')

        return super().write()


class Locals(Block):
    def __init__(self, arguments: Dict[str, Any]) -> None:
        name = "locals"
        super().__init__(name, [], arguments, [], [])


class Data(Block):
    def __init__(
        self,
        name: str,
        type: str,
        arguments: Optional[Dict[str, Any]] = None,
        valid_arguments: Optional[List[str]] = None,
        valid_attributes: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.type = type

        super().__init__(
            "data",
            [self.type, self.name],
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
        self.name = name
        self.type = type
        super().__init__(
            "resource",
            [self.type, self.name],
            arguments,
            valid_arguments,
            valid_attributes,
        )


class Output(Block):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name

        valid_arguments = ["description", "value"]
        super().__init__("output", [self.name], arguments, valid_arguments, [])


def create_labels(labels: List[str]):

    label_quotes = [f'"{label}"' for label in labels]

    return " ".join(label_quotes)


def create_subsection(name: str, values: Dict[str, Any], indent_level: int = 1):

    indent = "  " * indent_level

    code_block = f"{indent}{name} {{"

    for name, value in values.items():
        code_block = code_block + f"\n{indent}  {name} = {value}"

    return code_block + f"\n{indent}}}\n"
