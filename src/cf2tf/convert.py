from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import re
from cf2tf.terraform.code import SearchManager
from cf2tf.terraform.hcl2 import Locals, Variable, Resource, Block, Output
import cf2tf.conversion.expressions
from cf2tf import cloudformation as cf
from cf2tf.terraform import doc_file
from thefuzz import process

CFDict = Dict[str, Dict[str, Any]]
log = logging.getLogger("cf2tf")


def parse_template(cf_template: CFDict, search_manager: SearchManager) -> List[Block]:

    blocks: List[Block] = []

    blocks += parse_vars(cf_template)

    blocks += parse_resources(cf_template, search_manager)

    blocks += parse_outputs(cf_template)

    blocks += parse_mappings(cf_template)

    blocks += parse_conditions(cf_template, blocks)

    return blocks


def parse_vars(cf_template: CFDict):

    if "Parameters" not in cf_template:
        log.debug("Did not parse any Parameters from Cloudformation template.")
        return []

    cf_params = cf_template["Parameters"]

    return [create_tf_var(var_name, values) for var_name, values in cf_params.items()]


def create_tf_var(cf_name, cf_props):

    log.debug(f"Converting Cloudformation Parameter - {cf_name} to Terraform.")

    tf_name = pascal_to_snake(cf_name)
    log.debug(f"Converted name to {tf_name}")

    tmp_props: Dict[str, Any] = {
        "description": cf_props.get("Description", ""),
        "type": cf_props.get("Type", "").lower(),
        "default": cf_props.get("Default", ""),
    }

    converted_arguments = {k: v for k, v in tmp_props.items() if v != ""}
    log.debug(f"Converted properties to {converted_arguments}")
    print()

    return Variable(tf_name, converted_arguments)


def parse_resources(cf_template: CFDict, search_manager: SearchManager):

    if "Resources" not in cf_template:
        log.debug("Did not parse any Resources from Cloudformation template.")
        return []

    cf_resources = cf_template["Resources"]

    # todo The call to get_cf_resources could be refactored out
    resources = get_cf_resources(cf_resources)

    return [get_tf_resource(resource, search_manager) for resource in resources]


def get_cf_resources(cf_resources: CFDict):
    return [
        cf.Resource(logical_id, fields) for logical_id, fields in cf_resources.items()
    ]


def get_tf_resource(cf_resource: cf.Resource, search_manager: SearchManager):

    log.debug(
        f"Converting Cloudformation resource {cf_resource.logical_id} to Terraform."
    )

    tf_name = pascal_to_snake(cf_resource.logical_id)
    log.debug(f"Converted name to {tf_name}")

    docs_path = search_manager.find(cf_resource.type)

    log.debug(f"Found documentation file {docs_path}")

    valid_arguments, valid_attributes = doc_file.parse_attributes(docs_path)

    log.debug(
        f"Parsed the following arguments from the documentation: \n{valid_arguments}"
    )

    log.debug(
        f"Parsed the following attributes from the documentation: \n{valid_attributes}"
    )

    tf_type = create_resource_type(docs_path)

    log.debug(f"Converted type from {cf_resource.type} to {tf_type}")

    arguments = props_to_args(cf_resource.properties, valid_arguments, docs_path)

    print()

    return Resource(tf_name, tf_type, arguments, valid_arguments, valid_attributes)


