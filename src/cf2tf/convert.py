import datetime
import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type

from thefuzz import process  # type: ignore

import cf2tf.conversion.expressions as functions
import cf2tf.terraform._configuration as config
import cf2tf.terraform.doc_file as doc_file
from cf2tf.conversion.overrides import GLOBAL_OVERRIDES, OVERRIDE_DISPATCH
from cf2tf.terraform.blocks import Block, Locals, Output, Resource, Variable
from cf2tf.terraform.hcl2 import AllTypes
from cf2tf.terraform.hcl2.complex import ListType, MapType
from cf2tf.terraform.hcl2.custom import CommentType, LiteralType
from cf2tf.terraform.hcl2.primitive import (
    BooleanType,
    NumberType,
    StringType,
    TerraformType,
)

if TYPE_CHECKING:
    from cf2tf.terraform.code import SearchManager


# Wish I could go back to this style of import but getting cycle error
# from cf2tf.terraform import doc_file, Configuration

ResourceName = str
ResourceValues = Dict[str, Any]
Template = Dict[str, Any]
CFResource = Tuple[ResourceName, ResourceValues]
CFResources = List[CFResource]
Manifest = Dict[str, CFResources]

CFDict = Dict[str, Dict[str, Any]]

log = logging.getLogger("cf2tf")


