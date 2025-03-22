import click

from kevinbotlib_deploytool.cli.venv_create import create_venv_command


@click.group()
def venv_group():
    """Remote virtual environment management"""


venv_group.add_command(create_venv_command)
