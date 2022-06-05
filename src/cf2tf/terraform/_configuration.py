from __future__ import annotations

import logging
from typing import List

from cf2tf.save import Output
from cf2tf.terraform.hcl2 import Block

log = logging.getLogger("cf2tf")


class Configuration:
    def __init__(self, resources: List[Block]) -> None:
        self.resources = resources

    def save(self, output: Output):

        output.save(self.resources)
