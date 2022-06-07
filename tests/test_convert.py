from pathlib import Path
from typing import Any, Dict

import cf2tf.convert as convert
import pytest
from cf2tf.terraform import doc_file, code

# todo We should not have to checkout the terraform source to run tests
code.search_manager()

props_to_args_tests = [
    # (props, expected_args, docs_path)
    (
        {"BucketName": "foo"},
        {"bucket": "foo"},
        Path("/tmp/terraform_src/website/docs/r/s3_bucket.html.markdown"),
    ),
    (
        {"WebsiteConfiguration": {"IndexDocument": "foo"}},
        {"website": {"index_document": "foo"}},
        Path("/tmp/terraform_src/website/docs/r/s3_bucket.html.markdown"),
    ),
]


@pytest.mark.parametrize("props, expected_args, docs_path", props_to_args_tests)
def test_props_to_args(
    props: Dict[str, Any], expected_args: Dict[str, Any], docs_path: Path
):

    valid_arguments, _ = doc_file.parse_attributes(docs_path)

    converted_args = convert.props_to_args(props, valid_arguments, docs_path)

    assert converted_args == expected_args


convert_map_tests = [
    # (input, expected_result)
    (
        {"foo": '"bar"'},
        '{\n  foo = "bar"\n}',
    ),
    (
        {"foo": {"bar": '"baz"'}},
        '{\n  foo = {\n    bar = "baz"\n  }\n}',
    ),
]


@pytest.mark.parametrize("input, expected_result", convert_map_tests)
def test_convert_map(input: Dict[str, Any], expected_result: str):

    actual_result = convert.convert_map(input, 0)

    assert actual_result == expected_result
