from cf2tf.terraform.hcl2._block import Block
from cf2tf.terraform.hcl2.primitive import StringType


def test_no_labels():
    expected = "locals {}"
    block = Block("locals")
    result = block.render()

    assert result == expected


def test_with_labels():
    expected = "resource aws_s3_bucket my_bucket {}"

    block = Block("resource", ("aws_s3_bucket", "my_bucket"))
    result = block.render()

    assert result == expected


def test_with_args():
    expected = 'resource aws_s3_bucket my_bucket {\n  a = "a"\n}'

    block = Block("resource", ("aws_s3_bucket", "my_bucket"), {"a": StringType("a")})
    result = block.render()
    assert result == expected


def test_nested():
    expected = (
        'resource aws_s3_bucket my_bucket {\n  a = "a"\n  test {\n    c = "c"\n  }\n}'
    )

    nested_block = Block("test", arguments={"c": StringType("c")})

    block = Block(
        "resource",
        ("aws_s3_bucket", "my_bucket"),
        {"a": StringType("a"), "b": nested_block},
    )
    result = block.render()

    assert result == expected
