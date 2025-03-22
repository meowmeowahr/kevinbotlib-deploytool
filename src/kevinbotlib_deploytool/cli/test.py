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
    """Test SSH connection to the remote host"""
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

    with rich_spinner("Beginning transport session"):
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


@click.command("test")
@click.option(
    "-d",
    "--directory",
    default=".",
    help="Directory of the Deployfile",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def deployfile_test_command(directory: str):
    """Test the SSH connection"""

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

            # cpu arch
            _, stdout, _ = ssh.exec_command("uname -m")
            cpu_arch = stdout.read().decode().strip()
            console.print(f"[bold magenta]Remote CPU architecture:[/bold magenta] {cpu_arch}")
            if cpu_arch == df.arch:
                console.print(
                    f"[bold green]Remote CPU architecture matches Deployfile:[/bold green] {cpu_arch}=={df.arch}"
                )
            else:
                console.print(
                    f"[bold yellow]Remote CPU architecture does not match Deployfile:[/bold yellow] {cpu_arch}!={df.arch}"
                )

            # glibc version
            _, stdout, _ = ssh.exec_command("ldd --version")
            glibc_version = stdout.read().decode().strip().splitlines()[0].split(" ")[-1]
            console.print(f"[bold magenta]Remote glibc version:[/bold magenta] {glibc_version}")

            if glibc_version == df.glibc_version:
                console.print(
                    f"[bold green]Remote glibc version matches Deployfile:[/bold green] {glibc_version}=={df.glibc_version}"
                )
            else:
                console.print(
                    f"[bold yellow]Remote glibc version does not match Deployfile:[/bold yellow] {glibc_version}!={df.glibc_version}"
                )

            ssh.close()
        except Exception as e:
            console.print(f"[red]SSH connection failed: {e!r}[/red]")
            raise click.Abort from e
