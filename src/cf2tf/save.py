"""Save the results of the conversion.
"""
import logging
from itertools import groupby
from pathlib import Path
from typing import Iterable, List, Optional, Type

try:
    from typing import Protocol
except ImportError:
    # Python 3.6 and 3.7
    from typing_extensions import Protocol  # type: ignore

import cf2tf.terraform.hcl2 as hlc2

log = logging.getLogger("cf2tf")


class Output(Protocol):
    def save(self, resources: List[hlc2.Block]) -> None:
        """Save the results

        Args:
            resources (List[hlc2.Block]): The resources to be saved.
        """


class Directory:
    def __init__(self, directory: str) -> None:

        output_dir = Path(directory)

        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        if not output_dir.is_dir():
            raise Exception(f"Output {output_dir} should be a directory.")

        self.output_dir = output_dir

    def save(self, resources: List[hlc2.Block]) -> None:
        """Save the results to a directory where each resource type gets it's own file.

        Args:
            resources (List[hlc2.Block]): The resources to be saved.
        """
        log.info(f"Saving converted terraform objects to {self.output_dir.absolute()}")
        for k, g in groupby(resources, lambda s: type(s)):
            self.write_group(k, g)

    def write_group(self, block_type: Type[hlc2.Block], blocks: Iterable[hlc2.Block]):
        """Creates a file and writes the resources into it.

        Args:
            block_type (Type[hlc2.Block]): The type of terraform blocks
            blocks (List[hlc2.Block]): A list of terraform blocks.
        """
        block_name = block_type.__name__.lower()

        file_name = f"{block_name}.tf"

        file_path = self.output_dir / file_name

        with file_path.open("w", encoding="utf-8") as f:
            for block in blocks:
                contents = block.write()
                f.write(contents)
                f.write("\n")


class StdOut:
    def save(self, resources: List[hlc2.Block]) -> None:
        """Save the results to stdout

        Args:
            resources (List[hlc2.Block]): The resources to be saved.
        """

        for resource in resources:
            try:
                print()
                print(resource.write())
            except Exception as e:
                print(f"Unable to write {'.'.join(resource.labels)}")
                raise e


def create_writer(output: Optional[str]) -> Output:

    writer: Output

    if output:
        writer = Directory(output)
    else:
        writer = StdOut()

    return writer
