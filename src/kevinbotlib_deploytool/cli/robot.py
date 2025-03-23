import click

from kevinbotlib_deploytool.cli.deploy_code import deploy_code_command
from kevinbotlib_deploytool.cli.robot_delete import delete_robot_command


@click.group("robot")
def robot_group():
    """Robot code management tools"""


robot_group.add_command(delete_robot_command)
robot_group.add_command(deploy_code_command)
