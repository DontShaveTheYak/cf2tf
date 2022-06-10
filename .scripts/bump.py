#!/usr/bin/python

import sys
from typing import Any, Dict

import requests

import semver

# Should really get these from CICD :Rip:
repo: str = "cf2tf"
owner: str = "DontShaveTheYak"


def do_action(action, version):
    function = getattr(version, action)

    new_version = function()

    print(f"{version} {action} to {new_version}")
    return new_version


def get_response(url) -> Dict[str, Any]:
    response = requests.get(url)
    return response.json()


def get_action(pull_request: str) -> str:
    valid_labels = ["major", "minor", "patch"]
    response = get_response(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_request}"
    )

    label = [
        label["name"] for label in response["labels"] if label["name"] in valid_labels
    ][0]
    return label


def set_output(name: str, value: str):
    print(f"::set-output name={name}::{value}")


def prerelease(rule: str) -> str:
    return f"pre{rule}"


latest_tag = sys.argv[1]
pull_request = sys.argv[2]
branch = sys.argv[3]


action_methods = {"patch": "bump_patch", "minor": "bump_minor", "major": "bump_major"}

if branch != "master":
    action_name = get_action(pull_request)
    action = action_methods[action_name]

base_tag: str = ""
bump_rule: str = ""

print(f"Latest tag is {latest_tag}")

response = get_response(f"https://api.github.com/repos/{owner}/{repo}/releases/latest")
release_tag = str(semver.VersionInfo.parse(response["tag_name"]))

print(f"Latest release is {release_tag}")

if branch == "master":
    print("This release is a final release!")
    base_tag = latest_tag.split("-")[0]
    bump_rule = "None"

elif "-alpha" in latest_tag:
    print("This is an existing prerelease.")

    latest_ver = latest_tag.split("-")[0]

    next_tag = semver.VersionInfo.parse(release_tag)

    next_tag = do_action(action, next_tag)

    latest_ver = semver.VersionInfo.parse(latest_ver)

    compare = semver.compare(str(latest_ver), str(next_tag))

    next_tag = str(next_tag)
    latest_ver = str(latest_ver)

    if compare == -1:
        print(
            f"Creating {next_tag} because its version is higher than latest tag: {latest_ver}"
        )
        base_tag = release_tag
        bump_rule = prerelease(action_name)
    elif compare == 1:
        print(
            f"Reusing latest tag ({latest_tag}) because next tag ({next_tag}) is lower."
        )
        base_tag = latest_tag
        bump_rule = "prerelease"
    else:
        print(
            f"Reusing latest tag ({latest_tag}) because its version is equal to next tag ({next_tag})"  # noqa: B950
        )
        base_tag = latest_tag
        bump_rule = "prerelease"
else:
    print("This is a new prerelease.")
    base_tag = release_tag
    bump_rule = prerelease(action_name)


print(f"Using base tag {base_tag} with bump rule {bump_rule}.")


set_output("base_tag", base_tag)
set_output("bump_rule", bump_rule)
sys.exit(0)
