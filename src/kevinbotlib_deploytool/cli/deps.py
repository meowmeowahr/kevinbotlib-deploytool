import click

from kevinbotlib_deploytool.cli.deps_local import local
from kevinbotlib_deploytool.cli.deps_remote import remote


@click.group("deps")
def deps_group():
    """Robot dependency management"""


deps_group.add_command(local)
deps_group.add_command(remote)
