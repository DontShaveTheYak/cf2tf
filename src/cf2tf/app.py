import logging
from pathlib import Path
from typing import Optional

import click
import click_log

import cf2tf.save
from cf2tf.cloudformation import Template
from cf2tf.convert import TemplateConverter
from cf2tf.terraform import code

log = logging.getLogger("cf2tf")
click_log.basic_config(log)


@click.command()  # type: ignore
@click.version_option()
@click.option("--output", "-o", type=click.Path(exists=False))
@click_log.simple_verbosity_option(log)
@click.argument("template_path", type=click.Path(exists=True))
def cli(output: Optional[str], template_path: str):
    """Convert Cloudformation template into Terraform.

    Args:
        template_path (str): The path to the cloudformation template
    """

    # Need to take this path and parse the cloudformation file
    tmpl_path = Path(template_path)

    # Where/how we will write the results
    output_writer = cf2tf.save.create_writer(output)

    log.info(f"// Converting {tmpl_path.name} to Terraform!")
    log.debug(f"// Template location is {tmpl_path}")

    cf_template = Template.from_yaml(tmpl_path).template

    # Need to get the code from the repo
    search_manger = code.search_manager()

    # Turn Cloudformation template into a Terraform configuration
    config = TemplateConverter(tmpl_path.stem, cf_template, search_manger).convert()

    # Save this configuration to disc
    config.save(output_writer)


if __name__ == "__main__":
    cli()  # type: ignore
