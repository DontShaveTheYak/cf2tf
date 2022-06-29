"""Convert Expression

This module contains the logic to convert an AWS intrinsic function/conditional to
it's Terraform equivalent.
"""
import logging
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

import cf2tf.convert
import cf2tf.terraform.doc_file as doc_file
import cf2tf.terraform.hcl2 as hcl2

if TYPE_CHECKING:
    from cf2tf.convert import TemplateConverter

log = logging.getLogger("cf2tf")

Dispatch = Dict[str, Callable[..., Any]]

# todo Most of these exceptions are very similar
# either we expect a certain type and didnt get it.
# or we expect a certain length of list and didnt get it.
# We should make an two or three exceptions to cover this


def base64(_tc: "TemplateConverter", value: Any):
    """Converts Cloudformation Fn::Base64 intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If value is not a String.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"Fn::Base64 - The value must be a String, not {type(value).__name__}."
        )

    value = value.strip('"')
    return f"base64encode({value})"


def cidr(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::Cidr intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If length of values is not 3.

    Returns:
        str: Terraform equivalent expression.
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

    ip_block: str = values[0].strip('"')
    count = int(values[1])
    hostBits = int(values[2])

    mask = 32 - hostBits

    _, netmask = ip_block.split("/")

    newbits = mask - int(netmask)

    return f'cidrsubnets("{ip_block}", {", ".join([str(newbits)] * count)})'


def and_(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::And intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If length of values is not between 2 and 10.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::And - The values must be a List, not {type(values).__name__}."
        )

    len_ = len(values)

    if len_ < 2 or len_ > 10:
        raise ValueError("Fn::And - The values must have between 2 and 10 conditions.")

    return f"alltrue({values})"


def equals(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::Equals intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 2.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Equals - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 2:
        raise ValueError("Fn::Equals - The values must contain two values to compare.")

    return f"{values[0]} == {values[1]}"


def if_(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::If intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        TypeError: If the first value in the values is not str.

    Returns:
        str: Terraform equivalent expression.
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

    condition = condition.strip('"')

    return f"local.{condition} ? {values[1]} : {values[2]}"


def not_(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::Not intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 1.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Not - The values must be a List, not {type(values).__name__}."
        )

    if not len(values) == 1:
        raise ValueError("Fn::Not - The values must contain a single Condition.")

    condition: Any = values[0]

    # todo This needs fixed because python True needs to be terraform true
    return f"!{condition}"


def or_(_tc: "TemplateConverter", values: Any):
    """Converts Cloudformation Fn::Or intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not between 2 and 10.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(values, list):
        raise TypeError(
            f"Fn::Or - The values must be a List, not {type(values).__name__}."
        )

    len_: int = len(values)

    if len_ < 2 or len_ > 10:
        raise ValueError("Fn::Not - The values must have between 2 and 10 conditions.")

    # todo This isnt really correct. We need a way to convert a python
    # data object into a valid terraform argument value, which includes proper quoting
    # and maybe even indentation

    values = _terraform_list(values)

    return f"anytrue({values})"


def condition(template: "TemplateConverter", name: Any):
    """Converts Cloudformation Fn::Condition intrinsic function to it's Terraform equivalent.

    Args:
        _c (Configuration): The Terraform template.
        value (Any): The value passed to the intrinsic function.

    Raises:
        TypeError: If name is not a String.

    Returns:
        str: Terraform equivalent expression.
    """

    if not isinstance(name, str):
        raise TypeError(
            f"Fn::Condition - The value must be a String, not {type(name).__name__}."
        )

    name = name.strip('"')
    # todo We could check if condition is a key in the local args
    # if name not in template.template["Conditions"]:
    #     raise KeyError(
    #         f"Fn::Condition - Unable to find condition '{name}' in template."
    #     )

    return f"local.{name}"


