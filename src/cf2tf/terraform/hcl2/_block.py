import logging
from typing import Dict, List, Optional, Tuple, Union

from cf2tf.terraform.hcl2.custom import CommentType, LiteralType
from cf2tf.terraform.hcl2.primitive import StringType, TerraformType

log = logging.getLogger("cf2tf")

# BlockLabel = Tuple[Union[str, StringType, Tuple[()]]]

BlockLabel = Union[
    Tuple[()],
    Tuple[
        Union[
            str,
            StringType,
        ],
        ...,
    ],
]

Arguments = Dict[str, Union[TerraformType, "Block"]]


class Block:
    """A block creates a child body that is annotated
    with a block type and zero or more block labels."""

    def __init__(
        self,
        block_type: str,
        labels: Optional[BlockLabel] = None,
        arguments: Optional[Arguments] = None,
        valid_arguments: Optional[List[str]] = None,
        valid_attributes: Optional[List[str]] = None,
    ) -> None:
        self.block_type = block_type
        self.labels = labels if labels else ()
        self.arguments = arguments if arguments else {}
        self.valid_arguments = valid_arguments if valid_arguments else []
        self.valid_attributes = valid_attributes if valid_attributes else []

    def base_ref(self):
        return f"{self.block_type}.{'.'.join(self.labels)}".replace('"', "")

    def __repr__(self) -> str:
        return self.base_ref()

    def __str__(self) -> str:
        return self.render()

    def ref(self, attribute_name: Optional[str] = None):
        count = "[0]" if "count" in self.arguments else ""

        resource_name = f"{self.base_ref()}{count}"

        attribute = (
            self.valid_attributes[0] if attribute_name is None else attribute_name
        )

        return LiteralType(f"{resource_name}.{attribute}")

    def render(self, indent=0):
        brace_space = " " * indent

        indent += 2

        block_labels = " ".join(str(label) for label in self.labels)

        label_space = " " if self.labels else ""

        arg_newline = "\n" if self.arguments else ""

        block_args = render_arguments(self.arguments, indent)

        block = f"""{brace_space}{self.block_type}{label_space}{block_labels} {{{arg_newline}{block_args}{arg_newline}{brace_space}}}"""

        return block


def render_arguments(args: Arguments, indent=0):
    if not args:
        return ""

    indent_spacing = " " * indent

    results = []

    for name, value in args.items():
        try:
            if isinstance(value, (Block, CommentType)):
                results.append(value.render(indent))
                continue

            results.append(f"{indent_spacing}{name} = {value.render(indent)}")
        except AttributeError as ex:
            log.debug(f"Key is type {type(name)} with value {value} ")
            log.debug(f"Value is type {type(value)} with value {value} ")
            raise Exception(
                f"Failed to render argument {name} with value:\n{value}"
            ) from ex

    return "\n".join(results)
