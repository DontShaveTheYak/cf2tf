import click
from pathlib import Path
from cf2tf.terraform import code, Configuration
from cf2tf.cloudformation import Template
from cf2tf.convert import parse_template

import logging
import click_log

log = logging.getLogger("cf2tf")
click_log.basic_config(log)


@click.command()
@click_log.simple_verbosity_option(log)
@click.argument("template_path", type=click.Path(exists=True))
def cli(template_path: str):
    """Convert Cloudformation template into Terraform.

    Args:
        template_path (str): The path to the cloudformation template
    """

    # Need to take this path and parse the cloudformation file
    tmpl_path = Path(template_path)

    log.info(f"Converting {tmpl_path.name} to Terraform!")
    log.debug(f"Template location is {tmpl_path}")

    cf_template = Template.from_yaml(tmpl_path).template

    # Need to get the code from the repo
    search_manger = code.search_manager()

    # Turn cloudformation resources into unrendered terraform resources
    parsed_blocks = parse_template(cf_template, search_manger)

    # Create a terraform configuration
    config = Configuration("./", parsed_blocks)

    # Save this configuration to disc
    config.save()


if __name__ == "__main__":
    cli()
