from typing import TYPE_CHECKING, Callable, Dict

from cf2tf.terraform.hcl2.complex import ListType, MapType
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


def tag_conversion(_tc: "TemplateConverter", params: CFParams) -> CFParams:
    if isinstance(params["Tags"], dict):
        return params

    original_tags: ListType = params["Tags"]  # type: ignore

    first_item = original_tags[0]

    # It's possible that the tags might be one or more
    # conditional statements of LiteralType
    # This wont fix every case, but it should fix most
    # and it's better than nothing
    if not isinstance(first_item, (dict, MapType)):
        del params["Tags"]
        params["tags"] = first_item
        return params

    try:
        new_tags = {LiteralType(tag["Key"]): tag["Value"] for tag in original_tags}

        del params["Tags"]
        params["tags"] = MapType(new_tags)
        return params
    except Exception:
        del params["Tags"]
        params["tags"] = LiteralType(
            f"// Could not convert tags: {original_tags.render(4)}"
        )
        return params

    raise Exception("Could not convert tags")


OVERRIDE_DISPATCH: ResourceOverride = {
    "aws_s3_bucket": {"AccessControl": s3_bucket_acl},
    "aws_s3_bucket_policy": {"PolicyDocument": s3_bucket_policy},
}

GLOBAL_OVERRIDES: ParamOverride = {"Tags": tag_conversion}
