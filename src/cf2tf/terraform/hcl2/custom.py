from typing import Union

from cf2tf.terraform.hcl2.primitive import TerraformType


class LiteralType(str, TerraformType):
    """A literal value like the result of a terraform expression."""

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.render()

    def render(self, _=0):
        return self.value


class CommentType(str, TerraformType):
    """A comment in the Terraform file."""

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return self.render()

    def render(self, indent=0):
        spacing = " " * indent

        text = [f"{spacing}// {line}" for line in self.value.split("\n")]

        return "\n".join(text)


CustomTypes = Union[LiteralType, CommentType]
