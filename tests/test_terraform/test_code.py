from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cf2tf.terraform.code import (
    SearchManager,
    get_code,
    provider_repo_path,
    resource_type_to_name,
    search_manager,
    transform_file_name,
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
    ("AWS::AutoScaling::AutoScalingGroup", "autoscaling_group.html.markdown"),
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
    ("AWS::EC2::RouteTable", "ec2 routetable"),
    ("AWS::RDS::DBSubnetGroup", "rds dbsubnetgroup"),
    ("AWS::S3::Bucket", "s3 bucket"),
]


@pytest.mark.parametrize("input, expected", type_to_name_tests)
def test_resource_type_to_name(input, expected):
    result = resource_type_to_name(input)

    assert result == expected


def test_provider_repo_path_default():
    assert provider_repo_path().name == "terraform_src"
    assert provider_repo_path(None).name == "terraform_src"


def test_provider_repo_path_with_version():
    assert provider_repo_path("v5.31.0").name == "terraform_src_v5.31.0"


@patch("cf2tf.terraform.code.repo_from_existing")
@patch("cf2tf.terraform.code.Repo.clone_from")
def test_get_code_without_version(mock_clone_from, mock_repo_from_existing):
    mock_repo_from_existing.return_value = None
    mock_repo = MagicMock()
    mock_clone_from.return_value = mock_repo

    result = get_code()

    assert result is mock_repo
    mock_clone_from.assert_called_once()
    _, kwargs = mock_clone_from.call_args
    assert kwargs["url"].endswith("terraform-provider-aws.git")
    assert kwargs["depth"] == 1
    assert "branch" not in kwargs


@patch("cf2tf.terraform.code.repo_from_existing")
@patch("cf2tf.terraform.code.Repo.clone_from")
def test_get_code_with_version(mock_clone_from, mock_repo_from_existing):
    mock_repo_from_existing.return_value = None
    mock_repo = MagicMock()
    mock_clone_from.return_value = mock_repo

    result = get_code("v5.0.0")

    assert result is mock_repo
    mock_clone_from.assert_called_once()
    _, kwargs = mock_clone_from.call_args
    assert kwargs["branch"] == "v5.0.0"
    assert kwargs["to_path"].name == "terraform_src_v5.0.0"
