import click

from kevinbotlib_deploytool.cli.venv_commands import create_venv_command


@click.group()
def venv():
    """Remove virtual environment management"""


venv.add_command(create_venv_command)
