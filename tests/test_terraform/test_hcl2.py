import json

from cf2tf.terraform.hcl2.complex import ListType, MapType
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
