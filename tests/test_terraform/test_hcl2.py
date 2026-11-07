import json

import pytest

from cf2tf.terraform.hcl2.complex import ListType, MapType
from cf2tf.terraform.hcl2.custom import LiteralType
from cf2tf.terraform.hcl2.primitive import StringType


def test_list_render():
    a = StringType("a")
    b = StringType("b")
    c = StringType("c")

    example_value = [a, b, c]

    tf_list = ListType(example_value)

    one_list = tf_list.render()

    assert one_list == json.dumps(example_value, indent=2)

    nested_value = [tf_list, b, c]

    nested_list = ListType(nested_value)

    nested_list.value = nested_value

    two_list = nested_list.render()

    assert two_list == json.dumps([example_value, b, c], indent=2)

    triple_value = [nested_list, b, c]

    triple_nested = ListType(triple_value)

    triple_list = triple_nested.render()

    assert triple_list == json.dumps([[example_value, b, c], b, c], indent=2)


def test_map_render():
    a = StringType("a")
    b = StringType("b")
    c = StringType("c")

    example_value = {
        (a): a,
        (b): b,
        (c): c,
    }

    tf_map = MapType(example_value)

    map_result = tf_map.render()

    assert map_result == json.dumps(example_value, indent=2).replace(":", " =").replace(
        ",", ""
    )

    nested_value = {
        (a): tf_map,
        (b): b,
        (c): c,
    }

    nested_map = MapType(nested_value)

    nested_result = nested_map.render()

    assert nested_result == json.dumps(nested_value, indent=2).replace(
        ":", " ="
    ).replace(",", "")

    triple_value = {
        (a): nested_map,
        (b): b,
        (c): c,
    }

    triple_map = MapType(triple_value)

    triple_result = triple_map.render()

    assert triple_result == json.dumps(triple_value, indent=2).replace(
        ":", " ="
    ).replace(",", "")

    # Need to make blocks take lists? or maps? or just work better
    # with nested blocks


def test_map_renders_invalid_identifier_keys_quoted() -> None:
    """Regression test for https://github.com/DontShaveTheYak/cf2tf/issues/504."""
    # https://github.com/DontShaveTheYak/cf2tf/issues/504
    policy = MapType(
        {
            "ArnEquals": MapType(
                {
                    "ecs:cluster": StringType(
                        "arn:aws:ecs:us-east-1:123456789012:cluster/demo"
                    )
                }
            )
        }
    )

    assert policy.render() == (
        '{\n  ArnEquals = {\n    "ecs:cluster" = '
        '"arn:aws:ecs:us-east-1:123456789012:cluster/demo"\n  }\n}'
    )


@pytest.mark.parametrize(
    "raw_key",
    [
        "ecs:cluster",
        "aws:cloudformation:stack-name",
        "cost-center",
        "dot.key",
        "has space",
        'quote"key',
        "back\\slash",
        "",
    ],
)
def test_map_quotes_keys_that_are_not_valid_identifiers(raw_key: str) -> None:
    """Any static key that is not a valid HCL identifier must be double quoted.

    Args:
        raw_key (str): The CloudFormation map key under test.
    """
    rendered = MapType({raw_key: StringType("value")}).render()

    assert f"{json.dumps(raw_key, ensure_ascii=False)} = " in rendered


def test_map_keeps_valid_identifier_keys_bare() -> None:
    """Keys that are valid HCL identifiers keep rendering without quotes."""
    rendered = MapType(
        {"ArnEquals": StringType("allow"), "simple_key": StringType("allow")}
    ).render()

    assert "ArnEquals = " in rendered
    assert "simple_key = " in rendered
    assert '"ArnEquals"' not in rendered
    assert '"simple_key"' not in rendered


def test_map_keys_inside_lists_are_quoted() -> None:
    """Maps nested inside a ListType renderer must quote their keys too."""
    rendered = ListType([MapType({"ecs:cluster": StringType("arn")})]).render()

    assert '"ecs:cluster" = "arn"' in rendered


def test_literal_static_keys_with_colon_are_quoted() -> None:
    """Static LiteralType keys (used for resource tags) with colons get quoted."""
    rendered = MapType(
        {LiteralType("aws:cloudformation:stack-name"): StringType("demo")}
    ).render()

    assert '"aws:cloudformation:stack-name" = "demo"' in rendered


def test_literal_reference_keys_are_parenthesized() -> None:
    """Terraform reference expressions used as keys are wrapped in parentheses."""
    rendered = MapType({LiteralType("var.tag_key"): StringType("demo")}).render()

    assert "(var.tag_key) = " in rendered


def test_literal_identifier_keys_stay_bare() -> None:
    """Plain identifier LiteralType keys keep their original bare rendering."""
    rendered = MapType({LiteralType("Name"): StringType("demo")}).render()

    assert "Name = " in rendered
