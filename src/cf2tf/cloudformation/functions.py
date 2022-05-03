"""AWS Intrinsic functions.

This module contains the logic to solve both AWS Intrinsic
and Condition functions.
"""

import base64 as b64
import ipaddress
import json
import re
from typing import Any, Callable, Dict, List, TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from ._template import Template

Dispatch = Dict[str, Callable[..., Any]]

REGION_DATA = None


def base64(_t: "Template", value: Any) -> str:
    """Solves AWS Base64 intrinsic function.

    Args:
        _t (Template): Not used.
        value (Any): The value to encode.

    Raises:
        TypeError: If value is not a String.

    Returns:
        str: The value as a Base64 encoded String.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"Fn::Base64 - The value must be a String, not {type(value).__name__}."
        )

    b_string = b64.b64encode(value.encode("ascii"))

    return b_string.decode("ascii")


def cidr(_t: "Template", values: Any) -> List[str]:
    """Solves AWS Cidr intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If length of values is not 3.
        Exception: If unable to convert network address to desired subnets.

    Returns:
        List[str]: The subnets with network address and mask.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Cidr - The value must be a List, not {type(values).__name__}."
        )

    if not len(values) == 3:
        raise ValueError(
            (
                "Fn::Cidr - The value must contain "
                "a ipBlock, the count of subnets and the cidrBits."
            )
        )

    ip_block: str = values[0]
    count = int(values[1])
    hostBits = int(values[2])

    mask = 32 - hostBits

    network = ipaddress.IPv4Network(ip_block, strict=True)

    subnets = network.subnets(new_prefix=mask)

    try:
        return [next(subnets).exploded for _ in range(count)]
    except Exception:
        raise Exception(
            f"!Cidr or Fn::Cidr unable to convert {ip_block} into {count} subnets of /{mask}"
        )


def and_(_t: "Template", values: Any) -> bool:
    """Solves AWS And intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If length of values is not between 2 and 10.

    Returns:
        bool: True if all values are True.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::And - The values must be a List, not {type(values).__name__}."
        )

    len_ = len(values)

    if len_ < 2 or len_ > 10:
        raise ValueError("Fn::And - The values must have between 2 and 10 conditions.")

    return all(values)


def equals(_t: "Template", values: Any) -> bool:
    """Solves AWS Equals intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 2.

    Returns:
        bool: True if the values are equal.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Equals - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 2:
        raise ValueError("Fn::Equals - The values must contain two values to compare.")

    return values[0] == values[1]


def if_(template: "Template", values: Any) -> Any:
    """Solves AWS If intrinsic function.

    Args:
        template (Template): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        TypeError: If the first value in the values is not str.

    Returns:
        Any: The first value if True, otherwise second value.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::If - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 3:
        raise ValueError(
            (
                "Fn::If - The values must contain "
                "the name of a condition, a True value and "
                "a False value."
            )
        )

    condition = values[0]

    if not isinstance(condition, str):
        raise TypeError(
            f"Fn::If - The Condition should be a String, not {type(condition).__name__}."
        )

    condition = template.template["Conditions"][condition]

    if condition:
        return values[1]

    return values[2]


def not_(_t: "Template", values: Any) -> bool:
    """Solves AWS Not intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 1.

    Returns:
        bool: The opposite of values.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Not - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 1:
        raise ValueError("Fn::Not - The values must contain a single Condition.")

    condition: bool = values[0]

    return not condition


def or_(_t: "Template", values: Any) -> bool:
    """Solves AWS Or intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not between 2 and 10.

    Returns:
        bool: True if any value in the values is True.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Or - The values must be a List, not {type(values).__name__}."
        )

    len_: int = len(values)

    if len_ < 2 or len_ > 10:
        raise ValueError("Fn::Not - The values must have between 2 and 10 conditions.")

    return any(values)


def condition(template: "Template", name: Any) -> bool:
    """Solves AWS Condition function.

    Args:
        template (Template): The template being tested.
        name (Any): The name of the condition.

    Raises:
        TypeError: If name is not a String.
        KeyError: If name not found in template conditions.

    Returns:
        bool: The value of the condition.
    """

    if not isinstance(name, str):
        raise TypeError(
            f"Fn::Condition - The value must be a String, not {type(name).__name__}."
        )

    if name not in template.template["Conditions"]:
        raise KeyError(
            f"Fn::Condition - Unable to find condition '{name}' in template."
        )

    return template.template["Conditions"][name]


def find_in_map(template: "Template", values: Any) -> Any:
    """Solves AWS FindInMap intrinsic function.

    Args:
        template (Template): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        KeyError: If the Map or specified keys are missing.

    Returns:
        Any: The requested value from the Map.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::FindInMap - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 3:
        raise ValueError(
            (
                "Fn::FindInMap - The values must contain "
                "a MapName, TopLevelKey and SecondLevelKey."
            )
        )

    map_name = values[0]
    top_key = values[1]
    second_key = values[2]

    if "Mappings" not in template.template:
        raise KeyError("Unable to find Mappings section in template.")

    maps = template.template["Mappings"]

    if map_name not in maps:
        raise KeyError(f"Unable to find {map_name} in Mappings section of template.")

    map = maps[map_name]

    if top_key not in map:
        raise KeyError(f"Unable to find key {top_key} in map {map_name}.")

    first_level = map[top_key]

    if second_key not in first_level:
        raise KeyError(f"Unable to find key {second_key} in map {map_name}.")

    return first_level[second_key]


