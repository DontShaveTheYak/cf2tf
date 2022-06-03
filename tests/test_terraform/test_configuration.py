import pytest

from cf2tf.terraform import Configuration
from pathlib import Path


@pytest.fixture(scope="session")
def fake_c() -> Configuration:
    return Configuration(Path(), [])


resolve_values_tests = [
    # (input, expected_result, fake_c)
    (
        "A",
        '"A"',
        Configuration(Path(), []),
    ),
    (
        ["A", "B", "C"],
        ['"A"', '"B"', '"C"'],
        Configuration(Path(), []),
    ),
    (
        {"Foo": "Bar"},
        {"Foo": '"Bar"'},
        Configuration(Path(), []),
    ),
]


@pytest.mark.parametrize("input, expected_result, fake_c", resolve_values_tests)
def test_resolve_values(input, expected_result, fake_c: Configuration):

    result = fake_c.resolve_values(input, {})

    assert result == expected_result