def props_to_args(
    cf_props: Dict[str, Any], valid_tf_arguments: List[str], docs_path: Path
):

    # Search works better if we split the words apart, but we have to put it back together later
    search_items = [item.replace("_", " ") for item in valid_tf_arguments]

    converted_attrs: Dict[str, Any] = {}

    for prop_name, prop_value in cf_props.items():

        if prop_name in cf2tf.conversion.expressions.ALL_FUNCTIONS:
            log.debug(f"Skipping Cloudformation function {prop_name}.")
            converted_attrs[prop_name] = prop_value
            continue

        search_term = camel_case_split(prop_name)

        log.debug(f"Searching for {search_term} instead of {prop_name}")

        result = matcher(search_term, search_items, 50)

        if not result:
            log.debug(f"No match found for {prop_name}, commenting out this argument.")
            converted_attrs[f"// CF Property - {prop_name}"] = prop_value
            continue

        attribute_match, ranking = result

        # Putting the underscore back in
        tf_arg_name = attribute_match.replace(" ", "_")

        log.debug(f"Converted {prop_name} to {tf_arg_name} with {ranking}% match.")

        # Terraform sometimes has nested blocks, if prop_value is a map, its possible
        # that tf_attribute_name is a nested block in terraform

        if isinstance(prop_value, dict):
            section_name = find_section(tf_arg_name, docs_path)

            if not section_name:
                converted_attrs[tf_arg_name] = prop_value
                continue

            valid_sub_args = doc_file.read_section(docs_path, section_name)

            log.debug(f"Valid {tf_arg_name} arguments are {valid_sub_args}")

            sub_attrs = props_to_args(prop_value, valid_sub_args, docs_path)
            converted_attrs[tf_arg_name] = sub_attrs
            continue

        converted_attrs[tf_arg_name] = prop_value

    log.debug(f"Converted {cf_props.keys()} to {converted_attrs.keys()}")

    return converted_attrs


def parse_outputs(cf_template: CFDict):

    if "Outputs" not in cf_template:
        log.debug("Did not parse any Outputs from Cloudformation template.")
        return []

    cf_outputs = cf_template["Outputs"]

    return [create_tf_output(name, values) for name, values in cf_outputs.items()]


def create_tf_output(cf_name, cf_props):

    log.debug(f"Converting Cloudformation Output - {cf_name} to Terraform.")

    tf_name = pascal_to_snake(cf_name)
    log.debug(f"Converted name to {tf_name}")

    tmp_props: Dict[str, Any] = {
        "description": cf_props.get("Description", ""),
        "value": cf_props.get("Value"),
    }

    converted_args = {k: v for k, v in tmp_props.items() if v != ""}
    log.debug(f"Converted properties to {converted_args}")
    log.debug("")

    return Output(tf_name, converted_args)


def parse_mappings(cf_template: CFDict):

    if "Mappings" not in cf_template:
        log.debug("Did not parse any Mappings from Cloudformation template.")
        return []

    cf_mappings = cf_template["Mappings"]

    local_block = Locals(cf_mappings)

    return [local_block]


def parse_conditions(cf_template: CFDict, current_resources: List[Block]):

    if "Conditions" not in cf_template:
        log.debug("Did not parse any Conditions from Cloudformation template.")
        return []

    cf_conditions = cf_template["Conditions"]

    local_blocks = [block for block in current_resources if isinstance(block, Locals)]

    if local_blocks:
        local_block = local_blocks[0]
        local_block.arguments.update(cf_conditions)
        return []

    local_block = Locals(cf_conditions)

    return [local_block]


def find_section(tf_attribute_name: str, docs_path: Path):
    """Checks to see if the attribute is also a subsection in the terraform documentation

    Args:
        tf_attribute_name (str): A terraform attribute name.

    Returns:
        str: The name of the section if found, otherwise none.
    """

    log.debug(f"Checking if {tf_attribute_name} has a section in {docs_path}.")

    # Search works better if we split the words apart, but we have to put it back together later
    search_term = tf_attribute_name.replace("_", " ")

    search_items = doc_file.all_sections(docs_path)

    result = matcher(search_term, search_items, 90)

    if not result:
        log.warn(f"{tf_attribute_name} does not have a section in {docs_path}")
        return ""

    result_name, ranking = result

    log.debug(f"Found section {result_name} with {ranking}% match.")

    return result_name


def pascal_to_snake(name: str):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def matcher(search_term: str, search_items: List[str], score_cutoff=0):

    result: Optional[Tuple[str, int]] = process.extractOne(
        # search_term, search_items, scorer=fuzz.token_sort_ratio
        search_term,
        search_items,
        score_cutoff=score_cutoff
        # scorer=fuzz.token_sort_ratio,
    )

    return result


def camel_case_split(str) -> str:

    items = re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", str)

    return " ".join(items)


def create_resource_type(doc_path: Path):
    file_base_name = doc_path.name.split(".")[0]
    return f"aws_{file_base_name}"
