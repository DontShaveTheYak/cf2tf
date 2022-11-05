from typing import TYPE_CHECKING, Callable, Dict

from cf2tf.terraform.hcl2.custom import LiteralType
from cf2tf.terraform.hcl2.primitive import NullType, StringType, TerraformType

if TYPE_CHECKING:
    from cf2tf.convert import TemplateConverter

CFParams = Dict[str, TerraformType]

Override = Callable[["TemplateConverter", CFParams], CFParams]

ParamOverride = Dict[str, Override]

ResourceOverride = Dict[str, ParamOverride]


def s3_bucket_acl(_tc: "TemplateConverter", params: CFParams) -> CFParams:
    access_controls: CFParams = {
        "Private": StringType("private"),
        "PublicRead": StringType("public-read"),
        "PublicReadWrite": StringType("public-read-write"),
        "AuthenticatedRead": StringType("authenticated-read"),
        "LogDeliveryWrite": StringType("log-delivery-write"),
        "BucketOwnerRead": NullType(),
        "BucketOwnerFullControl": NullType(),
        "AwsExecRead": StringType("aws-exec-read"),
    }

    orig_value = params["AccessControl"]

    new_value = access_controls[orig_value]  # type: ignore

    del params["AccessControl"]

    params["acl"] = new_value
    return params


def s3_bucket_policy(_tc: "TemplateConverter", params: CFParams) -> CFParams:

    policy_value = params["PolicyDocument"]

    params["PolicyDocument"] = LiteralType(f"jsonencode({policy_value.render(4)}\n  )")

    return params


OVERRIDE_DISPATCH: ResourceOverride = {
    "aws_s3_bucket": {"AccessControl": s3_bucket_acl},
    "aws_s3_bucket_policy": {"PolicyDocument": s3_bucket_policy},
}
