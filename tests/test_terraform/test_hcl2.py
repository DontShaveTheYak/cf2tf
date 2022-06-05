from typing import Any, Dict, Tuple

import pytest
from cf2tf.terraform import hcl2

create_subsection_tests = [
    # (input, expected_result)
    (
        ("foo", {"bar": '"baz"'}),
        '  foo {\n    bar = "baz"\n  }\n',
    ),
]


@pytest.mark.parametrize("input, expected_result", create_subsection_tests)
def test_create_subsection(input: Tuple[str, Dict[str, Any]], expected_result: str):

    name, values = input

    actual_result = hcl2.create_subsection(name, values)

    assert actual_result == expected_result
