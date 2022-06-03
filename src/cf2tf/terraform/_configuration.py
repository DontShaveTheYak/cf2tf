from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from cf2tf.conversion import expressions as functions

from cf2tf.terraform.hcl2 import Block, Locals, Variable, Output, Data
import cf2tf.convert
import logging

from cf2tf.save import Output

log = logging.getLogger("cf2tf")


class Configuration:
    def __init__(self, output_path: Path, resources: List[Block]) -> None:
        self.resources = resources
        self.output_path = output_path

    def save(self, output: Output):

        # We should probably handle the actual saving of resources here

        self.resolve_objects()

        output.save(self.resources)

    def resolve_objects(self):

        # Cant loop over the actual list because we are adding items to it
        # which creates some pretty crazy bugs
        for block in self.resources.copy():

            # These dont have anything to resolve
            if isinstance(block, Data):
                continue

            log.debug(f"\n### Resolving values for {block.labels}")
            self.resolve_values(block.arguments, functions.ALL_FUNCTIONS)

    def resolve_values(self, data: Any, allowed_func: functions.Dispatch) -> Any:
        """Recurses through a Cloudformation template. Solving all
        references and variables along the way.

        Args:
            data (Any): Could be a dict, list, str or int.

        Returns:
            Any: Return the rendered data structure.
        """

        if isinstance(data, dict):

            # for key, value in data.items():

            for key in list(data):

                value = data[key]

                if key == "Ref":
                    return functions.ref(self, value)

                if "Fn::" not in key:
                    data[key] = self.resolve_values(value, allowed_func)
                    continue

                if key not in allowed_func:
                    raise ValueError(f"{key} not allowed here.")

                value = self.resolve_values(value, functions.ALLOWED_FUNCTIONS[key])

                return allowed_func[key](self, value)

            return data
        elif isinstance(data, list):
            return [self.resolve_values(item, allowed_func) for item in data]
        else:

            # This weirdess handles an empty string like "",
            # with out it, it becomes """" when printed()
            if not data:
                return data

            return f'"{data}"'

    def block_lookup(self, name: str, block_type: Type[Block]) -> Optional[Block]:

        name = cf2tf.convert.pascal_to_snake(name)

        for block in self.blocks_by_type(block_type):

            if name in block.labels:
                return block

    def blocks_by_type(self, block_type: Type[Block]):
        return [block for block in self.resources if isinstance(block, block_type)]
