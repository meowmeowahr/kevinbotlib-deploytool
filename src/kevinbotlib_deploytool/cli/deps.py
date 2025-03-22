import click

from kevinbotlib_deploytool.cli.deps_local import local


@click.group("deps")
def deps_group():
    """Robot dependency management"""


deps_group.add_command(local)
