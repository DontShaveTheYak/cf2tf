from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

import re

# from cf2tf.cloudformation.functions import sub
from cf2tf.conversion import expressions as functions

from .code import Output, Resource, Var, pascal_to_snake


class Configuration:
    def __init__(self, output_path: Path, resources: List[Resource]) -> None:
        self.resources = resources
        self.output_path = output_path

    def get_resource(self, name: str):
        for resource in self.resources:
            if not isinstance(resource, Resource):
                continue
            if resource.cf_resource.logical_id == name:
                return resource

    def save(self):

        # self.output_path.mkdir()

        # resource_path = self.output_path.joinpath("resources.tf")

        # resource_path.touch()

        # resource_path = self.output_path

        self.convert_resources()

        self.resolve_objects()

        for resource in self.resources:
            print()
            print(resource.write())

    def resolve_objects(self):

        for resource in self.resources:

            if isinstance(resource, Var):
                continue

            self.resolve_values(resource.attributes, functions.ALL_FUNCTIONS)

    def convert_resources(self):
        # make sure all resources have been converted
        for resource in self.resources:
            if isinstance(resource, Resource):
                resource.convert()

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
            return data

    # def resolve_objects(self):

    #     for resource in self.resources:
    #         if isinstance(resource, Var):
    #             continue
    #         self.resolve_attributes(resource.attributes)

    def resource_lookup(self, name: str):

        name = pascal_to_snake(name)

        for resource in self.resources:

            if (
                hasattr(resource, "cf_resource")
                and resource.cf_resource.logical_id == name
            ):
                return resource
            else:
                if resource.name == name:
                    return resource

    def resolve_attributes(self, data: Any):

        if isinstance(data, dict):

            # for key, value in data.items():

            for key in list(data):

                value = data[key]
                # print(f"Old value = {value}")
                value = self.resolve_attributes(value)
                # print(f"New value = {value}")

                data[key] = value

            return data
        elif isinstance(data, list):
            return [self.resolve_attributes(item) for item in data]
        else:
            return sub_s(self, data)


def sub_s(config: "Configuration", value: str) -> str:
    """Solves AWS Sub intrinsic function String version.

    Args:
        template (Template): The template being tested.
        value (str): The String containing variables.

    Returns:
        str: Input String with variables substituted.
    """

    # print(value)
    if not isinstance(value, str):
        return value

    def replace_var(m):
        var = m.group(2)
        result = resolve_attribute(config, var)
        return f"${{{result}}}"

    reVar = r"(?!\$\{\!)\$(\w+|\{([^}]*)\})"

    if re.search(reVar, value):
        return re.sub(reVar, replace_var, value).replace("${!", "${")

    return resolve_attribute(config, value)


def resolve_attribute(config: "Configuration", attr_value: Any) -> Any:

    if not isinstance(attr_value, str):
        return attr_value

    if not attr_value.startswith("SOME_TYPE."):
        return attr_value

    # print(attr_value)

    _, resource_name, *extras = attr_value.split(".")

    resource = resource_lookup(config, resource_name)

    if not resource:
        raise Exception(f"Could not find resouce {resource_name}")

    # print(resource.type)

    first_attr = next(iter(resource.all_attributes))

    return f"aws_{resource.type}.{resource.name}.{first_attr}"


def resource_lookup(config: "Configuration", name: str):

    for resource in config.resources:

        if hasattr(resource, "cf_resource") and resource.cf_resource.logical_id == name:
            return resource
        else:
            if resource.name == name:
                return resource
