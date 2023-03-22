import pytest

from cf2tf.convert import TemplateConverter
from cf2tf.terraform import code


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
