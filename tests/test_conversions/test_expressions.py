from cf2tf.conversion import expressions
from cf2tf.terraform import Configuration
from pathlib import Path

import pytest

import cf2tf.terraform.hcl2 as hcl2


@pytest.fixture(scope="session")
def fake_t() -> Configuration:
    return Configuration(Path(), [])


def test_find_in_map():
    pass


def test_get_att(fake_t: Configuration):

    # Test that it will only take a list
    with pytest.raises(TypeError) as e:
        expressions.get_att(fake_t, {})

    assert "Fn::GetAtt - The values must be a List, not dict." in str(e)

    # Test that list size must be two
    with pytest.raises(ValueError) as e:
        expressions.get_att(fake_t, [0])

    assert "values must contain the" in str(e)

    # Test that items must be of type String
    with pytest.raises(TypeError) as e:
        expressions.get_att(fake_t, [0, 0])

    assert "must be String." in str(e)

    # Test with resource not in the configuration
    resource_name = "fake_resource"
    with pytest.raises(KeyError) as e:
        expressions.get_att(fake_t, [resource_name, "name"])

    assert f"{resource_name} not found in template." in str(e)

    # We will create a resource for testing
    test_resource = hcl2.Resource(
        "test_stack",
        "aws_cloudformation_stack",
        {"name": "John Doe", "age": 30},
        ["name", "age"],
        ["name", "age", "outputs"],
    )

    fake_t.resources.append(test_resource)

    fake_attr = "weight"

    # Test with a fake attribute
    with pytest.raises(ValueError) as e:
        expressions.get_att(fake_t, [test_resource.name, fake_attr])

    assert f"Could not convert Cloudformation property {fake_attr}" in str(e)

    # Test with a normal attribute
    test_attr = "age"
    expected_result = f"{test_resource.type}.{test_resource.name}.{test_attr}"
    result = expressions.get_att(fake_t, [test_resource.name, test_attr])

    assert result == expected_result


def test_get_att_nested(fake_t: Configuration):
    """Test that nested cloudformation attributes work."""

    # This resource type is fake to invoke an error
    fake_resource = hcl2.Resource(
        "fake_stack",
        "aws_cloudformation_stack_fake",
        {"name": "John Doe", "age": 30},
        ["name", "age"],
        ["name", "age", "outputs"],
    )

    fake_t.resources.append(fake_resource)

    test_attr = "outputs.something"

    # Test that the fake resource does not work
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_t,
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

    fake_t.resources.append(test_resource)

    # Test attribute nested too far
    nested_attr = f"{test_attr}.toofar"
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_t,
            [test_resource.name, nested_attr],
        )

    assert f"Error parsing nested stack output for {nested_attr}" in str(e)

    # Test normal result

    expected_result = f"{test_resource.type}.{test_resource.name}.{test_attr}"

    result = expressions.get_att(fake_t, [test_resource.name, test_attr])

    assert result == expected_result


def test_get_azs(fake_t: Configuration):

    # Lets test that only valid Cloudformation functions work correctly.
    with pytest.raises(TypeError):
        not_valid_region = []
        _ = expressions.get_azs(fake_t, not_valid_region)

    # test that the return value is correct
    expected = "data.aws_availability_zones.available.names"
    result = expressions.get_azs(fake_t, "Testing")
    assert result == expected

    # Make sure the datasource was added correctly
    assert fake_t.block_lookup("available", block_type=hcl2.Data)


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


@pytest.mark.parametrize("fake_t, expression, expected", join_tests)
def test_join(fake_t, expression, expected):

    result = expressions.join(fake_t, expression)

    assert result == expected


def test_ref():
    """A reference in cloudformation is a direct reference to a variable."""

    var = hcl2.Variable("foo", {"value": "bar"})
    resources = [var]

    tf_config = Configuration(Path(), resources)

    expected_value = f"var.{var.name}"

    assert expected_value == expressions.ref(tf_config, var.name)


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

    var = hcl2.Variable("foo", {"value": "bar"})
    resources = [var]

    tf_config = Configuration(Path(), resources)

    expected_value = f"test ${{var.{var.name}}} string"

    test_string = f"test ${{{var.name}}} string"

    assert expected_value == expressions.sub_s(tf_config, test_string)


def test_transform(fake_t):

    with pytest.raises(Exception):
        _ = expressions.transform(fake_t, "Any Value")
