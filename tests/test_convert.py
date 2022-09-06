from contextlib import nullcontext as no_exception
from pathlib import Path
from typing import Any, Dict

import cf2tf.convert as convert
import pytest
from cf2tf.terraform import code, doc_file
from cf2tf.terraform.hcl2 import Data, Locals, Output


def tc():
    sm = (
        code.search_manager()
    )  # todo We should not have to checkout the terraform source to run tests

    tc = convert.TemplateConverter({}, sm)

    return tc


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


camel_case_tests = [
    # (input, expected_result)
    (
        "FooBarBazz",
        "Foo Bar Bazz",
    ),
    (
        "Foo2Bar",
        "Foo 2 Bar",
    ),
]


@pytest.mark.parametrize("input, expected", camel_case_tests)
def test_camel_case_split(input: str, expected: str):

    result = convert.camel_case_split(input)

    assert result == expected


convert_resources_tests = [
    # (tc, cf_resource, expectation)
    (tc(), ("InternetGateway", {"Type": "AWS::EC2::InternetGateway"}), no_exception()),
    (tc(), ("InternetGateway", {}), pytest.raises(Exception)),
]


@pytest.mark.parametrize("tc, cf_resource, expectation", convert_resources_tests)
def test_convert_resource(tc: convert.TemplateConverter, cf_resource, expectation):

    with expectation:
        tc.convert_resources([cf_resource])


def test_add_post_block():
    global tc

    template = tc()

    block_a = Locals({})
    block_b = Data(
        "test",
        "test",
    )

    template.add_post_block(block_a)

    assert block_a in template.post_proccess_blocks
    assert len(template.post_proccess_blocks) == 1

    template.add_post_block(block_b)

    assert block_b in template.post_proccess_blocks
    assert len(template.post_proccess_blocks) == 2

    template.add_post_block(block_b)

    assert len(template.post_proccess_blocks) == 2


def test_get_block_by_type():
    global tc

    template = tc()

    block_a = Locals({})
    block_b = Data(
        "test",
        "test",
    )

    template.post_proccess_blocks = [block_a, block_b]

    block = template.get_block_by_type(Locals)

    assert block is not None
    assert block is block_a

    block = template.get_block_by_type(Data)

    assert block is not None
    assert block is block_b

    block = template.get_block_by_type(Output)

    assert block is None