def get_att(template: "Template", values: Any) -> str:
    """Solves AWS GetAtt intrinsic function.

    Args:
        template (Template): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        TypeError: If the logicalNameOfResource and attributeName are not str.
        KeyError: If the logicalNameOfResource is not found in the template.

    Returns:
        str: The interpolated str `logicalNameOfResource.attributeName`.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::GetAtt - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 2:
        raise ValueError(
            (
                "Fn::GetAtt - The values must contain "
                "the logicalNameOfResource and attributeName."
            )
        )

    resource_name = values[0]
    att_name = values[1]

    if not isinstance(resource_name, str) or not isinstance(att_name, str):
        raise TypeError(
            "Fn::GetAtt - logicalNameOfResource and attributeName must be String."
        )

    if resource_name not in template.template["Resources"]:
        raise KeyError(f"Fn::GetAtt - Resource {resource_name} not found in template.")

    return f"{resource_name}.{att_name}"


def get_azs(_t: "Template", region: Any) -> List[str]:
    """Solves AWS GetAZs intrinsic function.

    Args:
        _t (Template): The template being tested.
        region (Any): The name of a region.

    Raises:
        TypeError: If region is not a string.

    Returns:
        List[str]: The list of AZs for the provided region.
    """

    if not isinstance(region, str):
        raise TypeError(
            f"Fn::GetAZs - The region must be a String, not {type(region).__name__}."
        )

    return get_region_azs(region)


def import_value(template: "Template", name: Any) -> str:
    """Solves AWS ImportValue intrinsic function.

    Args:
        template (Template): The template being tested.
        name (Any): The name of the Export to be Imported.

    Raises:
        TypeError: If name is not a String.
        ValueError: If no imports have been configured.
        KeyError: If name is not found in the imports.

    Returns:
        str: The value of name from the configured imports.
    """

    if not isinstance(name, str):
        raise TypeError(
            "Fn::ImportValue - The name of the Export "
            f"should be String, not {type(name).__name__}."
        )

    if not template.imports:
        raise ValueError("Fn::ImportValue - No imports have been configued.")

    if name not in template.imports:
        raise KeyError(f"Fn::ImportValue - {name} not found in the configured imports.")

    return template.imports[name]


def join(_t: "Template", values: Any) -> str:
    """Solves AWS Join intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value isn't a String and second isn't a List.

    Returns:
        str: The items in the List joined by the delimiter.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Join - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 2:
        raise ValueError(
            (
                "Fn::Join - The values must contain "
                "a delimiter and a list of items to join."
            )
        )

    delimiter: str
    items: List[str]

    if isinstance(values[0], str) and isinstance(values[1], list):
        delimiter = values[0]
        items = values[1]
    else:
        raise TypeError(
            "Fn::Join-- The first value must be a String and the second a List."
        )

    return delimiter.join(items)


def select(_t: "Template", values: Any) -> Any:
    """Solves AWS Select intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value is not a int and second is not a List.
        IndexError: If the List size is smaller than the index.

    Returns:
        Any: The selected value form the List.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Select - The values must be a List, not {type(values).__name__}."
        )

    if len(values) != 2:
        raise ValueError(
            (
                "Fn::Select - The values must contain "
                "an index and a list of items to select from."
            )
        )

    index: int
    items: List[Any]

    if isinstance(values[0], int) and isinstance(values[1], list):
        index = values[0]
        items = values[1]
    else:
        raise TypeError(
            "Fn::Select - The first value must be a Number and the second a List."
        )

    try:
        return items[index]
    except IndexError:
        raise IndexError("Fn::Select - List size is smaller than the Index given.")


def split(_t: "Template", values: Any) -> List[str]:
    """Solves AWS Split intrinsic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value isn't a String and second isn't a String.

    Returns:
        List[str]: The String split by the delimiter.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Split - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 2:
        raise ValueError(
            (
                "Fn::Split - The values must contain "
                "a delimiter and a String to split."
            )
        )

    delimiter: str
    source_string: str

    if isinstance(values[0], str) and isinstance(values[1], str):
        delimiter = values[0]
        source_string = values[1]
    else:
        raise TypeError(
            "Fn::Split-- The first value must be a String and the second a String."
        )

    return source_string.split(delimiter)


