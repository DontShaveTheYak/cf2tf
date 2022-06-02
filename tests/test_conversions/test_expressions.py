from cf2tf.conversion import expressions
from cf2tf.terraform import Configuration
from pathlib import Path

import pytest
from contextlib import nullcontext as no_exception

import cf2tf.terraform.hcl2 as hcl2


@pytest.fixture(scope="session")
def fake_c() -> Configuration:
    return Configuration(Path(), [])


base64_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    (
        "var.something",
        "base64encode(var.something)",
        no_exception(),
    ),
    pytest.param(
        "something",
        'base64encode("something")',
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", base64_tests)
def test_base64(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.base64(fake_c, input)

    assert result == expected_result


cidr_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([True], None, pytest.raises(ValueError)),
    ([True] * 4, None, pytest.raises(ValueError)),
    (
        ["10.1.0.0/16", "4", "12"],
        'cidrsubnets("10.1.0.0/16", 4, 4, 4, 4)',
        no_exception(),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", cidr_tests)
def test_cidr(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.cidr(fake_c, input)

    assert result == expected_result


and_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([True], None, pytest.raises(ValueError)),
    ([True] * 11, None, pytest.raises(ValueError)),
    (
        [0, 1],
        "alltrue([0, 1])",
        no_exception(),
    ),
    pytest.param(
        ["var.a", "true"],
        'alltrue([var.a, "true"])',
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", and_tests)
def test_and(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.and_(fake_c, input)

    assert result == expected_result


equals_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([True], None, pytest.raises(ValueError)),
    ([True] * 3, None, pytest.raises(ValueError)),
    (
        ["var.a", "var.b"],
        "var.a == var.b",
        no_exception(),
    ),
    pytest.param(
        ["var.a", "something"],
        'var.a == "something"',
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", equals_tests)
def test_equals(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.equals(fake_c, input)

    assert result == expected_result


if_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([], None, pytest.raises(ValueError)),
    ([True] * 4, None, pytest.raises(ValueError)),
    ([True] * 3, None, pytest.raises(TypeError)),
    (
        ["something", "var.a", "var.b"],
        "local.something ? var.a : var.b",
        no_exception(),
    ),
    pytest.param(
        ["something", "a", "b"],
        'local.something ? "a" : "b"',
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", if_tests)
def test_if(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.if_(fake_c, input)

    assert result == expected_result


not_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([], None, pytest.raises(ValueError)),
    ([True] * 2, None, pytest.raises(ValueError)),
    (["var.true"], "!var.true", no_exception()),
    pytest.param(
        [True],
        "!true",
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", not_tests)
def test_not(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.not_(fake_c, input)

    assert result == expected_result


# a tuple with a value for each parameter in the test function
or_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ([True], None, pytest.raises(ValueError)),
    ([True] * 11, None, pytest.raises(ValueError)),
    ([0, 1], "anytrue([0, 1])", no_exception()),
    pytest.param(
        [0, "one", True, "var.test"],
        'anytrue([0, "one", true, var.test])',
        no_exception(),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Conversion from python datatypes to terraform argument values needed",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", or_tests)
def test_or_(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.or_(fake_c, input)

    assert result == expected_result


condition_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ("something", "local.something", no_exception()),
]


@pytest.mark.parametrize("input, expected_result, expectation", condition_tests)
def test_condition(input, expected_result, expectation):

    # fake template that is not used
    fake_c: Configuration = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.condition(fake_c, input)

    assert result == expected_result


def test_find_in_map(fake_c: Configuration):

    # Test that it will only take a list
    with pytest.raises(TypeError) as e:
        expressions.find_in_map(fake_c, {})

    assert "Fn::FindInMap - The values must be a List, not dict." in str(e)

    # Test that it must contain three items

    with pytest.raises(ValueError) as e:
        expressions.find_in_map(fake_c, [""])

    assert "MapName, TopLevelKey and SecondLevelKey." in str(e)

    map_name = "RegionMap"
    top_level_key = "us-east-1"
    second_level_key = "HVM64"

    with pytest.raises(ValueError) as e:
        expressions.find_in_map(fake_c, ["a", "b", "c"])

    assert "Unable to find a locals block" in str(e)

    test_args = {map_name: {top_level_key: {second_level_key: "test value"}}}

    locals_block = hcl2.Locals(test_args)

    fake_c.resources.append(locals_block)

    # Test for map name
    with pytest.raises(KeyError) as e:
        expressions.find_in_map(fake_c, ["fakeMap", top_level_key, second_level_key])

    assert "Unable to find fakeMap" in str(e)

    # Test for top level key
    with pytest.raises(KeyError) as e:
        expressions.find_in_map(fake_c, [map_name, "fake_cop", second_level_key])

    assert "Unable to find key fake_cop" in str(e)

    # test for second level key
    with pytest.raises(KeyError) as e:
        expressions.find_in_map(fake_c, [map_name, top_level_key, "fake_second"])

    assert "Unable to find key fake_second" in str(e)

    expected_result = f'local.{map_name}["{top_level_key}"]["{second_level_key}"]'

    result = expressions.find_in_map(
        fake_c, [map_name, top_level_key, second_level_key]
    )

    assert result == expected_result


def test_get_att(fake_c: Configuration):

    # Test that it will only take a list
    with pytest.raises(TypeError) as e:
        expressions.get_att(fake_c, {})

    assert "Fn::GetAtt - The values must be a List, not dict." in str(e)

    # Test that list size must be two
    with pytest.raises(ValueError) as e:
        expressions.get_att(fake_c, [0])

    assert "values must contain the" in str(e)

    # Test that items must be of type String
    with pytest.raises(TypeError) as e:
        expressions.get_att(fake_c, [0, 0])

    assert "must be String." in str(e)

    # Test with resource not in the configuration
    resource_name = "fake_resource"
    with pytest.raises(KeyError) as e:
        expressions.get_att(fake_c, [resource_name, "name"])

    assert f"{resource_name} not found in configuration." in str(e)

    # We will create a resource for testing
    test_resource = hcl2.Resource(
        "test_stack",
        "aws_cloudformation_stack",
        {"name": "John Doe", "age": 30},
        ["name", "age"],
        ["name", "age", "outputs"],
    )

    fake_c.resources.append(test_resource)

    fake_attr = "weight"

    # Test with a fake attribute
    with pytest.raises(ValueError) as e:
        expressions.get_att(fake_c, [test_resource.name, fake_attr])

    assert f"Could not convert Cloudformation property {fake_attr}" in str(e)

    # Test with a normal attribute
    test_attr = "age"
    expected_result = f"{test_resource.type}.{test_resource.name}.{test_attr}"
    result = expressions.get_att(fake_c, [test_resource.name, test_attr])

    assert result == expected_result


def test_get_att_nested(fake_c: Configuration):
    """Test that nested cloudformation attributes work."""

    # This resource type is fake to invoke an error
    fake_resource = hcl2.Resource(
        "fake_stack",
        "aws_cloudformation_stack_fake",
        {"name": "John Doe", "age": 30},
        ["name", "age"],
        ["name", "age", "outputs"],
    )

    fake_c.resources.append(fake_resource)

    test_attr = "outputs.something"

    # Test that the fake resource does not work
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_c,
            [fake_resource.name, test_attr],
        )

    assert f"Unable to solve nested GetAttr {test_attr}" in str(e)

    # Add valid resource for testing
    test_resource = hcl2.Resource(
        "test_stack",
        "aws_cloudformation_stack",
        {"name": "John Doe", "age": 30},
        ["name", "age"],
        ["name", "age", "outputs"],
    )

    fake_c.resources.append(test_resource)

    # Test attribute nested too far
    nested_attr = f"{test_attr}.toofar"
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_c,
            [test_resource.name, nested_attr],
        )

    assert f"Error parsing nested stack output for {nested_attr}" in str(e)

    # Test normal result

    expected_result = f"{test_resource.type}.{test_resource.name}.{test_attr}"

    result = expressions.get_att(fake_c, [test_resource.name, test_attr])

    assert result == expected_result


def test_get_azs(fake_c: Configuration):

    # Lets test that only valid Cloudformation functions work correctly.
    with pytest.raises(TypeError):
        not_valid_region = []
        _ = expressions.get_azs(fake_c, not_valid_region)

    # test that the return value is correct
    expected = "data.aws_availability_zones.available.names"
    result = expressions.get_azs(fake_c, "Testing")
    assert result == expected

    # Make sure the datasource was added correctly
    assert fake_c.block_lookup("available", block_type=hcl2.Data)


join_tests = [
    (None, ["-", "var.something"], 'join("-", var.something)'),
    (None, ["-", ["A", "B", "C"]], 'join("-", ["A", "B", "C"])'),
    (None, ["-", ["A", "var.thing", "C"]], 'join("-", ["A", var.thing, "C"])'),
    (
        None,
        ["-", ["A", "aws_resource.name.attr", "C"]],
        'join("-", ["A", aws_resource.name.attr, "C"])',
    ),
]


@pytest.mark.parametrize("fake_c, expression, expected", join_tests)
def test_join(fake_c, expression, expected):

    result = expressions.join(fake_c, expression)

    assert result == expected


def test_ref():
    """A reference in cloudformation is a direct reference to a variable."""

    var = hcl2.Variable("foo", {"value": "bar"})
    resources = [var]

    tf_config = Configuration(Path(), resources)

    expected_value = f"var.{var.name}"

    assert expected_value == expressions.ref(tf_config, var.name)


def test_select(fake_c):

    cf_expression = [0, "var.something"]

    expected = "element(var.something, 0)"

    result = expressions.select(fake_c, cf_expression)

    assert result == expected

    cf_expression = [0, ["A", "B", "C"]]

    expected = 'element(["A", "B", "C"], 0)'

    result = expressions.select(fake_c, cf_expression)

    assert result == expected


def test_split(fake_c):

    cf_expression = [",", "A,B,C"]

    expected = 'split(",", "A,B,C")'

    result = expressions.split(fake_c, cf_expression)

    assert result == expected


def test_sub():
    """A Sub in cf is a string that contains references to variables, resources or AWS pseudo parameters."""

    var = hcl2.Variable("foo", {"value": "bar"})
    resources = [var]

    tf_config = Configuration(Path(), resources)

    expected_value = f"test ${{var.{var.name}}} string"

    test_string = f"test ${{{var.name}}} string"

    assert expected_value == expressions.sub_s(tf_config, test_string)


def test_transform(fake_c):

    with pytest.raises(Exception):
        _ = expressions.transform(fake_c, "Any Value")
