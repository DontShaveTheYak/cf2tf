from click.testing import CliRunner
from cf2tf.app import cli


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    print(result.output)
    assert result.exit_code == 0
    assert "0.0.0" in result.output


def test_cli_aws_provider_version_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--aws-provider-version" in result.output