def sub(template: "Template", values: Any) -> str:
    """Solves AWS Sub intrinsic function.

    Args:
        template (Template): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a String or List.

    Returns:
        str: Input String with variables substituted.
    """

    if isinstance(values, str):
        return sub_s(template, values)

    if isinstance(values, list):
        return sub_l(template, values)

    raise TypeError(
        f"Fn::Sub - The input must be a String or List, not {type(values).__name__}."
    )


def sub_s(template: "Template", value: str) -> str:
    """Solves AWS Sub intrinsic function String version.

    Args:
        template (Template): The template being tested.
        value (str): The String containing variables.

    Returns:
        str: Input String with variables substituted.
    """

    def replace_var(m):
        var = m.group(2)
        return ref(template, var)

    reVar = r"(?!\$\{\!)\$(\w+|\{([^}]*)\})"

    if re.search(reVar, value):
        return re.sub(reVar, replace_var, value).replace("${!", "${")

    return value.replace("${!", "${")


def sub_l(template: "Template", values: List) -> str:
    """Solves AWS Sub intrinsic function List version.

    Args:
        template (Template): The template being tested.
        values (List): The List containing input string and var Map.

    Raises:
        ValueError: If length of values is not 2.
        TypeError: If first value not String and second not Map.

    Returns:
        str: Input String with variables substituted.
    """

    source_string: str
    local_vars: Dict[str, str]

    if len(values) != 2:
        raise ValueError(
            (
                "Fn::Sub - The values must contain "
                "a source string and a Map of variables."
            )
        )

    if isinstance(values[0], str) and isinstance(values[1], dict):
        source_string = values[0]
        local_vars = values[1]
    else:
        raise TypeError(
            "Fn::Sub - The first value must be a String and the second a Map."
        )

    def replace_var(m):
        var = m.group(2)

        if var in local_vars:
            return local_vars[var]

        return ref(template, var)

    reVar = r"(?!\$\{\!)\$(\w+|\{([^}]*)\})"

    if re.search(reVar, source_string):
        return re.sub(reVar, replace_var, source_string).replace("${!", "${")

    return source_string.replace("${!", "${")


def transform(_t: "Template", values: Any) -> str:
    """Solves AWS Transform intrinstic function.

    Args:
        _t (Template): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a Dict.
        KeyError: If Name and Parameters are not in values.

    Returns:
        str: The value of Name from values.
    """

    if not isinstance(values, dict):
        raise TypeError(
            f"Fn::Transform - The values must be a Dict, not {type(values).__name__}."
        )

    if "Name" not in values and "Parameters" not in values:
        raise KeyError(
            ("Fn::Transform - The values must contain " "a Name and Parameters.")
        )

    return values["Name"]


def ref(template: "Template", var_name: str) -> Any:
    """Takes the name of a parameter, resource or pseudo variable and finds the value for it.

    Args:
        template (Template): The template being tested.
        var_name (str): The name of the parameter, resource or pseudo variable.

    Raises:
        ValueError: If the supplied pseudo variable doesn't exist.

    Returns:
        Any: The value of the parameter, resource or pseudo variable.
    """

    if "AWS::" in var_name:
        pseudo = var_name.replace("AWS::", "")

        # Can't treat region like a normal pseduo because
        # we don't want to update the class var for every run.
        if pseudo == "Region":

            # Create the region data source data "aws_region" "current" {}
            template.template["Data"] = {"aws_region": {"Name": "current"}}
            return "${aws_region.current.name}"
        try:
            return getattr(template, pseudo)
        except AttributeError:
            raise ValueError(f"Unrecognized AWS Pseduo variable: '{var_name}'.")

    if var_name in template.template["Parameters"]:
        return f"${{var.{var_name}}}"

    if var_name in template.template["Resources"]:
        return f"${{SOME_TYPE.{var_name}.???}}"

    raise Exception(f"Fn::Ref - {var_name} is not a valid Resource or Parameter.")


def get_region_azs(region_name: str) -> List[str]:
    """Retries AZs from REGION_DATA.

    Args:
        region_name (str): The name of the AWS region.

    Raises:
        Exception: If unable to find data for provided region name.

    Returns:
        List[str]: List of AZs for provided region name.
    """

    global REGION_DATA

    if not REGION_DATA:
        REGION_DATA = _fetch_region_data()

    for region in REGION_DATA:
        if region["code"] == region_name:
            return region["zones"]

    raise Exception(f"Unable to find region {region_name}.")


