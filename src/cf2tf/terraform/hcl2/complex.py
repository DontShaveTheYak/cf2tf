import logging
from typing import Dict, List, Union

from cf2tf.terraform.hcl2.primitive import PrimitiveTypes, TerraformType

log = logging.getLogger("cf2tf")


class ListType(list, TerraformType):
    def __init__(self, value: List[TerraformType]) -> None:
        """Default constructor

        Args:
            value (str): The value for this Terraform type.
        """
        super().__init__(value)
        self.value = value

    def __str__(self) -> str:
        return self.render()

    def render(self, indent=0):
        return render_tf_list(self, indent)


class MapType(dict, TerraformType):
    def __init__(self, value=Dict[PrimitiveTypes, TerraformType]) -> None:
        """Default constructor

        Args:
            value (str): The value for this Terraform type.
        """
        super().__init__(value)
        self.value = value

    def __str__(self) -> str:
        return self.render()

    def render(self, indent=0):
        return render_tf_map(self, indent)


ComplexTypes = Union[ListType, MapType]


def render_tf_list(items: List[TerraformType], indent=0):
    rear_brace = " " * indent

    indent += 2

    spacing = " " * indent

    result = "[\n"

    for item in items:
        comma = "" if item is items[-1] else ","

        result += f"{spacing}{item.render(indent)}{comma}\n"

    result += f"{rear_brace}]"

    return result


def render_tf_map(items: Dict[PrimitiveTypes, TerraformType], indent=0):
    rear_brace = " " * indent

    indent += 2

    spacing = " " * indent

    result = "{"

    for name, value in items.items():
        # if isinstance(value, ListType):
        #     result += f"\n{spacing}{name} = {value.render(indent)}"

        result = result + f"\n{spacing}{name} = {value.render(indent)}"

    return result + f"\n{rear_brace}}}"