def find_in_map(template: "TemplateConverter", values: Any):
    """Converts AWS FindInMap intrinsic function to it's Terraform equivalent.

    Args:
        template (Configuration): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        KeyError: If the Map or specified keys are missing.

    Returns:
        str: Terraform equivalent expression.
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

    # First we need to make sure that locals is a block present in the Terraform template.
    blocks = [
        block
        for block in template.post_proccess_blocks
        if isinstance(block, hcl2.Locals)
    ]

    if not blocks:
        raise ValueError("Unable to find a locals block in the template.")

    if len(blocks) > 1:
        raise ValueError(
            f"Expected one locals block but found {len(blocks)} blocks instead."
        )

    local_block: hcl2.Locals = blocks[0]

    maps = local_block.arguments

    if "mappings" not in maps:
        raise Exception("No Mappings found in locals block.")

    # Checking if the map names are valid doesn't work if the names were intrinsic functions/vars

    # Checking if the keys are valid doesn't work if the keys were intrinsic functions/vars

    return f"local.mappings[{map_name}][{top_key}][{second_key}]"


def get_att(template: "TemplateConverter", values: Any):
    """Converts AWS GetAtt intrinsic function to it's Terraform equivalent.

    Args:
        template (Configuration): The template being tested.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a list.
        ValueError: If length of values is not 3.
        TypeError: If the logicalNameOfResource and attributeName are not str.
        KeyError: If the logicalNameOfResource is not found in the template.

    Returns:
        str: Terraform equivalent expression.
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

    cf_name = values[0]
    cf_property = values[1]

    if not isinstance(cf_name, str) or not isinstance(cf_property, str):
        raise TypeError(
            "Fn::GetAtt - logicalNameOfResource and attributeName must be String."
        )

    cf_name = cf_name.strip('"')
    cf_property = cf_property.strip('"')
    nested_prop: Optional[List[str]] = None

    if "." in cf_property:
        cf_property, *nested_prop = cf_property.split(".")

    log.debug(f"Fn::GetAtt - Looking up resource {cf_name}")
    cf_resource = template.resource_lookup(cf_name, ["Resources"])

    if not cf_resource:
        raise KeyError(f"Fn::GetAtt - Resource {cf_name} not found in template.")

    resource_type = cf_resource.get("Type")

    if not resource_type:
        raise Exception("Type is required")

    docs_path = template.search_manager.find(resource_type)
    log.debug(f"Fn::GetAtt - Parsing attributes for {docs_path}")
    valid_arguments, valid_attributes = doc_file.parse_attributes(docs_path)

    result = cf2tf.convert.matcher(cf_property, valid_arguments + valid_attributes, 50)

    if not result:
        raise ValueError(
            f"Could not convert Cloudformation property {cf_property} to Terraform attribute of {valid_attributes}."
        )

    attribute_name, _ = result

    tf_name = cf2tf.convert.pascal_to_snake(cf_name)
    tf_type = cf2tf.convert.create_resource_type(docs_path)

    if nested_prop:

        prop = f"{cf_property}.{'.'.join(nested_prop)}"
        log.debug(
            f"Looking up nested attr {attribute_name} from {cf_property} for {tf_type}"
        )
        return nested_attr(tf_name, tf_type, prop, attribute_name)

    return f"{tf_type}.{tf_name}.{attribute_name}"


def nested_attr(tf_name: str, tf_type: str, cf_prop: str, tf_attr: str):

    if tf_type == "aws_cloudformation_stack" and tf_attr == "outputs":
        return get_attr_nested_stack(tf_name, tf_type, cf_prop, tf_attr)

    raise ValueError(f"Unable to solve nested GetAttr {cf_prop}")


def get_attr_nested_stack(tf_name: str, tf_type: str, cf_property, tf_attr):
    items = cf_property.split(".")

    if len(items) > 2:
        raise ValueError(f"Error parsing nested stack output for {cf_property}")

    _, stack_output_name = items

    return f"{tf_type}.{tf_name}.{tf_attr}.{stack_output_name}"


def get_azs(template: "TemplateConverter", region: Any):
    """Converts AWS GetAZs intrinsic function to it's Terraform equivalent.

    Args:
        template (Configuration): The Terraform Configuration.
        region (Any): The name of a region.

    Raises:
        TypeError: If region is not a string.

    Returns:
        str: Terraform equivalent expression.
    """

    # todo One issue here is that it appears Cloudformation allows you to lookup AZ's for any region,
    # where Terraform only allows you to lookup AZ's for the current region

    if not isinstance(region, str):
        raise TypeError(
            f"Fn::GetAZs - The region must be a String, not {type(region).__name__}."
        )

    region = region.strip('"')

    data = [
        data for data in template.post_proccess_blocks if isinstance(data, hcl2.Data)
    ]

    if not data:
        az_data = hcl2.Data("available", "availability_zones", {"state": "available"})
        template.post_proccess_blocks.insert(0, az_data)

    return "data.aws_availability_zones.available.names"


