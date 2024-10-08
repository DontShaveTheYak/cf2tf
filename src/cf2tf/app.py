import logging
from pathlib import Path
from typing import Optional

import click
import click_log

import boto3
import json

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
@click.argument("stack_name", type=click.STRING)
def cli(output: Optional[str], stack_name: str):
    """Convert Cloudformation template into Terraform.

    Args:
        template_path (str): The path to the cloudformation template
    """

# Download the CloudFormation template from AWS
    client = boto3.client('cloudformation')
    response = client.get_template(
        StackName=stack_name
    )
    cf_template_json = response['TemplateBody']

    # Save the CloudFormation template to a file in JSON format
    tmpl_path = Path(f"{stack_name}.json")
    with tmpl_path.open('w') as f:
        json.dump(cf_template_json, f, indent=4)


    # Where/how we will write the results
    output_writer = cf2tf.save.create_writer(output)

    log.info(f"// Converting {tmpl_path.name} to Terraform!")
    log.debug(f"// Template location is {tmpl_path}")

    cf_template = Template.from_yaml(tmpl_path).template

    # Need to get the code from the repo
    search_manger = code.search_manager()

    # Turn Cloudformation template into a Terraform configuration
    config = TemplateConverter(tmpl_path.stem, cf_template, search_manger).convert()

    # generate import statements for the resources
    # pull existing resources from the cloudformation stack
    response = client.describe_stack_resources(
        StackName=stack_name
    )
    stack_resources = response['StackResources']

    def find_resource(resource_name):
        for resource in stack_resources:
            if resource['LogicalResourceId'] == resource_name:
                return resource
        return None

    def generate_import_statement(resource_type, resource_name, cf_resource):
        identifier = None
        match resource_type.replace('"',''):
            case "aws_iam_role":
                identifier = cf_resource['PhysicalResourceId']
        if identifier:
            return f"terraform import {resource_type}.{resource_name} '{identifier}'"

    # iterate over all resource objects in the configuration
    for resource in config.resources:
        if resource.block_type != "resource":
            continue
        # get the resource type
        resource_type = resource.type
        # get the resource name
        resource_name = resource.name

        # find the resource in the stack resources
        stack_resource = find_resource(resource.cf_resource_id)
        if stack_resource is None:
            log.warning(f"Resource {resource_name} not found in the stack")
            continue
        # generate the import statement
        import_statement = generate_import_statement(resource_type, resource_name, stack_resource)
        if import_statement is not None:
            # print the import statement
            print(import_statement)

    # Save this configuration to disc
    config.save(output_writer)


if __name__ == "__main__":
    cli()  # type: ignore
