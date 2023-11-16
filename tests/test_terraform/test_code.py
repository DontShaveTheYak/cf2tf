from pathlib import Path

import pytest

from cf2tf.terraform.code import (
    SearchManager,
    resource_type_to_name,
    transform_file_name,
    search_manager,
)


@pytest.fixture()
def mock_sm():
    test_docs = Path(__file__) / "./../../data/docs"
    return SearchManager(test_docs.resolve())


@pytest.fixture(scope="session")
def sm():
    return search_manager()


def test_sm_(mock_sm: SearchManager):
    assert len(mock_sm.resources) == 2
    assert len(mock_sm.datas) == 1


sm_find_tests = [
    ("AWS::ApiGatewayV2::Integration", "apigatewayv2_integration.html.markdown"),
    ("AWS::Lambda::Function", "lambda_function.html.markdown"),
    ("AWS::Events::Rule", "cloudwatch_event_rule.html.markdown"),
    ("AWS::Cognito::UserPool", "cognito_user_pool.html.markdown"),
]


@pytest.mark.parametrize("cf_resource, tf_doc_name", sm_find_tests)
def test_sm_find(cf_resource: str, tf_doc_name: str, request):
    sm: SearchManager = request.getfixturevalue("sm")

    result = sm.find(cf_resource)

    assert result.name == tf_doc_name


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
