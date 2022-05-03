from typing import Any, Dict, List, Optional, Tuple
import logging
import re
from cf2tf.terraform.code import SearchManager, Var, Resource, Output
from cf2tf import terraform as tf
from cf2tf import cloudformation as cf
from cf2tf.terraform import doc_file
from thefuzz import process, fuzz

CFDict = Dict[str, Dict[str, Any]]
log = logging.getLogger("cf2tf")

# Might need to make this entire file a class, so I dont have to pass SearchManger
# on to convert_resources


class TerraformConverter:
    def __init__(self, cf_template: CFDict, search_manager: SearchManager) -> None:
        self.cf_template = cf_template
        self.search_manager = search_manager

    def convert(self):

        # for var in self.convert_vars(self.cf_template["Parameters"]):
        #     print(var.convert())

        vars = [var for var in self.convert_vars(self.cf_template["Parameters"])]

        # for resource in self.convert_resources(self.cf_template["Resources"]):
        #     print(resource.write())
        #     print()

        resources = [
            resource
            for resource in self.convert_resources(self.cf_template["Resources"])
        ]

        # return vars + resources

        # for output in self.convert_outputs(self.cf_template["Outputs"]):
        #     print(output.convert())

        outputs = [
            output for output in self.convert_outputs(self.cf_template["Outputs"])
        ]

        return vars + resources + outputs

    def convert_vars(self, cf_params: CFDict):

        for var_name, values in cf_params.items():
            yield Var(var_name, values)

    def convert_resources(self, cf_resources: CFDict):

        for logical_id, fields in cf_resources.items():

            # We need to handle instrinsic functions before we get here, but for now...
            # dirty hack

            for prop_name, prop_value in fields.get("Properties", {}).items():

                if isinstance(prop_value, dict):

                    # Get a key from the dict
                    value_key: str = next(iter(prop_value))

                    if "Fn::" in value_key or "Ref" in value_key:
                        log.error(
                            f"Found instrinsic function {value_key} in {logical_id}'s Properties!"
                        )
                        log.debug(f"Converting {prop_value} to {prop_value[value_key]}")
                        fields["Properties"][prop_name] = prop_value[value_key]

            cf_resource = cf.Resource(logical_id, fields)

            resource_converter = ResourceConverter(cf_resource, self.search_manager)
            yield resource_converter.convert()
            # docs_path = self.search_manager.find(cf_attributes["Type"])

            # yield Resource(cf_resource_name, cf_attributes["Properties"], docs_path)

    def convert_outputs(self, cf_params: CFDict):

        for var_name, values in cf_params.items():
            yield Output(var_name, values)


class ResourceConverter:
    def __init__(self, cf_resource: cf.Resource, terraform_docs: SearchManager) -> None:
        self.cf_resource = cf_resource
        self.terraform_docs = terraform_docs
        self.docs_path = self.terraform_docs.find(self.cf_resource.type)

    def convert(self):
        """Converts a Cloudformation resource into a Terraform one."""
        # log.debug(cf_resource)
        log.debug(f"Converting {self.cf_resource.logical_id} to Terraform.")

        docs_path = self.terraform_docs.find(self.cf_resource.type)

        log.debug(f"Using values from {docs_path} for conversion.")

        all_tf_attrs = doc_file.parse_attributes(docs_path)

        log.debug(f"Valid Terraform attributes are {all_tf_attrs}")

        log.debug(self.cf_resource)

        converted_attributes = self.attributes(
            self.cf_resource.properties, all_tf_attrs
        )

        log.debug(f"Converted attributes are {converted_attributes}")

        return tf.Resource(
            self.cf_resource.logical_id,
            docs_path.name.split(".")[0],
            converted_attributes,
            all_tf_attrs,
        )

    def attributes(self, cf_props: Dict[str, Any], valid_tf_attributes: List[str]):
        """Converts cloudformation propeties into terraform attributes."""

        # Search works better if we split the words apart, but we have to put it back together later
        search_items = [item.replace("_", " ") for item in valid_tf_attributes]

        converted_attrs: Dict[str, Any] = {}

        for prop_name, prop_value in cf_props.items():

            search_term = camel_case_split(prop_name)

            log.debug(f"Searching for {search_term} instead of {prop_name}")

            result = matcher(search_term, search_items, 50)

            if not result:
                converted_attrs[f"// CF Property - {prop_name}"] = prop_value
                continue

            attribute_match, ranking = result

            # Putting the underscore back in
            tf_attribute_name = attribute_match.replace(" ", "_")

            log.debug(
                f"Converted {prop_name} to {tf_attribute_name} with {ranking}% match."
            )

            # Terraform sometimes has nested blocks, if prop_value is a map, its possible
            # that tf_attribute_name is a nested block in terraform

            if isinstance(prop_value, dict):
                section_name = self.find_section(tf_attribute_name)

                if not section_name:
                    converted_attrs[tf_attribute_name] = prop_value
                    continue

                valid_sub_attributes = doc_file.read_section(
                    self.docs_path, section_name
                )

                log.debug(f"Valid Terraform attributes are {valid_sub_attributes}")

                sub_attrs = self.attributes(prop_value, valid_sub_attributes)
                converted_attrs[tf_attribute_name] = sub_attrs
                continue

            converted_attrs[tf_attribute_name] = prop_value

        return converted_attrs

    def find_section(self, tf_attribute_name: str):
        """Checks to see if the attribute is also a subsection in the terraform documentation

        Args:
            tf_attribute_name (str): A terraform attribute name.

        Returns:
            str: The name of the section if found, otherwise none.
        """

        log.debug(f"Checking if {tf_attribute_name} has a section in {self.docs_path}.")

        # Search works better if we split the words apart, but we have to put it back together later
        search_term = tf_attribute_name.replace("_", " ")

        search_items = doc_file.all_sections(self.docs_path)

        result = matcher(search_term, search_items, 90)

        if not result:
            log.warn(f"{tf_attribute_name} does not have a section in {self.docs_path}")
            return ""

        result_name, ranking = result

        log.debug(f"Found section {result_name} with {ranking}% match.")

        return result_name


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
