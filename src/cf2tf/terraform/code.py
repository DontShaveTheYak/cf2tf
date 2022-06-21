import logging
from pathlib import Path
from typing import Optional

import click
from git import RemoteProgress
from git.repo.base import Repo
from thefuzz import fuzz, process  # type: ignore

import cf2tf.convert

from click._termui_impl import ProgressBar

log = logging.getLogger("cf2tf")


class SearchManager:
    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path
        self.resources = list(docs_path.joinpath("r").glob("*.markdown"))
        self.datas = list(docs_path.joinpath("d").glob("*.markdown"))

    def find(self, name: str) -> Path:

        name = name.replace("::", " ").replace("AWS", "")

        name = cf2tf.convert.camel_case_split(name).lower().strip()

        log.debug(f"Searcing for {name} in terraform docs...")

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


def get_code():

    repo_path = Path("/tmp/terraform_src")

    if repo_path.exists():

        if repo_path.joinpath(".git").exists():
            # todo Need to check to make sure the remote is correct
            click.echo(" existing repo found.")
            repo = Repo(repo_path)
            return repo

    print(f"// Cloning Terraform src code to {repo_path}...", end="")

    repo_path.mkdir(exist_ok=True)

    repo = Repo.clone_from(
        "https://github.com/hashicorp/terraform-provider-aws.git",
        "/tmp/terraform_src",
        depth=1,
        progress=CloneProgress(),
    )
    click.echo(" code has been checked out.")

    return repo


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
