from contextlib import contextmanager
from pathlib import Path

import click
import paramiko
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from kevinbotlib_deploytool import deployfile
from kevinbotlib_deploytool.sshkeys import SSHKeyManager

console = Console()


@contextmanager
def rich_spinner(message: str, success_message: str | None = None):
    with console.status(f"[bold green]{message}...", spinner="dots"):
        try:
            yield
        finally:
            if success_message:
                console.print(f"[bold green]\u2714 {success_message}")


@click.command()
@click.option(
    "-d",
    "--directory",
    default=".",
    help="Directory of the Deployfile",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def remote(directory: str):
    """Retrieve remotely installed dependencies"""

    # Load Deployfile
    df = deployfile.read_deployfile(Path(directory) / "Deployfile.toml")

    key_manager = SSHKeyManager("KevinbotLibDeployTool")
    key_info = key_manager.list_keys()
    if df.name not in key_info:
        console.print(
            f"[red]Key '{df.name}' not found in key manager. Use `kevinbotlib ssh init` to create a new key`[/red]"
        )
        raise click.Abort

    private_key_path, _ = key_info[df.name]

    # Load the private key
    try:
        pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
    except Exception as e:
        console.print(f"[red]Failed to load private key: {e}[/red]")
        raise click.Abort from e

    with rich_spinner("Beginning transport session"):
        try:
            sock = paramiko.Transport((df.host, df.port))
            sock.connect(username=df.user, pkey=pkey)
            host_key = sock.get_remote_server_key()
            sock.close()
        except Exception as e:
            console.print(Panel(f"[red]Failed to get host key: {e}", title="Host Key Error"))
            raise click.Abort from e

    console.print(Panel(f"[yellow]Host key for {df.host}:\n{host_key.get_base64()}", title="Host Key Confirmation"))
    if not click.confirm("Do you want to continue connecting?"):
        raise click.Abort

    with rich_spinner("Fetching data via SSH"):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507 # * this is ok, because the user is asked beforehand
            ssh.connect(hostname=df.host, port=df.port, username=df.user, pkey=pkey, timeout=10)

            # Get installed deps at $HOME/robotenv
            _, stdout, _ = ssh.exec_command("$HOME/robotenv/bin/python3 -m pip list --format=freeze")

            installed_deps = stdout.read().decode("utf-8").strip().split("\n")
            if installed_deps:
                table = Table()
                table.add_column("Package", justify="left", style="cyan")
                table.add_column("Version", justify="right", style="magenta")

                for dep in installed_deps:
                    package, version = dep.split("==")
                    table.add_row(package, version)

                console.print(table)
            else:
                console.print("[red]No dependencies found.[/red]")

            ssh.close()
        except Exception as e:
            console.print(f"[red]SSH connection failed: {e!r}[/red]")
            raise click.Abort from e
