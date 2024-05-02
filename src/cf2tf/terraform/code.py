import logging
import re
from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir
from typing import Optional

import click
from click._termui_impl import ProgressBar
from git import RemoteProgress
from git.repo.base import InvalidGitRepositoryError, Repo
from thefuzz import fuzz, process  # type: ignore

# import cf2tf.convert

log = logging.getLogger("cf2tf")


class SearchManager:
    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path
        self.resources = list(docs_path.joinpath("r").glob("*.markdown"))
        self.datas = list(docs_path.joinpath("d").glob("*.markdown"))

    def find(self, resource_type: str) -> Path:
        name = resource_type_to_name(resource_type)

        log.debug(f"Searcing for {name} in terraform docs...")

        files = {
            doc_file: transform_file_name(doc_file.name) for doc_file in self.resources
        }

        resource_name: str
        ranking: int
        doc_path: Path
        resource_name, ranking, doc_path = process.extractOne(
            name.lower(), files, scorer=fuzz.ratio
        )

        log.debug(
            f"Best match was {resource_name} at {doc_path} with score of {ranking}."
        )

        return doc_path


def search_manager():
    docs_dir = "website/docs"

    repo = get_code()

    docs_path = Path(repo.working_dir).joinpath(docs_dir)

    if not docs_path.exists():
        print("The docs path does not exist")

    return SearchManager(docs_path)


def get_code() -> Repo:
    temp_dir = Path(gettempdir())
    repo_path = temp_dir.joinpath("terraform_src")

    try:
        existing_repo = repo_from_existing(repo_path)

        if existing_repo:
            return existing_repo

    except InvalidGitRepositoryError:
        rmtree(repo_path)
        repo_path.rmdir()

    print(f"// Cloning Terraform src code to {repo_path}...", end="")

    repo_path.mkdir(exist_ok=True)

    repo = Repo.clone_from(
        "https://github.com/hashicorp/terraform-provider-aws.git",
        repo_path,
        depth=1,
        progress=CloneProgress(),  # type: ignore
    )
    click.echo(" code has been checked out.")

    return repo


def repo_from_existing(repo_path: Path) -> Optional[Repo]:
    if repo_path.exists():
        if repo_path.joinpath(".git").exists():
            repo = Repo(repo_path)
            click.echo(f"// Existing Terraform src code found at {repo_path}.")
            return repo

    return None


def resource_type_to_name(resource_type: str) -> str:
    """Converts a Cloudformation Resource Type into something more search friendly.

    Args:
        resource_type (str): The Cloudformation resource type.

    Returns:
        str: A search term that can be used to match resources in the TF docs.
    """

    search_tokens = resource_type.replace("::", " ").replace("AWS", " ").split(" ")

    # I will leave the logic for camel case splitting here for now.
    # in case we want to use it later.
    # for i, token in enumerate(search_tokens):
    #     if len(token) >= 4:
    #         search_tokens[i] = cf2tf.convert.camel_case_split(token)

    search_term = " ".join(search_tokens).lower().strip()

    log.debug(f"Converted CF type {resource_type} to search term {search_term}.")

    return search_term


class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar: Optional[ProgressBar] = None

    def update(self, op_code, cur_count, max_count=None, message=""):
        if not self.pbar and max_count:
            self.create_pbar(int(max_count))

        if self.pbar:
            self.pbar.length = int(max_count)
            self.pbar.update(1)

    def create_pbar(self, max_count):
        self.pbar = click.progressbar(length=max_count)


def transform_file_name(og_name: str):
    no_extensions = og_name.split(".")[0]

    no_underscores = no_extensions.replace("_", " ")

    # Sometimes file names have v2 in them.
    split_numbers = re.split(r"(v\d)", no_underscores)

    return " ".join([item.strip() for item in split_numbers])
