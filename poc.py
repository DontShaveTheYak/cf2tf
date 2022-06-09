from typing import Dict, Any, Union
from cfn_tools import dump_yaml, load_yaml
from pathlib import Path
import yaml


def from_yaml(template_path: Union[str, Path]) -> Dict[str, Any]:
    """Loads a Cloudformation template from file.
    Args:
        template_path (Union[str, Path]): The path to the template.
        imports (Optional[Dict[str, str]], optional): Values this template plans
        to import from other stacks exports. Defaults to None.
    Returns:
        Template: A Template object ready for testing.
    """

    with open(template_path) as f:
        raw = f.read()

    tmp_yaml = load_yaml(raw)

    tmp_str = dump_yaml(tmp_yaml)

    template = yaml.load(tmp_str, Loader=yaml.FullLoader)

    return template


def solve(equation: Dict[str, list]):
    # print(equation)

    key, values = equation.popitem()

    conditional_name = values.pop()


class Output:
    def __init__(self, name: str, values: Dict[str, Any]) -> None:
        # print(values)
        self.name = name
        self.attributes: Dict[str, str] = {}

        self.attributes["description"] = values.get("Description", "")
        self.attributes["value"] = values.get("Value", "")

    def convert(self):

        if isinstance(self.attributes["value"], dict):
            solve(self.attributes["value"])

        newline = "\n"
        return f"""output "{self.name}" {{
{newline.join(f"  {name} = {value}" for name, value in self.attributes.items() if value)}
}}
        """


class Parameter:
    def __init__(self, name: str, values: Dict[str, Any]) -> None:
        # print(values)
        self.name = name
        self.attributes: Dict[str, str] = {}

        self.attributes["description"] = values.get("Description", "")
        self.attributes["default"] = values.get("Default", "")
        self.attributes["type"] = values.get("Type", "").lower()

    def convert(self):

        newline = "\n"
        return f"""variable "{self.name}" {{
{newline.join(f"  {name} = {value}" for name, value in self.attributes.items() if value)}
}}
        """


if __name__ == "__main__":
    template = from_yaml("./log_bucket.yaml")

    parameters: Dict[str, Dict[str, Any]] = template["Parameters"]

    for param_name in parameters.keys():
        param = Parameter(param_name, parameters[param_name])
        print(param.convert())