# todo Handle functions that are not applicable to terraform.
def import_value(template: "TemplateConverter", name: Any):
    # I'm not sure how to handle this but I think if any exception is encountered while
    # converting cf expressions to terraform, we should just comment out the entire line.

    # On second thought it probably makes sense to turn this into a input variable

    raise Exception(
        "Fn::Import Is Cloudformation native and unable to be converted to a Terraform expression."
    )


def join(_tc: "TemplateConverter", values: Any):
    """Converts AWS Join intrinsic function to it's Terraform equivalent.

    Args:
        _t (Configuration): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value isn't a String and second isn't a List.

    Returns:
        str: Terraform equivalent expression.
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
    items: Union[List[Any], str]

    if isinstance(values[0], str) and isinstance(values[1], (list, str)):
        delimiter = values[0].strip('"')
        items = values[1]
    else:
        raise TypeError(
            "Fn::Join-- The first value must be a String and the second a List or String."
        )

    if isinstance(items, str):
        return f'join("{delimiter}", {items})'

    return f'join("{delimiter}", {_terraform_list(items)})'


# todo I'm not sure this is that useful
def _terraform_list(items: List[Any]):

    # Not sure why I ever did this :thinkingface:
    # items = [item for item in items]

    return f"[{', '.join(items)}]"


def select(_tc: "TemplateConverter", values: Any):
    """Converts AWS Select intrinsic function to it's Terraform equivalent.

    Args:
        _t (Configuration): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value is not a int and second is not a List.
        IndexError: If the List size is smaller than the index.

    Returns:
        str: Terraform equivalent expression.
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

    index: int = values[0] if isinstance(values[0], int) else int(values[0].strip('"'))
    items: Union[List[Any], str] = values[1]

    if not isinstance(index, int) or not isinstance(items, (list, str)):
        raise TypeError(
            "Fn::Select - The first value must be a Number and the second a List or String."
        )

    if isinstance(items, str):
        items = items.strip('"')
    else:
        items = _terraform_list(items)

    try:
        return f"element({items}, {index})"
    except IndexError:
        raise IndexError("Fn::Select - List size is smaller than the Index given.")


def split(_tc: "TemplateConverter", values: Any):
    """Converts AWS Split intrinsic function to it's Terraform equivalent.

    Args:
        _t (Configuration): Not used.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a List.
        ValueError: If values length is not 2.
        TypeError: If first value isn't a String and second isn't a String.

    Returns:
        str: Terraform equivalent expression.
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
        delimiter = values[0].strip('"')
        source_string = values[1]
    else:
        raise TypeError(
            "Fn::Split-- The first value must be a String and the second a String."
        )

    return f'split("{delimiter}", "{source_string}")'


def sub(template: "TemplateConverter", values: Any):
    """Converts AWS Sub intrinsic function to it's Terraform equivalent.

    Args:
        template (Configuration): The cf template being converted.
        values (Any): The values passed to the function.

    Raises:
        TypeError: If values is not a String or List.

    Returns:
        str: Terraform equivalent expression.
    """

    if isinstance(values, str):
        return sub_s(template, values)

    if isinstance(values, list):
        return sub_l(template, values)

    raise TypeError(
        f"Fn::Sub - The input must be a String or List, not {type(values).__name__}."
    )


def sub_s(template: "TemplateConverter", value: str):
    """Converts AWS Sub intrinsic function String version to it's Terraform equivalent.

    Args:
        template (Configuration): The template being tested.
        value (str): The String containing variables.

    Returns:
        str: Terraform equivalent expression.
    """

    def replace_var(m):
        var = m.group(2)

        result = ref(template, var)
        return wrap_in_curlys(result)

    reVar = r"(?!\$\{\!)\$(\w+|\{([^}]*)\})"

    if re.search(reVar, value):
        return re.sub(reVar, replace_var, value).replace("${!", "${")

    return value.replace("${!", "${")


# todo This needs to create local variables in the template.
def sub_l(template: "TemplateConverter", values: List):
    """Converts AWS Sub intrinsic function List version to it's Terraform equivalent.

    Args:
        template (Configuration): The template being tested.
        values (List): The List containing input string and var Map.

    Raises:
        ValueError: If length of values is not 2.
        TypeError: If first value not String and second not Map.

    Returns:
        str: Terraform equivalent expression.
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
            result = local_vars[var]
            return wrap_in_curlys(result)

        result = ref(template, var)

        return wrap_in_curlys(result)

    reVar = r"(?!\$\{\!)\$(\w+|\{([^}]*)\})"

    if re.search(reVar, source_string):
        return re.sub(reVar, replace_var, source_string).replace("${!", "${")

    return source_string.replace("${!", "${")


