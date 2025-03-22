from contextlib import contextmanager

import click
import paramiko
from rich.console import Console
from rich.panel import Panel

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


@click.command("test")
@click.option("--host", prompt=True, help="Remote SSH host")
@click.option("--port", default=22, show_default=True, help="Remote SSH port")
@click.option("--user", prompt=True, help="SSH username")
@click.option("--key-name", prompt=True, help="SSH key name to use")
def ssh_test_command(host, port, user, key_name):
    """Test SSH connection to the remote host using a stored SSH key."""
    key_manager = SSHKeyManager("KevinbotLibDeployTool")
    key_info = key_manager.list_keys()
    if key_name not in key_info:
        console.print(f"[red]Key '{key_name}' not found in key manager.[/red]")
        raise click.Abort

    private_key_path, _ = key_info[key_name]

    # Load the private key
    try:
        pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
    except Exception as e:
        console.print(f"[red]Failed to load private key: {e}[/red]")
        raise click.Abort from e

    with rich_spinner("Getting host key"):
        try:
            sock = paramiko.Transport((host, port))
            sock.connect(username=user, pkey=pkey)
            host_key = sock.get_remote_server_key()
            sock.close()
        except Exception as e:
            console.print(Panel(f"[red]Failed to get host key: {e}", title="Host Key Error"))
            raise click.Abort from e

    console.print(Panel(f"[yellow]Host key for {host}:\n{host_key.get_base64()}", title="Host Key Confirmation"))
    if not click.confirm("Do you want to continue connecting?"):
        raise click.Abort

    with rich_spinner("Connecting via SSH", success_message="SSH Connection Test Completed"):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507 # * this is ok, because the user is asked beforehand
            ssh.connect(hostname=host, port=port, username=user, pkey=pkey, timeout=10)

            _, stdout, _ = ssh.exec_command("echo Hello from $(hostname) 👋")
            output = stdout.read().decode().strip()

            console.print(f"[bold green]Success! SSH test output:[/bold green] {output}")
            ssh.close()
        except Exception as e:
            console.print(f"[red]SSH connection failed: {e!r}[/red]")
            raise click.Abort from e
