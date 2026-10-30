from pathlib import Path

import pytest
from git.repo.base import InvalidGitRepositoryError, Repo

from cf2tf.terraform import code
from cf2tf.terraform.code import (
    SearchManager,
    get_code,
    repo_from_existing,
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


@pytest.fixture()
def temp_src(tmp_path, monkeypatch):
    """Point get_code() at a temp dir and stub out the network clone."""
    monkeypatch.setattr(code, "gettempdir", lambda: str(tmp_path))
    repo_path = tmp_path / "terraform_src"

    def fake_clone(url, to_path, *args, **kwargs):
        target = Path(to_path)
        target.mkdir(parents=True, exist_ok=True)
        return Repo.init(target)

    monkeypatch.setattr(code.Repo, "clone_from", staticmethod(fake_clone))
    return repo_path


def test_repo_from_existing_without_dir(tmp_path):
    assert repo_from_existing(tmp_path / "terraform_src") is None


def test_repo_from_existing_with_valid_repo(temp_src):
    Repo.init(temp_src)

    result = repo_from_existing(temp_src)

    assert isinstance(result, Repo)
    assert Path(result.working_tree_dir) == temp_src


def test_get_code_reuses_existing_repo(temp_src, monkeypatch):
    existing = Repo.init(temp_src)

    def fail_clone(*args, **kwargs):
        pytest.fail("clone_from must not be called for an existing valid repo")

    monkeypatch.setattr(code.Repo, "clone_from", staticmethod(fail_clone))

    result = get_code()

    assert result.working_tree_dir == existing.working_tree_dir


def test_get_code_reclones_invalid_git_dir(temp_src, caplog):
    # An interrupted clone can leave a .git dir that is not a valid repository.
    temp_src.mkdir()
    broken_git = temp_src / ".git"
    broken_git.mkdir()
    (broken_git / "HEAD").write_text("broken")

    caplog.set_level("WARNING", logger="cf2tf")
    result = get_code()

    assert Path(result.working_tree_dir, ".git", "HEAD").read_text() != "broken"
    Repo(result.working_tree_dir)  # construction fails if the repo is invalid
    assert Path(result.working_tree_dir) == temp_src
    assert str(temp_src) in caplog.text


def test_get_code_reclones_leftover_without_git_dir(temp_src, caplog):
    # A non-empty directory without a .git dir makes git clone refuse to run.
    temp_src.mkdir()
    (temp_src / "README.md").write_text("partial download")

    caplog.set_level("WARNING", logger="cf2tf")
    result = get_code()

    assert not (temp_src / "README.md").exists()
    assert (temp_src / ".git").is_dir()
    assert Path(result.working_tree_dir) == temp_src
    assert str(temp_src) in caplog.text


def test_repo_from_existing_raises_for_broken_git_dir(temp_src):
    temp_src.mkdir()
    (temp_src / ".git").mkdir()

    with pytest.raises(InvalidGitRepositoryError):
        repo_from_existing(temp_src)