class TemplateConverter:
    def __init__(
        self, template_name: str, cf_template: CFDict, search_manager: "SearchManager"
    ) -> None:
        self.name = template_name
        self.cf_template = cf_template
        self.search_manager = search_manager
        self.terraform = config.Configuration([])
        self.all_resources: Optional[CFResources]
        self.manifest: Manifest = {}

        self.post_proccess_blocks: List[Block] = []

        # This is not only the sections we are interested in, but the conversion order,
        # which is also important.
        self.valid_sections = [
            "Parameters",
            "Mappings",
            "Conditions",
            "Resources",
            "Outputs",
        ]

    @staticmethod
    def _json_encoder(value: Any) -> Any:
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()
        else:
            return value

    def add_post_block(self, block: Block):
        block_refs = [block.base_ref() for block in self.post_proccess_blocks]

        log.debug(block_refs)

        if block.base_ref() not in block_refs:
            self.post_proccess_blocks.insert(0, block)

    def get_block_by_type(self, block_type: Type[Block]):
        for block in self.post_proccess_blocks:
            if isinstance(block, block_type):
                return block

    def convert(self) -> config.Configuration:
        # Should convert the given cloudformation template to a terraform configuration
        self.parse_template()

        # This is used by the resolve values function
        self.all_resources = [
            resource for _, resources in self.manifest.items() for resource in resources
        ]

        # These are the resources converted directly from cloudformation
        tf_resources = self.convert_to_tf(self.manifest)

        # We also dynamicly generate new resources like the locals block
        tf_resources[:0] = self.post_proccess_blocks

        return config.Configuration(tf_resources)

    def parse_template(self):
        for section in self.valid_sections:
            if section not in self.cf_template:
                log.debug(
                    f"Ignoring section {section} not found in {self.valid_sections}"
                )
                continue

            section_values = self.cf_template[section]

            self.manifest[section] = list(section_values.items())

        log.debug(
            f"Parsed the following resources for processing:\n{json.dumps(self.manifest, default=self._json_encoder)}"
        )

    def resource_lookup(
        self, resource_name: str, sections: List[str]
    ) -> Optional[Dict[str, Any]]:
        for section in sections:
            section_resources = self.manifest.get(section)

            if section_resources:
                section_map: Dict[str, Dict[str, Any]] = dict(section_resources)  # type: ignore

                if resource_name in section_map:
                    resource = section_map[resource_name]
                    return resource

        return None

    def convert_to_tf(self, manifest: Manifest):
        tf_resources: List[Block] = []

        for section in list(manifest):
            resources = manifest[section]
            log.debug(f"Converting {len(resources)} {section}")

            converter = get_converter(self, section)

            tf_resources.extend(converter(resources))

        return tf_resources

    def resolve_values(  # noqa: max-complexity=13
        self,
        data: Any,
        allowed_func: functions.Dispatch,
        prev_func: Optional[str] = None,
    ):
        """Recurses through a Cloudformation template. Solving all
        references and variables along the way.

        Args:
            data (Any): Could be a dict, list, str or int.

        Returns:
            Any: Return the rendered data structure.
        """

        if isinstance(data, dict):
            key: str

            for key in list(data):
                value = data[key]

                if key == "Ref":
                    return functions.ref(self, value)

                # This takes care of keys that not intrinsic functions,
                #  except for the condition func
                if "Fn::" not in key and key != "Condition":
                    data[key] = self.resolve_values(value, allowed_func, prev_func)
                    continue

                # Takes care of the tricky 'Condition' key
                if key == "Condition":
                    # The real fix is to not resolve every key/value in the entire
                    # cloudformation template. We should only attempt to resolve what is needed,
                    # like outputs and resource properties.
                    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html

                    if "Properties" in data or "Value" in data:
                        continue

                    # If it's an intrinsic func
                    if is_condition_func(value):
                        return functions.condition(self, value)

                    # Normal key like in an IAM role
                    data[key] = self.resolve_values(value, allowed_func, prev_func)
                    continue

                if key not in allowed_func:
                    raise ValueError(f"{key} not allowed to be nested in {prev_func}.")

                prev_func = key

                value = self.resolve_values(
                    value, functions.ALLOWED_FUNCTIONS[key], prev_func
                )

                try:
                    return allowed_func[key](self, value)
                except Exception as e:
                    return CommentType(
                        f"Unable to resolve {key} with value: {value} because {e}"
                    )

            return MapType(data)
        elif isinstance(data, list):
            resolved_list_values = [
                self.resolve_values(item, allowed_func, prev_func) for item in data
            ]

            return ListType(resolved_list_values)
        elif isinstance(data, bool):
            return BooleanType(data)
        elif isinstance(data, str):
            return StringType(data)
        elif isinstance(data, (int, float)):
            return NumberType(data)
        elif isinstance(data, datetime.date):
            return StringType(str(data))
        else:
            log.error(f"Found type {type(data)} with value {data}")
            raise Exception(f"Unknown value {data}, in resolve function.")

    def convert_parameters(self, parameters: CFResources):
        tf_vars: List[Variable] = []

        for param_name, param_value in parameters:
            log.debug(
                f"Converting Cloudformation Parameter - {param_name} to Terraform."
            )

            tf_name = pascal_to_snake(param_name)
            log.debug(f"Converted name to {tf_name}")

            tmp_props: Dict[str, Any] = {
                "description": param_value.get("Description", ""),
                "type": param_value.get("Type", "").lower(),
                "default": param_value.get("Default", ""),
            }

            converted_arguments = {k: v for k, v in tmp_props.items() if v != ""}

            resolved_args = self.resolve_values(converted_arguments, {})

            if "type" in resolved_args:
                resolved_args["type"] = convert_parameter_type(resolved_args["type"])

            var = Variable(tf_name, MapType(resolved_args))

            tf_vars.append(var)

            # Add space for easier to read logging output
            add_space()

        return tf_vars

    def convert_mappings(self, mappings: CFResources):
        log.debug("Converting Mappings to Terraform Locals block.")

        dict_mappings = dict(mappings)

        resolved_values = self.resolve_values(dict_mappings, functions.ALL_FUNCTIONS)

        mapping_args = {"mappings": resolved_values}

        local_block = Locals(mapping_args)

        self.post_proccess_blocks.append(local_block)

        return []

    def convert_conditions(self, conditions: CFResources):
        log.debug("Converting Conditions to Terraform Locals block.")

        dict_conditons = dict(conditions)

        resolved_values = self.resolve_values(dict_conditons, functions.ALL_FUNCTIONS)

        log.debug(resolved_values)

        local_block = self.get_block_by_type(Locals)

        if local_block:
            local_block.arguments.update(resolved_values)
            return []

        local_block = Locals(resolved_values)

        self.post_proccess_blocks.append(local_block)

        return []

    def convert_resources(self, resources: CFResources):
        tf_resources: List[Resource] = []

        for resource_id, resource_values in resources:
            log.debug(f"Converting Cloudformation resource {resource_id} to Terraform.")

            tf_name = pascal_to_snake(resource_id)
            log.debug(f"Converted name to {tf_name}")

            resource_type = resource_values.get("Type")

            if not resource_type:
                raise Exception("Type is required")

            docs_path = self.search_manager.find(resource_type)

            log.debug(f"Found documentation file {docs_path}")

            tf_type = create_resource_type(docs_path)

            log.debug(f"Converted type from {resource_values.get('Type')} to {tf_type}")

            valid_arguments, valid_attributes = doc_file.parse_attributes(docs_path)

            log.debug(
                f"Parsed the following arguments from the documentation: \n{valid_arguments}"
            )

            log.debug(
                f"Parsed the following attributes from the documentation: \n{valid_attributes}"
            )

            properties: Dict[str, Any] = resource_values.get("Properties", {})

            arguments = MapType(properties)

            if properties:
                log.debug(
                    "Converting the intrinsic functions to Terraform expressions..."
                )

                resolved_values = self.resolve_values(
                    properties, functions.ALL_FUNCTIONS
                )

                log.debug("Overiding Properties")

                overrided_values = perform_resource_overrides(
                    tf_type, resolved_values, self
                )

                overrided_values = perform_global_overrides(
                    tf_type, overrided_values, self
                )

                log.debug("Converting property names to argument names...")

                arguments = props_to_args(overrided_values, valid_arguments, docs_path)

                log.debug(f"Converted properties to {arguments}")

            conditional = resource_values.get("Condition")

            if conditional is not None:
                condition_map = {"count": LiteralType(f"local.{conditional} ? 1 : 0")}
                arguments = MapType({**condition_map, **arguments})

            resource = Resource(
                tf_name, tf_type, arguments, valid_arguments, valid_attributes
            )
            tf_resources.append(resource)

            # Add space for easier to read logging output
            add_space()

        return tf_resources

    def convert_outputs(self, outputs: CFResources):
        tf_outputs: List[Output] = []

        for output_id, output_props in outputs:
            log.debug(f"Converting Cloudformation Output {output_id} to Terraform.")

            tf_name = pascal_to_snake(output_id)
            log.debug(f"Converted name to {tf_name}")

            tmp_props: Dict[str, Any] = {
                "description": output_props.get("Description", ""),
                "value": output_props.get("Value"),
            }

            converted_args = {k: v for k, v in tmp_props.items() if v != ""}

            resolved_args = self.resolve_values(converted_args, functions.ALL_FUNCTIONS)

            log.debug(f"Converted properties to {resolved_args}")

            tf_outputs.append(Output(tf_name, resolved_args))

            # Add space for easier to read logging output
            add_space()

        return tf_outputs


