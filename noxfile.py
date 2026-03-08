"""Nox sessions."""

import sys
from pathlib import Path
from textwrap import dedent

import nox

try:
    from nox_poetry import Session, session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.

    Please install it using the following command:

    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None

python_versions: list[str] = Path(".python-versions").read_text().splitlines()

nox.options.sessions = ("tests",)

locations = "src", "tests", "noxfile.py"


@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install("coverage[toml]", "pytest", "pygments")
    session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
