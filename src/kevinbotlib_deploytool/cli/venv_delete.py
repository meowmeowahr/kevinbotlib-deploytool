from contextlib import contextmanager
from pathlib import Path
import click
import paramiko

from rich.console import Console
from rich.panel import Panel

from kevinbotlib_deploytool import deployfile
from kevinbotlib_deploytool.sshkeys import SSHKeyManager


console = Console()

@contextmanager
def rich_spinner(message: str, success_message: str | None = None):
    with console.status(f"[bold green]{message}...", spinner="dots") as spinner:
        try:
            yield spinner
        finally:
            if success_message:
                console.print(f"[bold green]\u2714 {success_message}")


@click.command("delete")
@click.option(
    "-d",
    "--df-directory",
    default=".",
    help="Directory of the Deployfile",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def delete_venv_command(df_directory: str):
    """Delete the virtual environment on the remote system."""
    df = deployfile.read_deployfile(Path(df_directory) / "Deployfile.toml")

    key_manager = SSHKeyManager("KevinbotLibDeployTool")
    key_info = key_manager.list_keys()
    if df.name not in key_info:
        console.print(
            f"[red]Key '{df.name}' not found in key manager. Use `kevinbotlib ssh init` to create a new key[/red]"
        )
        raise click.Abort

    private_key_path, _ = key_info[df.name]

    # Load private key
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

    with rich_spinner("Connecting to remote host"):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=df.host, port=df.port, username=df.user, pkey=pkey, timeout=10)

            # Check if venv exists
            check_cmd = f"test -d $HOME/{df.name}/env && echo exists || echo missing"
            _, stdout, _ = ssh.exec_command(check_cmd)
            result = stdout.read().decode().strip()

            if result != "exists":
                console.print(f"[yellow]No virtual environment found at $HOME/{df.name}/env — nothing to delete.[/yellow]")
                return

            # Delete the venv
            console.print(f"[bold red]Deleting virtual environment at $HOME/{df.name}/env...[/bold red]")
            ssh.exec_command(f"rm -rf $HOME/{df.name}/env")
            console.print("[bold green]✔ Virtual environment deleted successfully[/bold green]")

            ssh.close()

        except Exception as e:
            console.print(f"[red]SSH operation failed: {e}[/red]")
            raise click.Abort from e