def get_converter(
    item: Any,
    section_name: str,
) -> Callable[[CFResources], List[Block]]:
    conveter_name = f"convert_{section_name.lower()}"

    converter = getattr(item, conveter_name)
    return converter


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

    # Score needs to bascially be an exact match
    result = matcher(search_term, search_items, 95)

    if not result:
        log.debug(f"{tf_attribute_name} does not have a section in {docs_path}")
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
        score_cutoff=score_cutoff,
    )

    return result


def camel_case_split(text: str) -> str:
    items = re.findall(r"[A-Z\d](?:[a-z]+|\d|[A-Z]*(?=[A-Z]|$))", text)

    return " ".join(items) if items else text


def create_resource_type(doc_path: Path):
    file_base_name = doc_path.name.split(".")[0]
    return f"aws_{file_base_name}"


# todo Not used yet, but I think it will be in a future refactoring
def contains_functions(self, data: Dict[str, Any]):
    functions = ["Ref", "Fn::"]

    for key in list(data):
        if key in functions:
            return True

    return False


def props_to_args(
    cf_props: Dict[str, AllTypes],
    valid_tf_arguments: List[str],
    docs_path: Path,
):
    # Search works better if we split the words apart, but we have to put it back together later
    search_items = [item.replace("_", " ") for item in valid_tf_arguments]

    converted_attrs: Dict[str, AllTypes] = {}

    for prop_name, prop_value in cf_props.items():
        tf_arg_name, tf_arg_value = convert_prop_to_arg(
            prop_name, prop_value, search_items, docs_path
        )

        converted_attrs[tf_arg_name] = tf_arg_value

    log.debug(f"Converted {cf_props.keys()} to {converted_attrs.keys()}")

    return MapType(converted_attrs)


