#!/usr/bin/env python3

from io import TextIOWrapper
from typing import Any, Dict

# from marko import Markdown, ast_renderer
from pprint import pprint
import re

from yaml import parse

# import marko


def parseAttributes(file: TextIOWrapper):

    attributes: list[str] = []

    while True:
        line = file.readline()

        # If line starts with whitespace its probably a multiline description
        if line.startswith((" ", "\t")):
            continue

        if line[0] == "*":

            regex = r"`([\w]+)`"

            attribute = re.search(regex, line).group(1)

            # attribute = line[line.find("`")+1:line.find("`")]
            # print(attribute)
            attributes.append(attribute)

        # We have reached a new markdown section
        if line[0] == "#":
            break

        if not line:
            print("We have ran out out attributes to parse")

    return attributes


def parseDoc(file: TextIOWrapper):

    name: str
    arguments: list[str] = []
    attributes: list[str] = []

    while True:
        line = file.readline()

        if "# Resource:" in line:
            name = line.split(":")[-1].strip()

        if "## Argument Reference" in line:
            arguments = parseAttributes(file)

        if "## Attributes Reference" in line:
            attributes = parseAttributes(file)
            break

        if not line:
            break

    print(name)
    pprint(arguments + attributes)


raw_markdown: str

with open("autoscaling_group.html.markdown") as file:
    parseDoc(file)

# print(raw_markdown)

# markdown = Markdown(renderer=ast_renderer.ASTRenderer)

# document: Dict[str, Any] = markdown.convert(raw_markdown)

# for item in document['children']:
#     if 'bullet' in item and item['bullet'] == '*':
#         pprint(item)
