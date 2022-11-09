from pathlib import Path

import pytest

from cf2tf.terraform.code import (
    SearchManager,
    resource_type_to_name,
    transform_file_name,
)


@pytest.fixture()
def sm():
    test_docs = Path(__file__) / "./../../data/docs"
    return SearchManager(test_docs.resolve())


def test_sm_(sm: SearchManager):
    assert len(sm.resources) == 2
    assert len(sm.datas) == 1


def test_sm_find(sm: SearchManager):
    aws_resource_type = "AWS::ApiGatewayV2::Integration"

    result = sm.find(aws_resource_type)

    assert result.name == "apigatewayv2_integration.markdown"


def test_transform_file_name():

    result = transform_file_name("apigatewayv2_integration.markdown")

    assert result == "apigateway v2 integration"


type_to_name_tests = [
    ("AWS::Ec2::Instance", "ec2 instance"),
    ("AWS::EC2::RouteTable", "ec2 route table"),
    ("AWS::RDS::DBSubnetGroup", "rds db subnet group"),
    ("AWS::S3::Bucket", "s3 bucket"),
]


@pytest.mark.parametrize("input, expected", type_to_name_tests)
def test_resource_type_to_name(input, expected):

    result = resource_type_to_name(input)

    assert result == expected
