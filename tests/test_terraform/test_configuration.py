import pytest

from cf2tf.convert import TemplateConverter
from cf2tf.terraform import code
from cf2tf.terraform.hcl2.primitive import (
    BooleanType,
    NumberType,
    StringType,
)


def tc() -> TemplateConverter:
    sm = code.search_manager()

    tc = TemplateConverter("test", {}, sm)

    tc.manifest = {section: [] for section in tc.valid_sections}
    return tc


resolve_values_tests = [
    # (input, expected_result, tc)
    ("A", "A", tc()),
    (["A", "B", "C"], ["A", "B", "C"], tc()),
    ({"Foo": "Bar"}, {"Foo": "Bar"}, tc()),
]


@pytest.mark.parametrize("input, expected_result, tc", resolve_values_tests)
def test_resolve_values(input, expected_result, tc: TemplateConverter):
    result = tc.resolve_values(input, {})

    assert result == expected_result


resolves_types_tests = [
    # (input, expected_result, rendered_value, tc)
    ("foo", StringType, '"foo"', tc()),
    (123, NumberType, 123, tc()),
    (True, BooleanType, "true", tc()),
    (False, BooleanType, "false", tc()),
]


@pytest.mark.parametrize(
    "input, expected_result, rendered_value, tc", resolves_types_tests
)
def test_resolve_types(input, expected_result, rendered_value, tc: TemplateConverter):
    result = tc.resolve_values(input, {})

    assert isinstance(result, expected_result)
    assert result.render() == rendered_value
