from click.testing import CliRunner
from cf2tf.app import cli

from pathlib import Path

import pytest

template_dir = (Path(__file__).parent / "../data/templates").resolve()


template_names = [template.name for template in template_dir.iterdir()]

tests = [(name) for name in template_names]


@pytest.mark.parametrize("template_name", tests)
def test_templates(template_name: str):
    global template_dir

    runner = CliRunner()

    template_path = template_dir / template_name

    result = runner.invoke(cli, [str(template_path)])

    assert result.exit_code == 0
