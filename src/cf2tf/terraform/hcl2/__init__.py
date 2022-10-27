from typing import Union

from cf2tf.terraform.hcl2._block import Block
from cf2tf.terraform.hcl2.complex import ComplexTypes
from cf2tf.terraform.hcl2.custom import CustomTypes
from cf2tf.terraform.hcl2.primitive import PrimitiveTypes

AllTypes = Union[Block, PrimitiveTypes, ComplexTypes, CustomTypes]
