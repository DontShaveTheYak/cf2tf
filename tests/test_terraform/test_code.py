from pathlib import Path
import pytest
from cf2tf.terraform.code import SearchManager, transform_file_name


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
