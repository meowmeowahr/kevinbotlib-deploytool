import click
from rich.console import Console
from rich.table import Table

from kevinbotlib_deploytool.packages import LocalPackageManagement


@click.command()
@click.option(
    "-r",
    "--raw",
    is_flag=True,
    help="Disable output formatting",
)
def local(*, raw: bool):
    """Retrieve locally installed dependencies"""
    deps = LocalPackageManagement.get_installed_packages()

    if raw:
        for package in deps:
            click.echo(package)
        return

    console = Console()
    table = Table(show_header=False)
    table.add_column("Package", justify="left", style="cyan")

    for package in deps:
        table.add_row(package)

    console.print(table)
