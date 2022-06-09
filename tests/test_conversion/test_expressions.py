from contextlib import nullcontext as no_exception
from typing import Any, List

import cf2tf.terraform.code as code
import cf2tf.terraform.hcl2 as hcl2
import pytest
from cf2tf.conversion import expressions
from cf2tf.convert import TemplateConverter


@pytest.fixture(scope="session")
def fake_tc() -> TemplateConverter:

    sm = code.search_manager()

    tc = TemplateConverter({}, sm)

    tc.manifest = {section: [] for section in tc.valid_sections}
    return tc


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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.base64(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.cidr(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.and_(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.equals(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.if_(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.not_(fake_tc, input)

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
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.or_(fake_tc, input)

    assert result == expected_result


condition_tests = [
    # (input, expected_result, expectation)
    ({}, None, pytest.raises(TypeError)),
    ("something", "local.something", no_exception()),
]


@pytest.mark.parametrize("input, expected_result, expectation", condition_tests)
def test_condition(input, expected_result, expectation):

    # fake template that is not used
    fake_tc: TemplateConverter = None

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.condition(fake_tc, input)

    assert result == expected_result


def test_find_in_map(fake_tc: TemplateConverter):

    # Test that it will only take a list
    with pytest.raises(TypeError) as type_error:
        expressions.find_in_map(fake_tc, {})

    assert "Fn::FindInMap - The values must be a List, not dict." in str(type_error)

    # Test that it must contain three items

    with pytest.raises(ValueError) as value_error:
        expressions.find_in_map(fake_tc, [""])

    assert "MapName, TopLevelKey and SecondLevelKey." in str(value_error)

    map_name = "RegionMap"
    top_level_key = "us-east-1"
    second_level_key = "HVM64"

    with pytest.raises(ValueError) as value_error:
        expressions.find_in_map(fake_tc, ["a", "b", "c"])

    assert "Unable to find a locals block" in str(value_error)

    test_args = {map_name: {top_level_key: {second_level_key: "test value"}}}

    locals_block = hcl2.Locals(test_args)

    fake_tc.post_proccess_blocks.append(locals_block)

    # Test for map name
    with pytest.raises(KeyError) as key_error:
        expressions.find_in_map(fake_tc, ["fakeMap", top_level_key, second_level_key])

    assert "Unable to find fakeMap" in str(key_error)

    # Test for top level key
    with pytest.raises(KeyError) as e:
        expressions.find_in_map(fake_tc, [map_name, "fake_cop", second_level_key])

    assert "Unable to find key fake_cop" in str(e)

    # test for second level key
    with pytest.raises(KeyError) as e:
        expressions.find_in_map(fake_tc, [map_name, top_level_key, "fake_second"])

    assert "Unable to find key fake_second" in str(e)

    expected_result = f'local.{map_name}["{top_level_key}"]["{second_level_key}"]'

    result = expressions.find_in_map(
        fake_tc, [map_name, top_level_key, second_level_key]
    )

    assert result == expected_result


def test_get_att(fake_tc: TemplateConverter):

    # Test that it will only take a list
    with pytest.raises(TypeError) as type_error:
        expressions.get_att(fake_tc, {})

    assert "Fn::GetAtt - The values must be a List, not dict." in str(type_error)

    # Test that list size must be two
    with pytest.raises(ValueError) as value_error:
        expressions.get_att(fake_tc, [0])

    assert "values must contain the" in str(value_error)

    # Test that items must be of type String
    with pytest.raises(TypeError) as type_error:
        expressions.get_att(fake_tc, [0, 0])

    assert "must be String." in str(type_error)

    # Test with resource not in the template
    resource_name = "fake_resource"
    with pytest.raises(KeyError) as key_error:
        expressions.get_att(fake_tc, [resource_name, "name"])

    assert f"{resource_name} not found in template." in str(key_error)

    resource_id = "test_stack"
    resource_props = {"Type": "AWS::CloudFormation::Stack"}

    fake_tc.manifest["Resources"] = [(resource_id, resource_props)]

    fake_attr = "weight"

    # Test with a fake attribute
    with pytest.raises(ValueError) as value_error:
        expressions.get_att(fake_tc, ["test_stack", fake_attr])

    assert f"Could not convert Cloudformation property {fake_attr}" in str(value_error)

    # Test with a normal attribute
    test_attr = "template_url"
    expected_result = f"aws_cloudformation_stack.{resource_id}.{test_attr}"
    result = expressions.get_att(fake_tc, [resource_id, test_attr])

    assert result == expected_result


def test_get_att_nested(fake_tc: TemplateConverter):
    """Test that nested cloudformation attributes work."""

    # This resource type is fake to invoke an error
    resource_id = "test_stack"
    resource_props = {"Type": "AWS::S3::Bucket"}

    fake_tc.manifest["Resources"] = [(resource_id, resource_props)]

    # fake_tc.post_proccess_blocks.append(fake_resource)

    # resource_id = "test_stack"
    # resource_props = {"Type": "AWS::CloudFormation::Stack"}

    # fake_tc.manifest["Resources"] = [(resource_id, resource_props)]

    test_attr = "BucketName.something"

    # Test that the fake resource does not work
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_tc,
            [resource_id, test_attr],
        )

    assert f"Unable to solve nested GetAttr {test_attr}" in str(e)

    resource_props["Type"] = "AWS::CloudFormation::Stack"

    fake_tc.manifest["Resources"] = [(resource_id, resource_props)]

    test_attr = "outputs.a"

    # Test attribute nested too far
    nested_attr = f"{test_attr}.toofar"
    with pytest.raises(ValueError) as e:
        expressions.get_att(
            fake_tc,
            [resource_id, nested_attr],
        )

    assert f"Error parsing nested stack output for {nested_attr}" in str(e)

    # Test normal result

    expected_result = f"aws_cloudformation_stack.{resource_id}.{test_attr}"

    result = expressions.get_att(fake_tc, [resource_id, test_attr])

    assert result == expected_result


def test_get_azs(fake_tc: TemplateConverter):

    # Lets test that only valid Cloudformation functions work correctly.
    with pytest.raises(TypeError):
        not_valid_region: List[Any] = []
        _ = expressions.get_azs(fake_tc, not_valid_region)

    # test that the return value is correct
    expected = "data.aws_availability_zones.available.names"
    result = expressions.get_azs(fake_tc, "Testing")
    assert result == expected

    data_blocks = [
        data for data in fake_tc.post_proccess_blocks if isinstance(data, hcl2.Data)
    ]

    # Make sure the datasource was added correctly
    assert len(data_blocks) != 0 and data_blocks[0].name == "available"


join_tests = [
    (None, ["-", "var.something"], 'join("-", var.something)'),
    (None, ["-", ["A", "B", "C"]], 'join("-", [A, B, C])'),
    (None, ["-", ["A", "var.thing", "C"]], 'join("-", [A, var.thing, C])'),
    (
        None,
        ["-", ["A", "aws_resource.name.attr", "C"]],
        'join("-", [A, aws_resource.name.attr, C])',
    ),
]


@pytest.mark.parametrize("fake_tc, expression, expected", join_tests)
def test_join(fake_tc, expression, expected):

    result = expressions.join(fake_tc, expression)

    assert result == expected


ref_tests = [
    # (input, expected_result, expectation, block)
    ({}, None, pytest.raises(TypeError)),
    ("bazz", None, pytest.raises(ValueError)),
    ("foo", "var.foo", no_exception()),
    (
        "bar",
        "aws_s3_bucket.bar.id",
        no_exception(),
    ),
    (
        "AWS::Region",
        "data.aws_region.current.name",
        no_exception(),
    ),
    (
        "AWS::Fake",
        None,
        pytest.raises(ValueError),
    ),
    (
        "AWS::NoValue",
        "null",
        no_exception(),
    ),
    (
        "AWS::URLSuffix",
        "data.aws_partition.current.dns_suffix",
        no_exception(),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation", ref_tests)
def test_ref(input, expected_result, expectation):

    cf_manifest = {
        "Parameters": [("foo", {"a": "a"})],
        "Resources": [("bar", {"Type": "AWS::S3::Bucket"})],
    }

    sm = code.search_manager()

    tc = TemplateConverter({}, sm)
    tc.manifest = cf_manifest

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.ref(tc, input)

    assert result == expected_result


def test_select(fake_tc):

    cf_expression = [0, "var.something"]

    expected = "element(var.something, 0)"

    result = expressions.select(fake_tc, cf_expression)

    assert result == expected

    cf_expression = [0, ['"A"', '"B"', '"C"']]

    expected = 'element(["A", "B", "C"], 0)'

    result = expressions.select(fake_tc, cf_expression)

    assert result == expected


def test_split(fake_tc):

    cf_expression = [",", "A,B,C"]

    expected = 'split(",", "A,B,C")'

    result = expressions.split(fake_tc, cf_expression)

    assert result == expected


sub_tests: Any = [
    # (input, expected_result, expectation, block)
    (
        {},
        None,
        pytest.raises(TypeError),
        None,
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation, block", sub_tests)
def test_sub(input, expected_result, expectation, block):

    cf_manifest = {
        "Parameters": [("foo", {"a": "a"})],
        "Resources": [("bar", {"Type": "AWS::S3::Bucket"})],
    }

    sm = code.search_manager()

    tc = TemplateConverter({}, sm)
    tc.manifest = cf_manifest

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.sub_s(tc, input)

    print(result)

    assert result == expected_result


sub_s_tests = [
    # (input, expected_result, expectation, block)
    (
        "some ${foo}",
        "some ${var.foo}",
        no_exception(),
        hcl2.Variable("foo", {"value": "bar"}),
    ),
    (
        "some ${bar}",
        "some ${aws_s3_bucket.bar.id}",
        no_exception(),
        hcl2.Resource("bar", "foo", {}, [], ["bazz"]),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation, block", sub_s_tests)
def test_sub_s(input, expected_result, expectation, block):

    cf_manifest = {
        "Parameters": [("foo", {"a": "a"})],
        "Resources": [("bar", {"Type": "AWS::S3::Bucket"})],
    }

    sm = code.search_manager()

    tc = TemplateConverter({}, sm)
    tc.manifest = cf_manifest

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.sub_s(tc, input)

    print(result)

    assert result == expected_result


sub_l_tests = [
    # (input, expected_result, expectation, block)
    ([None], None, pytest.raises(ValueError), None),
    ([None] * 3, None, pytest.raises(ValueError), None),
    ([None, None], None, pytest.raises(TypeError), None),
    (
        ["some ${foo} ${bar}", {"bar": "foo.bar.bazz"}],
        "some ${var.foo} ${foo.bar.bazz}",
        no_exception(),
        hcl2.Variable("foo", {"value": "bar"}),
    ),
    (
        ["some ${foo} ${bar}", {"bar": "var.foo"}],
        "some ${var.foo} ${var.foo}",
        no_exception(),
        hcl2.Variable("foo", {"value": "bar"}),
    ),
    pytest.param(
        ["some ${foo} ${bar}", {"bar": "some string"}],
        "some ${var.foo} some string",
        no_exception(),
        hcl2.Variable("foo", {"value": "bar"}),
        marks=pytest.mark.xfail(
            strict=True,
            reason="Strings are valid but shouldnt be used.",
        ),
    ),
]


@pytest.mark.parametrize("input, expected_result, expectation, block", sub_l_tests)
def test_sub_l(input, expected_result, expectation, block):

    cf_manifest = {
        "Parameters": [("foo", {"a": "a"})],
        "Resources": [("bar", {"Type": "AWS::S3::Bucket"})],
    }

    sm = code.search_manager()

    tc = TemplateConverter({}, sm)
    tc.manifest = cf_manifest

    # This is needed for tests that raise an exception
    result = expected_result

    with expectation:
        result = expressions.sub_l(tc, input)

    assert result == expected_result


def test_transform(fake_tc):

    with pytest.raises(Exception):
        _ = expressions.transform(fake_tc, "Any Value")
