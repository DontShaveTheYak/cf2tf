"""Nox sessions."""

import nox
import sys
from pathlib import Path

from textwrap import dedent

try:
    from nox_poetry import Session
    from nox_poetry import session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.
    Please install it using the following command:
    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None


python_versions = ["3.12", "3.11", "3.10", "3.9", "3.8"]

nox.options.sessions = (
    # "pre-commit",
    # "safety",
    # "mypy",
    "black",
    "lint",
    "mypy",
    "tests",
    # "typeguard",
    # "xdoctest",
    # "docs-build",
)

locations = "src", "tests", "noxfile.py"


@session(python=python_versions[1])
def black(session):
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@session(python=python_versions[1])
def lint(session):
    args = session.posargs or locations
    session.install("flake8")
    session.run("flake8", *args)


@session(python=python_versions[1])
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or [
        "--install-types",
        "--non-interactive",
        "src",
        "tests",
    ]
    session.install(".")
    session.install("mypy", "pytest")
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install("coverage[toml]", "pytest", "pygments")
    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@session(python=python_versions[1])
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.install("coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)
