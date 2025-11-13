import logging
import sys
from pathlib import Path
from typing import Optional

import click
import click_log
import yaml  # type: ignore
from cfn_tools import dump_yaml, load_yaml  # type: ignore

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
@click.argument("template_path", type=click.Path(exists=True), required=False)
def cli(output: Optional[str], template_path: Optional[str]):
    """Convert Cloudformation template into Terraform.

    Args:
        template_path (str): The path to the cloudformation template.
                            If not provided, reads from STDIN.
    """

    # Where/how we will write the results
    output_writer = cf2tf.save.create_writer(output)

    # Handle input from file or STDIN
    if template_path:
        # Need to take this path and parse the cloudformation file
        tmpl_path = Path(template_path)
        template_name = tmpl_path.stem
        
        log.info(f"// Converting {tmpl_path.name} to Terraform!")
        log.debug(f"// Template location is {tmpl_path}")
        
        cf_template = Template.from_yaml(tmpl_path).template
    else:
        # Read from STDIN
        template_name = "stdin"
        
        log.info("// Converting template from STDIN to Terraform!")
        log.debug("// Reading template from STDIN")
        
        raw = sys.stdin.read()
        tmp_yaml = load_yaml(raw)
        tmp_str = dump_yaml(tmp_yaml)
        template_dict = yaml.load(tmp_str, Loader=yaml.FullLoader)
        
        cf_template = Template(template_dict).template

    # Need to get the code from the repo
    search_manger = code.search_manager()

    # Turn Cloudformation template into a Terraform configuration
    config = TemplateConverter(template_name, cf_template, search_manger).convert()

    # Save this configuration to disc
    config.save(output_writer)


if __name__ == "__main__":
    cli()  # type: ignore
