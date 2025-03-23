import click


@click.group("service")
def service_group():
    """Robot systemd service management tools"""