def _fetch_region_data() -> List[dict]:
    """Fetchs Region JSON from URL.

    Returns:
        List[dict]: Region data.
    """

    url = "https://raw.githubusercontent.com/jsonmaur/aws-regions/master/regions.json"

    r = requests.get(url)

    if not r.status_code == requests.codes.ok:
        r.raise_for_status()

    return json.loads(r.text)


CONDITIONS: Dispatch = {
    "Fn::And": and_,
    "Fn::Equals": equals,
    "Fn::If": if_,
    "Fn::Not": not_,
    "Fn::Or": or_,
    "Fn::Condition": condition,
}

INTRINSICS: Dispatch = {
    "Fn::If": if_,  # Conditional function but is allowed here
    "Fn::Base64": base64,
    "Fn::Cidr": cidr,
    "Fn::FindInMap": find_in_map,
    "Fn::GetAtt": get_att,
    "Fn::GetAZs": get_azs,
    "Fn::ImportValue": import_value,
    "Fn::Join": join,
    "Fn::Select": select,
    "Fn::Split": split,
    "Fn::Sub": sub,
    "Fn::Transform": transform,
    "Ref": ref,
}

ALL_FUNCTIONS: Dispatch = {
    **CONDITIONS,
    **INTRINSICS,
}

ALLOWED_NESTED_CONDITIONS: Dispatch = {
    "Fn::FindInMap": find_in_map,
    "Ref": ref,
    **CONDITIONS,
}

ALLOWED_FUNCTIONS: Dict[str, Dispatch] = {
    "Fn::And": ALLOWED_NESTED_CONDITIONS,
    "Fn::Equals": ALLOWED_NESTED_CONDITIONS,
    "Fn::If": {
        "Fn::Base64": base64,
        "Fn::FindInMap": find_in_map,
        "Fn::GetAtt": get_att,
        "Fn::GetAZs": get_azs,
        "Fn::If": if_,
        "Fn::Join": join,
        "Fn::Select": select,
        "Fn::Sub": sub,
        "Ref": ref,
    },
    "Fn::Not": ALLOWED_NESTED_CONDITIONS,
    "Fn::Or": ALLOWED_NESTED_CONDITIONS,
    "Fn::Condition": {},  # Only allows strings
    "Fn::Base64": ALL_FUNCTIONS,
    "Fn::Cidr": {
        "Fn::Select": select,
        "Ref": ref,
    },
    "Fn::FindInMap": {
        "Fn::FindInMap": find_in_map,
        "Ref": ref,
    },
    "Fn::GetAtt": {},  # This one is complicated =/
    "Fn::GetAZs": {
        "Ref": ref,
    },
    "Fn::ImportValue": {
        "Fn::Base64": base64,
        "Fn::FindInMap": find_in_map,
        "Fn::If": if_,
        "Fn::Join": join,
        "Fn::Select": select,
        "Fn::Split": split,
        "Fn::Sub": sub,
        "Ref": ref,
    },  # Import value can't depend on resources (not implemented)
    "Fn::Join": {
        "Fn::Base64": base64,
        "Fn::FindInMap": find_in_map,
        "Fn::GetAtt": get_att,
        "Fn::GetAZs": get_azs,
        "Fn::If": if_,
        "Fn::ImportValue": import_value,
        "Fn::Join": join,
        "Fn::Split": split,
        "Fn::Select": select,
        "Fn::Sub": sub,
        "Ref": ref,
    },
    "Fn::Select": {
        "Fn::FindInMap": find_in_map,
        "Fn::GetAtt": get_att,
        "Fn::GetAZs": get_azs,
        "Fn::If": if_,
        "Fn::Split": split,
        "Ref": ref,
    },
    "Fn::Split": {
        "Fn::Base64": base64,
        "Fn::FindInMap": find_in_map,
        "Fn::GetAtt": get_att,
        "Fn::GetAZs": get_azs,
        "Fn::If": if_,
        "Fn::ImportValue": import_value,
        "Fn::Join": join,
        "Fn::Split": split,
        "Fn::Select": select,
        "Fn::Sub": sub,
        "Ref": ref,
    },
    "Fn::Sub": {
        "Fn::Base64": base64,
        "Fn::FindInMap": find_in_map,
        "Fn::GetAtt": get_att,
        "Fn::GetAZs": get_azs,
        "Fn::If": if_,
        "Fn::ImportValue": import_value,
        "Fn::Join": join,
        "Fn::Select": select,
        "Ref": ref,
    },
    "Fn::Transform": {},  # Transform isn't fully implemented
    "Ref": {},  # String only.
}