# todo Transform is an AWS native capability with no Terraform equivalent expression.
def transform(_tc: "TemplateConverter", values: Any):
    # I'm not sure how to handle this but I think if any exception is encountered while
    # converting cf expressions to terraform, we should just comment out the entire line.

    raise Exception(
        "Fn::Transform Is Cloudformation native and unable to be converted to a Terraform expression."
    )


def ref(template: "TemplateConverter", var_name: str):
    """Converts AWS Ref intrinsic function to it's Terraform equivalent.

    Args:
        template (Configuration): The template being converted.
        var_name (str): The name of the parameter, resource or pseudo variable.

    Raises:
        ValueError: If the supplied variable doesn't exist.

    Returns:
        str: Terraform equivalent expression.
    """

    if "AWS::" in var_name:

        return handle_pseduo_var(template, var_name)

    cf_param = template.resource_lookup(var_name, ["Parameters"])

    if cf_param:
        tf_name = cf2tf.convert.pascal_to_snake(var_name)
        return f"var.{tf_name}"

    cf_resource = template.resource_lookup(var_name, ["Resources"])

    if cf_resource:
        cf_resource_type = cf_resource.get("Type", "")
        docs_path = template.search_manager.find(cf_resource_type)
        _, valid_attributes = doc_file.parse_attributes(docs_path)
        tf_name = cf2tf.convert.pascal_to_snake(var_name)
        tf_type = cf2tf.convert.create_resource_type(docs_path)
        first_attr = next(iter(valid_attributes))
        return f"{tf_type}.{tf_name}.{first_attr}"

    raise ValueError(f"Fn::Ref - {var_name} is not a valid Resource or Parameter.")


pseduo_values = {
    "Region": hcl2.Data("current", "aws_region", valid_attributes=["name"]),
    "AccountId": hcl2.Data(
        "current", "aws_caller_identity", valid_attributes=["account_id"]
    ),
    "Partition": hcl2.Data("current", "aws_partition", valid_attributes=["partition"]),
}


def handle_pseduo_var(template: "TemplateConverter", pseudo_name: str):

    pseudo_type = pseudo_name.replace("AWS::", "")

    if pseudo_type not in pseduo_values:

        if pseudo_type == "NoValue":
            return "null"

        if pseudo_type == "URLSuffix":
            block = pseduo_values["Partition"]

            if block not in template.post_proccess_blocks:
                template.post_proccess_blocks.insert(0, block)

            return block.ref("dns_suffix")

        raise ValueError(f"Unable to process pseudo var {pseudo_name}.")

    block = pseduo_values[pseudo_type]

    if block not in template.post_proccess_blocks:
        template.post_proccess_blocks.insert(0, block)

    return block.ref()


def wrap_in_curlys(input: str):
    """Wrap the input in ${} to make a terraform variable."""

    return f"${{{input}}}"


# These are all the json keys for condition functions
CONDITIONS: Dispatch = {
    "Fn::And": and_,
    "Fn::Equals": equals,
    "Fn::If": if_,
    "Fn::Not": not_,
    "Fn::Or": or_,
    "Fn::Condition": condition,
}

# These are all the json keys for intrinsic functions
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

# This is a map of all cloudformation functions
ALL_FUNCTIONS: Dispatch = {
    **CONDITIONS,
    **INTRINSICS,
}


# These are the functions allowed to be called inside other condition functions
ALLOWED_NESTED_CONDITIONS: Dispatch = {
    "Fn::FindInMap": find_in_map,
    "Ref": ref,
    **CONDITIONS,
}

# Cloudformation only allows certain functions to be called from inside
# other functions. The keys are the function name and the values are the
# functions that are allowed to be nested inside it.
ALLOWED_FUNCTIONS: Dict[str, Dispatch] = {
    "Fn::And": ALLOWED_NESTED_CONDITIONS,
    "Fn::Equals": {**ALLOWED_NESTED_CONDITIONS, "Fn::Join": join},
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
