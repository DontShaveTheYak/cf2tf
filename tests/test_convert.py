from contextlib import nullcontext as no_exception
from pathlib import Path
from typing import Any, Dict

import pytest

import cf2tf.convert as convert
from cf2tf.terraform import code, doc_file
from cf2tf.terraform.blocks import Data, Locals, Output, Block
from cf2tf.terraform.hcl2.primitive import StringType


def tc():
    sm = (
        code.search_manager()
    )  # todo We should not have to checkout the terraform source to run tests

    tc = convert.TemplateConverter("test", {}, sm)

    return tc


def test_parse_attributes():
    arguments, attributes = doc_file.parse_attributes(
        "/tmp/terraform_src/website/docs/r/rds_cluster.html.markdown"
    )


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

    assert converted_args.keys() == expected_args.keys()


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


def test_perform_resource_overrides():
    template = tc()

    fake_params = {"foo": StringType("bar")}

    result = convert.perform_resource_overrides("fake_resource", fake_params, template)

    assert result is fake_params

    params = {"AccessControl": StringType("Private")}

    result = convert.perform_resource_overrides("aws_s3_bucket", params, tc)

    assert result is params

    assert "AccessControl" not in result
    assert "acl" in result
    assert "private" == result["acl"]


def test_perform_global_overrides():
    template = tc()

    params = {"Tags": [{"Key": "foo", "Value": "bar"}]}

    result = convert.perform_global_overrides("aws_s3_bucket", params, template)

    assert result is params

    assert "Tags" not in result
    assert "tags" in result
    assert "foo" in result["tags"]
    assert "bar" == result["tags"]["foo"]
    assert isinstance(result["tags"], dict)


parse_subsection_tests = [
    # (tf_arg_name, cf_props, docs_path, expected_type, expectation)
    (
        "ingress",
        {"FromPort": "foo"},
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        Block,
        no_exception(),
    ),
    (
        "foo",
        {"FromPort": "foo"},
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        Dict,
        no_exception(),
    ),
    (
        "Import",
        [],
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        list,
        no_exception(),
    ),
    (
        "ingress",
        (),
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        Block,
        pytest.raises(TypeError),
    ),
    (
        "ingress",
        [{"FromPort": "foo"}, {"ToPort": "bar"}],
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        list,
        no_exception(),
    ),
    (
        "ingress",
        [
            [{"FromPort": "foo"}, {"ToPort": "bar"}]
        ],  # This is invalid, but shouldn't raise an error
        Path("/tmp/terraform_src/website/docs/r/security_group.html.markdown"),
        list,
        no_exception(),
    ),
]


@pytest.mark.parametrize(
    "tf_arg_name, cf_props, docs_path, expected_type, expectation",
    parse_subsection_tests,
)
def test_parse_subection(
    tf_arg_name: str,
    cf_props: Dict[str, Any],
    docs_path: Path,
    expected_type: Any,
    expectation,
):
    with expectation:
        result = convert.parse_subsection(tf_arg_name, cf_props, docs_path)  # type: ignore
        assert isinstance(result[1], expected_type)
