from ast import expr
from cf2tf.conversion import expressions
from cf2tf.cloudformation import Template, _template

import pytest


@pytest.fixture(scope="session")
def fake_t() -> Template:
    return Template({})


join_tests = [
    (None, ["-", "var.something"], 'join("-", var.something)'),
    (None, ["-", ["A", "B", "C"]], 'join("-", ["A", "B", "C"])'),
    (None, ["-", ["A", "var.thing", "C"]], 'join("-", ["A", var.thing, "C"])'),
    (
        None,
        ["-", ["A", "SOME_TYPE.name.attr", "C"]],
        'join("-", ["A", SOME_TYPE.name.attr, "C"])',
    ),
]


@pytest.mark.parametrize("fake_t, expression, expected", join_tests)
def test_join(fake_t, expression, expected):

    result = expressions.join(fake_t, expression)

    assert result == expected


def test_ref():
    """A reference in cloudformation is a direct reference to a variable."""
    template = {"Parameters": {"foo": {"Value": "bar"}}, "Resources": {}}

    # _template.add_metadata(template, Template.Region)

    template = Template(template)

    some_var = "foo"

    expected_value = f"var.{some_var}"

    assert expected_value == expressions.ref(template, some_var)


def test_select(fake_t):

    cf_expression = [0, "var.something"]

    expected = "element(var.something, 0)"

    result = expressions.select(fake_t, cf_expression)

    assert result == expected

    cf_expression = [0, ["A", "B", "C"]]

    expected = 'element(["A", "B", "C"], 0)'

    result = expressions.select(fake_t, cf_expression)

    assert result == expected


def test_split(fake_t):

    cf_expression = [",", "A,B,C"]

    expected = 'split(",", "A,B,C")'

    result = expressions.split(fake_t, cf_expression)

    assert result == expected


def test_sub():
    """A Sub in cf is a string that contains references to variables, resources or AWS pseudo parameters."""

    template = {"Parameters": {"foo": {"Value": "bar"}}, "Resources": {}}

    template = Template(template)

    some_var = "foo"

    expected_value = f"test ${{var.{some_var}}} string"

    test_string = "test ${foo} string"

    assert expected_value == expressions.sub_s(template, test_string)


def test_transform(fake_t):

    with pytest.raises(Exception):
        _ = expressions.transform(fake_t, "Any Value")