def convert_prop_to_arg(
    prop_name: str, prop_value: AllTypes, search_items: List[str], docs_path: Path
) -> Tuple[str, AllTypes]:
    search_term = camel_case_split(prop_name)

    log.debug(f"Searching for {search_term} instead of {prop_name}")

    result = matcher(search_term, search_items, 80)

    if not result:
        log.debug(f"No match found for {prop_name}, commenting out this argument.")
        # return f"// CF Property({prop_name})", str(prop_value)
        return prop_name, CommentType(f"CF Property({prop_name}) = {prop_value}")

    attribute_match, ranking = result

    # Putting the underscore back in
    tf_arg_name = attribute_match.replace(" ", "_")

    log.debug(f"Converted {prop_name} to {tf_arg_name} with {ranking}% match.")

    # Terraform sometimes has nested blocks, if prop_value is a map/list, its possible
    # that tf_attribute_name is a nested block in terraform

    if not isinstance(prop_value, (list, dict)):
        return tf_arg_name, prop_value

    try:
        tf_arg, tf_values = parse_subsection(tf_arg_name, prop_value, docs_path)
        return tf_arg, tf_values
    except Exception:
        raise Exception(
            f"Failed to parse subsection for {prop_name}/{tf_arg_name} in {docs_path}"
        )


def parse_subsection(
    arg_name: str, prop_value: AllTypes, docs_path: Path
) -> Tuple[str, AllTypes]:
    """Checks for a subsection and parses it if found. If a subsection
    is not found it will return arg_name and prop_value unchanged.

    Args:
        arg_name (str): The Terraform argument name.
        prop_value (Any): The Cloudformation property to be converted to Terraform argument.

    Returns:
        Tuple[str, Any]: The arg_name and prop_value.
    """

    section_name = find_section(arg_name, docs_path)

    if not section_name:
        if isinstance(prop_value, dict):
            log.debug(f"{arg_name} has Map value but no subsection in {docs_path}")
            return arg_name, prop_value

        return arg_name, prop_value

    valid_sub_args = doc_file.read_section(docs_path, section_name)

    if not valid_sub_args:
        log.warning(f"{arg_name} has section in {docs_path} but section was empty.")
        return arg_name, prop_value

    log.debug(f"Valid {arg_name} arguments are {valid_sub_args}")

    if not isinstance(prop_value, (dict, list)):
        raise TypeError(
            f"Found section {section_name} but prop_value was {type(prop_value).__name__} not dict or list."
        )

    # todo Nested blocks now have better support but this function will need to be refactored.
    # Currently the function returns a tuple where the key is argument and the value is some terraform type.
    # This works if the section is a key -> map in Cloudformation and nested block in terraform. But
    # in some cases its key -> list in Cloudformation and Block, Block, Block in Terraform. This function
    # will need to be modified so it returns something capable of expressing this relationship.
    if isinstance(prop_value, list):
        sub_args: List[TerraformType] = []

        for sub_props in prop_value:
            if not isinstance(sub_props, Dict):
                sub_args.append(CommentType(sub_props))

            try:
                sub_args.append(props_to_args(sub_props, valid_sub_args, docs_path))
            except:  # noqa: E722
                sub_args.append(CommentType(sub_props))

        return arg_name, ListType(sub_args)

    sub_attrs = props_to_args(prop_value, valid_sub_args, docs_path)
    return arg_name, Block(arg_name, (), sub_attrs)


def convert_parameter_type(param_type: str):
    type_conversion = {
        "String": "string",
        "Number": "number",
        "List<Number>": "list(number)",
        "CommaDelimitedList": "list(string)",
    }

    # todo We might need to handle other types like the SSM ones?
    if param_type not in type_conversion:
        return LiteralType("string")

    return LiteralType(type_conversion[param_type])


def add_space():
    if log.level == logging.DEBUG:
        print()


def perform_resource_overrides(
    tf_type: str, params: Dict[str, TerraformType], tc: TemplateConverter
):
    log.debug(f"Overiding params for {tf_type}")
    if tf_type not in OVERRIDE_DISPATCH:
        return params

    param_overrides = OVERRIDE_DISPATCH[tf_type]

    for param, override in param_overrides.items():
        if param in params:
            params = override(tc, params)

    return params


def perform_global_overrides(
    tf_type: str, params: Dict[str, TerraformType], tc: TemplateConverter
):
    log.debug(f"Performing global overrides for {tf_type}")

    for param, override in GLOBAL_OVERRIDES.items():
        if param in params:
            params = override(tc, params)

    return params


# All the other Cloudformation intrinsic functions start with `Fn:` but for some reason
# the Condition function does not. This can be problem because
#  `Condition` is a valid key in an IAM policy but its value is always a Map.
def is_condition_func(value: Any) -> bool:
    """Checks if the 'Condition' key is a instrinsic function.

    Args:
        value (Any): The value of the 'Condition' key.

    Returns:
        bool: True if we think this `Condition` key is an instrinsic function.
    """
    if isinstance(value, str):
        return True

    return False
