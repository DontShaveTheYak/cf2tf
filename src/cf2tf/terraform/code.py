from pathlib import Path
from venv import create
from git.repo.base import Repo
from git import RemoteProgress
import logging


from typing import Dict, Any, List, Tuple
from thefuzz import process, fuzz

import click

from cf2tf.terraform import doc_file

# from yaml import parse

# from markdown import parseAttributes

# from cf2tf.convert import CFDict

log = logging.getLogger("cf2tf")


class SearchManager:
    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path
        self.resources = list(docs_path.joinpath("r").glob("*.html.markdown"))
        self.datas = list(docs_path.joinpath("d").glob("*.html.markdown"))

    def find(self, name: str) -> Path:

        name = name.replace("::", " ").lower().replace("aws", "").strip()

        # click.echo(f"Searcing for {name} in terraform docs...")

        files = {
            doc_file: doc_file.name.split(".")[0].replace("_", " ")
            for doc_file in self.resources
        }

        resource_name: str
        ranking: int
        doc_path: Path
        resource_name, ranking, doc_path = process.extractOne(
            name.lower(), files, scorer=fuzz.token_sort_ratio
        )

        # click.echo(
        #     f"Best match was {resource_name} at {doc_path} with score of {ranking}."
        # )

        return doc_path


def search_manager():
    docs_dir = "website/docs"

    repo = get_code()

    docs_path = Path(repo.working_dir).joinpath(docs_dir)

    if not docs_path.exists():
        print("The docs path does not exist")

    return SearchManager(docs_path)


def get_code():

    repo_path = Path("/tmp/terraform_src")

    click.echo(f"Cloning Terraform src code to {repo_path}...", nl=False)

    if repo_path.joinpath(".git").exists():
        # Need to check to make sure the remote is correct
        click.echo(" existing repo found.")
        repo = Repo(repo_path)
        return repo

    print("cloning ....")

    repo = Repo.clone_from(
        "https://github.com/hashicorp/terraform-provider-aws.git",
        "/tmp/terraform_src",
        depth=1,
        progress=CloneProgress(),
    )
    click.echo(" code has been checked out.")

    return repo


# class CloneProgress(RemoteProgress):
#     def __init__(self):
#         super().__init__()
#         self.pbar = tqdm()

#     def update(self, op_code, cur_count, max_count=None, message=""):
#         self.pbar.total = max_count
#         self.pbar.n = cur_count
#         self.pbar.refresh()


class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = None

    def update(self, op_code, cur_count, max_count=None, message=""):
        if not self.pbar and max_count:
            self.create_pbar(int(max_count))

        self.pbar.length = int(max_count)
        self.pbar.update(1)

    def create_pbar(self, max_count):
        self.pbar = click.progressbar(length=max_count)


class Var:
    def __init__(self, name: str, values: Dict[str, Any]) -> None:
        # print(values)
        self.name = name
        self.description = values.get("Description", "")
        self.default = values.get("Default", "")
        self.type = values.get("Type", "").lower()
        self.attributes = {}

        if self.default:
            self.attributes["value"] = self.default

    def write(self):

        code_block = f'variable "{self.name}" {{'

        if self.type:
            code_block = code_block + f"\n  type = {self.type}"

        if self.description:
            code_block = code_block + f'\n  description = "{self.description}"'

        if self.default:
            code_block = code_block + f'\n  default = "{self.default}"'

        return code_block + "\n}\n"


class Resource:
    def __init__(
        self,
        name: str,
        type: str,
        attributes: Dict[str, Any],
        all_attributes: List[str],
    ) -> None:
        self.name = name
        self.type = type
        self.attributes = attributes
        self.all_attributes = all_attributes

    def write(self):

        code_block = f'resource "aws_{self.type}" "{self.name}" {{'

        for name, value in self.attributes.items():

            if isinstance(value, dict):
                code_block = code_block + "\n\n" + self.create_subsection(name, value)
                continue
            code_block = code_block + f"\n  {name} = {use_quotes(value)}"

        return code_block + "\n}\n"

    def create_subsection(
        self, name: str, values: Dict[str, Any], indent_level: int = 1
    ):

        indent = "  " * indent_level

        code_block = f"{indent}{name} {{"

        for name, value in values.items():
            code_block = code_block + f"\n{indent}  {name} = {use_quotes(value)}"

        return code_block + f"\n{indent}}}\n"

    # def convert_attr(self, cf_attributes: Dict[str, Any]):

    #     converted_attrs: Dict[str, Any] = {}
    #     all_tf_attrs = doc_file.parse_attributes(self.docs_path)

    #     # print(all_tf_attrs)

    #     for cf_name, values in cf_attributes.items():
    #         # need to turn a cf attribute into a terraform attribute

    #         tf_attribute_name = self.attribute_matcher(cf_name, all_tf_attrs)

    #         if isinstance(values, dict):
    #             sub_attrs = self.convert_sub_attrs(tf_attribute_name, values)
    #             converted_attrs[tf_attribute_name] = sub_attrs
    #             continue

    #         converted_attrs[tf_attribute_name] = values

    #     return converted_attrs

    def convert_sub_attrs(self, cf_section_name: str, cf_attributes: Dict[str, Any]):

        converted_attrs: Dict[str, Any] = {}

        all_sections = doc_file.all_sections(self.docs_path)

        # need to refactor this function
        section_name = self.attribute_matcher(cf_section_name, all_sections)

        with open(self.docs_path) as file:
            all_tf_attrs = doc_file.parse_section(section_name, file)

        for cf_name, values in cf_attributes.items():
            # need to turn a cf attribute into a terraform attribute
            tf_attribute_name = self.attribute_matcher(cf_name, all_tf_attrs)

            if isinstance(values, dict):
                sub_attrs = self.convert_sub_attrs(cf_name, values)
                converted_attrs[tf_attribute_name] = sub_attrs
                continue

            converted_attrs[tf_attribute_name] = values

        return converted_attrs

    def attribute_matcher(self, cf_name: str, all_tf_attrs: List[str]):

        tf_attribute_name: str
        ranking: int

        result = process.extractOne(
            # cf_name, all_tf_attrs, scorer=fuzz.token_sort_ratio
            cf_name,
            all_tf_attrs,
        )

        if not result:
            log.error(f"Unable to find match for {cf_name} in {all_tf_attrs}.")
            return f"// {cf_name}"

        tf_attribute_name, ranking = result

        log.debug(f"Conveted {cf_name} to {tf_attribute_name} with {ranking}% match.")
        return tf_attribute_name


class Output:
    def __init__(self, name: str, attributes: Dict[str, Any]) -> None:
        # print(values)
        self.name = name

        self.description = attributes.get("Description", "")
        self.attributes = attributes

    def write(self):

        code_block = f'output "{self.name}" {{'

        if self.description:
            code_block = code_block + f'\n  description = "{self.description}"'

        value = self.attributes["Value"]

        code_block = code_block + f"\n  value = {use_quotes(value)}"

        return code_block + "\n}\n"


def use_quotes(item: str):

    if isinstance(item, dict):
        log.error(f"Found a map when writing a terraform attribute value {item}")
        value: str = next(iter(item))

        if "Fn::" in value or "Ref" in value:
            return str(item)

        return item
        # raise Exception("Found weird map when writing values")

    # Basically if the item references a variable then no quotes

    # Handle this in the future
    if isinstance(item, list):
        return item

    if item.startswith("aws_"):
        return item

    if item.startswith("var."):
        return item

    return f'"{item}"'
