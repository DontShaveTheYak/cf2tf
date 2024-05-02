import logging
import re
from io import TextIOWrapper
from pathlib import Path
from typing import List

log = logging.getLogger("cf2tf")


def parse_attributes(docs_path: Path):
    with open(docs_path) as file:
        try:
            arguments = parse_section("Argument Reference", file)
        except Exception as e:
            raise Exception(f"Unable to find arguments in {file.name}") from e

        try:
            attributes = parse_section("Attribute Reference", file)
        except Exception as e:
            raise Exception(f"Unable to find attributes in {file.name}") from e

    return (arguments, attributes)


def read_section(docs_path: Path, section_name: str):
    items: List[str]
    with open(docs_path) as file:
        items = parse_section(section_name, file)

    return items


def parse_section(name: str, file: TextIOWrapper):
    """
    Parses items from a specific section in a file.

    This function first finds the specified section in the file using the `find_section` function.
    Then, it parses the items in the found section using the `parse_items` function and returns a list of these items.

    Args:
        name (str): The name of the section to parse items from.
        file (TextIOWrapper): The file to parse items from.

    Returns:
        List[str]: A list of items found in the section. If no items are found, an empty list is returned.
    """
    # Throws an exception if the section is not found
    find_section(name, file)

    items = parse_items(file)

    # sometimes we dont find items and thats ok
    if not items:
        log.debug(f"Unable to find items in section {name} of {file.name}")

    return items


def parse_items(file: TextIOWrapper):
    """
    Parses attributes from a section in a file.

    This function reads through a file line by line until it finds a line that starts with a "*" character,
    which indicates an attribute. It then extracts the attribute using a regular expression and adds it to a list.
    The function stops parsing attributes when it encounters an empty line or a line that starts with a "#" character,
    which indicates a new section.

    Args:
        file (TextIOWrapper): The file to parse attributes from.

    Returns:
        List[str]: A list of attributes found in the section. If no attributes are found, an empty list is returned.
    """
    attributes: List[str] = []

    while True:
        # We need the  current postion incase we run into the next section
        cur_pos = file.tell()

        line = file.readline()

        if not line:
            log.debug("We have ran out out attributes to parse")
            break

        # If line starts with whitespace its probably a multiline description
        if line.startswith((" ", "\t")):
            continue

        # These should be the attributes we are after
        if line[0] == "*" or line[0] == "-":
            regex = r"`([\w.*]+)`"

            match = re.search(regex, line)

            if not match:
                log.debug(f"Did not find an item to parse in {line}")
                continue

            attribute = match.group(1)

            attributes.append(attribute)

        # We have reached a new markdown section
        if line[0] == "#":
            file.seek(cur_pos)
            break

    return attributes


def all_sections(docs_path: Path):
    sections: List[str] = []

    with open(docs_path) as file:
        while True:
            line = file.readline()

            # We dont care about the top level sections, only ## and ##
            if line.startswith("##"):
                sections.append(line.strip())

            if not line:
                break

    return sections


def find_section(name: str, file: TextIOWrapper):
    """Searches for a markdown section in a file and returns the position of the section.

    This function reads through a file line by line until it finds a line that starts with a "#" character
    and contains the specified name. It then returns the position of the next line in the file.
    If the end of the file is reached without finding the section, it logs a debug message and raises an exception.

    Args:
        name (str): The name of the section to find
        file (TextIOWrapper): The file to search

    Raises:
        Exception: If the section is not found

    Returns:
        int: The position of the next line after the section
    """
    while True:
        cur_pos = file.tell()

        line = file.readline()

        if line.startswith("#") and name in line:
            return cur_pos + 1

        if not line:
            raise Exception(f"Unable to find section {name} in {file.name}")
