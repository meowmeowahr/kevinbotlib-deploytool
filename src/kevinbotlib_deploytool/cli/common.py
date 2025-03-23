import click
import paramiko
import rich
import rich.panel

from kevinbotlib_deploytool import deployfile
from kevinbotlib_deploytool.cli.spinner import rich_spinner


def confirm_host_key_df(console: rich.console.Console, df: deployfile.DeployTarget, pkey: paramiko.RSAKey):
    with rich_spinner(console, "Beginning transport session"):
        try:
            sock = paramiko.Transport((df.host, df.port))
            sock.connect(username=df.user, pkey=pkey)
            host_key = sock.get_remote_server_key()
            sock.close()
        except Exception as e:
            console.print(rich.panel.Panel(f"[red]Failed to get host key: {e}", title="Host Key Error"))
            raise click.Abort from e

    console.print(
        rich.panel.Panel(f"[yellow]Host key for {df.host}:\n{host_key.get_base64()}", title="Host Key Confirmation")
    )
    if not click.confirm("Do you want to continue connecting?"):
        raise click.Abort


def confirm_host_key(console: rich.console.Console, host: str, user: str, port: int):
    with rich_spinner(console, "Beginning transport session"):
        try:
            sock = paramiko.Transport((host, port))
            sock.connect(username=user)
            host_key = sock.get_remote_server_key()
            sock.close()
        except Exception as e:
            console.print(rich.panel.Panel(f"[red]Failed to get host key: {e}", title="Host Key Error"))
            raise click.Abort from e

    console.print(
        rich.panel.Panel(f"[yellow]Host key for {host}:\n{host_key.get_base64()}", title="Host Key Confirmation")
    )
    if not click.confirm("Do you want to continue connecting?"):
        raise click.Abort
